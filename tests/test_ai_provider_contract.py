import asyncio
import json

import httpx

from backend.adapters.ai.anthropic import AnthropicQueryInterpreter
from backend.adapters.ai.openai import OpenAIQueryInterpreter
from backend.adapters.ai.schema import ParsedQueryPayload, SYSTEM_PROMPT


EXPECTED = {
    "intent": "comparació",
    "actuacions": [
        {"nom": "A", "castells": [{"notació": "5d9f", "resultat": "descarregat"}]},
        {"nom": "B", "castells": [{"notació": "4d9fa", "resultat": "descarregat"}]},
    ],
    "aclariment": None,
}


def test_openai_schema_is_strict_at_every_object_level() -> None:
    schema = ParsedQueryPayload.model_json_schema()

    def assert_strict_object(node: object) -> None:
        if isinstance(node, dict):
            if node.get("type") == "object":
                assert node.get("additionalProperties") is False
                assert set(node.get("required", [])) == set(node.get("properties", {}))
            for value in node.values():
                assert_strict_object(value)
        elif isinstance(node, list):
            for value in node:
                assert_strict_object(value)

    assert_strict_object(schema)


def test_model_prompt_accepts_natural_catalan_without_inventing_data() -> None:
    assert "errors tipogràfics lleus" in SYSTEM_PROMPT
    assert "denominacions verbals" in SYSTEM_PROMPT
    assert "No inventis" in SYSTEM_PROMPT
    assert "context de la conversa" in SYSTEM_PROMPT
    assert "només demana un aclariment" in SYSTEM_PROMPT


def test_model_prompt_contains_casteller_jargon_and_conventional_omissions() -> None:
    expected_guidance = [
        "«torre» i «dos»",
        "«net», «neta» i «sense folre»",
        "«folre i pilar»",
        "«quatre de 10»",
        "4d10fm",
        "«torre neta»",
        "2d8sf",
        "«dos de nou»",
        "2d9fm",
        "«pilar de set»",
        "pd7f",
        "4d10sm",
        "variants rares",
    ]

    for guidance in expected_guidance:
        assert guidance in SYSTEM_PROMPT


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
            json={
                "content": [
                    {
                        "type": "tool_use",
                        "name": "interpreta_consulta_castellera",
                        "input": EXPECTED,
                    }
                ]
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    interpreter = AnthropicQueryInterpreter("key", "model", client=client)

    query = asyncio.run(interpreter.interpret([], "5d9f o 4d9fa?"))
    asyncio.run(client.aclose())

    assert query.intent == "comparison"
    assert query.performances[1].castells[0].notation == "4d9fa"
