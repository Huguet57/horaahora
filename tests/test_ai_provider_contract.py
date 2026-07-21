import asyncio
import json

import httpx

from backend.adapters.ai.anthropic import AnthropicQueryInterpreter
from backend.adapters.ai.openai import OpenAIQueryInterpreter


EXPECTED = {
    "intent": "comparison",
    "performances": [
        {"label": "A", "castells": [{"notation": "5d9f", "outcome": "unloaded"}]},
        {"label": "B", "castells": [{"notation": "4d9fa", "outcome": "unloaded"}]},
    ],
    "clarification": None,
}


def test_openai_adapter_repairs_invalid_structured_output_once() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        text = "not-json" if calls == 1 else json.dumps(EXPECTED)
        return httpx.Response(
            200,
            json={"output": [{"type": "message", "content": [{"type": "output_text", "text": text}]}]},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    interpreter = OpenAIQueryInterpreter("key", "model", client=client)

    query = asyncio.run(interpreter.interpret([], "5d9f o 4d9fa?"))
    asyncio.run(client.aclose())

    assert calls == 2
    assert [performance.label for performance in query.performances] == ["A", "B"]


def test_anthropic_adapter_uses_same_domain_contract() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"content": [{"type": "tool_use", "name": "parse_castell_query", "input": EXPECTED}]},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    interpreter = AnthropicQueryInterpreter("key", "model", client=client)

    query = asyncio.run(interpreter.interpret([], "5d9f o 4d9fa?"))
    asyncio.run(client.aclose())

    assert query.intent == "comparison"
    assert query.performances[1].castells[0].notation == "4d9fa"
