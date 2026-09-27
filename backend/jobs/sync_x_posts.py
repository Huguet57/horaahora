from __future__ import annotations

import json
from dataclasses import asdict

from backend.composition.providers import (
    build_database,
    build_hour_by_hour_repository,
    build_social_post_sync,
)
from backend.config import Settings


def sync_once(settings: Settings) -> int:
    if settings.x_posts_mode == "disabled":
        raise RuntimeError("X_POSTS_MODE ha de ser shadow, feed o notify")
    database = build_database(settings)
    sync = build_social_post_sync(settings, database, build_hour_by_hour_repository(database))
    result = sync.run()
    print(
        json.dumps({"event": "x_posts_sync_finished", **asdict(result)}, ensure_ascii=False),
        flush=True,
    )
    return 0


def main() -> int:
    return sync_once(Settings.from_env())


if __name__ == "__main__":
    raise SystemExit(main())
