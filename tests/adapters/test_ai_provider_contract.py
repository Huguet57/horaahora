import asyncio
import json

import httpx
import pytest

from backend.adapters.ai.anthropic import AnthropicQueryInterpreter
from backend.adapters.ai.openai import OpenAIQueryInterpreter
from backend.adapters.ai.prompts.composer import PROMPT_MODULES, SYSTEM_PROMPT
from backend.adapters.ai.prompts.contest_results import CONTEST_RESULTS_PROMPT
from backend.adapters.ai.prompts.contest_rules import CONTEST_RULES_PROMPT
from backend.adapters.ai.prompts.response_policy import RESPONSE_POLICY_PROMPT
from backend.adapters.ai.schema import ParsedQueryPayload

EXPECTED = {
    "intent": "comparació",
    "actuacions": [
        {"nom": "A", "castells": [{"notació": "5d9f", "resultat": "descarregat"}]},
        {"nom": "B", "castells": [{"notació": "4d9fa", "resultat": "descarregat"}]},
    ],
    "aclariment": None,
    "resposta": None,
}

INFORMATION_EXPECTED = {
    "intent": "informació_concurs",
    "actuacions": [],
    "aclariment": None,
    "resposta": "Els Castellers de Vilafranca van guanyar el Concurs 2024.",
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


def test_system_prompt_composes_stable_modules_in_precedence_order() -> None:
    assert [module.name for module in PROMPT_MODULES] == [
        "calculator",
        "contest_rules",
        "contest_results",
        "response_policy",
    ]
    offsets = [SYSTEM_PROMPT.index(module.content) for module in PROMPT_MODULES]

    assert offsets == sorted(offsets)
    assert "canvis_confirmats_2026" in CONTEST_RULES_PROMPT
    assert "normativa_completa_2024" in CONTEST_RULES_PROMPT
    assert "2026 té prioritat" in RESPONSE_POLICY_PROMPT
    assert "1932" in CONTEST_RESULTS_PROMPT
    assert "2024" in CONTEST_RESULTS_PROMPT
    assert "no es va celebrar" in CONTEST_RESULTS_PROMPT


def test_information_payload_requires_an_answer_and_no_performances() -> None:
    payload = ParsedQueryPayload.model_validate(
        {
            "intent": "informació_concurs",
            "actuacions": [],
            "aclariment": None,
            "resposta": "Els Castellers de Vilafranca van guanyar el Concurs 2024.",
        }
    )

    query = payload.to_domain()

    assert query.intent == "contest_info"
    assert query.answer == "Els Castellers de Vilafranca van guanyar el Concurs 2024."
    assert query.performances == []


def test_information_payload_rejects_missing_answer_or_performances() -> None:
    invalid_payloads = [
        {
            "intent": "informació_concurs",
            "actuacions": [],
            "aclariment": None,
            "resposta": None,
        },
        {
            "intent": "informació_concurs",
            "actuacions": EXPECTED["actuacions"],
            "aclariment": None,
            "resposta": "Resposta",
        },
    ]

    for candidate in invalid_payloads:
        try:
            ParsedQueryPayload.model_validate(candidate)
        except ValueError:
            pass
        else:
            raise AssertionError("La resposta informativa invàlida s'ha acceptat")


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
        "`4d9fp`",
        "`4d9pf`",
        "`4d8p`",
        "`4d7p`",
        "`5d8p`",
        "`3d9fp`",
        "`td8sf`",
        "`t8n`",
        "`d`, `de`, `/`, `x` i `×`",
    ]

    for guidance in expected_guidance:
        assert guidance in SYSTEM_PROMPT


def test_model_prompt_distinguishes_short_net_notations_from_verbal_names() -> None:
    expected_guidance = [
        "`2d8` escrit exactament així",
        "`2d8sf`",
        "`3d9` escrit exactament així",
        "`3d9sf`",
        "`4d9` escrit exactament així",
        "`4d9sf`",
        "`pd7` escrit exactament així",
        "`pd7sf`",
        "la `f` és obligatòria",
        "| «torre/dos de vuit» sense modificadors | `2d8f` |",
        "| «tres de nou» sense modificadors | `3d9f` |",
        "| «quatre de nou» sense modificadors | `4d9f` |",
        "| «pilar de set» sense modificadors | `pd7f` |",
    ]

    for guidance in expected_guidance:
        assert guidance in SYSTEM_PROMPT


def test_openai_adapter_rejects_invalid_structured_output_without_retry() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            json={
                "output": [
                    {
                        "type": "message",
                        "content": [{"type": "output_text", "text": "not-json"}],
                    }
                ]
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    interpreter = OpenAIQueryInterpreter("key", "model", client=client)

    with pytest.raises(ValueError, match="interpretació vàlida"):
        asyncio.run(interpreter.interpret([], "5d9f o 4d9fa?"))
    asyncio.run(client.aclose())

    assert calls == 1


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


def test_anthropic_adapter_rejects_invalid_tool_input_without_retry() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            json={
                "content": [
                    {
                        "type": "tool_use",
                        "name": "interpreta_consulta_castellera",
                        "input": {"intent": "informació_concurs"},
                    }
                ]
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    interpreter = AnthropicQueryInterpreter("key", "model", client=client)

    with pytest.raises(ValueError, match="interpretació vàlida"):
        asyncio.run(interpreter.interpret([], "Qui va guanyar el Concurs 2024?"))
    asyncio.run(client.aclose())

    assert calls == 1


def test_openai_adapter_accepts_contest_information() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {
                                "type": "output_text",
                                "text": json.dumps(INFORMATION_EXPECTED),
                            }
                        ],
                    }
                ]
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    interpreter = OpenAIQueryInterpreter("key", "model", client=client)

    query = asyncio.run(interpreter.interpret([], "Qui va guanyar el Concurs 2024?"))
    asyncio.run(client.aclose())

    assert query.intent == "contest_info"
    assert query.answer == INFORMATION_EXPECTED["resposta"]


def test_openai_adapter_rejects_noncanonical_output_text_field() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"output_text": json.dumps(INFORMATION_EXPECTED)})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    interpreter = OpenAIQueryInterpreter("key", "model", client=client)

    with pytest.raises(ValueError, match="sense output_text"):
        asyncio.run(interpreter.interpret([], "Qui va guanyar el Concurs 2024?"))
    asyncio.run(client.aclose())


def test_anthropic_adapter_accepts_contest_information() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "content": [
                    {
                        "type": "tool_use",
                        "name": "interpreta_consulta_castellera",
                        "input": INFORMATION_EXPECTED,
                    }
                ]
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    interpreter = AnthropicQueryInterpreter("key", "model", client=client)

    query = asyncio.run(interpreter.interpret([], "Qui va guanyar el Concurs 2024?"))
    asyncio.run(client.aclose())

    assert query.intent == "contest_info"
    assert query.answer == INFORMATION_EXPECTED["resposta"]
