from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from backend.domain.calculator.models import CalculationResult
from backend.domain.contest.models import ScorePresentation


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


class ScoreRankingRowSchema(BaseModel):
    position: int
    notation: str
    loaded_points: int
    unloaded_points: int


class ScorePresentationSchema(BaseModel):
    type: Literal["score_ranking", "score_card"]
    title: str
    outcome: Literal["loaded", "unloaded", "both"]
    focus_notation: str | None
    rows: list[ScoreRankingRowSchema]

    @classmethod
    def from_domain(cls, presentation: ScorePresentation) -> "ScorePresentationSchema":
        return cls(
            type=presentation.kind,
            title=presentation.title,
            outcome=presentation.outcome,
            focus_notation=presentation.focus_notation,
            rows=[
                ScoreRankingRowSchema(
                    position=row.position,
                    notation=row.notation,
                    loaded_points=row.loaded_points,
                    unloaded_points=row.unloaded_points,
                )
                for row in presentation.rows
            ],
        )


class ChatResponseSchema(BaseModel):
    reply: str
    intent: str
    performances: list[PerformanceSchema]
    winner_label: str | None
    warnings: list[str]
    ruleset_version: str
    needs_clarification: bool
    presentation: ScorePresentationSchema | None

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
            presentation=(
                ScorePresentationSchema.from_domain(result.presentation)
                if result.presentation is not None
                else None
            ),
        )
