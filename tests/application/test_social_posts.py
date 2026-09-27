from contextlib import nullcontext
from datetime import UTC, datetime, timedelta

from backend.adapters.persistence.database import Database
from backend.adapters.persistence.social_post_repository import SQLAlchemySocialPostRepository
from backend.application.social_posts import SocialPostSync, SocialPostSyncResult
from backend.domain.social.models import (
    HeadlinedPost,
    SocialHeadline,
    SocialWatchlist,
    WatchedAccount,
)
from tests.support.social import social_post

NOW = datetime(2026, 9, 27, 12, tzinfo=UTC)
WATCHLIST = SocialWatchlist(
    min_likes=10, accounts=(WatchedAccount("Gran", min_likes=50),), hashtags=("castells",)
)
QUIJO = social_post(
    "quijo", username="JoanQuijorna", likes=12, published_at=NOW - timedelta(hours=1)
)
GRAN = social_post("gran", username="Gran", likes=30, published_at=NOW - timedelta(minutes=30))
ANON = social_post("anon", username="anonim", likes=10, published_at=NOW - timedelta(hours=2))


class Source:
    def __init__(self, posts=(), error: Exception | None = None) -> None:
        self.posts, self.error = list(posts), error
        self.calls: list[tuple[SocialWatchlist, datetime]] = []
        self.timeouts: list[float] = []

    def search(self, watchlist, *, since, timeout):
        self.calls.append((watchlist, since))
        self.timeouts.append(timeout)
        if self.error is not None:
            raise self.error
        return self.posts


class Writer:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.written: list[str] = []

    def write(self, post, *, timeout):
        assert 0 < timeout <= 15
        self.written.append(post.post_id)
        if self.error is not None:
            raise self.error
        publishable = post.post_id != "anon"
        return SocialHeadline(
            publishable=publishable,
            headline=f"Titular {post.post_id}" if publishable else "",
            model="test-model",
        )


class Publisher:
    def __init__(self) -> None:
        self.published: list[list[HeadlinedPost]] = []

    def publish(self, posts):
        self.published.append(posts)
        return len(posts)


def sync(source, writer, *, repository=None, **options) -> SocialPostSync:
    return SocialPostSync(
        source,
        repository or SQLAlchemySocialPostRepository(Database("sqlite+pysqlite:///:memory:")),
        writer,
        WATCHLIST,
        clock=lambda: NOW,
        **options,
    )


def test_posts_over_their_threshold_get_headlines_newest_first() -> None:
    source, writer = Source([GRAN, QUIJO, ANON]), Writer()
    repository = SQLAlchemySocialPostRepository(Database("sqlite+pysqlite:///:memory:"))

    result = sync(source, writer, repository=repository).run()

    assert result == SocialPostSyncResult(
        status="completed", fetched=3, candidates=2, discovered=2, accepted=1, rejected=1
    )
    assert source.calls == [(WATCHLIST, NOW - timedelta(hours=12))]
    # The search gets a share of the run's budget, leaving time for headlines.
    assert 19 < source.timeouts[0] <= 20
    # Gran has its own, higher threshold; the others use the global one.
    assert writer.written == ["quijo", "anon"]
    assert repository.accepted_since(NOW - timedelta(days=1), limit=10) == [
        HeadlinedPost(post=QUIJO, headline="Titular quijo")
    ]


def test_decided_posts_are_never_sent_to_the_model_again() -> None:
    source, writer = Source([QUIJO]), Writer()
    repository = SQLAlchemySocialPostRepository(Database("sqlite+pysqlite:///:memory:"))

    sync(source, writer, repository=repository).run()
    second = sync(source, writer, repository=repository).run()

    assert writer.written == ["quijo"]
    assert (second.candidates, second.discovered, second.accepted) == (1, 0, 0)


def test_headline_errors_are_retried_until_the_attempt_limit() -> None:
    source, writer = Source([QUIJO]), Writer(error=TimeoutError())
    repository = SQLAlchemySocialPostRepository(Database("sqlite+pysqlite:///:memory:"))

    results = [sync(source, writer, repository=repository).run() for _ in range(4)]

    assert [result.failed for result in results] == [1, 1, 1, 0]
    assert writer.written == ["quijo"] * 3
    assert repository.pending_headlines(limit=10) == []


def test_a_search_failure_still_finishes_pending_headlines() -> None:
    repository = SQLAlchemySocialPostRepository(Database("sqlite+pysqlite:///:memory:"))
    sync(Source([QUIJO]), Writer(), repository=repository, time_budget_seconds=0).run()
    writer = Writer()

    result = sync(Source(error=RuntimeError("X down")), writer, repository=repository).run()

    assert result.source_error == "RuntimeError"
    assert (result.fetched, result.accepted) == (0, 1)
    assert writer.written == ["quijo"]


def test_headlines_wait_for_the_next_run_when_the_time_budget_is_spent() -> None:
    writer = Writer()
    repository = SQLAlchemySocialPostRepository(Database("sqlite+pysqlite:///:memory:"))

    source = Source([QUIJO])

    result = sync(source, writer, repository=repository, time_budget_seconds=0).run()

    assert source.timeouts == [0]
    assert (result.discovered, result.accepted) == (1, 0)
    assert writer.written == []
    assert [post.post_id for post in repository.pending_headlines(limit=10)] == ["quijo"]


def test_the_publisher_receives_the_accepted_posts_of_the_last_week() -> None:
    publisher = Publisher()

    result = sync(Source([QUIJO, ANON]), Writer(), publisher=publisher).run()

    assert result.published == 1
    assert publisher.published == [[HeadlinedPost(post=QUIJO, headline="Titular quijo")]]


def test_a_run_is_skipped_while_another_one_holds_the_lock() -> None:
    source = Source([QUIJO])

    result = sync(source, Writer(), lock=lambda: nullcontext(False)).run()

    assert result == SocialPostSyncResult(status="already_running")
    assert source.calls == []
