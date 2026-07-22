from __future__ import annotations

from pathlib import Path

from backend.adapters.ai.local import RegexQueryInterpreter
from backend.adapters.content.cccc_agenda import (
    CCCCAgendaFixtureSource,
    CCCCAgendaHTMLSource,
    CCCCAgendaSnapshotSource,
)
from backend.adapters.notifications.apns import (
    APNsAuthorizationTokenProvider,
    APNsGateway,
)
from backend.adapters.persistence.database import Database
from backend.adapters.persistence.notifications import SQLAlchemyNotificationRepository
from backend.adapters.persistence.sqlalchemy import SQLAlchemyContentRepository
from backend.adapters.rate_limit.postgres import PostgresRateLimiter
from backend.config import Settings
from backend.domain.ports import (
    AgendaSource,
    ContentRepository,
    NotificationGateway,
    NotificationRepository,
    QueryInterpreter,
    RateLimiter,
)
from backend.domain.models import NotificationDisposition, NotificationSendResult


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


def build_database(settings: Settings) -> Database:
    return Database(settings.database_url)


def build_content_repository(settings: Settings, database: Database | None = None) -> ContentRepository:
    return SQLAlchemyContentRepository(database or build_database(settings))


def build_notification_repository(
    settings: Settings, database: Database | None = None
) -> NotificationRepository:
    return SQLAlchemyNotificationRepository(database or build_database(settings))


def build_rate_limiter(
    settings: Settings, database: Database | None = None
) -> RateLimiter:
    return PostgresRateLimiter(
        database or build_database(settings),
        hash_secret=settings.rate_limit_hash_secret,
        max_requests=settings.rate_limit_max_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )


def build_notification_gateway(settings: Settings) -> NotificationGateway:
    if not settings.can_deliver_push:
        return _PushDisabledGateway()
    missing = [
        name
        for name, value in (
            ("APNS_KEY_P8", settings.apns_key_p8),
            ("APNS_KEY_ID", settings.apns_key_id),
            ("APNS_TEAM_ID", settings.apns_team_id),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(f"Falten secrets APNs: {', '.join(missing)}")
    return APNsGateway(
        authorization_token=APNsAuthorizationTokenProvider(
            key_p8=settings.apns_key_p8,
            key_id=settings.apns_key_id,
            team_id=settings.apns_team_id,
        )
    )


class _PushDisabledGateway:
    def send(self, _delivery) -> NotificationSendResult:
        return NotificationSendResult(NotificationDisposition.FAILED, "PushDisabled")


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
