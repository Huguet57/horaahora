from pathlib import Path

from backend.adapters.content.cccc_agenda import (
    CCCCAgendaFixtureSource,
    CCCCAgendaHTMLSource,
    CCCCAgendaSnapshotSource,
)
from backend.adapters.contest.snapshot import SnapshotContestKnowledgeRepository
from backend.adapters.notifications.apns import APNsAuthorizationTokenProvider, APNsGateway
from backend.adapters.persistence.agenda_repository import SQLAlchemyAgendaRepository
from backend.adapters.persistence.database import Database
from backend.adapters.persistence.hour_by_hour_repository import SQLAlchemyHourByHourRepository
from backend.adapters.persistence.notification_repository import SQLAlchemyNotificationRepository
from backend.adapters.persistence.push_subscription_repository import (
    SQLAlchemyPushSubscriptionRepository,
)
from backend.adapters.rate_limit.postgres import PostgresRateLimiter
from backend.config import Settings
from backend.domain.calculator.ports import ChatModel
from backend.domain.content.ports import AgendaRepository, AgendaSource, HourByHourRepository
from backend.domain.contest.ports import ContestKnowledgeRepository
from backend.domain.notifications.models import NotificationDisposition, NotificationSendResult
from backend.domain.notifications.ports import NotificationGateway, NotificationRepository
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


def build_hour_by_hour_repository(
    database: Database,
) -> HourByHourRepository:
    return SQLAlchemyHourByHourRepository(database)


def build_agenda_repository(database: Database) -> AgendaRepository:
    return SQLAlchemyAgendaRepository(database)


def build_push_repository(database: Database) -> SQLAlchemyPushSubscriptionRepository:
    return SQLAlchemyPushSubscriptionRepository(database)


def build_notification_repository(database: Database) -> NotificationRepository:
    return SQLAlchemyNotificationRepository(database)


def build_rate_limiter(settings: Settings, database: Database) -> RateLimiter:
    return PostgresRateLimiter(
        database,
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
        return CCCCAgendaFixtureSource(_data_path(settings.cccc_agenda_fixture_path))
    if settings.agenda_source == "cccc_snapshot":
        _require_agenda_authorization(settings, "usar la instantània oficial")
        return CCCCAgendaSnapshotSource(_data_path(settings.cccc_agenda_snapshot_path))
    if settings.agenda_source == "cccc_html":
        _require_agenda_authorization(settings, "activar la font HTML real")
        return CCCCAgendaHTMLSource(settings.cccc_agenda_url)
    raise RuntimeError(f"AGENDA_SOURCE no suportat: {settings.agenda_source}")


def _data_path(configured_path: str) -> Path:
    path = Path(configured_path)
    return path if path.is_absolute() else Path(__file__).parents[2] / path


def _require_agenda_authorization(settings: Settings, action: str) -> None:
    if not settings.cccc_agenda_authorized:
        raise RuntimeError(f"CCCC_AGENDA_AUTHORIZED=true és obligatori per {action}")
