from datetime import UTC, datetime

from backend.domain.social.models import SocialHeadline, SocialWatchlist
from scripts.smoke_x_posts import run
from tests.support.social import social_post

SINCE = datetime(2026, 9, 27, tzinfo=UTC)


class Source:
    def search(self, watchlist, *, since):
        assert since == SINCE
        return [social_post("1", likes=12), social_post("2", likes=3), social_post("3", likes=20)]


class Writer:
    def write(self, post, *, timeout):
        if post.post_id == "3":
            raise TimeoutError()
        return SocialHeadline(True, "Titular", "model", {"cost": 0.001})


def test_the_smoke_run_reports_candidates_and_decisions_without_storing_anything() -> None:
    lines: list[dict] = []

    run(Source(), Writer(), SocialWatchlist(min_likes=10), since=SINCE, limit=5, emit=lines.append)

    assert lines[0] == {"event": "x_posts_found", "fetched": 3, "candidates": 2}
    assert lines[1]["publicable"] is True
    assert lines[1]["titular"] == "Titular"
    assert lines[1]["url"] == "https://x.com/JoanQuijorna/status/1"
    assert lines[2]["error"] == "TimeoutError"
    assert len(lines) == 3


def test_the_smoke_run_respects_the_headline_limit() -> None:
    lines: list[dict] = []

    run(Source(), Writer(), SocialWatchlist(min_likes=10), since=SINCE, limit=1, emit=lines.append)

    assert len(lines) == 2
