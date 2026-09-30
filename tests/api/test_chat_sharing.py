from datetime import UTC, datetime, timedelta
from uuid import UUID

import httpx
import pytest

from backend.config import Settings
from backend.domain.calculator.models import ChatTurn, ParsedCastellQuery
from backend.domain.calculator.sharing import SharedConversation
from tests.support.application import make_test_client

CONVERSATION_ID = "3a35386d-f0e4-49cc-86d2-18fac079645c"
INSTALLATION_ID = "installation-that-must-not-be-kept"


class RecordingSharedConversations:
    def __init__(self, *, fails: bool = False) -> None:
        self.saved: list[SharedConversation] = []
        self.cutoffs: list[datetime] = []
        self.fails = fails

    def save(self, conversation: SharedConversation) -> None:
        if self.fails:
            raise RuntimeError("database unavailable")
        self.saved.append(conversation)

    def delete_older_than(self, cutoff: datetime) -> int:
        self.cutoffs.append(cutoff)
        return 2


class InvalidInterpretationChatModel:
    async def interpret(
        self, history: list[ChatTurn], message: str, *, scenario=None
    ) -> ParsedCastellQuery:
        del history, message
        raise ValueError("El proveïdor no ha retornat una interpretació vàlida")

    async def resolve_contest(
        self, history, message, context, *, scenario=None
    ) -> ParsedCastellQuery:
        raise AssertionError("No s'ha de resoldre cap consulta del Concurs")


class UnavailableChatModel:
    async def interpret(
        self, history: list[ChatTurn], message: str, *, scenario=None
    ) -> ParsedCastellQuery:
        del history, message
        raise httpx.ConnectError("provider unavailable")

    async def resolve_contest(
        self, history, message, context, *, scenario=None
    ) -> ParsedCastellQuery:
        raise AssertionError("No s'ha de resoldre cap consulta del Concurs")


def chat_payload(**overrides) -> dict:
    payload = {
        "conversation_id": CONVERSATION_ID,
        "installation_id": INSTALLATION_ID,
        "messages": [
            {"role": "user", "content": "Què val el 5d9f?"},
            {"role": "assistant", "content": "El 5d9f descarregat val 1.975 punts."},
            {"role": "user", "content": "5d9f o 4d9fa?"},
        ],
    }
    payload.update(overrides)
    return payload


def test_shared_conversation_keeps_messages_and_response_without_device_identifiers() -> None:
    shared = RecordingSharedConversations()
    client = make_test_client(shared_conversation_repository=shared)

    response = client.post(
        "/v1/chat",
        json=chat_payload(share_for_improvement=True),
        headers={"X-Installation-ID": INSTALLATION_ID},
    )

    assert response.status_code == 200
    [conversation] = shared.saved
    assert conversation.conversation_id == UUID(CONVERSATION_ID)
    assert conversation.messages == [
        ChatTurn(role="user", content="Què val el 5d9f?"),
        ChatTurn(role="assistant", content="El 5d9f descarregat val 1.975 punts."),
        ChatTurn(role="user", content="5d9f o 4d9fa?"),
    ]
    assert conversation.response == response.json()
    assert conversation.error is None
    assert INSTALLATION_ID not in repr(conversation)
    assert "testclient" not in repr(conversation)


def test_conversations_are_not_kept_unless_the_app_shares_them() -> None:
    # Versions up to 1.3 never send the flag: their users were told nothing is stored.
    shared = RecordingSharedConversations()
    client = make_test_client(shared_conversation_repository=shared)

    assert client.post("/v1/chat", json=chat_payload()).status_code == 200
    assert (
        client.post("/v1/chat", json=chat_payload(share_for_improvement=False)).status_code == 200
    )
    assert shared.saved == []


def test_failed_queries_are_kept_with_the_error_to_improve_the_calculator() -> None:
    shared = RecordingSharedConversations()
    client = make_test_client(
        chat_model=InvalidInterpretationChatModel(),
        shared_conversation_repository=shared,
    )

    response = client.post("/v1/chat", json=chat_payload(share_for_improvement=True))

    assert response.status_code == 400
    [conversation] = shared.saved
    assert conversation.response is None
    assert conversation.error == "El proveïdor no ha retornat una interpretació vàlida"


def test_provider_outages_are_kept_by_error_type_only() -> None:
    shared = RecordingSharedConversations()
    client = make_test_client(
        chat_model=UnavailableChatModel(),
        shared_conversation_repository=shared,
    )

    with pytest.raises(httpx.ConnectError):
        client.post("/v1/chat", json=chat_payload(share_for_improvement=True))

    [conversation] = shared.saved
    assert conversation.response is None
    assert conversation.error == "ConnectError"


def test_sharing_failures_never_break_the_calculator() -> None:
    client = make_test_client(
        shared_conversation_repository=RecordingSharedConversations(fails=True)
    )

    response = client.post("/v1/chat", json=chat_payload(share_for_improvement=True))

    assert response.status_code == 200
    assert response.json()["winner_label"] == "Amb 4d9fa"


def test_maintenance_deletes_shared_conversations_after_ninety_days() -> None:
    shared = RecordingSharedConversations()
    client = make_test_client(
        settings=Settings(
            database_url="sqlite+pysqlite:///:memory:",
            hour_by_hour_source_enabled=False,
            vercel_env="production",
            cron_secret="cron-secret",
        ),
        shared_conversation_repository=shared,
    )

    response = client.get(
        "/internal/cron/maintenance",
        headers={"Authorization": "Bearer cron-secret"},
    )

    assert response.status_code == 200
    assert response.json()["shared_conversations_deleted"] == 2
    [cutoff] = shared.cutoffs
    expected = datetime.now(UTC) - timedelta(days=90)
    assert abs(cutoff - expected) < timedelta(minutes=1)
