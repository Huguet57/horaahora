from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str = "sqlite:///./horaahora.db"
    ai_provider: str = "local"
    ai_model: str = ""
    ai_api_key: str = ""
    ai_base_url: str = ""
    hour_by_hour_source_enabled: bool = True
    hour_by_hour_refresh_seconds: int = 300
    revista_castells_url: str = "https://revistacastells.cat/castells-hora-a-hora/"
    agenda_source: str = "disabled"
    agenda_refresh_seconds: int = 1_800
    cccc_agenda_url: str = "https://castellscat.cat/ca/agenda"
    cccc_agenda_fixture_path: str = "backend/data/cccc_agenda_fixture.html"
    cccc_agenda_authorized: bool = False
    redis_url: str = ""
    rate_limit_max_requests: int = 30
    rate_limit_window_seconds: int = 600

    @classmethod
    def from_env(cls) -> "Settings":
        defaults = cls()
        return cls(
            database_url=os.getenv("DATABASE_URL", defaults.database_url),
            ai_provider=os.getenv("AI_PROVIDER", defaults.ai_provider).lower(),
            ai_model=os.getenv("AI_MODEL", ""),
            ai_api_key=os.getenv("AI_API_KEY", ""),
            ai_base_url=os.getenv("AI_BASE_URL", ""),
            hour_by_hour_source_enabled=_bool_env("HOUR_BY_HOUR_SOURCE_ENABLED", True),
            hour_by_hour_refresh_seconds=int(os.getenv("HOUR_BY_HOUR_REFRESH_SECONDS", "300")),
            revista_castells_url=os.getenv("REVISTA_CASTELLS_URL", defaults.revista_castells_url),
            agenda_source=os.getenv("AGENDA_SOURCE", defaults.agenda_source).lower(),
            agenda_refresh_seconds=int(os.getenv("AGENDA_REFRESH_SECONDS", "1800")),
            cccc_agenda_url=os.getenv("CCCC_AGENDA_URL", defaults.cccc_agenda_url),
            cccc_agenda_fixture_path=os.getenv(
                "CCCC_AGENDA_FIXTURE_PATH", defaults.cccc_agenda_fixture_path
            ),
            cccc_agenda_authorized=_bool_env("CCCC_AGENDA_AUTHORIZED", False),
            redis_url=os.getenv("REDIS_URL", ""),
            rate_limit_max_requests=int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "30")),
            rate_limit_window_seconds=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "600")),
        )


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}
