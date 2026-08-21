from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True, slots=True)
class ContestKnowledgeQuery:
    source: Literal["rules", "results", "scores"]
    years: list[int] = field(default_factory=list)
    groups: list[str] = field(default_factory=list)
    result_scope: Literal["editions", "winners", "classification"] | None = None
    score_scope: Literal["ranking"] | None = None
    score_outcome: Literal["loaded", "unloaded", "both"] | None = None
    ranking_selection: Literal["top", "bottom", "position", "neighbors", "full"] | None = None
    ranking_limit: int | None = None
    ranking_notation: str | None = None


@dataclass(frozen=True, slots=True)
class ScoreRankingRow:
    position: int
    notation: str
    loaded_points: int
    unloaded_points: int


@dataclass(frozen=True, slots=True)
class ScorePresentation:
    kind: Literal["score_ranking", "score_card"]
    title: str
    outcome: Literal["loaded", "unloaded", "both"]
    rows: list[ScoreRankingRow]
    focus_notation: str | None = None
