import logging
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from backend.domain.calculator.models import ChatTurn
from backend.domain.calculator.sharing import (
    SHARED_CONVERSATION_RETENTION,
    SharedConversation,
    SharedConversationRepository,
)

logger = logging.getLogger(__name__)


class ConversationSharingService:
    def __init__(
        self,
        repository: SharedConversationRepository,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.repository = repository
        self.clock = clock or (lambda: datetime.now(UTC))

    def record(
        self,
        conversation_id: UUID,
        messages: list[ChatTurn],
        *,
        response: Mapping[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        try:
            self.repository.save(
                SharedConversation(
                    conversation_id=conversation_id,
                    messages=messages,
                    response=response,
                    error=error,
                    created_at=self.clock(),
                )
            )
        except Exception as failure:
            # Sharing must never break the calculator, and logs never carry conversations.
            logger.warning("shared_conversation_not_saved error=%s", type(failure).__name__)

    def purge_expired(self) -> int:
        return self.repository.delete_older_than(self.clock() - SHARED_CONVERSATION_RETENTION)
