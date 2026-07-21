from pathlib import Path

from fastapi.testclient import TestClient

from backend.adapters.ai.local import RegexQueryInterpreter
from backend.adapters.persistence.memory import InMemoryContentRepository
from backend.adapters.rate_limit.memory import InMemoryRateLimiter
from backend.app import create_app
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


def test_privacy_index_is_catalan_and_links_every_language() -> None:
    response = make_client().get("/privacy")

    assert response.status_code == 200
    assert response.headers["content-language"] == "ca"
    assert response.headers["content-type"].startswith("text/html")
    assert response.headers["cache-control"] == "public, max-age=3600"
    assert "set-cookie" not in response.headers
    assert '<html lang="ca">' in response.text
    assert 'href="/privacy/ca"' in response.text
    assert 'href="/privacy/es"' in response.text
    assert 'href="/privacy/en"' in response.text


def test_localized_privacy_pages_are_static_and_complete() -> None:
    expected_copy = {
        "ca": "Política de privacitat",
        "es": "Política de privacidad",
        "en": "Privacy policy",
    }
    client = make_client()

    for locale, heading in expected_copy.items():
        response = client.get(f"/privacy/{locale}")

        assert response.status_code == 200
        assert response.headers["content-language"] == locale
        assert response.headers["content-type"].startswith("text/html")
        assert response.headers["cache-control"] == "public, max-age=3600"
        assert "set-cookie" not in response.headers
        assert f'<html lang="{locale}">' in response.text
        assert heading in response.text
        assert "Castells en vena" in response.text
        assert "Andreu Huguet" in response.text
        assert "tenimaletaapp@gmail.com" in response.text
        assert "OpenAI" in response.text
        assert "Vercel" in response.text
        assert "Apple" in response.text
        assert "Google" in response.text
        assert "TotCastells" not in response.text
        assert "<script" not in response.text.lower()
        assert "[nom" not in response.text.lower()
        assert "[correu" not in response.text.lower()
        assert "[data" not in response.text.lower()


def test_unknown_privacy_locale_is_not_found() -> None:
    response = make_client().get("/privacy/fr")

    assert response.status_code == 404


def test_privacy_routes_are_additive_to_the_v1_contract() -> None:
    client = make_client()
    paths = client.app.openapi()["paths"]

    assert {"/v1/chat", "/v1/events", "/v1/hour-by-hour"} <= set(paths)
    assert {"/privacy", "/privacy/{locale}"} <= set(paths)


def test_catalan_policy_document_has_no_draft_placeholders_or_old_name() -> None:
    policy_path = Path(__file__).parents[1] / "docs" / "privacy-policy-ca.md"
    policy = policy_path.read_text()

    assert policy.startswith("# Política de privacitat — Castells en vena")
    assert "Andreu Huguet" in policy
    assert "tenimaletaapp@gmail.com" in policy
    assert "TotCastells" not in policy
    assert "[nom" not in policy.lower()
    assert "[correu" not in policy.lower()
    assert "[data" not in policy.lower()
