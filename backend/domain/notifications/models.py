from dataclasses import dataclass
from enum import Enum

from backend.domain.notifications.interest import GroupSelection, InterestLevel


class PushPlatform(str, Enum):
    """The push service a device token belongs to."""

    IOS = "ios"  # Apple Push Notification service
    ANDROID = "android"  # Firebase Cloud Messaging


@dataclass(frozen=True, slots=True)
class PushSubscriptionRegistration:
    installation_id: str
    device_token: str
    app_version: str
    locale: str
    minimum_interest: InterestLevel | None = None
    group_selection: GroupSelection | None = None
    platform: PushPlatform = PushPlatform.IOS


@dataclass(frozen=True, slots=True)
class ActivePushSubscription:
    id: str
    installation_id: str
    device_token: str
    environment: str
    topic: str
    minimum_interest: InterestLevel = InterestLevel.LOW
    group_selection: GroupSelection = GroupSelection()
    platform: PushPlatform = PushPlatform.IOS


@dataclass(frozen=True, slots=True)
class NotificationIngestionResult:
    baseline_created: bool
    notifications_created: int
    classified: int = 0
    classification_skipped: int = 0


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
    platform: PushPlatform = PushPlatform.IOS


class NotificationDisposition(str, Enum):
    DELIVERED = "delivered"
    RETRY = "retry"
    INVALID_TOKEN = "invalid_token"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class NotificationSendResult:
    disposition: NotificationDisposition
    reason: str = ""
