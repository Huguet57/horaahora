from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.adapters.persistence.database import Database
from backend.adapters.persistence.models import SharedConversationRecord
from backend.adapters.persistence.shared_conversation_repository import (
    SQLAlchemySharedConversationRepository,
)
from backend.domain.calculator.models import ChatTurn
from backend.domain.calculator.sharing import SharedConversation

NOW = datetime(2026, 9, 27, 12, 0, tzinfo=UTC)


def shared(created_at: datetime, *, content: str = "5d9f o 4d9fa?") -> SharedConversation:
    return SharedConversation(
        conversation_id=UUID("3a35386d-f0e4-49cc-86d2-18fac079645c"),
        messages=[ChatTurn(role="user", content=content)],
        response={"reply": "Guanya el 4d9fa.", "intent": "comparison"},
        error=None,
        created_at=created_at,
    )


def test_saves_messages_and_response_as_json() -> None:
    database = Database("sqlite+pysqlite:///:memory:")
    repository = SQLAlchemySharedConversationRepository(database)

    repository.save(shared(NOW))

    with Session(database.engine) as session:
        record = session.scalars(select(SharedConversationRecord)).one()
    assert record.conversation_id == "3a35386d-f0e4-49cc-86d2-18fac079645c"
    assert record.messages == [{"role": "user", "content": "5d9f o 4d9fa?"}]
    assert record.response == {"reply": "Guanya el 4d9fa.", "intent": "comparison"}
    assert record.error is None
    assert len(record.id) == 36


def test_deletes_only_conversations_older_than_the_cutoff() -> None:
    database = Database("sqlite+pysqlite:///:memory:")
    repository = SQLAlchemySharedConversationRepository(database)
    repository.save(shared(NOW - timedelta(days=91), content="antiga"))
    repository.save(shared(NOW - timedelta(days=1), content="recent"))

    deleted = repository.delete_older_than(NOW - timedelta(days=90))

    assert deleted == 1
    with Session(database.engine) as session:
        remaining = session.scalars(select(SharedConversationRecord)).all()
    assert [record.messages[0]["content"] for record in remaining] == ["recent"]
