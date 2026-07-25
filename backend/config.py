from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str = ""
    ai_provider: str = "local"
    ai_model: str = ""
    ai_api_key: str = ""
    ai_base_url: str = ""
    hour_by_hour_source_enabled: bool = True
    hour_by_hour_refresh_seconds: int = 300
    revista_castells_url: str = "https://revistacastells.cat/castells-hora-a-hora/"
    agenda_source: str = "disabled"
    agenda_refresh_seconds: int = 1_800
    agenda_refresh_on_request: bool = False
    agenda_sync_interval_seconds: int = 86_400
    agenda_sync_months_back: int = 1
    agenda_sync_months_ahead: int = 12
    cccc_agenda_url: str = "https://castellscat.cat/public/ca/agenda"
    cccc_agenda_fixture_path: str = "backend/data/cccc_agenda_fixture.html"
    cccc_agenda_snapshot_path: str = "backend/data/cccc_agenda_poc_2026_07.html"
    cccc_agenda_authorized: bool = False
    rate_limit_max_requests: int = 30
    rate_limit_window_seconds: int = 600
    rate_limit_hash_secret: str = "test-rate-limit-secret"
    vercel_env: str = ""
    cron_secret: str = ""
    push_delivery_enabled: bool = False
    apns_key_p8: str = ""
    apns_key_id: str = ""
    apns_team_id: str = ""
    apns_bundle_id: str = "com.ahuguet.castellsenvena"

    @classmethod
    def from_env(cls) -> Settings:
        defaults = cls()
        database_url = os.getenv("DATABASE_URL", "").strip()
        if not database_url:
            raise RuntimeError("DATABASE_URL és obligatòria; vincula el projecte amb Neon")
        if not database_url.startswith(("postgres://", "postgresql://", "postgresql+psycopg://")):
            raise RuntimeError(
                "DATABASE_URL ha d'apuntar a PostgreSQL; SQLite només es permet als tests"
            )
        rate_limit_hash_secret = os.getenv("RATE_LIMIT_HASH_SECRET", "").strip()
        if not rate_limit_hash_secret:
            raise RuntimeError("RATE_LIMIT_HASH_SECRET és obligatori")
        return cls(
            database_url=database_url,
            ai_provider=os.getenv("AI_PROVIDER", defaults.ai_provider).lower(),
            ai_model=os.getenv("AI_MODEL", ""),
            ai_api_key=os.getenv("AI_API_KEY", ""),
            ai_base_url=os.getenv("AI_BASE_URL", ""),
            hour_by_hour_source_enabled=_bool_env("HOUR_BY_HOUR_SOURCE_ENABLED", True),
            hour_by_hour_refresh_seconds=int(os.getenv("HOUR_BY_HOUR_REFRESH_SECONDS", "300")),
            revista_castells_url=os.getenv("REVISTA_CASTELLS_URL", defaults.revista_castells_url),
            agenda_source=os.getenv("AGENDA_SOURCE", defaults.agenda_source).lower(),
            agenda_refresh_seconds=int(os.getenv("AGENDA_REFRESH_SECONDS", "1800")),
            agenda_refresh_on_request=_bool_env("AGENDA_REFRESH_ON_REQUEST", False),
            agenda_sync_interval_seconds=int(os.getenv("AGENDA_SYNC_INTERVAL_SECONDS", "86400")),
            agenda_sync_months_back=int(os.getenv("AGENDA_SYNC_MONTHS_BACK", "1")),
            agenda_sync_months_ahead=int(os.getenv("AGENDA_SYNC_MONTHS_AHEAD", "12")),
            cccc_agenda_url=os.getenv("CCCC_AGENDA_URL", defaults.cccc_agenda_url),
            cccc_agenda_fixture_path=os.getenv(
                "CCCC_AGENDA_FIXTURE_PATH", defaults.cccc_agenda_fixture_path
            ),
            cccc_agenda_snapshot_path=os.getenv(
                "CCCC_AGENDA_SNAPSHOT_PATH", defaults.cccc_agenda_snapshot_path
            ),
            cccc_agenda_authorized=_bool_env("CCCC_AGENDA_AUTHORIZED", False),
            rate_limit_max_requests=int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "30")),
            rate_limit_window_seconds=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "600")),
            rate_limit_hash_secret=rate_limit_hash_secret,
            vercel_env=os.getenv("VERCEL_ENV", "").lower(),
            cron_secret=os.getenv("CRON_SECRET", ""),
            push_delivery_enabled=_bool_env("PUSH_DELIVERY_ENABLED", False),
            apns_key_p8=os.getenv("APNS_KEY_P8", ""),
            apns_key_id=os.getenv("APNS_KEY_ID", ""),
            apns_team_id=os.getenv("APNS_TEAM_ID", ""),
            apns_bundle_id=os.getenv("APNS_BUNDLE_ID", defaults.apns_bundle_id),
        )

    @property
    def can_deliver_push(self) -> bool:
        return self.vercel_env == "production" and self.push_delivery_enabled

    @property
    def apns_environment(self) -> str:
        return "production" if self.vercel_env == "production" else "development"


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}
