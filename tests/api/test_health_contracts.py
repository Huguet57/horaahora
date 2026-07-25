from backend.adapters.persistence.database import Database
from backend.config import Settings
from tests.support.application import make_test_client


def test_readiness_returns_503_when_neon_is_unavailable(monkeypatch) -> None:
    database = Database("sqlite+pysqlite:///:memory:")
    monkeypatch.setattr(database, "is_ready", lambda: False)
    client = make_test_client(
        settings=Settings(
            database_url="sqlite+pysqlite:///:memory:",
            hour_by_hour_source_enabled=False,
        ),
        database=database,
    )

    assert client.get("/health/ready").status_code == 503
