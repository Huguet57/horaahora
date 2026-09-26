from backend.adapters.persistence.database import Database
from backend.application.notifications import NotificationRunResult
from backend.config import Settings
from backend.domain.notifications.interest import GroupSelection, InterestLevel
from backend.domain.notifications.models import PushPlatform, PushSubscriptionRegistration
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


def test_notification_preferences_are_normalized_and_invalid_levels_rejected():
    repository = RecordingPushRepository()
    client = make_test_client(push_repository=repository)
    payload = {
        "device_token": "ab" * 32,
        "minimum_interest": "high",
        "group_selection": {"mode": "custom", "keys": ["  MINYONS  ", "Minyons"]},
    }
    assert client.put("/v1/push-subscriptions/install-1", json=payload).status_code == 204
    registered = repository.registrations[0][0]
    assert registered.minimum_interest is InterestLevel.HIGH
    assert registered.group_selection == GroupSelection("custom", frozenset({"minyons"}))
    payload["minimum_interest"] = "urgent"
    assert client.put("/v1/push-subscriptions/install-1", json=payload).status_code == 422
    payload["minimum_interest"] = "low"
    payload["group_selection"]["mode"] = "unknown"
    assert client.put("/v1/push-subscriptions/install-1", json=payload).status_code == 422


def test_android_registers_a_firebase_token_for_the_android_package() -> None:
    repository = RecordingPushRepository()
    client = make_test_client(
        settings=Settings(
            database_url="sqlite://",
            hour_by_hour_source_enabled=False,
            apns_bundle_id="com.example.ios",
            android_package_name="com.example.android",
        ),
        push_repository=repository,
    )
    token = "fGh1_Jk-2:APA91bExampleFirebaseRegistrationToken_0123456789abcdef"

    registered = client.put(
        "/v1/push-subscriptions/install-2",
        json={
            "device_token": f"  {token} ",
            "app_version": "1.3 (1)",
            "locale": "ca-ES",
            "environment": "production",
            "platform": "android",
        },
    )
    removed = client.delete(
        "/v1/push-subscriptions/install-2?environment=production&platform=android"
    )

    assert registered.status_code == 204
    assert removed.status_code == 204
    registration, environment, topic = repository.registrations[0]
    # Firebase tokens are case-sensitive: only surrounding spaces are removed.
    assert registration.device_token == token
    assert registration.platform is PushPlatform.ANDROID
    assert (environment, topic) == ("production", "com.example.android")
    assert repository.unregistrations == [("install-2", "production", "com.example.android")]


def test_each_platform_validates_its_own_token_format():
    repository = RecordingPushRepository()
    client = make_test_client(push_repository=repository)
    firebase_token = "fGh1_Jk-2:APA91bExampleFirebaseRegistrationToken_0123456789abcdef"

    android_hex = client.put(
        "/v1/push-subscriptions/install-3",
        json={"device_token": "ab" * 32, "platform": "android"},
    )
    android_spaces = client.put(
        "/v1/push-subscriptions/install-3",
        json={"device_token": "not a firebase token at all, it has spaces", "platform": "android"},
    )
    ios_firebase = client.put(
        "/v1/push-subscriptions/install-3",
        json={"device_token": firebase_token, "platform": "ios"},
    )
    unknown = client.put(
        "/v1/push-subscriptions/install-3",
        json={"device_token": "ab" * 32, "platform": "windows"},
    )
    ios_default = client.put(
        "/v1/push-subscriptions/install-3",
        json={"device_token": "AB" * 32},
    )

    assert android_hex.status_code == 204
    assert android_spaces.status_code == 422
    assert ios_firebase.status_code == 422
    assert unknown.status_code == 422
    assert ios_default.status_code == 204
    assert repository.registrations[-1][0].platform is PushPlatform.IOS
    assert repository.registrations[-1][0].device_token == "ab" * 32
