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
