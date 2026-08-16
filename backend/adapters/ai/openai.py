from __future__ import annotations

import json

import httpx
from pydantic import BaseModel, ValidationError

from backend.adapters.ai.prompts import (
    INTERPRETATION_PROMPT,
    compose_contest_resolution_prompt,
)
from backend.adapters.ai.schema import QueryRoutingPayload, ResolvedQueryPayload
from backend.domain.calculator.models import ChatTurn, ParsedCastellQuery


class OpenAIChatModel:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not api_key or not model:
            raise ValueError("AI_API_KEY i AI_MODEL són obligatoris per a l'adaptador OpenAI")
        self.model = model
        self.base_url = (base_url or "https://api.openai.com").rstrip("/")
        self._owns_client = client is None
        self.client = client or httpx.AsyncClient(
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30,
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
        input_messages = [{"role": turn.role, "content": turn.content} for turn in history[-11:]]
        input_messages.append({"role": "user", "content": message})
        response = await self.client.post(
            f"{self.base_url}/v1/responses",
            json={
                "model": self.model,
                "instructions": instructions,
                "input": input_messages,
                "store": False,
                "text": {
                    "format": {
                        "type": "json_schema",
                        "name": schema_name,
                        "strict": True,
                        "schema": schema.model_json_schema(),
                    }
                },
            },
        )
        response.raise_for_status()
        payload = response.json()
        for output in payload.get("output", []):
            for content in output.get("content", []):
                if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                    return content["text"]
        raise ValueError("Resposta OpenAI sense output_text")

    async def close(self) -> None:
        if self._owns_client:
            await self.client.aclose()
