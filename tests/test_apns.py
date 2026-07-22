from __future__ import annotations

from backend.adapters.notifications.apns import APNsGateway
from backend.domain.models import NotificationDisposition, PendingNotificationDelivery


class Response:
    def __init__(self, status_code: int, payload: dict | None = None) -> None:
        self.status_code = status_code
        self._payload = payload or {}

    def json(self) -> dict:
        return self._payload


class RecordingClient:
    def __init__(self, response: Response) -> None:
        self.response = response
        self.calls = []

    def post(self, url, *, headers, json, timeout):
        self.calls.append((url, headers, json, timeout))
        return self.response


def delivery(environment: str = "production") -> PendingNotificationDelivery:
    return PendingNotificationDelivery(
        id="delivery-1",
        subscription_id="subscription-1",
        outbox_id="outbox-1",
        device_token="ab" * 32,
        environment=environment,
        topic="com.ahuguet.castellsenvena",
        title="Notícia",
        body="Resum",
        url="https://example.com/directe",
        collapse_id="hour-by-hour:item-1",
        attempt_count=1,
    )


def test_apns_gateway_uses_production_headers_and_alert_payload() -> None:
    client = RecordingClient(Response(200))
    gateway = APNsGateway(client=client, authorization_token=lambda: "jwt-token")

    result = gateway.send(delivery())

    assert result.disposition is NotificationDisposition.DELIVERED
    url, headers, payload, _ = client.calls[0]
    assert url == f"https://api.push.apple.com/3/device/{'ab' * 32}"
    assert headers["authorization"] == "bearer jwt-token"
    assert headers["apns-topic"] == "com.ahuguet.castellsenvena"
    assert headers["apns-priority"] == "10"
    assert headers["apns-id"] == "delivery-1"
    assert headers["apns-collapse-id"] == "hour-by-hour:item-1"
    assert payload["aps"] == {
        "alert": {"title": "Notícia", "body": "Resum"},
        "sound": "default",
    }
    assert payload["url"] == "https://example.com/directe"


def test_apns_gateway_classifies_invalid_and_transient_responses() -> None:
    invalid = APNsGateway(
        client=RecordingClient(Response(410, {"reason": "Unregistered"})),
        authorization_token=lambda: "jwt-token",
    ).send(delivery())
    transient = APNsGateway(
        client=RecordingClient(Response(429, {"reason": "TooManyRequests"})),
        authorization_token=lambda: "jwt-token",
    ).send(delivery("development"))

    assert invalid.disposition is NotificationDisposition.INVALID_TOKEN
    assert invalid.reason == "Unregistered"
    assert transient.disposition is NotificationDisposition.RETRY
    assert transient.reason == "TooManyRequests"
