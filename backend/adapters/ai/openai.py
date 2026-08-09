from __future__ import annotations

import json

import httpx
from pydantic import ValidationError

from backend.adapters.ai.prompts import SYSTEM_PROMPT
from backend.adapters.ai.schema import ParsedQueryPayload
from backend.domain.calculator.models import ChatTurn, ParsedCastellQuery


class OpenAIQueryInterpreter:
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
        feedback: str | None = None
        for attempt in range(2):
            raw = await self._request(history, message, feedback)
            try:
                return ParsedQueryPayload.model_validate_json(raw).to_domain()
            except (ValidationError, ValueError, json.JSONDecodeError) as error:
                if attempt == 1:
                    raise ValueError(
                        "El proveïdor no ha retornat una interpretació vàlida"
                    ) from error
                feedback = (
                    f"La resposta anterior no complia l'esquema: {error}. Torna-la a generar."
                )
        raise AssertionError("unreachable")

    async def _request(self, history: list[ChatTurn], message: str, feedback: str | None) -> str:
        input_messages = [{"role": turn.role, "content": turn.content} for turn in history[-11:]]
        input_messages.append({"role": "user", "content": message})
        if feedback:
            input_messages.append({"role": "user", "content": feedback})
        response = await self.client.post(
            f"{self.base_url}/v1/responses",
            json={
                "model": self.model,
                "instructions": SYSTEM_PROMPT,
                "input": input_messages,
                "store": False,
                "text": {
                    "format": {
                        "type": "json_schema",
                        "name": "consulta_castellera_interpretada",
                        "strict": True,
                        "schema": ParsedQueryPayload.model_json_schema(),
                    }
                },
            },
        )
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload.get("output_text"), str):
            return payload["output_text"]
        for output in payload.get("output", []):
            for content in output.get("content", []):
                if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                    return content["text"]
        raise ValueError("Resposta OpenAI sense output_text")

    async def close(self) -> None:
        if self._owns_client:
            await self.client.aclose()
