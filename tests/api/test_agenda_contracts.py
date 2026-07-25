from pathlib import Path

from backend.adapters.content.cccc_agenda import CCCCAgendaFixtureSource
from backend.adapters.content.group_directory import load_group_directory
from backend.composition.providers import build_agenda_source
from backend.config import Settings
from tests.support.application import make_test_client


def test_group_directory_snapshot_is_non_empty_sorted_and_unique() -> None:
    directory = load_group_directory()

    assert len(directory.groups) > 80
    assert directory.groups == sorted(directory.groups, key=str.casefold)
    assert len(directory.groups) == len(set(directory.groups))


def test_group_directory_exposes_the_versioned_official_snapshot() -> None:
    response = make_test_client().get("/v1/groups")

    assert response.status_code == 200
    payload = response.json()
    assert payload["revision"] == "2026-07-25"
    assert payload["official_url"] == "https://castellscat.cat/public/ca/les-colles-llistat"
    assert len(payload["groups"]) > 80
    assert len(payload["groups"]) == len(set(payload["groups"]))
    assert payload["groups"] == sorted(payload["groups"], key=str.casefold)
    assert {
        "Castellers de Vilafranca",
        "Castellers de Rubí",
        "Castellers del Lluçanès",
        "Arreplegats de la Zona Universitària",
        "Castellers de Sydney",
    } <= set(payload["groups"])
    assert response.headers["cache-control"] == (
        "public, s-maxage=86400, stale-while-revalidate=604800"
    )

    refreshed = make_test_client().get("/v1/groups?refresh=true")
    assert refreshed.headers["cache-control"] == "no-store"


def test_disabled_agenda_has_a_neutral_unavailable_contract() -> None:
    response = make_test_client().get("/v1/events?from=2026-07-21&to=2026-07-21")

    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "next_cursor": None,
        "official_url": "https://castellscat.cat/ca/agenda",
        "from_cache": True,
        "source_status": "unavailable",
    }
    assert response.headers["cache-control"] == (
        "public, s-maxage=300, stale-while-revalidate=86400"
    )


def test_forced_agenda_refresh_is_not_http_cached() -> None:
    response = make_test_client().get("/v1/events?from=2026-07-21&to=2026-07-21&refresh=true")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"


def test_agenda_rejects_ranges_longer_than_a_year() -> None:
    response = make_test_client().get("/v1/events?from=2025-01-01&to=2026-07-21")

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
    client = make_test_client(
        settings=settings,
        agenda_source=CCCCAgendaFixtureSource(fixture),
    )

    first = client.get("/v1/events?from=2026-07-21&to=2026-07-21&municipality=Vàlls&limit=50")
    second = client.get("/v1/events?from=2026-07-21&to=2026-07-21&municipality=Vàlls&limit=50")

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
