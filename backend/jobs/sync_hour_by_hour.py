from __future__ import annotations

import json

from backend.adapters.content.revista_castells import RevistaCastellsHTMLSource
from backend.bootstrap import build_database, build_notification_repository
from backend.config import Settings


def sync_once(settings: Settings) -> int:
    if not settings.hour_by_hour_source_enabled:
        raise RuntimeError("HOUR_BY_HOUR_SOURCE_ENABLED ha d'estar activa")
    repository = build_notification_repository(settings, build_database(settings))
    source = RevistaCastellsHTMLSource(settings.revista_castells_url)
    result = repository.ingest_hour_by_hour(source.fetch())
    print(
        json.dumps(
            {
                "event": "hour_by_hour_sync_finished",
                "baseline_created": result.baseline_created,
                "notifications_created": result.notifications_created,
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return 0


def main() -> int:
    return sync_once(Settings.from_env())


if __name__ == "__main__":
    raise SystemExit(main())
