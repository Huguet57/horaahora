from backend.adapters.contest.snapshot import SnapshotContestKnowledgeRepository
from backend.adapters.persistence.database import Database
from backend.adapters.persistence.shared_conversation_repository import (
    SQLAlchemySharedConversationRepository,
)
from backend.adapters.rate_limit.postgres import PostgresRateLimiter
from backend.config import Settings
from backend.domain.calculator.ports import ChatModel
from backend.domain.calculator.sharing import SharedConversationRepository
from backend.domain.contest.ports import ContestKnowledgeRepository
from backend.domain.rate_limit import RateLimiter


def build_chat_model(settings: Settings) -> ChatModel:
    if settings.ai_provider == "openai":
        from backend.adapters.ai.openai import OpenAIChatModel

        return OpenAIChatModel(
            api_key=settings.ai_api_key,
            model=settings.ai_model,
            base_url=settings.ai_base_url or None,
        )
    if settings.ai_provider == "anthropic":
        from backend.adapters.ai.anthropic import AnthropicChatModel

        return AnthropicChatModel(
            api_key=settings.ai_api_key,
            model=settings.ai_model,
            base_url=settings.ai_base_url or None,
            effort="low",
        )
    if settings.ai_provider == "openrouter":
        from backend.adapters.ai.openrouter import OpenRouterChatModel

        return OpenRouterChatModel(
            api_key=settings.ai_api_key,
            model=settings.ai_model,
            base_url=settings.ai_base_url or None,
            reasoning_effort="low",
        )
    raise RuntimeError("AI_PROVIDER ha de ser openai, anthropic o openrouter")


def build_contest_repository() -> ContestKnowledgeRepository:
    return SnapshotContestKnowledgeRepository.default()


def build_database(settings: Settings) -> Database:
    return Database(settings.database_url)


def build_shared_conversation_repository(database: Database) -> SharedConversationRepository:
    return SQLAlchemySharedConversationRepository(database)


def build_rate_limiter(settings: Settings, database: Database) -> RateLimiter:
    return PostgresRateLimiter(
        database,
        hash_secret=settings.rate_limit_hash_secret,
        max_requests=settings.rate_limit_max_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )
