from backend.domain.calculator.models import ChatTurn, ParsedCastellQuery
from backend.domain.contest.models import ContestKnowledgeQuery
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
    }
