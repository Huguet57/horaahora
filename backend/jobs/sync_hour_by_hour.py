from __future__ import annotations

import json

from backend.composition.providers import (
    build_database,
    build_hour_by_hour_source,
    build_notification_repository,
)
from backend.config import Settings


def sync_once(settings: Settings) -> int:
    source = build_hour_by_hour_source(settings)
    if source is None:
        raise RuntimeError("HOUR_BY_HOUR_SOURCE_ENABLED ha d'estar activa")
    repository = build_notification_repository(build_database(settings))
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
