from __future__ import annotations

from dataclasses import dataclass

from backend.adapters.persistence.database import Database
from backend.application.chat import ChatService
from backend.application.conversation_sharing import ConversationSharingService
from backend.composition.providers import (
    build_chat_model,
    build_contest_repository,
    build_database,
    build_rate_limiter,
    build_shared_conversation_repository,
)
from backend.config import Settings
from backend.domain.calculator.ports import ChatModel
from backend.domain.calculator.scoring import ScoringEngine
from backend.domain.calculator.sharing import SharedConversationRepository
from backend.domain.calculator.table import ScoreTable
from backend.domain.contest.ports import ContestKnowledgeRepository
from backend.domain.rate_limit import RateLimiter


@dataclass(slots=True)
class ApplicationOverrides:
    database: Database | None = None
    chat_model: ChatModel | None = None
    contest_repository: ContestKnowledgeRepository | None = None
    rate_limiter: RateLimiter | None = None
    shared_conversation_repository: SharedConversationRepository | None = None


@dataclass(slots=True)
class ApplicationContainer:
    settings: Settings
    database: Database
    chat_service: ChatService
    conversation_sharing: ConversationSharingService
    rate_limiter: RateLimiter


def build_container(
    settings: Settings, overrides: ApplicationOverrides | None = None
) -> ApplicationContainer:
    overrides = overrides or ApplicationOverrides()
    database = overrides.database or build_database(settings)
    chat_model = overrides.chat_model or build_chat_model(settings)
    contest_repository = overrides.contest_repository or build_contest_repository()
    rate_limiter = overrides.rate_limiter or build_rate_limiter(settings, database)
    shared_conversation_repository = (
        overrides.shared_conversation_repository or build_shared_conversation_repository(database)
    )

    return ApplicationContainer(
        settings=settings,
        database=database,
        chat_service=ChatService(
            chat_model,
            contest_repository,
            ScoringEngine(ScoreTable.default()),
        ),
        conversation_sharing=ConversationSharingService(shared_conversation_repository),
        rate_limiter=rate_limiter,
    )
