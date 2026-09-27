from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Protocol
from uuid import UUID

from backend.domain.calculator.models import ChatTurn

SHARED_CONVERSATION_RETENTION = timedelta(days=90)


@dataclass(frozen=True, slots=True)
class SharedConversation:
    """A calculator exchange the app shared to improve the product.

    It deliberately carries no installation identifier or IP address.
    """

    conversation_id: UUID
    messages: list[ChatTurn]
    response: Mapping[str, Any] | None
    error: str | None
    created_at: datetime


class SharedConversationRepository(Protocol):
    def save(self, conversation: SharedConversation) -> None: ...
    def delete_older_than(self, cutoff: datetime) -> int: ...
