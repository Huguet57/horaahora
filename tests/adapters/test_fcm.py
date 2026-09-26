from __future__ import annotations

import json
import time
from dataclasses import replace

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from backend.adapters.notifications.fcm import FCMGateway, GoogleServiceAccountTokenProvider
from backend.adapters.notifications.routing import PlatformRoutingGateway
from backend.composition.providers import build_notification_gateway
from backend.config import Settings
from backend.domain.notifications.models import (
    NotificationDisposition,
    NotificationSendResult,
    PendingNotificationDelivery,
    PushPlatform,
)

FCM_TOKEN = "fGh1_Jk-2:APA91bExampleFirebaseRegistrationToken_0123456789abcdefABCDEF"


class Response:
    def __init__(self, status_code: int, payload: dict | None = None, *, text_only=False) -> None:
        self.status_code = status_code
        self._payload = payload or {}
        self._text_only = text_only

    def json(self) -> dict:
        if self._text_only:
            raise ValueError("not JSON")
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class RecordingClient:
    def __init__(self, *responses: Response) -> None:
        self.responses = list(responses)
        self.calls: list[dict] = []

    def post(self, url, **kwargs):
        self.calls.append({"url": url, **kwargs})
        return self.responses.pop(0)


def delivery(url: str = "https://example.com/directe") -> PendingNotificationDelivery:
    return PendingNotificationDelivery(
        id="delivery-1",
        subscription_id="subscription-1",
        outbox_id="outbox-1",
        device_token=FCM_TOKEN,
        environment="production",
        topic="com.ahuguet.castellsenvena",
        title="Notícia",
        body="Resum",
        url=url,
        collapse_id="hour-by-hour:item-1",
        attempt_count=1,
        platform=PushPlatform.ANDROID,
    )


def fcm_error(status_code: int, status: str, error_code: str | None = None) -> Response:
    details = (
        [{"@type": "type.googleapis.com/google.firebase.fcm.v1.FcmError", "errorCode": error_code}]
        if error_code
        else []
    )
    return Response(
        status_code,
        {"error": {"code": status_code, "status": status, "message": "…", "details": details}},
    )


def test_fcm_gateway_sends_a_notification_with_the_link_and_channel() -> None:
    client = RecordingClient(Response(200, {"name": "projects/castells/messages/1"}))
    gateway = FCMGateway(project_id="castells", access_token=lambda: "oauth-token", client=client)

    result = gateway.send(delivery())

    assert result.disposition is NotificationDisposition.DELIVERED
    call = client.calls[0]
    assert call["url"] == "https://fcm.googleapis.com/v1/projects/castells/messages:send"
    assert call["headers"] == {"authorization": "Bearer oauth-token"}
    assert call["json"] == {
        "message": {
            "token": FCM_TOKEN,
            "notification": {"title": "Notícia", "body": "Resum"},
            "data": {"collapse_id": "hour-by-hour:item-1", "url": "https://example.com/directe"},
            "android": {
                "priority": "HIGH",
                "notification": {"channel_id": "hour_by_hour", "tag": "hour-by-hour:item-1"},
            },
        }
    }


def test_fcm_gateway_omits_an_empty_link() -> None:
    client = RecordingClient(Response(200))
    FCMGateway(project_id="castells", access_token=lambda: "token", client=client).send(
        delivery(url="")
    )

    assert client.calls[0]["json"]["message"]["data"] == {"collapse_id": "hour-by-hour:item-1"}


@pytest.mark.parametrize(
    ("response", "disposition", "reason"),
    [
        (
            fcm_error(404, "NOT_FOUND", "UNREGISTERED"),
            NotificationDisposition.INVALID_TOKEN,
            "UNREGISTERED",
        ),
        (
            fcm_error(403, "PERMISSION_DENIED", "SENDER_ID_MISMATCH"),
            NotificationDisposition.INVALID_TOKEN,
            "SENDER_ID_MISMATCH",
        ),
        (
            fcm_error(429, "RESOURCE_EXHAUSTED", "QUOTA_EXCEEDED"),
            NotificationDisposition.RETRY,
            "QUOTA_EXCEEDED",
        ),
        (fcm_error(503, "UNAVAILABLE"), NotificationDisposition.RETRY, "UNAVAILABLE"),
        (Response(500, text_only=True), NotificationDisposition.RETRY, "HTTP 500"),
        (
            fcm_error(400, "INVALID_ARGUMENT", "INVALID_ARGUMENT"),
            NotificationDisposition.FAILED,
            "INVALID_ARGUMENT",
        ),
        (
            fcm_error(401, "UNAUTHENTICATED", "THIRD_PARTY_AUTH_ERROR"),
            NotificationDisposition.FAILED,
            "THIRD_PARTY_AUTH_ERROR",
        ),
    ],
)
def test_fcm_gateway_classifies_errors(response, disposition, reason) -> None:
    gateway = FCMGateway(
        project_id="castells", access_token=lambda: "token", client=RecordingClient(response)
    )

    result = gateway.send(delivery())

    assert result.disposition is disposition
    assert result.reason == reason


def service_account() -> tuple[str, rsa.RSAPrivateKey]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    info = {
        "type": "service_account",
        "project_id": "castells-en-vena",
        "client_email": "push@castells-en-vena.iam.gserviceaccount.com",
        "private_key": pem,
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    return json.dumps(info), key


def test_service_account_tokens_are_signed_and_reused_until_they_expire() -> None:
    account_json, key = service_account()
    now = [time.time()]
    client = RecordingClient(
        Response(200, {"access_token": "first", "expires_in": 3600}),
        Response(200, {"access_token": "second", "expires_in": 3600}),
    )
    provider = GoogleServiceAccountTokenProvider(account_json, client=client, clock=lambda: now[0])

    assert provider.project_id == "castells-en-vena"
    assert provider() == "first"
    now[0] += 3_000
    assert provider() == "first"
    now[0] += 400
    assert provider() == "second"

    request = client.calls[0]
    assert request["url"] == "https://oauth2.googleapis.com/token"
    assert request["data"]["grant_type"] == "urn:ietf:params:oauth:grant-type:jwt-bearer"
    claims = jwt.decode(
        request["data"]["assertion"],
        key.public_key(),
        algorithms=["RS256"],
        audience="https://oauth2.googleapis.com/token",
    )
    assert claims["iss"] == "push@castells-en-vena.iam.gserviceaccount.com"
    assert claims["scope"] == "https://www.googleapis.com/auth/firebase.messaging"
    assert claims["exp"] - claims["iat"] == 3600


class RecordingGateway:
    def __init__(self, name: str) -> None:
        self.name = name
        self.sent: list[PendingNotificationDelivery] = []

    def send(self, delivery: PendingNotificationDelivery) -> NotificationSendResult:
        self.sent.append(delivery)
        return NotificationSendResult(NotificationDisposition.DELIVERED, self.name)


def test_routing_gateway_sends_each_token_through_its_platform() -> None:
    apns, fcm = RecordingGateway("apns"), RecordingGateway("fcm")
    gateway = PlatformRoutingGateway({PushPlatform.IOS: apns, PushPlatform.ANDROID: fcm})

    android = gateway.send(delivery())
    ios = gateway.send(replace(delivery(), platform=PushPlatform.IOS, device_token="ab" * 32))

    assert (android.reason, ios.reason) == ("fcm", "apns")
    assert len(fcm.sent) == len(apns.sent) == 1


def test_android_deliveries_fail_until_firebase_is_configured() -> None:
    gateway = PlatformRoutingGateway({PushPlatform.IOS: RecordingGateway("apns")})

    result = gateway.send(delivery())

    assert result.disposition is NotificationDisposition.FAILED
    assert result.reason == "PushServiceNotConfigured"


def production_settings(**overrides) -> Settings:
    return Settings(
        vercel_env="production",
        push_delivery_enabled=True,
        apns_key_p8="key",
        apns_key_id="id",
        apns_team_id="team",
        **overrides,
    )


def test_production_gateway_adds_fcm_when_a_service_account_is_configured() -> None:
    account_json, _ = service_account()

    without_fcm = build_notification_gateway(production_settings())
    with_fcm = build_notification_gateway(
        production_settings(fcm_service_account_json=account_json)
    )

    assert isinstance(without_fcm, PlatformRoutingGateway)
    assert set(without_fcm.gateways) == {PushPlatform.IOS}
    assert isinstance(with_fcm, PlatformRoutingGateway)
    assert isinstance(with_fcm.gateways[PushPlatform.ANDROID], FCMGateway)
    assert with_fcm.gateways[PushPlatform.ANDROID].project_id == "castells-en-vena"


def test_an_invalid_service_account_fails_at_startup() -> None:
    with pytest.raises(RuntimeError, match="FCM_SERVICE_ACCOUNT_JSON"):
        build_notification_gateway(production_settings(fcm_service_account_json="{not json"))
