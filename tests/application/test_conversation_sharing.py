import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from backend.application.conversation_sharing import ConversationSharingService
from backend.domain.calculator.models import ChatTurn
from backend.domain.calculator.sharing import (
    SHARED_CONVERSATION_RETENTION,
    SharedConversation,
)

NOW = datetime(2026, 9, 27, 12, 0, tzinfo=UTC)
CONVERSATION_ID = UUID("3a35386d-f0e4-49cc-86d2-18fac079645c")


class RecordingRepository:
    def __init__(self, *, fails: bool = False) -> None:
        self.saved: list[SharedConversation] = []
        self.cutoffs: list[datetime] = []
        self.fails = fails

    def save(self, conversation: SharedConversation) -> None:
        if self.fails:
            raise RuntimeError("could not store 'Vilafranca 4d10fm'")
        self.saved.append(conversation)

    def delete_older_than(self, cutoff: datetime) -> int:
        self.cutoffs.append(cutoff)
        return 5


def test_recording_timestamps_the_shared_conversation() -> None:
    repository = RecordingRepository()
    service = ConversationSharingService(repository, clock=lambda: NOW)

    service.record(
        CONVERSATION_ID,
        [ChatTurn(role="user", content="Vilafranca 4d10fm")],
        response={"reply": "Val 3.345 punts."},
    )

    assert repository.saved == [
        SharedConversation(
            conversation_id=CONVERSATION_ID,
            messages=[ChatTurn(role="user", content="Vilafranca 4d10fm")],
            response={"reply": "Val 3.345 punts."},
            error=None,
            created_at=NOW,
        )
    ]


def test_storage_errors_are_logged_without_the_conversation(caplog) -> None:
    service = ConversationSharingService(RecordingRepository(fails=True), clock=lambda: NOW)

    with caplog.at_level(logging.WARNING):
        service.record(
            CONVERSATION_ID,
            [ChatTurn(role="user", content="Vilafranca 4d10fm")],
            error="ConnectError",
        )

    assert "shared_conversation_not_saved" in caplog.text
    assert "RuntimeError" in caplog.text
    assert "Vilafranca" not in caplog.text


def test_purge_removes_conversations_older_than_the_retention_period() -> None:
    repository = RecordingRepository()
    service = ConversationSharingService(repository, clock=lambda: NOW)

    assert service.purge_expired() == 5
    assert repository.cutoffs == [NOW - SHARED_CONVERSATION_RETENTION]
    assert SHARED_CONVERSATION_RETENTION == timedelta(days=90)
