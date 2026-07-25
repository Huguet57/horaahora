from fastapi.testclient import TestClient

from backend.app import create_app
from backend.config import Settings
from tests.support.application import application_overrides


def _app():
    return create_app(
        settings=Settings(
            database_url="sqlite://",
            hour_by_hour_source_enabled=False,
            ai_provider="local",
        ),
        overrides=application_overrides(),
    )


def test_factory_registers_the_complete_delivery_surface() -> None:
    app = _app()
    routes = {
        (method.upper(), path)
        for path, operations in app.openapi()["paths"].items()
        for method in operations
        if method in {"get", "post", "put", "delete", "patch"}
    }

    assert {
        ("GET", "/health"),
        ("GET", "/health/ready"),
        ("GET", "/v1/hour-by-hour"),
        ("GET", "/v1/events"),
        ("POST", "/v1/chat"),
        ("PUT", "/v1/push-subscriptions/{installation_id}"),
        ("DELETE", "/v1/push-subscriptions/{installation_id}"),
        ("GET", "/internal/cron/hour-by-hour"),
        ("GET", "/internal/cron/maintenance"),
    }.issubset(routes)

    client = TestClient(app)
    assert client.get("/privacy").status_code == 200
    assert client.get("/privacy/ca").status_code == 200


def test_router_error_mapping_keeps_validation_and_domain_errors_distinct() -> None:
    client = TestClient(_app())

    invalid_limit = client.get("/v1/hour-by-hour?limit=0")
    invalid_cursor = client.get("/v1/hour-by-hour?cursor=not-base64")
    invalid_range = client.get("/v1/events?from=2026-07-22&to=2026-07-21")

    assert invalid_limit.status_code == 422
    assert invalid_cursor.status_code == 400
    assert invalid_range.status_code == 400
