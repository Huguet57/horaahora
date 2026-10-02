from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

from backend.domain.contest.models import ContestKnowledgeQuery, ScorePresentation

# A porra can list a whole jornada of the Concurs; both apps scroll the comparison sideways.
MAX_PERFORMANCES = 16


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
    # The performance the user wants to beat while trying variants of their own.
    reference: bool = False


@dataclass(frozen=True, slots=True)
class ParsedCastellQuery:
    intent: Literal[
        "lookup",
        "comparison",
        "total",
        "contest_info",
        "conversation",
        "clarification",
        "unsupported",
    ]
    performances: list[ParsedPerformance] = field(default_factory=list)
    clarification: str | None = None
    answer: str | None = None
    knowledge_query: ContestKnowledgeQuery | None = None


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
    reference: bool = False


@dataclass(slots=True)
class CalculationResult:
    reply: str
    intent: str
    performances: list[PerformanceResult]
    winner_label: str | None
    warnings: list[str]
    ruleset_version: str = "concurs-2026"
    needs_clarification: bool = False
    presentation: ScorePresentation | None = None
