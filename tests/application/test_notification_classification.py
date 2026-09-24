import time
from dataclasses import replace

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.adapters.persistence.hour_by_hour_repository import SQLAlchemyHourByHourRepository
from backend.adapters.persistence.models import (
    NotificationDeliveryRecord,
    NotificationOutboxRecord,
)
from backend.application.notification_ingestion import NotificationIngestionService
from backend.application.notifications import HourByHourNotificationCoordinator
from backend.domain.notifications.interest import (
    GroupSelection,
    InterestClassification,
    InterestLevel,
)
from tests.application.test_notifications import (
    AcceptingGateway,
    MutableSource,
    hour_item,
    registration,
    repositories,
)
from tests.support.notifications import queue_recipients_before_threshold_changes


class Classifier:
    def __init__(self, level=InterestLevel.MEDIUM, groups=frozenset({"a"}), fail=False):
        self.calls = 0
        self.level, self.groups, self.fail = level, groups, fail

    def classify(self, title, summary, groups, *, timeout, content=None):
        self.calls += 1
        if self.fail:
            raise TimeoutError()
        return InterestClassification(self.level, self.groups, "test-model", "v1", {}, 1.0)


def test_classifies_once_and_filters_with_personalized_interest():
    subscriptions, repo = repositories()
    subscriptions.register(
        replace(
            registration(),
            minimum_interest=InterestLevel.HIGH,
            group_selection=GroupSelection("custom", frozenset({"a"})),
        ),
        environment="production",
        topic="app",
    )
    classifier = Classifier()
    service = NotificationIngestionService(repo, classifier, ["a"])
    service.ingest([hour_item("baseline")])
    assert classifier.calls == 0
    service.ingest([hour_item("new"), hour_item("baseline")])
    service.ingest([hour_item("new"), hour_item("baseline")])
    assert classifier.calls == 1
    assert len(repo.claim_deliveries(10)) == 1


def test_jev_failure_is_terminal_but_content_is_saved():
    subscriptions, repo = repositories()
    subscriptions.register(registration(), environment="production", topic="app")
    classifier = Classifier(fail=True)
    service = NotificationIngestionService(repo, classifier, [])
    service.ingest([hour_item("baseline")])
    result = service.ingest([hour_item("new")])
    service.ingest([hour_item("new")])
    assert classifier.calls == 1
    assert result.classification_skipped == 1
    assert repo.claim_deliveries(10) == []
    assert SQLAlchemyHourByHourRepository(repo.database).count_hour_by_hour() == 2
    with Session(repo.engine) as session:
        record = session.scalar(
            select(NotificationOutboxRecord).where(NotificationOutboxRecord.external_id == "new")
        )
        assert record.classification_status == "skipped"
        assert record.audience == []


def test_budget_defers_unstarted_items_without_adding_later_subscribers():
    subscriptions, repo = repositories()
    classifier = Classifier()
    service = NotificationIngestionService(repo, classifier, [])
    service.ingest([hour_item("baseline")])
    service.ingest([hour_item("new")], deadline=time.monotonic() - 1)
    assert classifier.calls == 0
    subscriptions.register(registration(), environment="production", topic="app")
    service.ingest([])
    assert classifier.calls == 1
    assert repo.claim_deliveries(10) == []


def test_interrupted_attempt_is_not_repeated():
    _, repo = repositories()
    classifier = Classifier()
    service = NotificationIngestionService(repo, classifier, [])
    service.ingest([hour_item("baseline")])
    repo.ingest_hour_by_hour([hour_item("new")])
    candidate = repo.pending_classifications()[0]
    assert repo.begin_classification(candidate.id)
    result = service.ingest([])
    assert result.classification_skipped == 1
    assert classifier.calls == 0
    assert repo.pending_classifications() == []


def test_changing_selection_does_not_retroactively_expand_audience():
    subscriptions, repo = repositories()
    original = replace(registration(), minimum_interest=InterestLevel.HIGH)
    subscriptions.register(original, environment="production", topic="app")
    service = NotificationIngestionService(repo, Classifier(), ["a"])
    service.ingest([hour_item("baseline")])
    service.ingest([hour_item("new")], deadline=time.monotonic() - 1)
    subscriptions.register(
        replace(original, group_selection=GroupSelection("custom", frozenset({"a"}))),
        environment="production",
        topic="app",
    )
    service.ingest([])
    assert repo.claim_deliveries(10) == []


def test_old_clients_preserve_preferences_and_pending_deliveries_are_rechecked():
    subscriptions, repo = repositories()
    selected = replace(
        registration(),
        minimum_interest=InterestLevel.MEDIUM,
        group_selection=GroupSelection("custom", frozenset({"a"})),
    )
    subscriptions.register(selected, environment="production", topic="app")
    subscriptions.register(registration(), environment="production", topic="app")
    active = subscriptions.list_active_subscriptions()[0]
    assert active.minimum_interest is InterestLevel.MEDIUM
    assert active.group_selection == selected.group_selection
    service = NotificationIngestionService(repo, Classifier(InterestLevel.LOW), ["a"])
    service.ingest([hour_item("baseline")])
    service.ingest([hour_item("new")])
    subscriptions.register(
        replace(selected, minimum_interest=InterestLevel.HIGH),
        environment="production",
        topic="app",
    )
    assert repo.claim_deliveries(10) == []
    subscriptions.register(selected, environment="production", topic="app")
    assert repo.claim_deliveries(10) == []


@pytest.mark.parametrize(
    ("eligibility", "limit", "expected"),
    [
        ([False] * 5 + [True] * 3, 2, [5, 6]),
        ([True, False, False, False, True, True], 2, [0, 4]),
        ([False] * 5 + [True], 2, [5]),
        ([False] * 5, 2, []),
        ([False, True, True], 1, [1]),
    ],
)
def test_claim_refills_after_preference_skips_and_respects_limit(eligibility, limit, expected):
    subscriptions, repo = repositories()
    queue_recipients_before_threshold_changes(subscriptions, repo, eligibility)

    claimed = repo.claim_deliveries(limit)

    assert [delivery.id for delivery in claimed] == [f"queued-{index}" for index in expected]
    if len(expected) < limit:
        with Session(repo.engine) as session:
            assert all(
                delivery.status == "skipped"
                for delivery in session.scalars(select(NotificationDeliveryRecord))
                if not eligibility[int(delivery.id.removeprefix("queued-"))]
            )
    remaining = repo.claim_deliveries(100)
    assert {delivery.id for delivery in remaining} == {
        f"queued-{index}"
        for index, eligible in enumerate(eligibility)
        if eligible and index not in expected
    }
    with Session(repo.engine) as session:
        for delivery in session.scalars(select(NotificationDeliveryRecord)):
            index = int(delivery.id.removeprefix("queued-"))
            if eligibility[index]:
                assert delivery.status == "processing"
                assert delivery.attempt_count == 1
            else:
                assert delivery.status == "skipped"
                assert delivery.last_error == "PreferenceChanged"
                assert delivery.locked_until is None
                assert delivery.attempt_count == 0


def test_coordinator_sends_eligible_recipients_in_the_same_run_after_skips():
    subscriptions, repo = repositories()
    service = queue_recipients_before_threshold_changes(
        subscriptions, repo, [False] * 5 + [True] * 3
    )
    gateway = AcceptingGateway()
    result = HourByHourNotificationCoordinator(
        repo,
        MutableSource([]),
        gateway,
        enabled=True,
        ingestion_service=service,
        batch_size=2,
    ).run()

    assert result.attempted == result.delivered == 2
    assert [delivery.id for delivery in gateway.deliveries] == ["queued-5", "queued-6"]


class ArticleSource:
    def __init__(self, text="La millor diada de la seva història.", error=None):
        self.text, self.error, self.calls = text, error, []

    def fetch(self, url, *, timeout):
        self.calls.append((url, timeout))
        if self.error:
            raise self.error
        return self.text


class ContentClassifier(Classifier):
    def classify(self, title, summary, groups, *, timeout, content=None):
        self.received_content = content
        return super().classify(title, summary, groups, timeout=timeout)


def test_article_is_fetched_once_and_forwarded_before_classification():
    _, repo = repositories()
    classifier, articles = ContentClassifier(), ArticleSource()
    service = NotificationIngestionService(repo, classifier, [], article_source=articles)
    service.ingest([hour_item("baseline")])
    assert articles.calls == []
    item = replace(hour_item("new"), action_url="https://revistacastells.cat/cronica/")
    service.ingest([item])
    service.ingest([item])
    assert classifier.calls == 1
    assert classifier.received_content.text == articles.text
    assert len(articles.calls) == 1
    assert articles.calls[0][0] == item.action_url


@pytest.mark.parametrize("error", [None, TimeoutError(), ValueError("invalid page")])
def test_article_unavailable_falls_back_to_summary(error):
    subscriptions, repo = repositories()
    subscriptions.register(registration(), environment="production", topic="app")
    classifier = ContentClassifier()
    service = NotificationIngestionService(
        repo, classifier, [], article_source=ArticleSource(text="", error=error)
    )
    service.ingest([hour_item("baseline")])
    result = service.ingest([hour_item("new")])
    assert result.classified == 1
    assert result.classification_skipped == 0
    assert classifier.received_content is None
    assert len(repo.claim_deliveries(10)) == 1


def test_article_fetch_that_exhausts_budget_leaves_jev_unstarted(monkeypatch):
    _, repo = repositories()
    classifier = ContentClassifier()
    clock = [100.0]
    monkeypatch.setattr(
        "backend.application.notification_ingestion.time.monotonic", lambda: clock[0]
    )

    class SlowSource(ArticleSource):
        def fetch(self, url, *, timeout):
            clock[0] += 2
            return self.text

    service = NotificationIngestionService(repo, classifier, [], article_source=SlowSource())
    service.ingest([hour_item("baseline")])
    result = service.ingest([hour_item("new")], deadline=101)
    assert result.classified == result.classification_skipped == 0
    assert classifier.calls == 0
    assert len(repo.pending_classifications()) == 1
    service.ingest([], deadline=110)
    assert classifier.calls == 1


@pytest.mark.parametrize("separate_link", [False, True])
def test_content_provenance_is_frozen_when_discovered(separate_link):
    _, repo = repositories()
    classifier, articles = ContentClassifier(), ArticleSource()
    service = NotificationIngestionService(repo, classifier, [], article_source=articles)
    service.ingest([hour_item("baseline")])
    article_url = "https://revistacastells.cat/hora-a-hora/actualitat/"
    target = "https://revistacastells.cat/2015/perfil/" if separate_link else article_url
    item = replace(hour_item("new"), article_url=article_url, action_url=target)
    service.ingest([item], deadline=time.monotonic() - 1)
    # A feed refresh must not change the reference paired with the queued title/summary.
    changed = replace(item, article_url=target, action_url=None)
    service.ingest([changed])
    content = classifier.received_content
    assert content.text == articles.text
    assert content.url == target
    assert content.role == ("linked_context" if separate_link else "article_body")
    with Session(repo.engine) as session:
        record = session.scalar(
            select(NotificationOutboxRecord).where(NotificationOutboxRecord.external_id == "new")
        )
        assert record.article_url == article_url


def test_pre_migration_pending_content_has_conservative_provenance():
    _, repo = repositories()
    classifier, articles = ContentClassifier(), ArticleSource()
    service = NotificationIngestionService(repo, classifier, [], article_source=articles)
    service.ingest([hour_item("baseline")])
    service.ingest([hour_item("new")], deadline=time.monotonic() - 1)
    with Session(repo.engine) as session, session.begin():
        record = session.scalar(
            select(NotificationOutboxRecord).where(NotificationOutboxRecord.external_id == "new")
        )
        record.article_url = ""
    service.ingest([])
    assert classifier.received_content.role == "linked_context"
