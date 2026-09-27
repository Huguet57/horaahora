"""Read-only check of the X tracker: no database writes and nothing is published.

Run: uv run --env-file .env.x.local python -m scripts.smoke_x_posts --hours 12 --limit 10

Needs X_BEARER_TOKEN and the OpenRouter AI_API_KEY and AI_MODEL. The watchlist comes from
X_WATCHLIST_JSON or X_WATCHLIST_PATH, as in the backend. X bills every post read and
OpenRouter every headline, so keep --limit small.
"""

import argparse
import json
import os
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from backend.adapters.ai.social_headlines import OpenRouterSocialHeadlineWriter
from backend.adapters.social.x_recent_search import XRecentSearchSource
from backend.composition.providers import build_x_watchlist
from backend.config import Settings
from backend.domain.social.models import SocialWatchlist
from backend.domain.social.ports import SocialHeadlineWriter, SocialPostSource

MAX_HOURS = 167  # X recent search only covers the last seven days.


def run(
    source: SocialPostSource,
    writer: SocialHeadlineWriter,
    watchlist: SocialWatchlist,
    *,
    since: datetime,
    limit: int,
    emit: Callable[[dict], None],
) -> None:
    posts = source.search(watchlist, since=since, timeout=60)
    candidates = [post for post in posts if watchlist.qualifies(post)]
    emit({"event": "x_posts_found", "fetched": len(posts), "candidates": len(candidates)})
    for post in candidates[:limit]:
        result = {
            "url": post.url,
            "likes": post.like_count,
            "author": post.author.name,
            "text": post.text,
            "context": [context.text for context in post.context],
        }
        try:
            headline = writer.write(post, timeout=30)
        except Exception as error:
            emit(result | {"error": type(error).__name__})
            continue
        emit(
            result
            | {
                "publicable": headline.publishable,
                "titular": headline.headline,
                "usage": headline.usage,
            }
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Prova de lectura del seguiment de X")
    parser.add_argument("--hours", type=int, default=12, help="finestra de cerca, en hores")
    parser.add_argument("--limit", type=int, default=10, help="titulars a generar com a màxim")
    args = parser.parse_args()
    if not 1 <= args.hours <= MAX_HOURS:
        parser.error(f"--hours ha d'estar entre 1 i {MAX_HOURS}")
    watchlist = build_x_watchlist(
        Settings(
            x_watchlist_path=os.getenv("X_WATCHLIST_PATH", Settings().x_watchlist_path),
            x_watchlist_json=os.getenv("X_WATCHLIST_JSON", ""),
        )
    )
    run(
        XRecentSearchSource(os.environ["X_BEARER_TOKEN"]),
        OpenRouterSocialHeadlineWriter(
            os.environ["AI_API_KEY"], os.environ["AI_MODEL"], os.getenv("AI_BASE_URL") or None
        ),
        watchlist,
        since=datetime.now(UTC) - timedelta(hours=args.hours),
        limit=args.limit,
        emit=lambda line: print(json.dumps(line, ensure_ascii=False), flush=True),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
