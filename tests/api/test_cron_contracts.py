from backend.adapters.rate_limit.memory import InMemoryRateLimiter
from backend.config import Settings
from tests.support.application import make_test_client


class ExpiringRateLimiter(InMemoryRateLimiter):
    def cleanup_expired(self) -> int:
        return 4


class ExpiringSharedConversations:
    def save(self, _conversation) -> None:
        pass

    def delete_older_than(self, _cutoff) -> int:
        return 2


def production_client(**overrides):
    return make_test_client(
        settings=Settings(
            database_url="sqlite+pysqlite:///:memory:",
            vercel_env="production",
            cron_secret="cron-secret",
        ),
        **overrides,
    )


def test_maintenance_cron_requires_the_production_secret() -> None:
    preview = make_test_client(
        settings=Settings(database_url="sqlite://", cron_secret="cron-secret")
    )
    client = production_client()

    assert (
        preview.get(
            "/internal/cron/maintenance", headers={"Authorization": "Bearer cron-secret"}
        ).status_code
        == 404
    )
    assert client.get("/internal/cron/maintenance").status_code == 401
    assert (
        client.get(
            "/internal/cron/maintenance", headers={"Authorization": "Bearer other"}
        ).status_code
        == 401
    )


def test_maintenance_cron_purges_only_the_calculator_state() -> None:
    client = production_client(
        rate_limiter=ExpiringRateLimiter(max_requests=100, window_seconds=60),
        shared_conversation_repository=ExpiringSharedConversations(),
    )

    response = client.get(
        "/internal/cron/maintenance", headers={"Authorization": "Bearer cron-secret"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "completed",
        "rate_limit_buckets_deleted": 4,
        "shared_conversations_deleted": 2,
    }
