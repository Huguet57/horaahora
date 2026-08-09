from __future__ import annotations

import httpx
from pydantic import ValidationError

from backend.adapters.ai.prompts import SYSTEM_PROMPT
from backend.adapters.ai.schema import ParsedQueryPayload
from backend.domain.calculator.models import ChatTurn, ParsedCastellQuery


class AnthropicQueryInterpreter:
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
        feedback: str | None = None
        for attempt in range(2):
            raw = await self._request(history, message, feedback)
            try:
                return ParsedQueryPayload.model_validate(raw).to_domain()
            except (ValidationError, ValueError) as error:
                if attempt == 1:
                    raise ValueError(
                        "El proveïdor no ha retornat una interpretació vàlida"
                    ) from error
                feedback = (
                    f"La resposta anterior no complia l'esquema: {error}. Torna-la a generar."
                )
        raise AssertionError("unreachable")

    async def _request(self, history: list[ChatTurn], message: str, feedback: str | None) -> dict:
        messages = [{"role": turn.role, "content": turn.content} for turn in history[-11:]]
        content = message if not feedback else f"{message}\n\n{feedback}"
        messages.append({"role": "user", "content": content})
        response = await self.client.post(
            f"{self.base_url}/v1/messages",
            json={
                "model": self.model,
                "max_tokens": 1_000,
                "system": SYSTEM_PROMPT,
                "messages": messages,
                "tools": [
                    {
                        "name": "interpreta_consulta_castellera",
                        "description": "Retorna la interpretació estructurada de la consulta castellera.",
                        "input_schema": ParsedQueryPayload.model_json_schema(),
                    }
                ],
                "tool_choice": {"type": "tool", "name": "interpreta_consulta_castellera"},
            },
        )
        response.raise_for_status()
        for content_item in response.json().get("content", []):
            if (
                content_item.get("type") == "tool_use"
                and content_item.get("name") == "interpreta_consulta_castellera"
            ):
                return content_item.get("input", {})
        raise ValueError("Resposta Anthropic sense tool_use")

    async def close(self) -> None:
        if self._owns_client:
            await self.client.aclose()
