from datetime import datetime
from typing import Protocol

from backend.domain.social.models import HeadlinedPost, SocialHeadline, SocialPost, SocialWatchlist


class SocialPostSource(Protocol):
    def search(
        self, watchlist: SocialWatchlist, *, since: datetime, timeout: float
    ) -> list[SocialPost]: ...


class SocialHeadlineWriter(Protocol):
    def write(self, post: SocialPost, *, timeout: float) -> SocialHeadline: ...


class SocialPostRepository(Protocol):
    def save_candidates(self, posts: list[SocialPost], *, seen_at: datetime) -> int: ...
    def pending_headlines(self, limit: int) -> list[SocialPost]: ...
    def record_headline(
        self, post: SocialPost, headline: SocialHeadline, *, decided_at: datetime
    ) -> None: ...
    def record_headline_failure(
        self, post: SocialPost, reason: str, *, max_attempts: int
    ) -> bool: ...
    def accepted_since(self, since: datetime, limit: int) -> list[HeadlinedPost]: ...
    def hide(self, network: str, post_id: str) -> bool: ...


class SocialPostPublisher(Protocol):
    def publish(self, posts: list[HeadlinedPost]) -> int: ...
