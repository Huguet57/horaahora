from fastapi import FastAPI

from backend.api.request_context import request_context_middleware
from backend.api.routers import agenda, chat, cron, health, hour_by_hour, privacy, push
from backend.composition.container import ApplicationOverrides, build_container
from backend.config import Settings
from backend.observability import configure_logging


def create_app(
    settings: Settings | None = None,
    overrides: ApplicationOverrides | None = None,
) -> FastAPI:
    resolved_settings = settings or Settings.from_env()
    configure_logging()
    app = FastAPI(
        title="Castells Super-app API",
        version="1.0.0",
        description="Contractes neutrals per a contingut casteller i càlcul de puntuacions.",
    )
    app.middleware("http")(request_context_middleware)
    app.state.container = build_container(resolved_settings, overrides)
    for router in (
        privacy.router,
        health.router,
        hour_by_hour.router,
        agenda.router,
        chat.router,
        push.router,
        cron.router,
    ):
        app.include_router(router)
    return app
