from __future__ import annotations

import json

import httpx
from pydantic import BaseModel, ValidationError

from backend.adapters.ai.openrouter import openrouter_schema
from backend.adapters.ai.prompts import (
    INTERPRETATION_PROMPT,
    compose_contest_resolution_prompt,
)
from backend.adapters.ai.scenario import history_messages, message_with_scenario
from backend.adapters.ai.schema import QueryRoutingPayload, ResolvedQueryPayload
from backend.domain.calculator.models import ChatTurn, ParsedCastellQuery, ParsedPerformance


class AnthropicChatModel:
    """Chat model adapter for Anthropic's Messages API with structured outputs."""

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str | None = None,
        client: httpx.AsyncClient | None = None,
        effort: str | None = None,
    ) -> None:
        if not api_key or not model:
            raise ValueError("AI_API_KEY i AI_MODEL són obligatoris per a l'adaptador Anthropic")
        self.model = model
        self.effort = effort
        self.base_url = (base_url or "https://api.anthropic.com").rstrip("/")
        self._owns_client = client is None
        self.client = client or httpx.AsyncClient(
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            timeout=30,
        )

    async def interpret(
        self,
        history: list[ChatTurn],
        message: str,
        *,
        scenario: list[ParsedPerformance] | None = None,
    ) -> ParsedCastellQuery:
        raw = await self._request(
            history,
            message_with_scenario(message, scenario),
            instructions=INTERPRETATION_PROMPT,
            schema=QueryRoutingPayload,
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
        *,
        scenario: list[ParsedPerformance] | None = None,
    ) -> ParsedCastellQuery:
        raw = await self._request(
            history,
            message_with_scenario(message, scenario),
            instructions=compose_contest_resolution_prompt(context),
            schema=ResolvedQueryPayload,
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
    ) -> str:
        messages = history_messages(history)
        messages.append({"role": "user", "content": message})
        # Current Claude models reject forced tool use, so the schema constrains the reply
        # itself. Length and range limits are not part of the supported schema subset; the
        # payload models enforce them after parsing.
        output_config: dict = {
            "format": {
                "type": "json_schema",
                "schema": openrouter_schema(schema.model_json_schema()),
            }
        }
        if self.effort is not None:
            output_config["effort"] = self.effort
        response = await self.client.post(
            f"{self.base_url}/v1/messages",
            json={
                "model": self.model,
                # Thinking cannot be disabled on these models and shares this budget.
                "max_tokens": 16_000,
                "system": instructions,
                "messages": messages,
                "output_config": output_config,
            },
        )
        response.raise_for_status()
        payload = response.json()
        stop_reason = payload.get("stop_reason")
        if stop_reason in {"refusal", "max_tokens"}:
            raise ValueError(f"Resposta Anthropic incompleta: {stop_reason}")
        for content_item in payload.get("content", []):
            if content_item.get("type") == "text":
                return content_item.get("text", "")
        raise ValueError("Resposta Anthropic sense text")

    async def close(self) -> None:
        if self._owns_client:
            await self.client.aclose()
