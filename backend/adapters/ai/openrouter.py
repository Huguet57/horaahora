from __future__ import annotations

import json
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from backend.adapters.ai.prompts import (
    INTERPRETATION_PROMPT,
    compose_contest_resolution_prompt,
)
from backend.adapters.ai.schema import QueryRoutingPayload, ResolvedQueryPayload
from backend.domain.calculator.models import ChatTurn, ParsedCastellQuery

_UNSUPPORTED_SCHEMA_KEYWORDS = {
    "title",
    "description",
    "default",
    "examples",
    "minLength",
    "maxLength",
    "minItems",
    "maxItems",
    "minimum",
    "maximum",
}


def openrouter_schema(value: Any) -> Any:
    """Keep the portable JSON Schema subset shared by OpenRouter providers."""
    if isinstance(value, list):
        return [openrouter_schema(item) for item in value]
    if not isinstance(value, dict):
        return value
    compatible = {}
    for key, item in value.items():
        if key in _UNSUPPORTED_SCHEMA_KEYWORDS:
            continue
        if key == "const":
            compatible["enum"] = [openrouter_schema(item)]
        else:
            compatible[key] = openrouter_schema(item)
    return compatible


class OpenRouterChatModel:
    """Chat model adapter for OpenRouter's stable Chat Completions API."""

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str | None = None,
        client: httpx.AsyncClient | None = None,
        schema_mode: str = "json_schema",
        reasoning_effort: str | None = None,
    ) -> None:
        if not api_key or not model:
            raise ValueError("AI_API_KEY i AI_MODEL són obligatoris per a l'adaptador OpenRouter")
        self.model = model
        self.base_url = (base_url or "https://openrouter.ai/api").rstrip("/")
        if schema_mode not in {"json_schema", "json_object"}:
            raise ValueError(f"Mode d'esquema OpenRouter desconegut: {schema_mode}")
        self.schema_mode = schema_mode
        self.reasoning_effort = reasoning_effort
        self._owns_client = client is None
        self.client = client or httpx.AsyncClient(
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=180,
        )

    async def interpret(self, history: list[ChatTurn], message: str) -> ParsedCastellQuery:
        raw = await self._request(
            history,
            message,
            instructions=INTERPRETATION_PROMPT,
            schema=QueryRoutingPayload,
            schema_name="consulta_castellera",
        )
        try:
            return QueryRoutingPayload.model_validate_json(raw).to_domain()
        except (ValidationError, ValueError, json.JSONDecodeError) as error:
            raise ValueError("El proveïdor no ha retornat una interpretació vàlida") from error

    async def resolve_contest(
        self,
        history: list[ChatTurn],
        message: str,
        context: str,
    ) -> ParsedCastellQuery:
        raw = await self._request(
            history,
            message,
            instructions=compose_contest_resolution_prompt(context),
            schema=ResolvedQueryPayload,
            schema_name="resolucio_concurs",
        )
        try:
            return ResolvedQueryPayload.model_validate_json(raw).to_domain()
        except (ValidationError, ValueError, json.JSONDecodeError) as error:
            raise ValueError("El proveïdor no ha retornat una resolució vàlida") from error

    async def _request(
        self,
        history: list[ChatTurn],
        message: str,
        *,
        instructions: str,
        schema: type[BaseModel],
        schema_name: str,
    ) -> str:
        portable_schema = openrouter_schema(schema.model_json_schema())
        if self.schema_mode == "json_object":
            instructions += (
                "\n\n<esquema_json>\n"
                + json.dumps(portable_schema, ensure_ascii=False, separators=(",", ":"))
                + "\n</esquema_json>\nRespon exclusivament amb un objecte que compleixi l'esquema."
            )
        messages = [{"role": "system", "content": instructions}]
        messages.extend({"role": turn.role, "content": turn.content} for turn in history[-11:])
        messages.append({"role": "user", "content": message})
        if self.schema_mode == "json_schema":
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "strict": True,
                    "schema": portable_schema,
                },
            }
        else:
            response_format = {"type": "json_object"}
        request = {
            "model": self.model,
            "messages": messages,
            "response_format": response_format,
            "provider": {"require_parameters": True},
            "usage": {"include": True},
        }
        if self.reasoning_effort is not None:
            request["reasoning"] = {"effort": self.reasoning_effort}
        response = await self.client.post(
            f"{self.base_url}/v1/chat/completions",
            json=request,
        )
        response.raise_for_status()
        payload = response.json()
        choices = payload.get("choices") or []
        if choices:
            content = (choices[0].get("message") or {}).get("content")
            if isinstance(content, str):
                return content
        raise ValueError("Resposta OpenRouter sense message.content")

    async def close(self) -> None:
        if self._owns_client:
            await self.client.aclose()
