from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Literal


class Outcome(str, Enum):
    LOADED = "loaded"
    UNLOADED = "unloaded"
    ATTEMPT = "attempt"


@dataclass(frozen=True, slots=True)
class ChatTurn:
    role: Literal["user", "assistant"]
    content: str


@dataclass(frozen=True, slots=True)
class ParsedCastell:
    notation: str
    outcome: Outcome = Outcome.UNLOADED


@dataclass(frozen=True, slots=True)
class ParsedPerformance:
    label: str
    castells: list[ParsedCastell]


@dataclass(frozen=True, slots=True)
class ParsedCastellQuery:
    intent: Literal["lookup", "comparison", "total", "clarification", "unsupported"]
    performances: list[ParsedPerformance] = field(default_factory=list)
    clarification: str | None = None


@dataclass(slots=True)
class ScoredCastell:
    input: str
    canonical: str | None
    outcome: Outcome
    points: int
    counted: bool = False
    reason: str | None = None


@dataclass(slots=True)
class PerformanceResult:
    label: str
    total: int
    castells: list[ScoredCastell]


@dataclass(slots=True)
class CalculationResult:
    reply: str
    intent: str
    performances: list[PerformanceResult]
    winner_label: str | None
    warnings: list[str]
    ruleset_version: str = "concurs-2026"
    needs_clarification: bool = False


@dataclass(frozen=True, slots=True)
class HourByHourItem:
    id: str
    source_id: str
    external_id: str
    title: str
    display_title: str
    summary: str
    published_at: datetime | None
    source_order: int
    article_url: str
    action_url: str | None
    attribution: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class CastellEvent:
    id: str
    source_id: str
    external_id: str
    title: str
    local_date: date
    starts_at: datetime | None
    time_label: str
    timezone: str
    venue: str
    municipality: str
    participating_groups: list[str]
    notes: str
    source_url: str
    source_order: int
    attribution: str
    revision: str
    updated_at: datetime


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
