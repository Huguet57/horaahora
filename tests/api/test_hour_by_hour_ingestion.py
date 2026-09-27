from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

import requests

from backend.adapters.content.el_mon_casteller import ElMonCastellerRSSSource
from backend.adapters.content.revista_castells import RevistaCastellsHTMLSource
from backend.adapters.persistence.database import Database
from backend.adapters.persistence.hour_by_hour_repository import SQLAlchemyHourByHourRepository
from backend.adapters.persistence.models import Base
from backend.adapters.persistence.notification_repository import SQLAlchemyNotificationRepository
from backend.config import Settings
from tests.support.application import make_test_client

FIXTURES = Path(__file__).parents[1] / "fixtures"
ELMON_FEED = (FIXTURES / "el_mon_casteller.xml").read_text()
REVISTA_HTML = (FIXTURES / "revista_hour_by_hour.html").read_text()


def test_cron_ingests_both_publishers_and_exposes_deduplicated_articles_in_the_api(monkeypatch):
    database = Database("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(database.engine)
    content = SQLAlchemyHourByHourRepository(database)
    notifications = SQLAlchemyNotificationRepository(database)
    notifications.ingest_hour_by_hour(RevistaCastellsHTMLSource().parse(REVISTA_HTML))
    settings = Settings(
        database_url="sqlite+pysqlite:///:memory:",
        hour_by_hour_sources=("revista-castells", "el-mon-casteller"),
        revista_castells_url="https://revista.example/hora-a-hora/",
        vercel_env="production",
        cron_secret="test-secret",
        push_delivery_enabled=True,
    )
    feed = ELMON_FEED

    def get(url, **kwargs):
        if url == settings.revista_castells_url:
            return Mock(text=REVISTA_HTML)
        return Mock(content=feed.encode())

    monkeypatch.setattr(requests, "get", get)
    monkeypatch.setattr(
        "backend.composition.container.build_notification_gateway", lambda _: Mock()
    )
    client = make_test_client(
        settings=settings,
        database=database,
        hour_by_hour_repository=content,
        notification_repository=notifications,
    )

    def sync():
        response = client.get(
            "/internal/cron/hour-by-hour",
            headers={"Authorization": "Bearer test-secret"},
        )
        assert response.status_code == 200
        return response.json()

    baseline = sync()
    assert baseline["notifications_created"] == 0
    page = client.get("/v1/hour-by-hour?limit=30").json()
    assert len(page["items"]) == 4
    assert [item["source_id"] for item in page["items"]] == [
        "el-mon-casteller",
        "el-mon-casteller",
        "revista-castells",
        "revista-castells",
    ]
    assert page["items"][0]["action_url"] == "https://www.elmoncasteller.cat/una-diada/"
    assert page["items"][0]["attribution"] == "El Món Casteller"
    assert notifications.claim_deliveries(limit=10) == []

    # A new article shared by all four feeds must generate only one notification.
    feed = ELMON_FEED.replace("?p=123", "?p=124").replace("una-diada/", "nova-diada/")
    update = sync()
    repeated = sync()
    assert content.count_hour_by_hour() == 5
    assert update["notifications_created"] == 1
    assert repeated["notifications_created"] == 0


def test_disabled_revista_castells_keeps_its_articles_and_returns_without_a_burst(monkeypatch):
    database = Database("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(database.engine)
    content = SQLAlchemyHourByHourRepository(database)
    notifications = SQLAlchemyNotificationRepository(database)
    notifications.ingest_hour_by_hour(RevistaCastellsHTMLSource().parse(REVISTA_HTML))
    settings = Settings(
        database_url="sqlite+pysqlite:///:memory:",
        vercel_env="production",
        cron_secret="test-secret",
        push_delivery_enabled=True,
    )
    revista_html = REVISTA_HTML
    requested_urls = []

    def get(url, **kwargs):
        requested_urls.append(url)
        if url == settings.revista_castells_url:
            return Mock(text=revista_html)
        return Mock(content=ELMON_FEED.encode())

    monkeypatch.setattr(requests, "get", get)
    monkeypatch.setattr(
        "backend.composition.container.build_notification_gateway", lambda _: Mock()
    )

    def sync(**settings_values):
        client = make_test_client(
            settings=replace(settings, **settings_values),
            database=database,
            hour_by_hour_repository=content,
            notification_repository=notifications,
        )
        response = client.get(
            "/internal/cron/hour-by-hour",
            headers={"Authorization": "Bearer test-secret"},
        )
        assert response.status_code == 200
        return client, response.json()

    client, _ = sync()
    assert sorted(requested_urls) == sorted(ElMonCastellerRSSSource.FEED_URLS)
    page = client.get("/v1/hour-by-hour?limit=30").json()
    assert [item["source_id"] for item in page["items"]] == [
        "el-mon-casteller",
        "el-mon-casteller",
        "revista-castells",
        "revista-castells",
    ]

    # Back on, the article published meanwhile is listed without notifying it.
    both = ("revista-castells", "el-mon-casteller")
    revista_html = REVISTA_HTML.replace("/segona", "/tercera")
    _, resumed = sync(hour_by_hour_sources=both)
    revista_html = REVISTA_HTML.replace("/segona", "/quarta")
    _, latest = sync(hour_by_hour_sources=both)

    assert resumed["notifications_created"] == 0
    assert latest["notifications_created"] == 1
    assert content.count_hour_by_hour() == 6
