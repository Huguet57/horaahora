import json

import httpx
import pytest

from backend.adapters.ai.openrouter import OpenRouterChatModel
from backend.adapters.ai.schema import QueryRoutingPayload
from backend.domain.calculator.models import ChatTurn, ParsedCastellQuery
from backend.domain.contest.models import ContestKnowledgeQuery
from scripts.smoke_score_ranking_api import CASES, _validate
from tests.support.application import make_test_client


class ContestInformationChatModel:
    async def interpret(self, history: list[ChatTurn], message: str) -> ParsedCastellQuery:
        del history, message
        return ParsedCastellQuery(
            intent="contest_info",
            knowledge_query=ContestKnowledgeQuery(
                source="results",
                years=[2020],
                result_scope="editions",
            ),
        )

    async def resolve_contest(
        self,
        history: list[ChatTurn],
        message: str,
        context: str,
    ) -> ParsedCastellQuery:
        del history, message
        assert "2020" in context
        return ParsedCastellQuery(
            intent="contest_info",
            answer="El Concurs 2020 no es va celebrar per la pandèmia de la COVID-19.",
        )


class ScoreRankingChatModel:
    async def interpret(self, history: list[ChatTurn], message: str) -> ParsedCastellQuery:
        del history, message
        return ParsedCastellQuery(
            intent="contest_info",
            knowledge_query=ContestKnowledgeQuery(
                source="scores",
                score_scope="ranking",
                score_outcome="both",
                ranking_selection="top",
                ranking_limit=2,
            ),
        )

    async def resolve_contest(
        self,
        history: list[ChatTurn],
        message: str,
        context: str,
    ) -> ParsedCastellQuery:
        del history, message
        assert "1 | 3de10sm" in context
        assert "2 | 4de10sm" in context
        assert "3 | 2de10fmp" not in context
        return ParsedCastellQuery(
            intent="contest_info",
            answer="Els dos primers són el 3de10sm i el 4de10sm.",
        )


def test_chat_contract_does_not_expose_provider() -> None:
    response = make_test_client().post(
        "/v1/chat",
        json={
            "conversation_id": "3a35386d-f0e4-49cc-86d2-18fac079645c",
            "installation_id": "test-installation",
            "locale": "ca-ES",
            "ruleset": "concurs-2026",
            "messages": [{"role": "user", "content": "5d9f o 4d9fa?"}],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["winner_label"] == "Amb 4d9fa"
    assert "provider" not in payload
    assert "model" not in payload


def test_chat_contract_supports_contest_information_without_calculation_rows() -> None:
    response = make_test_client(chat_model=ContestInformationChatModel()).post(
        "/v1/chat",
        json={
            "conversation_id": "3a35386d-f0e4-49cc-86d2-18fac079645c",
            "installation_id": "test-installation",
            "locale": "ca-ES",
            "ruleset": "concurs-2026",
            "messages": [{"role": "user", "content": "Què va passar amb el Concurs 2020?"}],
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "reply": "El Concurs 2020 no es va celebrar per la pandèmia de la COVID-19.",
        "intent": "contest_info",
        "performances": [],
        "winner_label": None,
        "warnings": [],
        "ruleset_version": "concurs-2026",
        "needs_clarification": False,
        "presentation": None,
    }


def test_chat_contract_exposes_a_typed_score_ranking_presentation() -> None:
    response = make_test_client(chat_model=ScoreRankingChatModel()).post(
        "/v1/chat",
        json={
            "conversation_id": "3a35386d-f0e4-49cc-86d2-18fac079645c",
            "installation_id": "test-score-presentation",
            "locale": "ca-ES",
            "ruleset": "concurs-2026",
            "messages": [{"role": "user", "content": "Quins són els dos primers?"}],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["presentation"] == {
        "type": "score_ranking",
        "title": "Rànquing de puntuacions 2026",
        "outcome": "both",
        "focus_notation": None,
        "rows": [
            {
                "position": 1,
                "notation": "3de10sm",
                "loaded_points": 6205,
                "unloaded_points": 7475,
            },
            {
                "position": 2,
                "notation": "4de10sm",
                "loaded_points": 5910,
                "unloaded_points": 7120,
            },
        ],
    }


@pytest.mark.parametrize("with_history", [False, True])
def test_partial_scenario_retrieves_scores_through_the_provider_and_chat_api(with_history) -> None:
    case = next(case for case in CASES if case.name == "partial-victory-scenario")
    history = (
        [{"role": role, "content": content} for role, content in case.history]
        if with_history
        else []
    )
    calls = []
    reply = (
        "Sí, en punts podria ser possible, però depèn de la resta de les actuacions. "
        "A la taula 2026, el 3de10fm descarregat val 4.525 punts i el 4de10fm "
        "descarregat en val 4.930. Amb una resta d'actuació computable equivalent, "
        "aquest seria un avantatge. Quins altres castells vols comparar?"
    )

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        calls.append(body)
        assert body["messages"][1:] == [*history, {"role": "user", "content": case.question}]
        if len(calls) == 1:
            payload = {
                "intent": "informació_concurs",
                "actuacions": [],
                "aclariment": None,
                "consulta_concurs": {
                    "font": "puntuacions",
                    "anys": [],
                    "colles": [],
                    "abast_resultats": None,
                    "abast_puntuacions": "rànquing",
                    "resultat_puntuacions": "descarregat",
                    "selecció_rànquing": "per_sobre",
                    "límit_rànquing": None,
                    "castell_rànquing": "3d10fm",
                },
            }
            QueryRoutingPayload.model_validate(payload)
        else:
            context = body["messages"][0]["content"]
            assert "10 | 3de10fm | 4525" in context
            assert "9 | 4de10fm | 4930" in context
            assert "1 | 3de10sm | 7475" in context
            assert "Referència: 3de10fm" in context
            assert "11 | 2de8sf" not in context
            payload = {
                "intent": "informació_concurs",
                "actuacions": [],
                "aclariment": None,
                "resposta": reply,
            }
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": json.dumps(payload)}}],
            },
        )

    model = OpenRouterChatModel(
        "test-key",
        "test-model",
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    with make_test_client(chat_model=model) as client:
        response = client.post(
            "/v1/chat",
            json={
                "conversation_id": "3a35386d-f0e4-49cc-86d2-18fac079645c",
                "installation_id": "partial-scenario",
                "locale": "ca-ES",
                "ruleset": "concurs-2026",
                "messages": [*history, {"role": "user", "content": case.question}],
            },
        )

    assert response.status_code == 200
    assert len(calls) == 2
    result = response.json()
    assert _validate(case, result) == reply
    assert result["needs_clarification"] is False
    assert result["winner_label"] is None
    assert result["performances"] == []
    assert result["presentation"]["focus_notation"] == "3de10fm"
