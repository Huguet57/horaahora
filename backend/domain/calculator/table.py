from __future__ import annotations

import csv
from pathlib import Path

from backend.domain.calculator.models import Outcome


DATA_FILE = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "taula_puntuacions_concurs_castells_2026.csv"
)


class ScoreTable:
    def __init__(self, scores: dict[str, dict[Outcome, int]]) -> None:
        self.scores = scores

    @classmethod
    def from_csv(cls, path: Path) -> "ScoreTable":
        scores: dict[str, dict[Outcome, int]] = {}
        with path.open(newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                scores[row["castell"]] = {
                    Outcome.LOADED: int(row["punts_carregat"]),
                    Outcome.UNLOADED: int(row["punts_descarregat"]),
                    Outcome.ATTEMPT: 0,
                }
        return cls(scores)

    @classmethod
    def default(cls) -> "ScoreTable":
        return cls.from_csv(DATA_FILE)

    def contains(self, canonical: str) -> bool:
        return canonical in self.scores

    def points(self, canonical: str, outcome: Outcome) -> int:
        return self.scores[canonical][outcome]
