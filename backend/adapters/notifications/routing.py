from __future__ import annotations

from collections.abc import Mapping

from backend.domain.notifications.models import (
    NotificationDisposition,
    NotificationSendResult,
    PendingNotificationDelivery,
    PushPlatform,
)
from backend.domain.notifications.ports import NotificationGateway


class PlatformRoutingGateway:
    """Sends each delivery through the push service of its token: APNs or FCM."""

    def __init__(self, gateways: Mapping[PushPlatform, NotificationGateway]) -> None:
        self.gateways = dict(gateways)

    def send(self, delivery: PendingNotificationDelivery) -> NotificationSendResult:
        gateway = self.gateways.get(delivery.platform)
        if gateway is None:
            return NotificationSendResult(
                NotificationDisposition.FAILED, "PushServiceNotConfigured"
            )
        return gateway.send(delivery)
