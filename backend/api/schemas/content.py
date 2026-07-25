from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.domain.content.models import CastellEvent, HourByHourItem


class HourByHourItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_id: str
    external_id: str
    title: str = Field(description="Títol editorial original, conservat per a notificacions")
    display_title: str = Field(description="Títol net per mostrar a la llista de l'app")
    summary: str
    published_at: datetime | None
    source_order: int
    article_url: str
    action_url: str | None
    attribution: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, item: HourByHourItem) -> "HourByHourItemSchema":
        return cls.model_validate(item)


class HourByHourPageSchema(BaseModel):
    items: list[HourByHourItemSchema]
    next_cursor: str | None
    from_cache: bool


class CastellEventSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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

    @classmethod
    def from_domain(cls, event: CastellEvent) -> "CastellEventSchema":
        return cls.model_validate(event)


class AgendaPageSchema(BaseModel):
    items: list[CastellEventSchema]
    next_cursor: str | None
    official_url: str = "https://castellscat.cat/ca/agenda"
    from_cache: bool
    source_status: Literal["active", "unavailable"]
