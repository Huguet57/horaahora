from fastapi import FastAPI

from backend.api.routers import chat, cron, health, privacy
from backend.composition.container import ApplicationOverrides, build_container
from backend.config import Settings


def create_app(
    settings: Settings | None = None,
    overrides: ApplicationOverrides | None = None,
) -> FastAPI:
    resolved_settings = settings or Settings.from_env()
    app = FastAPI(
        title="API de La calculadora de l'Aleta",
        version="1.0.0",
        description=(
            "Xat de la calculadora del Concurs de Castells: interpreta les actuacions, "
            "calcula les puntuacions i respon dubtes sobre les normes i els resultats."
        ),
    )
    app.state.container = build_container(resolved_settings, overrides)
    for router in (
        privacy.router,
        health.router,
        chat.router,
        cron.router,
    ):
        app.include_router(router)
    return app
