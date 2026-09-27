import json
from unittest.mock import Mock

import pytest

from backend.application.social_posts import SocialPostSyncResult
from backend.config import Settings
from backend.jobs import sync_x_posts


def test_manual_job_runs_the_configured_tracker_and_reports_the_result(monkeypatch, capsys):
    database, hour_repository = object(), object()
    result = SocialPostSyncResult(status="completed", discovered=2, accepted=1)
    factory = Mock(return_value=Mock(run=Mock(return_value=result)))
    monkeypatch.setattr(sync_x_posts, "build_database", lambda _: database)
    monkeypatch.setattr(sync_x_posts, "build_hour_by_hour_repository", lambda _: hour_repository)
    monkeypatch.setattr(sync_x_posts, "build_social_post_sync", factory)
    settings = Settings(x_posts_mode="shadow")

    assert sync_x_posts.sync_once(settings) == 0

    factory.assert_called_once_with(settings, database, hour_repository)
    output = json.loads(capsys.readouterr().out)
    assert output["event"] == "x_posts_sync_finished"
    assert (output["status"], output["discovered"], output["accepted"]) == ("completed", 2, 1)


def test_disabled_job_stops_before_accessing_the_database(monkeypatch):
    database = Mock(side_effect=AssertionError("A disabled tracker must not access the database"))
    monkeypatch.setattr(sync_x_posts, "build_database", database)

    with pytest.raises(RuntimeError, match="X_POSTS_MODE"):
        sync_x_posts.sync_once(Settings())

    database.assert_not_called()
