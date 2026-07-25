from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True, slots=True)
class PushSubscriptionRegistration:
    installation_id: str
    device_token: str
    app_version: str
    locale: str


@dataclass(frozen=True, slots=True)
class ActivePushSubscription:
    id: str
    installation_id: str
    device_token: str
    environment: str
    topic: str


@dataclass(frozen=True, slots=True)
class NotificationIngestionResult:
    baseline_created: bool
    notifications_created: int


@dataclass(frozen=True, slots=True)
class PendingNotificationDelivery:
    id: str
    subscription_id: str
    outbox_id: str
    device_token: str
    environment: str
    topic: str
    title: str
    body: str
    url: str
    collapse_id: str
    attempt_count: int


class NotificationDisposition(str, Enum):
    DELIVERED = "delivered"
    RETRY = "retry"
    INVALID_TOKEN = "invalid_token"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class NotificationSendResult:
    disposition: NotificationDisposition
    reason: str = ""
