from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from backend.domain.calculator.models import CalculationResult


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
