from __future__ import annotations

from pathlib import Path

from backend.adapters.ai.local import RegexQueryInterpreter
from backend.adapters.content.cccc_agenda import (
    CCCCAgendaFixtureSource,
    CCCCAgendaHTMLSource,
    CCCCAgendaSnapshotSource,
)
from backend.adapters.persistence.memory import InMemoryContentRepository
from backend.adapters.rate_limit.memory import InMemoryRateLimiter
from backend.config import Settings
from backend.domain.ports import AgendaSource, ContentRepository, QueryInterpreter, RateLimiter


def build_interpreter(settings: Settings) -> QueryInterpreter:
    if settings.ai_provider == "local":
        return RegexQueryInterpreter()
    if settings.ai_provider == "openai":
        from backend.adapters.ai.openai import OpenAIQueryInterpreter

        return OpenAIQueryInterpreter(
            api_key=settings.ai_api_key,
            model=settings.ai_model,
            base_url=settings.ai_base_url or None,
        )
    if settings.ai_provider == "anthropic":
        from backend.adapters.ai.anthropic import AnthropicQueryInterpreter

        return AnthropicQueryInterpreter(
            api_key=settings.ai_api_key,
            model=settings.ai_model,
            base_url=settings.ai_base_url or None,
        )
    raise RuntimeError(f"AI_PROVIDER no suportat: {settings.ai_provider}")


def build_content_repository(settings: Settings) -> ContentRepository:
    try:
        from backend.adapters.persistence.sqlalchemy import SQLAlchemyContentRepository

        return SQLAlchemyContentRepository(settings.database_url)
    except ImportError:
        return InMemoryContentRepository()


def build_rate_limiter(settings: Settings) -> RateLimiter:
    if settings.redis_url:
        try:
            from backend.adapters.rate_limit.redis import RedisRateLimiter

            return RedisRateLimiter(
                settings.redis_url,
                settings.rate_limit_max_requests,
                settings.rate_limit_window_seconds,
            )
        except ImportError:
            pass
    return InMemoryRateLimiter(
        settings.rate_limit_max_requests,
        settings.rate_limit_window_seconds,
    )


def build_agenda_source(settings: Settings) -> AgendaSource | None:
    if settings.agenda_source == "disabled":
        return None
    if settings.agenda_source == "fixture":
        fixture_path = Path(settings.cccc_agenda_fixture_path)
        if not fixture_path.is_absolute():
            fixture_path = Path(__file__).parents[1] / fixture_path
        return CCCCAgendaFixtureSource(fixture_path)
    if settings.agenda_source == "cccc_snapshot":
        if not settings.cccc_agenda_authorized:
            raise RuntimeError(
                "CCCC_AGENDA_AUTHORIZED=true és obligatori per usar la instantània oficial"
            )
        snapshot_path = Path(settings.cccc_agenda_snapshot_path)
        if not snapshot_path.is_absolute():
            snapshot_path = Path(__file__).parents[1] / snapshot_path
        return CCCCAgendaSnapshotSource(snapshot_path)
    if settings.agenda_source == "cccc_html":
        if not settings.cccc_agenda_authorized:
            raise RuntimeError(
                "CCCC_AGENDA_AUTHORIZED=true és obligatori per activar la font HTML real"
            )
        return CCCCAgendaHTMLSource(settings.cccc_agenda_url)
    raise RuntimeError(f"AGENDA_SOURCE no suportat: {settings.agenda_source}")
