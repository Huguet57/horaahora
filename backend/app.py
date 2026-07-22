from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Annotated, Literal

from fastapi import FastAPI, Header, HTTPException, Query, Request, Response, status

from backend.adapters.content.revista_castells import RevistaCastellsHTMLSource
from backend.api.schemas import (
    AgendaPageSchema,
    CastellEventSchema,
    ChatRequestSchema,
    ChatResponseSchema,
    HourByHourItemSchema,
    HourByHourPageSchema,
    PushSubscriptionRequestSchema,
)
from backend.application.notifications import HourByHourNotificationCoordinator
from backend.application.services import AgendaService, ChatService, HourByHourService
from backend.bootstrap import (
    build_agenda_source,
    build_content_repository,
    build_database,
    build_interpreter,
    build_notification_gateway,
    build_notification_repository,
    build_rate_limiter,
)
from backend.adapters.persistence.database import Database
from backend.config import Settings
from backend.domain.models import ChatTurn, PushSubscriptionRegistration
from backend.domain.ports import (
    AgendaSource,
    ContentRepository,
    HourByHourSource,
    NotificationRepository,
    PushSubscriptionRepository,
    QueryInterpreter,
    RateLimiter,
)
from backend.domain.scoring import ScoreTable, ScoringEngine
from backend.privacy import router as privacy_router


@dataclass(slots=True)
class ApplicationContainer:
    database: Database
    chat_service: ChatService
    hour_by_hour_service: HourByHourService
    agenda_service: AgendaService
    rate_limiter: RateLimiter
    push_repository: PushSubscriptionRepository
    notification_repository: NotificationRepository
    notification_coordinator: HourByHourNotificationCoordinator | None


def create_app(
    settings: Settings | None = None,
    interpreter: QueryInterpreter | None = None,
    content_repository: ContentRepository | None = None,
    rate_limiter: RateLimiter | None = None,
    hour_by_hour_source: HourByHourSource | None = None,
    agenda_source: AgendaSource | None = None,
    database: Database | None = None,
    push_repository: PushSubscriptionRepository | None = None,
    notification_repository: NotificationRepository | None = None,
    notification_coordinator: HourByHourNotificationCoordinator | None = None,
) -> FastAPI:
    settings = settings or Settings.from_env()
    database = database or build_database(settings)
    interpreter = interpreter or build_interpreter(settings)
    content_repository = content_repository or build_content_repository(settings, database)
    rate_limiter = rate_limiter or build_rate_limiter(settings, database)
    notification_repository = notification_repository or build_notification_repository(
        settings, database
    )
    push_repository = push_repository or notification_repository
    if hour_by_hour_source is None and settings.hour_by_hour_source_enabled:
        hour_by_hour_source = RevistaCastellsHTMLSource(settings.revista_castells_url)
    if agenda_source is None:
        agenda_source = build_agenda_source(settings)
    if notification_coordinator is None and hour_by_hour_source is not None:
        notification_coordinator = HourByHourNotificationCoordinator(
            notification_repository,
            hour_by_hour_source,
            build_notification_gateway(settings),
            enabled=settings.can_deliver_push,
        )

    container = ApplicationContainer(
        database=database,
        chat_service=ChatService(interpreter, ScoringEngine(ScoreTable.default())),
        hour_by_hour_service=HourByHourService(
            content_repository,
            hour_by_hour_source,
            settings.hour_by_hour_refresh_seconds,
        ),
        agenda_service=AgendaService(
            content_repository,
            agenda_source,
            settings.agenda_refresh_seconds,
            refresh_on_request=settings.agenda_refresh_on_request,
        ),
        rate_limiter=rate_limiter,
        push_repository=push_repository,
        notification_repository=notification_repository,
        notification_coordinator=notification_coordinator,
    )
    app = FastAPI(
        title="Castells Super-app API",
        version="1.0.0",
        description="Contractes neutrals per a contingut casteller i càlcul de puntuacions.",
    )
    app.state.container = container
    app.include_router(privacy_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready")
    def readiness() -> dict[str, str]:
        if not container.database.is_ready():
            raise HTTPException(status_code=503, detail="La base de dades no està disponible")
        return {"status": "ready"}

    @app.get("/v1/hour-by-hour", response_model=HourByHourPageSchema)
    def hour_by_hour(
        cursor: str | None = None,
        limit: Annotated[int, Query(ge=1, le=100)] = 30,
        refresh: bool = False,
    ) -> HourByHourPageSchema:
        try:
            page = container.hour_by_hour_service.list(cursor, limit, force_refresh=refresh)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except Exception as error:
            raise HTTPException(status_code=502, detail="No s'ha pogut actualitzar Hora a Hora") from error
        return HourByHourPageSchema(
            items=[HourByHourItemSchema.from_domain(item) for item in page.items],
            next_cursor=page.next_cursor,
            from_cache=page.from_cache,
        )

    @app.get("/v1/events", response_model=AgendaPageSchema)
    def events(
        response: Response,
        date_from: date | None = Query(default=None, alias="from"),
        date_to: date | None = Query(default=None, alias="to"),
        group: str | None = None,
        municipality: str | None = None,
        cursor: str | None = None,
        limit: Annotated[int, Query(ge=1, le=100)] = 50,
        refresh: bool = False,
    ) -> AgendaPageSchema:
        try:
            page = container.agenda_service.list(
                date_from,
                date_to,
                group,
                municipality,
                cursor,
                limit,
                force_refresh=refresh,
            )
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except Exception as error:
            raise HTTPException(status_code=502, detail="No s'ha pogut actualitzar l'agenda") from error
        response.headers["Cache-Control"] = (
            "no-store"
            if refresh
            else "public, s-maxage=300, stale-while-revalidate=86400"
        )
        return AgendaPageSchema(
            items=[CastellEventSchema.from_domain(item) for item in page.items],
            next_cursor=page.next_cursor,
            from_cache=page.from_cache,
            source_status=page.source_status,
        )

    @app.post("/v1/chat", response_model=ChatResponseSchema)
    async def chat(
        payload: ChatRequestSchema,
        request: Request,
        response: Response,
        installation_header: Annotated[str | None, Header(alias="X-Installation-ID")] = None,
    ) -> ChatResponseSchema:
        client_ip = request.client.host if request.client else "unknown"
        identifier = f"{client_ip}:{installation_header or payload.installation_id}"
        allowed, retry_after = container.rate_limiter.allow(identifier)
        if not allowed:
            response.headers["Retry-After"] = str(retry_after)
            raise HTTPException(status_code=429, detail="Massa consultes. Torna-ho a provar més tard.")

        history = [ChatTurn(role=message.role, content=message.content) for message in payload.messages]
        try:
            result = await container.chat_service.respond(history)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return ChatResponseSchema.from_domain(result)

    @app.put(
        "/v1/push-subscriptions/{installation_id}",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    def register_push_subscription(
        installation_id: str,
        payload: PushSubscriptionRequestSchema,
    ) -> Response:
        if not 1 <= len(installation_id) <= 128:
            raise HTTPException(status_code=422, detail="Identificador d'instal·lació no vàlid")
        container.push_repository.register(
            PushSubscriptionRegistration(
                installation_id=installation_id,
                device_token=payload.device_token,
                app_version=payload.app_version,
                locale=payload.locale,
            ),
            environment=payload.environment or settings.apns_environment,
            topic=settings.apns_bundle_id,
        )
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @app.delete(
        "/v1/push-subscriptions/{installation_id}",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    def unregister_push_subscription(
        installation_id: str,
        environment: Literal["development", "production"] | None = None,
    ) -> Response:
        if not 1 <= len(installation_id) <= 128:
            raise HTTPException(status_code=422, detail="Identificador d'instal·lació no vàlid")
        container.push_repository.unregister(
            installation_id,
            environment=environment or settings.apns_environment,
            topic=settings.apns_bundle_id,
        )
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    def authorize_cron(authorization: str | None) -> None:
        if settings.vercel_env != "production":
            raise HTTPException(status_code=404, detail="No disponible")
        if not settings.cron_secret or authorization != f"Bearer {settings.cron_secret}":
            raise HTTPException(status_code=401, detail="Cron no autoritzat")

    @app.get("/internal/cron/hour-by-hour")
    def hour_by_hour_cron(
        authorization: Annotated[str | None, Header()] = None,
    ) -> dict[str, int | str]:
        authorize_cron(authorization)
        if container.notification_coordinator is None:
            return {"status": "unavailable"}
        result = container.notification_coordinator.run()
        return {
            "status": result.status,
            "notifications_created": result.notifications_created,
            "attempted": result.attempted,
            "delivered": result.delivered,
            "retried": result.retried,
            "invalidated": result.invalidated,
            "failed": result.failed,
        }

    @app.get("/internal/cron/maintenance")
    def maintenance_cron(
        authorization: Annotated[str | None, Header()] = None,
    ) -> dict[str, int | str]:
        authorize_cron(authorization)
        notification_counts = container.notification_repository.cleanup()
        rate_limit_count = (
            container.rate_limiter.cleanup_expired()
            if hasattr(container.rate_limiter, "cleanup_expired")
            else 0
        )
        return {
            "status": "completed",
            "rate_limit_buckets_deleted": rate_limit_count,
            **notification_counts,
        }

    return app
