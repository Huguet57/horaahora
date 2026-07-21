from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.domain.models import CalculationResult, CastellEvent, HourByHourItem


class ChatMessageSchema(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2_000)


class ChatRequestSchema(BaseModel):
    conversation_id: UUID
    installation_id: str = Field(min_length=1, max_length=128)
    locale: str = Field(default="ca-ES", max_length=16)
    ruleset: Literal["concurs-2026"] = "concurs-2026"
    messages: list[ChatMessageSchema] = Field(min_length=1, max_length=12)


class ScoredCastellSchema(BaseModel):
    input: str
    canonical: str | None
    outcome: str
    points: int
    counted: bool
    reason: str | None


class PerformanceSchema(BaseModel):
    label: str
    total: int
    castells: list[ScoredCastellSchema]


class ChatResponseSchema(BaseModel):
    reply: str
    intent: str
    performances: list[PerformanceSchema]
    winner_label: str | None
    warnings: list[str]
    ruleset_version: str
    needs_clarification: bool

    @classmethod
    def from_domain(cls, result: CalculationResult) -> "ChatResponseSchema":
        return cls(
            reply=result.reply,
            intent=result.intent,
            performances=[
                PerformanceSchema(
                    label=performance.label,
                    total=performance.total,
                    castells=[
                        ScoredCastellSchema(
                            input=castell.input,
                            canonical=castell.canonical,
                            outcome=castell.outcome.value,
                            points=castell.points,
                            counted=castell.counted,
                            reason=castell.reason,
                        )
                        for castell in performance.castells
                    ],
                )
                for performance in result.performances
            ],
            winner_label=result.winner_label,
            warnings=result.warnings,
            ruleset_version=result.ruleset_version,
            needs_clarification=result.needs_clarification,
        )


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
