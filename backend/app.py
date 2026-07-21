from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Annotated

from fastapi import FastAPI, Header, HTTPException, Query, Request, Response

from backend.adapters.content.revista_castells import RevistaCastellsHTMLSource
from backend.api.schemas import (
    AgendaPageSchema,
    CastellEventSchema,
    ChatRequestSchema,
    ChatResponseSchema,
    HourByHourItemSchema,
    HourByHourPageSchema,
)
from backend.application.services import AgendaService, ChatService, HourByHourService
from backend.bootstrap import (
    build_agenda_source,
    build_content_repository,
    build_interpreter,
    build_rate_limiter,
)
from backend.config import Settings
from backend.domain.models import ChatTurn
from backend.domain.ports import AgendaSource, ContentRepository, HourByHourSource, QueryInterpreter, RateLimiter
from backend.domain.scoring import ScoreTable, ScoringEngine


@dataclass(slots=True)
class ApplicationContainer:
    chat_service: ChatService
    hour_by_hour_service: HourByHourService
    agenda_service: AgendaService
    rate_limiter: RateLimiter


def create_app(
    settings: Settings | None = None,
    interpreter: QueryInterpreter | None = None,
    content_repository: ContentRepository | None = None,
    rate_limiter: RateLimiter | None = None,
    hour_by_hour_source: HourByHourSource | None = None,
    agenda_source: AgendaSource | None = None,
) -> FastAPI:
    settings = settings or Settings.from_env()
    interpreter = interpreter or build_interpreter(settings)
    content_repository = content_repository or build_content_repository(settings)
    rate_limiter = rate_limiter or build_rate_limiter(settings)
    if hour_by_hour_source is None and settings.hour_by_hour_source_enabled:
        hour_by_hour_source = RevistaCastellsHTMLSource(settings.revista_castells_url)
    if agenda_source is None:
        agenda_source = build_agenda_source(settings)

    container = ApplicationContainer(
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
    )
    app = FastAPI(
        title="Castells Super-app API",
        version="1.0.0",
        description="Contractes neutrals per a contingut casteller i càlcul de puntuacions.",
    )
    app.state.container = container

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

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

    return app


app = create_app()
