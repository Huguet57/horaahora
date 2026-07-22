import json
from pathlib import Path

from fastapi.testclient import TestClient

from api.index import app


def test_vercel_entrypoint_exposes_the_portable_api() -> None:
    client = TestClient(app)

    assert client.get("/health").json() == {"status": "ok"}
    paths = app.openapi()["paths"]
    assert {"/v1/chat", "/v1/events", "/v1/hour-by-hour"} <= set(paths)


def test_vercel_runs_the_backend_in_paris() -> None:
    config_path = Path(__file__).parents[1] / "vercel.json"
    config = json.loads(config_path.read_text())

    assert config["regions"] == ["cdg1"]
