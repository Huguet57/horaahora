import asyncio
import json

import httpx
import pytest

from backend.adapters.ai.anthropic import AnthropicChatModel
from backend.adapters.ai.openai import OpenAIChatModel
from backend.adapters.ai.prompts.composer import (
    INTERPRETATION_MODULES,
    INTERPRETATION_PROMPT,
    compose_contest_resolution_prompt,
)
from backend.adapters.ai.schema import QueryRoutingPayload, ResolvedQueryPayload

CALCULATION_ROUTE = {
    "intent": "comparació",
    "actuacions": [
        {"nom": "A", "castells": [{"notació": "5d9f", "resultat": "descarregat"}]},
        {"nom": "B", "castells": [{"notació": "4d9fa", "resultat": "descarregat"}]},
    ],
    "aclariment": None,
    "consulta_concurs": None,
}

CONTEST_ROUTE = {
    "intent": "informació_concurs",
    "actuacions": [],
    "aclariment": None,
    "consulta_concurs": {
        "font": "resultats",
        "anys": [1998],
        "colles": [],
        "abast_resultats": "classificació",
    },
}

INFORMATION_RESOLUTION = {
    "intent": "informació_concurs",
    "actuacions": [],
    "aclariment": None,
    "resposta": "La Colla Joves Xiquets de Valls va quedar quarta amb 16.337 punts.",
}

RECALCULATION_RESOLUTION = {
    "intent": "total",
    "actuacions": [
        {
            "nom": "C. de Vilafranca",
            "castells": [
                {"notació": "3d10fm", "resultat": "descarregat"},
                {"notació": "9d9f", "resultat": "intent"},
                {"notació": "4d9fa", "resultat": "carregat"},
                {"notació": "9d9f", "resultat": "carregat"},
                {"notació": "4d10fm", "resultat": "carregat"},
            ],
        }
    ],
    "aclariment": None,
    "resposta": None,
}


def _assert_strict_schema(model: type[QueryRoutingPayload] | type[ResolvedQueryPayload]) -> None:
    schema = model.model_json_schema()

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


def _openai_output(payload: dict) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "output": [
                {
                    "type": "message",
                    "content": [{"type": "output_text", "text": json.dumps(payload)}],
                }
            ]
        },
    )


def _anthropic_output(payload: dict, tool_name: str) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "content": [
                {
                    "type": "tool_use",
                    "name": tool_name,
                    "input": payload,
                }
            ]
        },
    )


def test_both_model_schemas_are_strict_at_every_object_level() -> None:
    _assert_strict_schema(QueryRoutingPayload)
    _assert_strict_schema(ResolvedQueryPayload)


def test_interpretation_prompt_is_small_and_contains_no_contest_snapshot() -> None:
    assert [module.name for module in INTERPRETATION_MODULES] == [
        "calculator",
        "contest_router",
    ]
    assert len(INTERPRETATION_PROMPT) < 15_000
    assert "<resultats_anteriors>" not in INTERPRETATION_PROMPT
    assert "<coneixement_normatiu>" not in INTERPRETATION_PROMPT
    assert "16.337 punts" not in INTERPRETATION_PROMPT
    assert "errors tipogràfics lleus" in INTERPRETATION_PROMPT
    assert "context de la conversa" in INTERPRETATION_PROMPT


@pytest.mark.parametrize(
    "guidance",
    [
        "«torre» i «dos»",
        "«net», «neta» i «sense folre»",
        "`4d9fp`",
        "`td8sf`",
        "`d`, `de`, `/`, `x` i `×`",
        "`2d8` escrit exactament així",
        "| «torre/dos de vuit» sense modificadors | `2d8f` |",
        "variants rares",
    ],
)
def test_interpretation_prompt_keeps_casteller_notation_rules(guidance: str) -> None:
    assert guidance in INTERPRETATION_PROMPT


def test_resolution_prompt_contains_only_the_retrieved_context() -> None:
    prompt = compose_contest_resolution_prompt(
        "<coneixement_recuperat>Concurs 1998 | Joves | 16.337 punts</coneixement_recuperat>"
    )

    assert "Concurs 1998 | Joves | 16.337 punts" in prompt
    assert "Concurs 2024" not in prompt
    assert "2026 té prioritat" in prompt


def test_routing_payload_requires_a_structured_contest_query() -> None:
    query = QueryRoutingPayload.model_validate(CONTEST_ROUTE).to_domain()

    assert query.intent == "contest_info"
    assert query.knowledge_query is not None
    assert query.knowledge_query.source == "results"
    assert query.knowledge_query.years == [1998]
    assert query.answer is None

    invalid = dict(CONTEST_ROUTE, consulta_concurs=None)
    with pytest.raises(ValueError, match="consulta_concurs"):
        QueryRoutingPayload.model_validate(invalid)


def test_resolution_payload_keeps_information_and_calculation_exclusive() -> None:
    information = ResolvedQueryPayload.model_validate(INFORMATION_RESOLUTION).to_domain()
    recalculation = ResolvedQueryPayload.model_validate(RECALCULATION_RESOLUTION).to_domain()

    assert information.intent == "contest_info"
    assert information.answer == INFORMATION_RESOLUTION["resposta"]
    assert information.performances == []
    assert recalculation.intent == "total"
    assert recalculation.answer is None
    assert len(recalculation.performances[0].castells) == 5


def test_openai_uses_routing_then_dynamic_resolution_prompts() -> None:
    calls: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        calls.append(body)
        return _openai_output(CONTEST_ROUTE if len(calls) == 1 else INFORMATION_RESOLUTION)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    model = OpenAIChatModel("key", "model", client=client)

    route = asyncio.run(model.interpret([], "Qui va quedar quart el 1998?"))
    resolution = asyncio.run(
        model.resolve_contest(
            [],
            "Qui va quedar quart el 1998?",
            "<coneixement_recuperat>Joves | 16.337 punts</coneixement_recuperat>",
        )
    )
    asyncio.run(client.aclose())

    assert route.knowledge_query is not None
    assert resolution.answer == INFORMATION_RESOLUTION["resposta"]
    assert calls[0]["instructions"] == INTERPRETATION_PROMPT
    assert "Joves | 16.337 punts" in calls[1]["instructions"]
    assert "Joves | 16.337 punts" not in calls[0]["instructions"]
    assert calls[0]["text"]["format"]["name"] == "consulta_castellera"
    assert calls[1]["text"]["format"]["name"] == "resolucio_concurs"


def test_openai_rejects_invalid_structured_output_without_retry() -> None:
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
    model = OpenAIChatModel("key", "model", client=client)

    with pytest.raises(ValueError, match="interpretació vàlida"):
        asyncio.run(model.interpret([], "5d9f o 4d9fa?"))
    asyncio.run(client.aclose())

    assert calls == 1


def test_openai_rejects_noncanonical_output_text_field() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"output_text": json.dumps(CALCULATION_ROUTE)})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    model = OpenAIChatModel("key", "model", client=client)

    with pytest.raises(ValueError, match="sense output_text"):
        asyncio.run(model.interpret([], "5d9f o 4d9fa?"))
    asyncio.run(client.aclose())


def test_anthropic_uses_the_same_two_phase_contract() -> None:
    calls: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        calls.append(body)
        if len(calls) == 1:
            return _anthropic_output(CONTEST_ROUTE, "interpreta_consulta_castellera")
        return _anthropic_output(INFORMATION_RESOLUTION, "resol_concurs")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    model = AnthropicChatModel("key", "model", client=client)

    route = asyncio.run(model.interpret([], "Qui va quedar quart el 1998?"))
    resolution = asyncio.run(
        model.resolve_contest(
            [],
            "Qui va quedar quart el 1998?",
            "<coneixement_recuperat>Joves | 16.337 punts</coneixement_recuperat>",
        )
    )
    asyncio.run(client.aclose())

    assert route.knowledge_query is not None
    assert resolution.intent == "contest_info"
    assert calls[0]["system"] == INTERPRETATION_PROMPT
    assert "Joves | 16.337 punts" in calls[1]["system"]
    assert calls[0]["tool_choice"]["name"] == "interpreta_consulta_castellera"
    assert calls[1]["tool_choice"]["name"] == "resol_concurs"


def test_anthropic_rejects_invalid_tool_input_without_retry() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return _anthropic_output({"intent": "informació_concurs"}, "interpreta_consulta_castellera")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    model = AnthropicChatModel("key", "model", client=client)

    with pytest.raises(ValueError, match="interpretació vàlida"):
        asyncio.run(model.interpret([], "Qui va guanyar el Concurs 2024?"))
    asyncio.run(client.aclose())

    assert calls == 1
