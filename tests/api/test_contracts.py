from pathlib import Path

from fastapi.testclient import TestClient

from backend.adapters.content.cccc_agenda import CCCCAgendaFixtureSource
from backend.app import create_app
from backend.adapters.persistence.database import Database
from backend.application.notifications import NotificationRunResult
from backend.composition.providers import build_agenda_source
from backend.config import Settings
from backend.domain.notifications.models import PushSubscriptionRegistration
from tests.support.application import application_overrides


def make_client() -> TestClient:
    settings = Settings(
        database_url="sqlite://",
        hour_by_hour_source_enabled=False,
        ai_provider="local",
        rate_limit_max_requests=100,
    )
    app = create_app(
        settings=settings,
        overrides=application_overrides(),
    )
    return TestClient(app)


class RecordingPushRepository:
    def __init__(self) -> None:
        self.registrations: list[tuple[PushSubscriptionRegistration, str, str]] = []
        self.unregistrations: list[tuple[str, str, str]] = []

    def register(self, registration, *, environment, topic):
        self.registrations.append((registration, environment, topic))

    def unregister(self, installation_id, *, environment, topic):
        self.unregistrations.append((installation_id, environment, topic))


def test_push_subscription_contract_registers_and_unregisters_current_installation() -> None:
    repository = RecordingPushRepository()
    settings = Settings(
        database_url="sqlite://",
        hour_by_hour_source_enabled=False,
        ai_provider="local",
        apns_bundle_id="com.example.app",
        vercel_env="production",
    )
    app = create_app(
        settings=settings,
        overrides=application_overrides(push_repository=repository),
    )
    client = TestClient(app)

    registered = client.put(
        "/v1/push-subscriptions/install-1",
        json={
            "device_token": "ab" * 32,
            "app_version": "1.0 (3)",
            "locale": "ca-ES",
            "environment": "development",
        },
    )
    removed = client.delete(
        "/v1/push-subscriptions/install-1?environment=development"
    )

    assert registered.status_code == 204
    assert removed.status_code == 204
    assert repository.registrations[0][0].device_token == "ab" * 32
    assert repository.registrations[0][1:] == ("development", "com.example.app")
    assert repository.unregistrations == [("install-1", "development", "com.example.app")]


class NotificationRepositoryStub(RecordingPushRepository):
    def cleanup(self):
        return {
            "subscriptions_invalidated": 1,
            "deliveries_deleted": 2,
            "outboxes_deleted": 1,
        }


class CoordinatorStub:
    def __init__(self) -> None:
        self.call_count = 0

    def run(self):
        self.call_count += 1
        return NotificationRunResult(status="completed", delivered=3)


def test_cron_routes_require_production_secret_and_return_persisted_results() -> None:
    notifications = NotificationRepositoryStub()
    coordinator = CoordinatorStub()
    database = Database("sqlite+pysqlite:///:memory:")
    settings = Settings(
        database_url="sqlite+pysqlite:///:memory:",
        hour_by_hour_source_enabled=False,
        vercel_env="production",
        cron_secret="cron-secret",
    )
    app = create_app(
        settings=settings,
        overrides=application_overrides(
            database=database,
            push_repository=notifications,
            notification_repository=notifications,
            notification_coordinator=coordinator,
        ),
    )
    client = TestClient(app)

    assert client.get("/internal/cron/hour-by-hour").status_code == 401
    response = client.get(
        "/internal/cron/hour-by-hour",
        headers={"Authorization": "Bearer cron-secret"},
    )

    assert response.status_code == 200
    assert response.json()["delivered"] == 3
    assert coordinator.call_count == 1


def test_readiness_returns_503_when_neon_is_unavailable(monkeypatch) -> None:
    database = Database("sqlite+pysqlite:///:memory:")
    monkeypatch.setattr(database, "is_ready", lambda: False)
    app = create_app(
        settings=Settings(
            database_url="sqlite+pysqlite:///:memory:",
            hour_by_hour_source_enabled=False,
        ),
        overrides=application_overrides(database=database),
    )

    assert TestClient(app).get("/health/ready").status_code == 503


def test_chat_contract_does_not_expose_provider() -> None:
    response = make_client().post(
        "/v1/chat",
        json={
            "conversation_id": "3a35386d-f0e4-49cc-86d2-18fac079645c",
            "installation_id": "test-installation",
            "locale": "ca-ES",
            "ruleset": "concurs-2026",
            "messages": [{"role": "user", "content": "5d9f o 4d9fa?"}],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["winner_label"] == "Amb 4d9fa"
    assert "provider" not in payload
    assert "model" not in payload


def test_hour_by_hour_contract_is_paginated() -> None:
    response = make_client().get("/v1/hour-by-hour?limit=30")

    assert response.status_code == 200
    assert response.json() == {"items": [], "next_cursor": None, "from_cache": True}


def test_hour_by_hour_pull_to_refresh_reads_persisted_content_without_fetching_source() -> None:
    class RecordingSource:
        def __init__(self) -> None:
            self.fetch_count = 0

        def fetch(self):
            self.fetch_count += 1
            return []

    source = RecordingSource()
    settings = Settings(
        database_url="sqlite://",
        hour_by_hour_source_enabled=False,
        ai_provider="local",
        rate_limit_max_requests=100,
    )
    app = create_app(
        settings=settings,
        overrides=application_overrides(
            hour_by_hour_source=source,
            notification_coordinator=CoordinatorStub(),
        ),
    )

    response = TestClient(app).get("/v1/hour-by-hour?limit=30&refresh=true")

    assert response.status_code == 200
    assert source.fetch_count == 0


def test_privacy_page_is_localized_and_explains_prefilled_support_email() -> None:
    response = make_client().get("/privacy")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert 'lang="ca"' in response.text
    assert 'href="/privacy/ca"' in response.text
    assert 'href="/privacy/es"' in response.text
    assert 'href="/privacy/en"' in response.text
    assert "correu editable" in response.text
    assert "només es transmet si revises el correu i prems manualment" in response.text
    assert "<script" not in response.text.lower()


def test_disabled_agenda_has_a_neutral_unavailable_contract() -> None:
    response = make_client().get("/v1/events?from=2026-07-21&to=2026-07-21")

    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "next_cursor": None,
        "official_url": "https://castellscat.cat/ca/agenda",
        "from_cache": True,
        "source_status": "unavailable",
    }
    assert response.headers["cache-control"] == "public, s-maxage=300, stale-while-revalidate=86400"


def test_forced_agenda_refresh_is_not_http_cached() -> None:
    response = make_client().get(
        "/v1/events?from=2026-07-21&to=2026-07-21&refresh=true"
    )

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"


def test_agenda_rejects_ranges_longer_than_a_year() -> None:
    response = make_client().get("/v1/events?from=2025-01-01&to=2026-07-21")

    assert response.status_code == 400


def test_agenda_fixture_contract_supports_cache_and_filters() -> None:
    fixture = Path(__file__).parents[2] / "backend" / "data" / "cccc_agenda_fixture.html"
    settings = Settings(
        database_url="sqlite://",
        hour_by_hour_source_enabled=False,
        agenda_source="disabled",
        agenda_refresh_on_request=True,
        ai_provider="local",
        rate_limit_max_requests=100,
    )
    app = create_app(
        settings=settings,
        overrides=application_overrides(
            agenda_source=CCCCAgendaFixtureSource(fixture),
        ),
    )
    client = TestClient(app)

    first = client.get(
        "/v1/events?from=2026-07-21&to=2026-07-21&municipality=Vàlls&limit=50"
    )
    second = client.get(
        "/v1/events?from=2026-07-21&to=2026-07-21&municipality=Vàlls&limit=50"
    )

    assert first.status_code == 200
    payload = first.json()
    assert payload["source_status"] == "active"
    assert payload["from_cache"] is False
    assert len(payload["items"]) == 1
    assert payload["items"][0]["local_date"] == "2026-07-21"
    assert payload["items"][0]["time_label"] == "12:00"
    assert payload["items"][0]["starts_at"] is not None
    assert payload["items"][0]["source_id"] == "cccc-fixture"
    assert payload["items"][0]["attribution"] == "Dades de demostració — no oficials"
    assert second.json()["from_cache"] is True


def test_live_cccc_html_source_requires_explicit_authorization() -> None:
    settings = Settings(agenda_source="cccc_html", cccc_agenda_authorized=False)

    try:
        build_agenda_source(settings)
    except RuntimeError as error:
        assert "CCCC_AGENDA_AUTHORIZED" in str(error)
    else:
        raise AssertionError("The live CCCC source must require explicit authorization")
