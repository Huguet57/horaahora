from backend.config import Settings
from tests.support.application import make_test_client


def test_hour_by_hour_contract_is_paginated() -> None:
    response = make_test_client().get("/v1/hour-by-hour?limit=30")

    assert response.status_code == 200
    assert response.json() == {"items": [], "next_cursor": None, "from_cache": True}


def test_pull_to_refresh_reads_persisted_content_without_fetching_source() -> None:
    class RecordingSource:
        def __init__(self) -> None:
            self.fetch_count = 0

        def fetch(self):
            self.fetch_count += 1
            return []

    source = RecordingSource()
    client = make_test_client(
        settings=Settings(
            database_url="sqlite://",
            hour_by_hour_source_enabled=False,
            ai_provider="local",
            rate_limit_max_requests=100,
        ),
        hour_by_hour_source=source,
        notification_coordinator=CoordinatorStub(),
    )

    response = client.get("/v1/hour-by-hour?limit=30&refresh=true")

    assert response.status_code == 200
    assert source.fetch_count == 0


class CoordinatorStub:
    def run(self):
        raise AssertionError("Refresh requests must not run notification delivery")
