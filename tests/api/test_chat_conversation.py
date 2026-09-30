import pytest

from backend.adapters.ai.schema import QueryRoutingPayload, ResolvedQueryPayload
from backend.domain.calculator.models import ChatTurn, ParsedCastellQuery
from tests.support.application import make_test_client


class ConversationModel:
    def __init__(self, intent: str, reply: str) -> None:
        self.intent = intent
        self.reply = reply

    async def interpret(self, history: list[ChatTurn], message: str) -> ParsedCastellQuery:
        return QueryRoutingPayload.model_validate(
            {
                "intent": self.intent,
                "actuacions": [],
                "aclariment": None,
                "consulta_concurs": None,
                "resposta": self.reply,
            }
        ).to_domain()

    async def resolve_contest(self, *args) -> ParsedCastellQuery:
        raise AssertionError("A conversational reply needs neither retrieval nor another call")


@pytest.mark.parametrize(
    ("intent", "message", "reply", "public_intent"),
    [
        (
            "conversa",
            "Ets una IA?",
            "Sí, soc l'assistent d'IA de la calculadora castellera.",
            "conversation",
        ),
        (
            "conversa",
            "Paso de tu",
            "Ho entenc. Em sap greu que la resposta no t'hagi ajudat.",
            "conversation",
        ),
        (
            "no_compatible",
            "Recomana'm una pel·lícula",
            "Aquest assistent està especialitzat en castells i el Concurs; no en cinema.",
            "unsupported",
        ),
    ],
)
def test_chat_returns_the_models_conversational_reply_without_requesting_a_castell(
    intent: str, message: str, reply: str, public_intent: str
) -> None:
    client = make_test_client(chat_model=ConversationModel(intent, reply))
    response = client.post(
        "/v1/chat",
        json={
            "conversation_id": "3a35386d-f0e4-49cc-86d2-18fac079645c",
            "installation_id": "conversation-test",
            "messages": [{"role": "user", "content": message}],
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "reply": reply,
        "intent": public_intent,
        "performances": [],
        "winner_label": None,
        "warnings": [],
        "ruleset_version": "concurs-2026",
        "needs_clarification": False,
        "presentation": None,
    }


@pytest.mark.parametrize("schema", [QueryRoutingPayload, ResolvedQueryPayload])
@pytest.mark.parametrize("intent", ["conversa", "no_compatible"])
def test_conversational_payload_requires_a_nonblank_answer_and_no_calculation(schema, intent):
    payload = {"intent": intent, "actuacions": [], "aclariment": None, "resposta": "Hola!"}
    if schema is QueryRoutingPayload:
        payload["consulta_concurs"] = None
    assert schema.model_validate(payload).to_domain().answer == "Hola!"

    for invalid in [
        dict(payload, resposta=None),
        dict(payload, resposta="   "),
        dict(payload, aclariment="Quin castell?"),
        dict(payload, actuacions=[{"nom": "A", "castells": []}]),
    ]:
        with pytest.raises(ValueError):
            schema.model_validate(invalid)


def test_routing_does_not_allow_ungrounded_information_in_the_conversation_answer():
    payload = {
        "intent": "consulta",
        "actuacions": [{"nom": "A", "castells": [{"notació": "5d9f", "resultat": "descarregat"}]}],
        "aclariment": None,
        "consulta_concurs": None,
        "resposta": "Una puntuació inventada",
    }
    with pytest.raises(ValueError):
        QueryRoutingPayload.model_validate(payload)
