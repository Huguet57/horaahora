from dataclasses import replace
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.adapters.persistence.database import Database
from backend.adapters.persistence.hour_by_hour_repository import SQLAlchemyHourByHourRepository
from backend.adapters.persistence.models import NotificationDeliveryRecord
from backend.adapters.persistence.notification_repository import SQLAlchemyNotificationRepository
from backend.adapters.persistence.push_subscription_repository import (
    SQLAlchemyPushSubscriptionRepository,
)
from backend.adapters.persistence.social_post_repository import SQLAlchemySocialPostRepository
from backend.domain.notifications.interest import InterestLevel
from backend.domain.notifications.models import PushSubscriptionRegistration
from backend.domain.social.models import (
    HeadlinedPost,
    SocialAuthor,
    SocialHeadline,
    SocialPostContext,
)
from tests.support.hour_by_hour import hour_item
from tests.support.notifications import ingest
from tests.support.social import social_post

NOW = datetime(2026, 9, 27, 12, tzinfo=UTC)
ACCEPTED = SocialHeadline(publishable=True, headline="Titular", model="model")
REJECTED = SocialHeadline(publishable=False, headline="", model="model")


def repository() -> SQLAlchemySocialPostRepository:
    return SQLAlchemySocialPostRepository(Database("sqlite+pysqlite:///:memory:"))


def test_new_posts_wait_for_a_headline_and_known_posts_only_refresh_their_likes() -> None:
    posts = repository()
    context = SocialPostContext(
        relation="quoted",
        text="Els Moixiganguers van posar quints a la tde9fm.",
        author=SocialAuthor("13", "revistacastells", "Revista Castells"),
    )
    reply_context = SocialPostContext(relation="replied_to", text="Post original")
    discovered = social_post("1", likes=10, context=(context, reply_context))

    assert posts.save_candidates([discovered], seen_at=NOW) == 1
    edited = replace(discovered, text="Text editat després", like_count=40)
    assert posts.save_candidates([edited], seen_at=NOW + timedelta(minutes=5)) == 0

    # The headline must describe what was discovered, so only engagement changes.
    assert posts.pending_headlines(limit=10) == [replace(discovered, like_count=40)]


def test_pending_posts_are_newest_first_and_decisions_are_final() -> None:
    posts = repository()
    older = social_post("1", published_at=NOW - timedelta(hours=2))
    newer = social_post("2", published_at=NOW - timedelta(hours=1))
    posts.save_candidates([older, newer], seen_at=NOW)

    assert [post.post_id for post in posts.pending_headlines(limit=10)] == ["2", "1"]
    assert [post.post_id for post in posts.pending_headlines(limit=1)] == ["2"]

    posts.record_headline(newer, ACCEPTED, decided_at=NOW)
    posts.record_headline(older, REJECTED, decided_at=NOW)
    posts.record_headline(older, ACCEPTED, decided_at=NOW + timedelta(minutes=1))

    assert posts.pending_headlines(limit=10) == []
    assert posts.accepted_since(NOW - timedelta(days=1), limit=10) == [
        HeadlinedPost(post=newer, headline="Titular")
    ]


def test_failed_headlines_are_retried_until_the_attempt_limit() -> None:
    posts = repository()
    post = social_post("1")
    posts.save_candidates([post], seen_at=NOW)

    assert posts.record_headline_failure(post, "TimeoutError", max_attempts=2) is False
    assert [pending.post_id for pending in posts.pending_headlines(limit=10)] == ["1"]
    assert posts.record_headline_failure(post, "TimeoutError", max_attempts=2) is True
    assert posts.pending_headlines(limit=10) == []
    assert posts.record_headline_failure(post, "TimeoutError", max_attempts=2) is False
    posts.record_headline(post, ACCEPTED, decided_at=NOW)
    assert posts.accepted_since(NOW - timedelta(days=1), limit=10) == []


def test_accepted_posts_are_limited_to_the_publication_window() -> None:
    posts = repository()
    old = social_post("old", published_at=NOW - timedelta(days=8))
    recent = [
        social_post(f"recent-{hour}", published_at=NOW - timedelta(hours=hour)) for hour in (1, 2)
    ]
    posts.save_candidates([old, *recent], seen_at=NOW)
    for post in [old, *recent]:
        posts.record_headline(post, ACCEPTED, decided_at=NOW)

    window = posts.accepted_since(NOW - timedelta(days=7), limit=10)

    assert [item.post.post_id for item in window] == ["recent-1", "recent-2"]
    assert len(posts.accepted_since(NOW - timedelta(days=7), limit=1)) == 1


def test_a_hidden_post_leaves_the_feed_and_is_never_published_again() -> None:
    database = Database("sqlite+pysqlite:///:memory:")
    posts = SQLAlchemySocialPostRepository(database)
    feed = SQLAlchemyHourByHourRepository(database)
    post, other = social_post("1"), social_post("2")
    posts.save_candidates([post, other], seen_at=NOW)
    for item in (post, other):
        posts.record_headline(item, ACCEPTED, decided_at=NOW)
    feed.upsert_hour_by_hour([hour_item("1", source_id="x"), hour_item("2", source_id="x")])

    assert posts.hide("x", "1") is True

    assert [item.external_id for item in feed.list_hour_by_hour(0, 10)] == ["2"]
    assert [item.post.post_id for item in posts.accepted_since(NOW - timedelta(days=1), 10)] == [
        "2"
    ]
    posts.save_candidates([post], seen_at=NOW + timedelta(minutes=5))
    assert posts.pending_headlines(limit=10) == []
    assert posts.hide("x", "unknown") is False


def test_hiding_a_post_cancels_the_notifications_it_has_not_sent() -> None:
    database = Database("sqlite+pysqlite:///:memory:")
    posts = SQLAlchemySocialPostRepository(database)
    notifications = SQLAlchemyNotificationRepository(database)
    SQLAlchemyPushSubscriptionRepository(database).register(
        PushSubscriptionRegistration(
            installation_id="install",
            device_token="ab" * 32,
            app_version="1.0 (1)",
            locale="ca-ES",
            minimum_interest=InterestLevel.LOW,
        ),
        environment="production",
        topic="app",
    )
    classified, unclassified, other = social_post("1"), social_post("2"), social_post("3")
    posts.save_candidates([classified, unclassified, other], seen_at=NOW)
    for post in (classified, unclassified, other):
        posts.record_headline(post, ACCEPTED, decided_at=NOW)
    ingest(notifications, [hour_item("baseline", source_id="x")])
    # Classified: a delivery per subscription waits for APNs.
    ingest(notifications, [hour_item("1", source_id="x"), hour_item("3", source_id="x")])
    # Discovered but not classified yet: Jev must not create deliveries after the withdrawal.
    notifications.ingest_hour_by_hour([hour_item("2", source_id="x")])

    assert posts.hide("x", "1") is True
    assert posts.hide("x", "2") is True

    assert notifications.pending_classifications() == []
    assert [delivery.title for delivery in notifications.claim_deliveries(limit=10)] == [
        "Notícia 3"
    ]
    with Session(database.engine) as session:
        cancelled = session.scalars(
            select(NotificationDeliveryRecord).where(NotificationDeliveryRecord.status == "skipped")
        ).all()
    assert [delivery.last_error for delivery in cancelled] == ["Hidden"]
