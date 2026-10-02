from fastapi.testclient import TestClient

from backend.app import create_app
from backend.config import Settings
from tests.support.application import application_overrides


def _app():
    return create_app(
        settings=Settings(
            database_url="sqlite://",
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

    assert routes == {
        ("GET", "/health"),
        ("GET", "/health/ready"),
        ("POST", "/v1/chat"),
        ("GET", "/internal/cron/maintenance"),
    }

    client = TestClient(app)
    assert client.get("/privacy").status_code == 200
    assert client.get("/privacy/ca").status_code == 200
