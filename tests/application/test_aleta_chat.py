import asyncio
import json

import httpx

from backend.adapters.ai.openrouter import OpenRouterChatModel
from backend.application.chat import ChatService
from backend.domain.calculator.models import ChatTurn
from backend.domain.calculator.scoring import ScoringEngine
from backend.domain.calculator.table import ScoreTable
from tests.api.test_chat_conversation import ConversationModel
from tests.support.application import make_test_client

ALETA_REPLY = "Aleta permet confirmar assistència i consultar pinyes. https://aleta.castellera.cat"


class UnexpectedDependency:
    def __getattr__(self, name: str):
        raise AssertionError(f"Una resposta d'Aleta no necessita {name}")


class UnexpectedScoring(ScoringEngine):
    """Its normalizer may tidy notation in the message, but nothing gets scored."""

    def calculate(self, query):
        raise AssertionError("Una resposta d'Aleta no necessita cap càlcul")


def test_aleta_uses_the_product_context_without_retrieval_or_scoring() -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        calls.append(body)
        instructions = body["messages"][0]["content"]
        assert '<coneixement_aleta verificat="2026-09-30">' in instructions
        assert "https://aleta.castellera.cat/descarrega" in instructions
        assert "aletacastellera@gmail.com" in instructions
        assert "75 €/mes" in instructions
        assert "`conversa`" in instructions
        payload = {
            "intent": "conversa",
            "actuacions": [],
            "aclariment": None,
            "consulta_concurs": None,
            "resposta": ALETA_REPLY,
        }
        return httpx.Response(
            200, json={"choices": [{"message": {"content": json.dumps(payload)}}]}
        )

    async def respond():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            model = OpenRouterChatModel("key", "model", client=client)
            service = ChatService(
                model, UnexpectedDependency(), UnexpectedScoring(ScoreTable.default())
            )
            return await service.respond([ChatTurn("user", "Què és l'Aleta?")])

    result = asyncio.run(respond())
    assert len(calls) == 1
    assert result.reply == ALETA_REPLY
    assert result.intent == "conversation"
    assert result.performances == []
    assert result.presentation is None
    assert not result.needs_clarification


def test_chat_api_returns_aleta_information_without_calculation_rows() -> None:
    response = make_test_client(chat_model=ConversationModel("conversa", ALETA_REPLY)).post(
        "/v1/chat",
        json={
            "conversation_id": "3a35386d-f0e4-49cc-86d2-18fac079645c",
            "installation_id": "test-aleta-information",
            "messages": [{"role": "user", "content": "Què és l'Aleta?"}],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["reply"] == ALETA_REPLY
    assert payload["intent"] == "conversation"
    assert payload["performances"] == []
    assert payload["winner_label"] is None
    assert payload["presentation"] is None
    assert not payload["needs_clarification"]
