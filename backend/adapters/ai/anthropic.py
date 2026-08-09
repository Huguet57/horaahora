from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from backend.adapters.ai.prompts import (
    INTERPRETATION_PROMPT,
    compose_contest_resolution_prompt,
)
from backend.adapters.ai.schema import QueryRoutingPayload, ResolvedQueryPayload
from backend.domain.calculator.models import ChatTurn, ParsedCastellQuery


class AnthropicChatModel:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not api_key or not model:
            raise ValueError("AI_API_KEY i AI_MODEL són obligatoris per a l'adaptador Anthropic")
        self.model = model
        self.base_url = (base_url or "https://api.anthropic.com").rstrip("/")
        self._owns_client = client is None
        self.client = client or httpx.AsyncClient(
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            timeout=30,
        )

    async def interpret(self, history: list[ChatTurn], message: str) -> ParsedCastellQuery:
        raw = await self._request(
            history,
            message,
            instructions=INTERPRETATION_PROMPT,
            schema=QueryRoutingPayload,
            tool_name="interpreta_consulta_castellera",
            description="Encamina una consulta castellera o extreu-ne les actuacions.",
        )
        try:
            return QueryRoutingPayload.model_validate(raw).to_domain()
        except (ValidationError, ValueError) as error:
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
            tool_name="resol_concurs",
            description="Resol la consulta amb el coneixement local recuperat.",
        )
        try:
            return ResolvedQueryPayload.model_validate(raw).to_domain()
        except (ValidationError, ValueError) as error:
            raise ValueError("El proveïdor no ha retornat una resolució vàlida") from error

    async def _request(
        self,
        history: list[ChatTurn],
        message: str,
        *,
        instructions: str,
        schema: type[BaseModel],
        tool_name: str,
        description: str,
    ) -> dict[str, Any]:
        messages = [{"role": turn.role, "content": turn.content} for turn in history[-11:]]
        messages.append({"role": "user", "content": message})
        response = await self.client.post(
            f"{self.base_url}/v1/messages",
            json={
                "model": self.model,
                "max_tokens": 1_000,
                "system": instructions,
                "messages": messages,
                "tools": [
                    {
                        "name": tool_name,
                        "description": description,
                        "input_schema": schema.model_json_schema(),
                    }
                ],
                "tool_choice": {"type": "tool", "name": tool_name},
            },
        )
        response.raise_for_status()
        for content_item in response.json().get("content", []):
            if content_item.get("type") == "tool_use" and content_item.get("name") == tool_name:
                return content_item.get("input", {})
        raise ValueError("Resposta Anthropic sense tool_use")

    async def close(self) -> None:
        if self._owns_client:
            await self.client.aclose()
