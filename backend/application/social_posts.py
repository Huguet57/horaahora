import logging
import time
from collections.abc import Callable
from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from backend.application.social_publication import PUBLICATION_LIMIT, PUBLICATION_WINDOW
from backend.domain.social.models import SocialPost, SocialWatchlist
from backend.domain.social.ports import (
    SocialHeadlineWriter,
    SocialPostPublisher,
    SocialPostRepository,
    SocialPostSource,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

SOCIAL_POSTS_LOCK_KEY = 2_026_092_708
LOOKBACK = timedelta(hours=12)
MAX_HEADLINE_ATTEMPTS = 3
_PENDING_BATCH = 50
_SEARCH_TIMEOUT_SECONDS = 20.0
_HEADLINE_TIMEOUT_SECONDS = 15.0
_MIN_HEADLINE_SECONDS = 5.0


@dataclass(frozen=True, slots=True)
class SocialPostSyncResult:
    status: str
    fetched: int = 0
    candidates: int = 0
    discovered: int = 0
    accepted: int = 0
    rejected: int = 0
    failed: int = 0
    published: int = 0
    source_error: str = ""


class SocialPostSync:
    """Find popular posts, write each headline once and hand accepted posts to a publisher."""

    def __init__(
        self,
        source: SocialPostSource,
        repository: SocialPostRepository,
        writer: SocialHeadlineWriter,
        watchlist: SocialWatchlist,
        *,
        publisher: SocialPostPublisher | None = None,
        lock: Callable[[], AbstractContextManager[bool]] = lambda: nullcontext(True),
        lookback: timedelta = LOOKBACK,
        time_budget_seconds: float = 45,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.source = source
        self.repository = repository
        self.writer = writer
        self.watchlist = watchlist
        self.publisher = publisher
        self.lock = lock
        self.lookback = lookback
        self.time_budget_seconds = time_budget_seconds
        self.clock = clock

    def run(self) -> SocialPostSyncResult:
        with self.lock() as acquired:
            if not acquired:
                return SocialPostSyncResult(status="already_running")
            deadline = time.monotonic() + self.time_budget_seconds
            now = self.clock()
            search_timeout = min(_SEARCH_TIMEOUT_SECONDS, deadline - time.monotonic())
            posts, source_error = self._search(now, timeout=max(0.0, search_timeout))
            candidates = [post for post in posts if self.watchlist.qualifies(post)]
            discovered = self.repository.save_candidates(candidates, seen_at=now)
            accepted = rejected = failed = 0
            for post in self.repository.pending_headlines(_PENDING_BATCH):
                remaining = deadline - time.monotonic()
                if remaining < _MIN_HEADLINE_SECONDS:
                    # Undecided posts stay pending for the next run.
                    break
                decision = self._decide(post, timeout=min(_HEADLINE_TIMEOUT_SECONDS, remaining))
                if decision is None:
                    failed += 1
                elif decision:
                    accepted += 1
                else:
                    rejected += 1
            published = 0
            if self.publisher is not None:
                published = self.publisher.publish(
                    self.repository.accepted_since(now - PUBLICATION_WINDOW, PUBLICATION_LIMIT)
                )
            return SocialPostSyncResult(
                status="completed",
                fetched=len(posts),
                candidates=len(candidates),
                discovered=discovered,
                accepted=accepted,
                rejected=rejected,
                failed=failed,
                published=published,
                source_error=source_error,
            )

    def _search(self, now: datetime, *, timeout: float) -> tuple[list[SocialPost], str]:
        try:
            posts = self.source.search(self.watchlist, since=now - self.lookback, timeout=timeout)
            return posts, ""
        except Exception as error:
            # Keep deciding pending posts: they do not depend on this search.
            logger.warning("social_posts_search_failed reason=%s", type(error).__name__)
            return [], type(error).__name__

    def _decide(self, post: SocialPost, *, timeout: float) -> bool | None:
        try:
            headline = self.writer.write(post, timeout=timeout)
        except Exception as error:
            gave_up = self.repository.record_headline_failure(
                post, type(error).__name__, max_attempts=MAX_HEADLINE_ATTEMPTS
            )
            logger.warning(
                "social_post_headline_failed network=%s id=%s reason=%s gave_up=%s",
                post.network,
                post.post_id,
                type(error).__name__,
                gave_up,
            )
            return None
        self.repository.record_headline(post, headline, decided_at=self.clock())
        logger.info(
            "social_post_decided network=%s id=%s likes=%d publishable=%s model=%s usage=%s "
            "headline=%s",
            post.network,
            post.post_id,
            post.like_count,
            headline.publishable,
            headline.model,
            headline.usage,
            headline.headline,
        )
        return headline.publishable
