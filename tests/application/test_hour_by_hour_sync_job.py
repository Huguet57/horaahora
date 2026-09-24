import json
from unittest.mock import Mock

import pytest

from backend.config import Settings
from backend.domain.notifications.models import NotificationIngestionResult
from backend.jobs import sync_hour_by_hour
from tests.support.hour_by_hour import hour_item


def test_manual_job_ingests_the_configured_sources_and_reports_the_result(monkeypatch, capsys):
    items = [hour_item("revista-one"), hour_item("elmon-one", source_id="el-mon-casteller")]
    source = Mock(fetch=Mock(return_value=items))
    repository = Mock(ingest_hour_by_hour=Mock(return_value=NotificationIngestionResult(True, 0)))
    factory = Mock(return_value=source)
    monkeypatch.setattr(sync_hour_by_hour, "build_hour_by_hour_source", factory)
    monkeypatch.setattr(sync_hour_by_hour, "build_database", lambda _: object())
    monkeypatch.setattr(sync_hour_by_hour, "build_notification_repository", lambda _: repository)
    settings = Settings()

    assert sync_hour_by_hour.sync_once(settings) == 0

    factory.assert_called_once_with(settings)
    source.fetch.assert_called_once_with()
    repository.ingest_hour_by_hour.assert_called_once_with(items)
    assert json.loads(capsys.readouterr().out) == {
        "event": "hour_by_hour_sync_finished",
        "baseline_created": True,
        "notifications_created": 0,
    }


def test_disabled_job_stops_before_accessing_the_database(monkeypatch):
    database = Mock(side_effect=AssertionError("Disabled ingestion must not access the database"))
    monkeypatch.setattr(sync_hour_by_hour, "build_database", database)

    with pytest.raises(RuntimeError, match="HOUR_BY_HOUR_SOURCE_ENABLED"):
        sync_hour_by_hour.sync_once(Settings(hour_by_hour_source_enabled=False))

    database.assert_not_called()
