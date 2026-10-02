from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str = ""
    ai_provider: str = ""
    ai_model: str = ""
    ai_api_key: str = ""
    ai_base_url: str = ""
    rate_limit_max_requests: int = 30
    rate_limit_window_seconds: int = 600
    rate_limit_hash_secret: str = "test-rate-limit-secret"
    vercel_env: str = ""
    cron_secret: str = ""

    @classmethod
    def from_env(cls) -> Settings:
        defaults = cls()
        database_url = _database_url_from_env("SUPABASE_DATABASE_URL", "DATABASE_URL")
        rate_limit_hash_secret = os.getenv("RATE_LIMIT_HASH_SECRET", "").strip()
        if not rate_limit_hash_secret:
            raise RuntimeError("RATE_LIMIT_HASH_SECRET és obligatori")
        return cls(
            database_url=database_url,
            ai_provider=os.getenv("AI_PROVIDER", defaults.ai_provider).lower(),
            ai_model=os.getenv("AI_MODEL", ""),
            ai_api_key=os.getenv("AI_API_KEY", ""),
            ai_base_url=os.getenv("AI_BASE_URL", ""),
            rate_limit_max_requests=int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "30")),
            rate_limit_window_seconds=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "600")),
            rate_limit_hash_secret=rate_limit_hash_secret,
            vercel_env=os.getenv("VERCEL_ENV", "").lower(),
            cron_secret=os.getenv("CRON_SECRET", ""),
        )


def migration_database_url_from_env() -> str:
    return _first_configured_url(
        "SUPABASE_MIGRATION_DATABASE_URL",
        "SUPABASE_DATABASE_URL",
        "DATABASE_URL",
    )


def _database_url_from_env(*names: str) -> str:
    database_url = _first_configured_url(*names)
    postgres_schemes = ("postgres://", "postgresql://", "postgresql+psycopg://")
    if not database_url.startswith(postgres_schemes):
        raise RuntimeError(
            f"{names[0]} ha d'apuntar a PostgreSQL; SQLite només es permet als tests"
        )
    return database_url


def _first_configured_url(*names: str) -> str:
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    joined_names = " o ".join(names)
    raise RuntimeError(f"{joined_names} és obligatòria")
