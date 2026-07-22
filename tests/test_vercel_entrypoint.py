import json
import importlib
from pathlib import Path

from fastapi.testclient import TestClient


def test_vercel_entrypoint_exposes_the_portable_api(monkeypatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://user:password@localhost:5432/horaahora_test",
    )
    monkeypatch.setenv("RATE_LIMIT_HASH_SECRET", "test-secret")
    app = importlib.import_module("api.index").app
    client = TestClient(app)

    assert client.get("/health").json() == {"status": "ok"}
    paths = app.openapi()["paths"]
    assert {
        "/v1/chat",
        "/v1/events",
        "/v1/hour-by-hour",
        "/v1/push-subscriptions/{installation_id}",
    } <= set(paths)


def test_vercel_runs_the_backend_in_paris() -> None:
    config_path = Path(__file__).parents[1] / "vercel.json"
    config = json.loads(config_path.read_text())

    assert config["regions"] == ["cdg1"]
    assert config["crons"] == [
        {"path": "/internal/cron/hour-by-hour", "schedule": "* * * * *"},
        {"path": "/internal/cron/maintenance", "schedule": "17 3 * * *"},
    ]
