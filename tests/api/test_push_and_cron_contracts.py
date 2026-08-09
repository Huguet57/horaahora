from backend.adapters.persistence.database import Database
from backend.application.notifications import NotificationRunResult
from backend.config import Settings
from backend.domain.notifications.models import PushSubscriptionRegistration
from tests.support.application import make_test_client


class RecordingPushRepository:
    def __init__(self) -> None:
        self.registrations: list[tuple[PushSubscriptionRegistration, str, str]] = []
        self.unregistrations: list[tuple[str, str, str]] = []

    def register(self, registration, *, environment, topic):
        self.registrations.append((registration, environment, topic))

    def unregister(self, installation_id, *, environment, topic):
        self.unregistrations.append((installation_id, environment, topic))


class NotificationRepositoryStub(RecordingPushRepository):
    def cleanup(self):
        return {
            "subscriptions_invalidated": 1,
            "deliveries_deleted": 2,
            "outboxes_deleted": 1,
        }


class CoordinatorStub:
    def __init__(self) -> None:
        self.call_count = 0

    def run(self):
        self.call_count += 1
        return NotificationRunResult(status="completed", delivered=3)


def test_push_subscription_contract_registers_and_unregisters_current_installation() -> None:
    repository = RecordingPushRepository()
    client = make_test_client(
        settings=Settings(
            database_url="sqlite://",
            hour_by_hour_source_enabled=False,
            apns_bundle_id="com.example.app",
            vercel_env="production",
        ),
        push_repository=repository,
    )

    registered = client.put(
        "/v1/push-subscriptions/install-1",
        json={
            "device_token": "ab" * 32,
            "app_version": "1.0 (3)",
            "locale": "ca-ES",
            "environment": "development",
        },
    )
    removed = client.delete("/v1/push-subscriptions/install-1?environment=development")

    assert registered.status_code == 204
    assert removed.status_code == 204
    assert repository.registrations[0][0].device_token == "ab" * 32
    assert repository.registrations[0][1:] == ("development", "com.example.app")
    assert repository.unregistrations == [("install-1", "development", "com.example.app")]


def test_cron_routes_require_production_secret_and_return_persisted_results() -> None:
    notifications = NotificationRepositoryStub()
    coordinator = CoordinatorStub()
    database = Database("sqlite+pysqlite:///:memory:")
    client = make_test_client(
        settings=Settings(
            database_url="sqlite+pysqlite:///:memory:",
            hour_by_hour_source_enabled=False,
            vercel_env="production",
            cron_secret="cron-secret",
        ),
        database=database,
        push_repository=notifications,
        notification_repository=notifications,
        notification_coordinator=coordinator,
    )

    assert client.get("/internal/cron/hour-by-hour").status_code == 401
    response = client.get(
        "/internal/cron/hour-by-hour",
        headers={"Authorization": "Bearer cron-secret"},
    )

    assert response.status_code == 200
    assert response.json()["delivered"] == 3
    assert coordinator.call_count == 1
