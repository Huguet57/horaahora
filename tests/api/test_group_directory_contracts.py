from tests.support.application import make_test_client


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
