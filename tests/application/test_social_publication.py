import uuid
from datetime import UTC, datetime, timedelta

from backend.adapters.persistence.in_memory.hour_by_hour import InMemoryHourByHourRepository
from backend.application.social_publication import (
    SocialFeedPublisher,
    SocialHourByHourSource,
    hour_by_hour_items,
)
from backend.domain.content.models import HourByHourItem
from backend.domain.social.models import HeadlinedPost
from tests.support.social import social_post

NOW = datetime(2026, 9, 27, 12, tzinfo=UTC)
ACCEPTED = HeadlinedPost(
    post=social_post("1970000000000000001", username="JoanQuijorna"),
    headline="Joan Colominas qüestiona el gamma extra",
)


def test_accepted_posts_become_attributed_hour_by_hour_items() -> None:
    [item] = hour_by_hour_items([ACCEPTED], now=NOW)

    assert item == HourByHourItem(
        id=str(uuid.uuid5(uuid.NAMESPACE_URL, "x:1970000000000000001")),
        source_id="x",
        external_id="1970000000000000001",
        title="Joan Colominas qüestiona el gamma extra",
        display_title="Joan Colominas qüestiona el gamma extra",
        summary="Opinió castellera 1970000000000000001",
        published_at=ACCEPTED.post.published_at,
        source_order=0,
        article_url="https://x.com/JoanQuijorna/status/1970000000000000001",
        action_url="https://x.com/JoanQuijorna/status/1970000000000000001",
        attribution="Nom JoanQuijorna a X · titular amb IA",
        created_at=NOW,
        updated_at=NOW,
    )


def test_the_feed_publisher_shows_posts_without_touching_notifications() -> None:
    repository = InMemoryHourByHourRepository()

    published = SocialFeedPublisher(repository, clock=lambda: NOW).publish([ACCEPTED])

    assert published == 1
    [item] = repository.list_hour_by_hour(0, 10)
    assert item.display_title == "Joan Colominas qüestiona el gamma extra"


def test_the_notifying_source_reads_the_accepted_posts_of_the_last_week() -> None:
    class Repository:
        def __init__(self) -> None:
            self.calls: list[tuple[datetime, int]] = []

        def accepted_since(self, since, limit):
            self.calls.append((since, limit))
            return [ACCEPTED]

    repository = Repository()

    items = SocialHourByHourSource(repository, clock=lambda: NOW).fetch()

    assert [item.external_id for item in items] == ["1970000000000000001"]
    assert repository.calls == [(NOW - timedelta(days=7), 100)]
