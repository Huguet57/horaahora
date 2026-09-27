from datetime import datetime
from uuid import uuid4

from sqlalchemy import delete
from sqlalchemy.orm import Session

from backend.adapters.persistence.database import Database
from backend.adapters.persistence.models import SharedConversationRecord
from backend.adapters.persistence.repository_support import database_datetime, resolve_engine
from backend.domain.calculator.sharing import SharedConversation


class SQLAlchemySharedConversationRepository:
    def __init__(self, database: Database) -> None:
        self.database, self.engine = resolve_engine(database)

    def save(self, conversation: SharedConversation) -> None:
        with Session(self.engine) as session, session.begin():
            session.add(
                SharedConversationRecord(
                    id=str(uuid4()),
                    conversation_id=str(conversation.conversation_id),
                    messages=[
                        {"role": turn.role, "content": turn.content}
                        for turn in conversation.messages
                    ],
                    response=(
                        dict(conversation.response) if conversation.response is not None else None
                    ),
                    error=conversation.error,
                    created_at=database_datetime(conversation.created_at),
                )
            )

    def delete_older_than(self, cutoff: datetime) -> int:
        with Session(self.engine) as session, session.begin():
            deleted = session.execute(
                delete(SharedConversationRecord).where(
                    SharedConversationRecord.created_at < database_datetime(cutoff)
                )
            ).rowcount
        return deleted or 0
