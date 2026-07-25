from dataclasses import dataclass
from datetime import date, datetime


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
