import json
import os
import time
from abc import ABC, abstractmethod

import jwt
import requests


class Notifier(ABC):
    @abstractmethod
    def send(self, title: str, body: str) -> None: ...


class APNsNotifier(Notifier):
    """Send push notifications via Apple Push Notification service (HTTP/2 + JWT)."""

    def __init__(
        self,
        key_p8: str,        # Contents of the .p8 file
        key_id: str,         # 10-char Key ID from Apple
        team_id: str,        # Apple Developer Team ID
        bundle_id: str,      # App bundle identifier
        device_token: str,   # Target device token (hex string)
        sandbox: bool = False,
    ):
        self.key_p8 = key_p8
        self.key_id = key_id
        self.team_id = team_id
        self.bundle_id = bundle_id
        self.device_token = device_token
        self.host = (
            "https://api.sandbox.push.apple.com"
            if sandbox
            else "https://api.push.apple.com"
        )

    def _make_token(self) -> str:
        payload = {
            "iss": self.team_id,
            "iat": int(time.time()),
        }
        return jwt.encode(payload, self.key_p8, algorithm="ES256", headers={"kid": self.key_id})

    def send(self, title: str, body: str) -> None:
        token = self._make_token()
        url = f"{self.host}/3/device/{self.device_token}"

        headers = {
            "authorization": f"bearer {token}",
            "apns-topic": self.bundle_id,
            "apns-push-type": "alert",
            "apns-priority": "10",
        }

        payload = {
            "aps": {
                "alert": {
                    "title": title,
                    "body": body,
                },
                "sound": "default",
            }
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=10)

        if resp.status_code != 200:
            raise RuntimeError(
                f"APNs error {resp.status_code}: {resp.text}"
            )


def create_notifier() -> Notifier:
    """Create a notifier from environment variables."""
    return APNsNotifier(
        key_p8=os.environ["APNS_KEY_P8"],
        key_id=os.environ["APNS_KEY_ID"],
        team_id=os.environ["APNS_TEAM_ID"],
        bundle_id=os.environ["BUNDLE_ID"],
        device_token=os.environ["DEVICE_TOKEN"],
        sandbox=os.environ.get("APNS_SANDBOX", "").lower() == "true",
    )
