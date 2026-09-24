from pathlib import Path
from unittest.mock import Mock

import pytest
import requests

from backend.adapters.content.revista_castells import RevistaCastellsHTMLSource
from backend.adapters.persistence.database import Database
from backend.adapters.persistence.hour_by_hour_repository import SQLAlchemyHourByHourRepository
from backend.adapters.persistence.models import Base
from backend.adapters.persistence.notification_repository import SQLAlchemyNotificationRepository
from backend.composition.providers import build_hour_by_hour_source
from backend.config import Settings
from backend.jobs import sync_hour_by_hour
from tests.support.application import make_test_client

FIXTURES = Path(__file__).parents[1] / "fixtures"
ELMON_FEED = (FIXTURES / "el_mon_casteller.xml").read_text()
REVISTA_HTML = (FIXTURES / "revista_hour_by_hour.html").read_text()


@pytest.mark.parametrize("via_cron", [False, True], ids=["manual-job", "cron"])
def test_sync_adds_the_new_publisher_without_alerting_old_articles(monkeypatch, via_cron):
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
    feed = ELMON_FEED

    def get(url, **kwargs):
        if url == settings.revista_castells_url:
            return Mock(text=REVISTA_HTML)
        return Mock(content=feed.encode())

    monkeypatch.setattr(requests, "get", get)
    monkeypatch.setattr(
        "backend.composition.container.build_notification_gateway", lambda _: Mock()
    )
    monkeypatch.setattr(sync_hour_by_hour, "build_database", lambda _: database)
    client = make_test_client(
        settings=settings,
        database=database,
        hour_by_hour_repository=content,
        notification_repository=notifications,
    )

    def sync():
        if via_cron:
            response = client.get(
                "/internal/cron/hour-by-hour",
                headers={"Authorization": "Bearer test-secret"},
            )
            assert response.status_code == 200
            return response.json()
        assert sync_hour_by_hour.sync_once(settings) == 0
        return None

    baseline = sync()
    if via_cron:
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
    if via_cron:
        assert update["notifications_created"] == 1
        assert repeated["notifications_created"] == 0


def test_source_switch_still_disables_all_publishers() -> None:
    assert build_hour_by_hour_source(Settings(hour_by_hour_source_enabled=False)) is None
