import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from backend.domain.content.models import HourByHourItem
from backend.domain.content.ports import HourByHourRepository
from backend.domain.social.models import HeadlinedPost
from backend.domain.social.ports import SocialPostRepository

NETWORK_LABELS = {"x": "X"}
PUBLICATION_WINDOW = timedelta(days=7)
PUBLICATION_LIMIT = 100


def hour_by_hour_items(posts: list[HeadlinedPost], *, now: datetime) -> list[HourByHourItem]:
    items = []
    for order, accepted in enumerate(posts):
        post = accepted.post
        network = NETWORK_LABELS.get(post.network, post.network)
        items.append(
            HourByHourItem(
                id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{post.network}:{post.post_id}")),
                source_id=post.network,
                external_id=post.post_id,
                title=accepted.headline,
                display_title=accepted.headline,
                summary=post.text,
                published_at=post.published_at,
                source_order=order,
                article_url=post.url,
                action_url=post.url,
                # The original post stays one tap away; the label discloses the AI headline.
                attribution=f"{post.author.name} a {network} · titular amb IA",
                created_at=now,
                updated_at=now,
            )
        )
    return items


class SocialFeedPublisher:
    """Show accepted posts in Hora a Hora without creating notifications."""

    def __init__(
        self,
        repository: HourByHourRepository,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.repository = repository
        self.clock = clock

    def publish(self, posts: list[HeadlinedPost]) -> int:
        items = hour_by_hour_items(posts, now=self.clock())
        if items:
            self.repository.upsert_hour_by_hour(items)
        return len(items)


class SocialHourByHourSource:
    """Offer accepted posts to the Hora a Hora ingestion, which also notifies them."""

    def __init__(
        self,
        repository: SocialPostRepository,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.repository = repository
        self.clock = clock

    def fetch(self) -> list[HourByHourItem]:
        now = self.clock()
        accepted = self.repository.accepted_since(now - PUBLICATION_WINDOW, PUBLICATION_LIMIT)
        return hour_by_hour_items(accepted, now=now)
