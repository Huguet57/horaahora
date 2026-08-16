from __future__ import annotations

from dataclasses import dataclass

from backend.adapters.content.revista_castells import RevistaCastellsHTMLSource
from backend.adapters.persistence.database import Database
from backend.application.agenda import AgendaService
from backend.application.chat import ChatService
from backend.application.hour_by_hour import HourByHourService
from backend.application.notifications import HourByHourNotificationCoordinator
from backend.composition.providers import (
    build_agenda_repository,
    build_agenda_source,
    build_chat_model,
    build_contest_repository,
    build_database,
    build_hour_by_hour_repository,
    build_notification_gateway,
    build_notification_repository,
    build_push_repository,
    build_rate_limiter,
)
from backend.config import Settings
from backend.domain.calculator.ports import ChatModel
from backend.domain.calculator.scoring import ScoringEngine
from backend.domain.calculator.table import ScoreTable
from backend.domain.content.ports import (
    AgendaRepository,
    AgendaSource,
    HourByHourRepository,
    HourByHourSource,
)
from backend.domain.contest.ports import ContestKnowledgeRepository
from backend.domain.notifications.ports import NotificationRepository, PushSubscriptionRepository
from backend.domain.rate_limit import RateLimiter


@dataclass(slots=True)
class ApplicationOverrides:
    database: Database | None = None
    chat_model: ChatModel | None = None
    contest_repository: ContestKnowledgeRepository | None = None
    hour_by_hour_repository: HourByHourRepository | None = None
    agenda_repository: AgendaRepository | None = None
    rate_limiter: RateLimiter | None = None
    hour_by_hour_source: HourByHourSource | None = None
    agenda_source: AgendaSource | None = None
    push_repository: PushSubscriptionRepository | None = None
    notification_repository: NotificationRepository | None = None
    notification_coordinator: HourByHourNotificationCoordinator | None = None


@dataclass(slots=True)
class ApplicationContainer:
    settings: Settings
    database: Database
    chat_service: ChatService
    hour_by_hour_service: HourByHourService
    agenda_service: AgendaService
    rate_limiter: RateLimiter
    push_repository: PushSubscriptionRepository
    notification_repository: NotificationRepository
    notification_coordinator: HourByHourNotificationCoordinator | None


def build_container(
    settings: Settings, overrides: ApplicationOverrides | None = None
) -> ApplicationContainer:
    overrides = overrides or ApplicationOverrides()
    database = overrides.database or build_database(settings)
    chat_model = overrides.chat_model or build_chat_model(settings)
    contest_repository = overrides.contest_repository or build_contest_repository()
    hour_repository = overrides.hour_by_hour_repository or build_hour_by_hour_repository(database)
    agenda_repository = overrides.agenda_repository or build_agenda_repository(database)
    rate_limiter = overrides.rate_limiter or build_rate_limiter(settings, database)
    notification_repository = overrides.notification_repository or build_notification_repository(
        database
    )
    push_repository = overrides.push_repository or build_push_repository(database)

    hour_source = overrides.hour_by_hour_source
    if hour_source is None and settings.hour_by_hour_source_enabled:
        hour_source = RevistaCastellsHTMLSource(settings.revista_castells_url)
    agenda_source = overrides.agenda_source
    if agenda_source is None:
        agenda_source = build_agenda_source(settings)

    coordinator = overrides.notification_coordinator
    if coordinator is None and hour_source is not None:
        coordinator = HourByHourNotificationCoordinator(
            notification_repository,
            hour_source,
            build_notification_gateway(settings),
            enabled=settings.can_deliver_push,
        )

    return ApplicationContainer(
        settings=settings,
        database=database,
        chat_service=ChatService(
            chat_model,
            contest_repository,
            ScoringEngine(ScoreTable.default()),
        ),
        hour_by_hour_service=HourByHourService(hour_repository, source=None),
        agenda_service=AgendaService(
            agenda_repository,
            agenda_source,
            settings.agenda_refresh_seconds,
            refresh_on_request=settings.agenda_refresh_on_request,
        ),
        rate_limiter=rate_limiter,
        push_repository=push_repository,
        notification_repository=notification_repository,
        notification_coordinator=coordinator,
    )
