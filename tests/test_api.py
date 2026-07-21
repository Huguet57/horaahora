from pathlib import Path

from fastapi.testclient import TestClient

from backend.adapters.ai.local import RegexQueryInterpreter
from backend.adapters.content.cccc_agenda import CCCCAgendaFixtureSource
from backend.adapters.persistence.memory import InMemoryContentRepository
from backend.adapters.rate_limit.memory import InMemoryRateLimiter
from backend.app import build_agenda_source, create_app
from backend.config import Settings


def make_client() -> TestClient:
    settings = Settings(
        database_url="sqlite://",
        hour_by_hour_source_enabled=False,
        ai_provider="local",
        rate_limit_max_requests=100,
    )
    app = create_app(
        settings=settings,
        interpreter=RegexQueryInterpreter(),
        content_repository=InMemoryContentRepository(),
        rate_limiter=InMemoryRateLimiter(max_requests=100, window_seconds=60),
    )
    return TestClient(app)


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


def test_privacy_page_is_localized_and_explains_prefilled_support_email() -> None:
    response = make_client().get("/privacy")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert 'lang="ca"' in response.text
    assert 'data-language="es"' in response.text
    assert 'data-language="en"' in response.text
    assert "només s’envia quan prems manualment el botó d’enviament" in response.text
    assert "solo se envía cuando pulsas manualmente el botón de envío" in response.text
    assert "is only sent when you manually tap the send button" in response.text


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
    fixture = Path(__file__).parents[1] / "backend" / "data" / "cccc_agenda_fixture.html"
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
        interpreter=RegexQueryInterpreter(),
        content_repository=InMemoryContentRepository(),
        rate_limiter=InMemoryRateLimiter(max_requests=100, window_seconds=60),
        agenda_source=CCCCAgendaFixtureSource(fixture),
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
