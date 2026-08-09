from pathlib import Path

from fastapi.testclient import TestClient

from backend.api.routers.privacy import router as privacy_router
from backend.app import create_app
from backend.config import Settings
from tests.support.application import application_overrides


def make_client() -> TestClient:
    settings = Settings(
        database_url="sqlite://",
        hour_by_hour_source_enabled=False,
        rate_limit_max_requests=100,
    )
    app = create_app(
        settings=settings,
        overrides=application_overrides(),
    )
    return TestClient(app)


def test_privacy_index_is_catalan_and_links_every_language() -> None:
    response = make_client().get("/privacy")

    assert response.status_code == 200
    assert response.headers["content-language"] == "ca"
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert response.headers["cache-control"] == "public, max-age=3600"
    assert "set-cookie" not in response.headers
    assert '<html lang="ca">' in response.text
    assert 'href="/privacy/ca"' in response.text
    assert 'href="/privacy/es"' in response.text
    assert 'href="/privacy/en"' in response.text
    assert "correu editable" in response.text
    assert "només es transmet si revises el correu i prems manualment" in response.text
    assert "<script" not in response.text.lower()


def test_localized_privacy_pages_are_static_and_complete() -> None:
    expected_copy = {
        "ca": (
            "Política de privacitat",
            "correu editable",
            "número de build",
            "identificador tècnic",
            "prems manualment",
            "no exporta converses",
            "Dades desades només al dispositiu",
            "Dades tècniques",
            "Conservació",
            "Transferències internacionals",
            "RGPD",
            "drets",
            "menors",
            "tracking",
        ),
        "es": (
            "Política de privacidad",
            "correo editable",
            "número de build",
            "identificador técnico",
            "pulsas manualmente",
            "no exporta conversaciones",
            "Datos guardados únicamente en el dispositivo",
            "Datos técnicos",
            "Conservación",
            "Transferencias internacionales",
            "RGPD",
            "derechos",
            "menores",
            "seguimiento",
        ),
        "en": (
            "Privacy policy",
            "editable email",
            "build number",
            "technical identifier",
            "manually tap",
            "does not export conversations",
            "Data stored only on the device",
            "Technical data",
            "Retention",
            "International transfers",
            "GDPR",
            "rights",
            "children",
            "tracking",
        ),
    }
    client = make_client()

    for locale, required_copy in expected_copy.items():
        response = client.get(f"/privacy/{locale}")

        assert response.status_code == 200
        assert response.headers["content-language"] == locale
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        assert response.headers["cache-control"] == "public, max-age=3600"
        assert "set-cookie" not in response.headers
        assert f'<html lang="{locale}">' in response.text
        for linked_locale in ("ca", "es", "en"):
            assert f'href="/privacy/{linked_locale}"' in response.text
        for copy in required_copy:
            assert copy in response.text
        assert "Castells en vena" in response.text
        assert "Andreu Huguet" in response.text
        assert "tenimaletaapp@gmail.com" in response.text
        assert "12" in response.text
        assert "OpenAI" in response.text
        assert "store: false" in response.text
        assert "Vercel" in response.text
        assert "Neon" in response.text
        assert "cdg1" in response.text
        assert "Apple" in response.text
        assert "APNs" in response.text
        assert "Google" in response.text
        assert "Gmail" in response.text
        assert "AEPD" in response.text
        assert "CCCC" in response.text
        assert "Revista Castells" in response.text
        assert "TotCastells" not in response.text
        assert "<script" not in response.text.lower()
        assert "[nom" not in response.text.lower()
        assert "[correu" not in response.text.lower()
        assert "[data" not in response.text.lower()


def test_unknown_privacy_locale_is_not_found() -> None:
    response = make_client().get("/privacy/fr")

    assert response.status_code == 404


def test_privacy_routes_are_web_documents_owned_by_the_privacy_module() -> None:
    client = make_client()
    paths = client.app.openapi()["paths"]
    privacy_routes = {route.path: route for route in privacy_router.routes}

    assert {"/v1/chat", "/v1/events", "/v1/hour-by-hour"} <= set(paths)
    assert "/privacy" not in paths
    assert "/privacy/{locale}" not in paths
    assert set(privacy_routes) == {"/privacy", "/privacy/{locale}"}
    assert all(
        route.endpoint.__module__ == "backend.api.routers.privacy"
        for route in privacy_routes.values()
    )
    assert all(route.include_in_schema is False for route in privacy_routes.values())


def test_catalan_policy_document_has_no_draft_placeholders_or_old_name() -> None:
    policy_path = Path(__file__).parents[2] / "docs" / "privacy-policy-ca.md"
    policy = policy_path.read_text()

    assert policy.startswith("# Política de privacitat — Castells en vena")
    assert "Andreu Huguet" in policy
    assert "tenimaletaapp@gmail.com" in policy
    assert "correu editable" in policy
    assert "número de build" in policy
    assert "identificador tècnic" in policy
    assert "manualment" in policy
    assert "no exporta converses" in policy
    assert "`store: false`" in policy
    assert "`cdg1`" in policy
    assert "TotCastells" not in policy
    assert "[nom" not in policy.lower()
    assert "[correu" not in policy.lower()
    assert "[data" not in policy.lower()


def test_only_explicit_conversation_sharing_remains_pending() -> None:
    followups_path = Path(__file__).parents[2] / "docs" / "privacy-app-followups.md"
    followups = followups_path.read_text()

    assert "## Implementat" in followups
    assert "secció «Ajustos»" in followups
    assert "correu editable" in followups
    assert "tokens APNs" in followups
    assert "## Pendent" in followups
    assert "compartició explícita de converses" in followups
    pending = followups.split("## Pendent", 1)[1]
    assert "registre i revocació de tokens APNs" not in pending
    assert "Afegir una pantalla" not in followups
    assert "Preparar un correu" not in followups


def test_final_app_name_is_consistent_in_xcode_and_testflight_docs() -> None:
    repository_root = Path(__file__).parents[2]
    project = (
        repository_root / "HoraAHoraApp" / "HoraAHoraApp.xcodeproj" / "project.pbxproj"
    ).read_text()
    readiness = (repository_root / "docs" / "testflight-readiness.md").read_text()
    metadata = (repository_root / "docs" / "testflight-metadata-ca.md").read_text()
    readme = (repository_root / "README.md").read_text()

    assert project.count('INFOPLIST_KEY_CFBundleDisplayName = "Castells en vena";') == 2
    assert project.count("PRODUCT_BUNDLE_IDENTIFIER = com.ahuguet.castellsenvena;") == 2
    assert project.count("CURRENT_PROJECT_VERSION = 5;") == 2
    assert "com.andreu.HoraAHoraApp" not in project
    assert "Nom visible `Castells en vena`" in readiness
    assert "`com.ahuguet.castellsenvena`" in readiness
    assert "Castells en vena és" in metadata
    assert "`com.ahuguet.castellsenvena`" in readme
