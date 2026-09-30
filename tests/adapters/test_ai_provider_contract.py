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
from backend.adapters.ai.schema import (
    ContestKnowledgeQueryPayload,
    QueryRoutingPayload,
    ResolvedQueryPayload,
)

CALCULATION_ROUTE = {
    "intent": "comparació",
    "actuacions": [
        {"nom": "A", "castells": [{"notació": "5d9f", "resultat": "descarregat"}]},
        {"nom": "B", "castells": [{"notació": "4d9fa", "resultat": "descarregat"}]},
    ],
    "aclariment": None,
    "consulta_concurs": None,
    "resposta": None,
}

CONTEST_ROUTE = {
    "intent": "informació_concurs",
    "actuacions": [],
    "aclariment": None,
    "resposta": None,
    "consulta_concurs": {
        "font": "resultats",
        "anys": [1998],
        "colles": [],
        "abast_resultats": "classificació",
        "abast_puntuacions": None,
        "resultat_puntuacions": None,
        "selecció_rànquing": None,
        "límit_rànquing": None,
        "castell_rànquing": None,
    },
}

SCORE_RANKING_ROUTE = {
    "intent": "informació_concurs",
    "actuacions": [],
    "aclariment": None,
    "resposta": None,
    "consulta_concurs": {
        "font": "puntuacions",
        "anys": [],
        "colles": [],
        "abast_resultats": None,
        "abast_puntuacions": "rànquing",
        "resultat_puntuacions": "tots_dos",
        "selecció_rànquing": "primers",
        "límit_rànquing": 5,
        "castell_rànquing": None,
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


def _anthropic_output(payload: dict, *, stop_reason: str = "end_turn") -> httpx.Response:
    return httpx.Response(
        200,
        json={
            # Adaptive thinking can put an empty thinking block before the answer.
            "content": [
                {"type": "thinking", "thinking": "", "signature": "sig"},
                {"type": "text", "text": json.dumps(payload)},
            ],
            "stop_reason": stop_reason,
        },
    )


def test_both_model_schemas_are_strict_at_every_object_level() -> None:
    _assert_strict_schema(QueryRoutingPayload)
    _assert_strict_schema(ResolvedQueryPayload)


def test_interpretation_prompt_is_small_and_contains_no_contest_snapshot() -> None:
    assert [module.name for module in INTERPRETATION_MODULES] == [
        "calculator",
        "creator",
        "contest_router",
    ]
    # The prompt states the situation and the casteller jargon; a new rule per reported
    # failure belongs in the evaluation fixtures, not here.
    assert len(INTERPRETATION_PROMPT) < 12_000
    assert "<resultats_anteriors>" not in INTERPRETATION_PROMPT
    assert "<coneixement_normatiu>" not in INTERPRETATION_PROMPT
    assert "16.337 punts" not in INTERPRETATION_PROMPT
    assert "`escenari_vigent`" in INTERPRETATION_PROMPT


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


@pytest.mark.parametrize(
    "field",
    [
        *QueryRoutingPayload.model_fields,
        *ContestKnowledgeQueryPayload.model_fields,
    ],
)
def test_interpretation_prompt_explains_every_routing_field(field: str) -> None:
    # The portable schema carries no descriptions, so the prompt is their only definition.
    assert f"`{field}`" in INTERPRETATION_PROMPT


def test_resolution_prompt_contains_only_the_retrieved_context() -> None:
    prompt = compose_contest_resolution_prompt(
        "<coneixement_recuperat>Concurs 1998 | Joves | 16.337 punts</coneixement_recuperat>"
    )

    assert "Concurs 1998 | Joves | 16.337 punts" in prompt
    assert "Concurs 2024" not in prompt
    assert "2026 té prioritat" in prompt
    assert "la taula 2026 és l'única font de punts" in prompt


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


def test_routing_payload_supports_the_2026_score_ranking() -> None:
    query = QueryRoutingPayload.model_validate(SCORE_RANKING_ROUTE).to_domain()

    assert query.intent == "contest_info"
    assert query.knowledge_query is not None
    assert query.knowledge_query.source == "scores"
    assert query.knowledge_query.score_scope == "ranking"
    assert query.knowledge_query.score_outcome == "both"
    assert query.knowledge_query.ranking_selection == "top"
    assert query.knowledge_query.ranking_limit == 5


@pytest.mark.parametrize(
    "overrides",
    [
        {"abast_puntuacions": None},
        {"resultat_puntuacions": None},
        {"abast_resultats": "classificació"},
        {"anys": [2026]},
        {"colles": ["Vella"]},
        {"selecció_rànquing": None},
        {"límit_rànquing": None},
        {"castell_rànquing": "Pde7sf"},
    ],
)
def test_score_ranking_route_rejects_incompatible_filters(overrides: dict) -> None:
    contest_query = dict(SCORE_RANKING_ROUTE["consulta_concurs"], **overrides)
    invalid = dict(SCORE_RANKING_ROUTE, consulta_concurs=contest_query)

    with pytest.raises(ValueError):
        QueryRoutingPayload.model_validate(invalid)


@pytest.mark.parametrize("selection", ["posició", "veïns"])
def test_score_ranking_route_requires_a_castell_for_relative_selections(selection: str) -> None:
    contest_query = dict(
        SCORE_RANKING_ROUTE["consulta_concurs"],
        selecció_rànquing=selection,
        límit_rànquing=None,
        castell_rànquing=None,
    )
    invalid = dict(SCORE_RANKING_ROUTE, consulta_concurs=contest_query)

    with pytest.raises(ValueError, match="castell"):
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


def test_model_written_text_is_trimmed() -> None:
    # Constrained decoding sometimes closes the string after stray line breaks.
    conversation = dict(INFORMATION_RESOLUTION, intent="conversa", resposta="Hola!\n\n")
    clarification = dict(
        CALCULATION_ROUTE, intent="aclariment", actuacions=[], aclariment="Quin castell?\n"
    )

    assert ResolvedQueryPayload.model_validate(conversation).to_domain().answer == "Hola!"
    assert (
        QueryRoutingPayload.model_validate(clarification).to_domain().clarification
        == "Quin castell?"
    )


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
        return _anthropic_output(CONTEST_ROUTE if len(calls) == 1 else INFORMATION_RESOLUTION)

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
    assert set(calls[0]["output_config"]["format"]["schema"]["properties"]) == set(
        QueryRoutingPayload.model_fields
    )
    assert set(calls[1]["output_config"]["format"]["schema"]["properties"]) == set(
        ResolvedQueryPayload.model_fields
    )


def test_anthropic_requests_structured_output_without_forcing_a_tool() -> None:
    calls: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(json.loads(request.content))
        return _anthropic_output(CALCULATION_ROUTE)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    model = AnthropicChatModel("key", "claude-sonnet-5-5", client=client, effort="low")

    query = asyncio.run(model.interpret([], "5d9f o 4d9fa?"))
    asyncio.run(client.aclose())

    body = calls[0]
    # Claude Sonnet 5.5 rejects forced tool use and thinking cannot be disabled.
    assert "tool_choice" not in body
    assert "tools" not in body
    assert "thinking" not in body
    assert body["output_config"]["effort"] == "low"
    assert body["output_config"]["format"]["type"] == "json_schema"
    # Thinking shares the output budget with the answer.
    assert body["max_tokens"] >= 8_000
    serialized_schema = json.dumps(body["output_config"]["format"]["schema"])
    for unsupported in ("minLength", "maxLength", "maxItems", "minimum", "maximum"):
        assert unsupported not in serialized_schema
    assert query.intent == "comparison"
    assert len(query.performances) == 2


def test_anthropic_omits_effort_unless_configured() -> None:
    calls: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(json.loads(request.content))
        return _anthropic_output(CALCULATION_ROUTE)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    model = AnthropicChatModel("key", "model", client=client)

    asyncio.run(model.interpret([], "5d9f o 4d9fa?"))
    asyncio.run(client.aclose())

    assert "effort" not in calls[0]["output_config"]


def test_anthropic_rejects_invalid_structured_output_without_retry() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return _anthropic_output({"intent": "informació_concurs"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    model = AnthropicChatModel("key", "model", client=client)

    with pytest.raises(ValueError, match="interpretació vàlida"):
        asyncio.run(model.interpret([], "Qui va guanyar el Concurs 2024?"))
    asyncio.run(client.aclose())

    assert calls == 1


@pytest.mark.parametrize("stop_reason", ["refusal", "max_tokens"])
def test_anthropic_rejects_refused_or_truncated_output(stop_reason: str) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return _anthropic_output(CALCULATION_ROUTE, stop_reason=stop_reason)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    model = AnthropicChatModel("key", "model", client=client)

    with pytest.raises(ValueError, match=stop_reason):
        asyncio.run(model.interpret([], "5d9f o 4d9fa?"))
    asyncio.run(client.aclose())


def test_open_alternatives_route_by_explicit_outcome_and_cover_mixed_results():
    from backend.adapters.ai.prompts.contest_router import CONTEST_ROUTER_PROMPT

    assert "mateix resultat" in CONTEST_ROUTER_PROMPT
    assert "resultats diferents" in CONTEST_ROUTER_PROMPT
    assert "`tots_dos` i `complet`" in CONTEST_ROUTER_PROMPT
    assert "`selecció_rànquing=veïns`, `resultat_puntuacions=tots_dos`" not in CONTEST_ROUTER_PROMPT
