from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
import time

import httpx

from backend.domain.notifications.models import (
    NotificationDisposition,
    NotificationSendResult,
    PendingNotificationDelivery,
)


_INVALID_TOKEN_REASONS = {"BadDeviceToken", "DeviceTokenNotForTopic", "Unregistered"}
_TRANSIENT_STATUSES = {429, 500, 503}


class APNsGateway:
    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        authorization_token: Callable[[], str],
    ) -> None:
        self.client = client or httpx.Client(http2=True)
        self.authorization_token = authorization_token

    def send(self, delivery: PendingNotificationDelivery) -> NotificationSendResult:
        host = (
            "https://api.push.apple.com"
            if delivery.environment == "production"
            else "https://api.sandbox.push.apple.com"
        )
        response = self.client.post(
            f"{host}/3/device/{delivery.device_token}",
            headers={
                "authorization": f"bearer {self.authorization_token()}",
                "apns-topic": delivery.topic,
                "apns-push-type": "alert",
                "apns-priority": "10",
                "apns-id": delivery.id,
                "apns-collapse-id": delivery.collapse_id,
            },
            json={
                "aps": {
                    "alert": {"title": delivery.title, "body": delivery.body},
                },
                **({"url": delivery.url} if delivery.url else {}),
            },
            timeout=10,
        )
        if response.status_code == 200:
            return NotificationSendResult(NotificationDisposition.DELIVERED)

        try:
            reason = str(response.json().get("reason", f"HTTP {response.status_code}"))
        except Exception:
            reason = f"HTTP {response.status_code}"
        if reason in _INVALID_TOKEN_REASONS:
            return NotificationSendResult(NotificationDisposition.INVALID_TOKEN, reason)
        if response.status_code in _TRANSIENT_STATUSES:
            return NotificationSendResult(NotificationDisposition.RETRY, reason)
        return NotificationSendResult(NotificationDisposition.FAILED, reason)


class APNsAuthorizationTokenProvider:
    def __init__(self, *, key_p8: str, key_id: str, team_id: str) -> None:
        self.key_p8 = key_p8.replace("\\n", "\n")
        self.key_id = key_id
        self.team_id = team_id
        self._token = ""
        self._created_at = 0.0

    def __call__(self) -> str:
        import jwt

        now = time.time()
        if self._token and now - self._created_at < 50 * 60:
            return self._token
        self._token = jwt.encode(
            {"iss": self.team_id, "iat": int(datetime.now(UTC).timestamp())},
            self.key_p8,
            algorithm="ES256",
            headers={"kid": self.key_id},
        )
        self._created_at = now
        return self._token
