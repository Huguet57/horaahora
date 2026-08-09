from __future__ import annotations

from dataclasses import dataclass, field
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
    intent: Literal[
        "lookup",
        "comparison",
        "total",
        "contest_info",
        "clarification",
        "unsupported",
    ]
    performances: list[ParsedPerformance] = field(default_factory=list)
    clarification: str | None = None
    answer: str | None = None


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
