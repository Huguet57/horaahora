from __future__ import annotations

import json
import time
from collections.abc import Callable

import httpx

from backend.domain.notifications.models import (
    NotificationDisposition,
    NotificationSendResult,
    PendingNotificationDelivery,
)

FCM_SCOPE = "https://www.googleapis.com/auth/firebase.messaging"
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
# The Android app shows news in this notification channel.
HOUR_BY_HOUR_CHANNEL_ID = "hour_by_hour"

_INVALID_TOKEN_CODES = {"UNREGISTERED", "SENDER_ID_MISMATCH"}
_TRANSIENT_STATUSES = {429, 500, 502, 503, 504}


class FCMGateway:
    """Sends news notifications to Android devices with the FCM HTTP v1 API."""

    def __init__(
        self,
        *,
        project_id: str,
        access_token: Callable[[], str],
        client: httpx.Client | None = None,
    ) -> None:
        self.project_id = project_id
        self.access_token = access_token
        self.client = client or httpx.Client()

    def send(self, delivery: PendingNotificationDelivery) -> NotificationSendResult:
        response = self.client.post(
            f"https://fcm.googleapis.com/v1/projects/{self.project_id}/messages:send",
            headers={"authorization": f"Bearer {self.access_token()}"},
            json={"message": _message(delivery)},
            timeout=10,
        )
        if response.status_code == 200:
            return NotificationSendResult(NotificationDisposition.DELIVERED)

        reason = _error_code(response)
        if reason in _INVALID_TOKEN_CODES or response.status_code == 404:
            return NotificationSendResult(NotificationDisposition.INVALID_TOKEN, reason)
        if response.status_code in _TRANSIENT_STATUSES:
            return NotificationSendResult(NotificationDisposition.RETRY, reason)
        return NotificationSendResult(NotificationDisposition.FAILED, reason)


def _message(delivery: PendingNotificationDelivery) -> dict:
    # The system shows the notification while the app is in the background;
    # tapping it opens the app with the data as extras. The tag plays the role
    # of the APNs collapse identifier: a newer notification replaces the older.
    data = {"collapse_id": delivery.collapse_id}
    if delivery.url:
        data["url"] = delivery.url
    return {
        "token": delivery.device_token,
        "notification": {"title": delivery.title, "body": delivery.body},
        "data": data,
        "android": {
            "priority": "HIGH",
            "notification": {
                "channel_id": HOUR_BY_HOUR_CHANNEL_ID,
                "tag": delivery.collapse_id,
            },
        },
    }


def _error_code(response: httpx.Response) -> str:
    """The FCM error code (UNREGISTERED, QUOTA_EXCEEDED…) or the status."""
    try:
        error = response.json().get("error", {})
    except Exception:
        return f"HTTP {response.status_code}"
    for detail in error.get("details", []):
        code = detail.get("errorCode")
        if code:
            return str(code)
    return str(error.get("status") or f"HTTP {response.status_code}")


class GoogleServiceAccountTokenProvider:
    """OAuth access tokens for a Google service account, renewed before they expire."""

    def __init__(
        self,
        service_account_json: str,
        *,
        client: httpx.Client | None = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        info = json.loads(service_account_json)
        self.project_id: str = info["project_id"]
        self.client_email: str = info["client_email"]
        self.private_key: str = info["private_key"]
        self.token_uri: str = info.get("token_uri") or GOOGLE_TOKEN_URI
        self.client = client or httpx.Client()
        self.clock = clock
        self._token = ""
        self._expires_at = 0.0

    def __call__(self) -> str:
        import jwt

        now = self.clock()
        if self._token and now < self._expires_at - 300:
            return self._token
        assertion = jwt.encode(
            {
                "iss": self.client_email,
                "scope": FCM_SCOPE,
                "aud": self.token_uri,
                "iat": int(now),
                "exp": int(now) + 3_600,
            },
            self.private_key,
            algorithm="RS256",
        )
        response = self.client.post(
            self.token_uri,
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": assertion,
            },
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        self._token = str(payload["access_token"])
        self._expires_at = now + float(payload.get("expires_in", 3_600))
        return self._token
