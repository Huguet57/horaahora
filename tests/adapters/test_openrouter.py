import asyncio
import json

import httpx
import pytest

from backend.adapters.ai.openrouter import OpenRouterChatModel, openrouter_schema

CALCULATION_ROUTE = {
    "intent": "comparació",
    "actuacions": [
        {"nom": "A", "castells": [{"notació": "5d9f", "resultat": "descarregat"}]},
        {"nom": "B", "castells": [{"notació": "4d9fa", "resultat": "descarregat"}]},
    ],
    "aclariment": None,
    "consulta_concurs": None,
}


def test_openrouter_schema_removes_unsupported_annotations_recursively() -> None:
    schema = {
        "title": "Root",
        "properties": {
            "kind": {"const": "comparison", "description": "route"},
            "score": {"type": "integer", "minimum": 0},
        },
    }

    assert openrouter_schema(schema) == {
        "properties": {
            "kind": {"enum": ["comparison"]},
            "score": {"type": "integer"},
        }
    }


def test_openrouter_uses_chat_completions_with_strict_schema_and_reasoning() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": json.dumps(CALCULATION_ROUTE)}}]},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    model = OpenRouterChatModel(
        "key",
        "google/gemini-3.7-flash",
        client=client,
        reasoning_effort="low",
    )

    result = asyncio.run(model.interpret([], "5d9f o 4d9fa?"))
    asyncio.run(client.aclose())

    body = json.loads(requests[0].content)
    assert result.intent == "comparison"
    assert str(requests[0].url) == "https://openrouter.ai/api/v1/chat/completions"
    assert body["model"] == "google/gemini-3.7-flash"
    assert body["response_format"]["type"] == "json_schema"
    assert body["response_format"]["json_schema"]["strict"] is True
    assert body["provider"] == {"require_parameters": True}
    assert body["reasoning"] == {"effort": "low"}


def test_openrouter_rejects_invalid_structured_output_without_retry() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json={"choices": [{"message": {"content": "not-json"}}]})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    model = OpenRouterChatModel("key", "model", client=client)

    with pytest.raises(ValueError, match="interpretació vàlida"):
        asyncio.run(model.interpret([], "5d9f o 4d9fa?"))
    asyncio.run(client.aclose())

    assert calls == 1
