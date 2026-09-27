from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, slots=True)
class SocialAuthor:
    user_id: str
    username: str
    name: str


@dataclass(frozen=True, slots=True)
class SocialPostContext:
    """A post quoted by, or replied to by, a tracked post."""

    relation: str
    text: str
    author: SocialAuthor | None = None


@dataclass(frozen=True, slots=True)
class SocialPost:
    network: str
    post_id: str
    author: SocialAuthor
    text: str
    url: str
    published_at: datetime
    like_count: int
    context: tuple[SocialPostContext, ...] = ()


@dataclass(frozen=True, slots=True)
class SocialHeadline:
    publishable: bool
    headline: str
    model: str
    usage: dict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class HeadlinedPost:
    post: SocialPost
    headline: str


@dataclass(frozen=True, slots=True)
class WatchedAccount:
    username: str
    min_likes: int | None = None


@dataclass(frozen=True, slots=True)
class SocialWatchlist:
    """Accounts and hashtags whose popular posts can become Hora a Hora items."""

    min_likes: int
    accounts: tuple[WatchedAccount, ...] = ()
    hashtags: tuple[str, ...] = ()

    @property
    def is_empty(self) -> bool:
        return not self.accounts and not self.hashtags

    @property
    def search_min_likes(self) -> int:
        overrides = [
            account.min_likes for account in self.accounts if account.min_likes is not None
        ]
        return min([self.min_likes, *overrides])

    def threshold_for(self, username: str) -> int:
        key = username.casefold()
        for account in self.accounts:
            if account.username.casefold() == key and account.min_likes is not None:
                return account.min_likes
        return self.min_likes

    def qualifies(self, post: SocialPost) -> bool:
        return post.like_count >= self.threshold_for(post.author.username)
