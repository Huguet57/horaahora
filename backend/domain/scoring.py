from __future__ import annotations

import csv
import itertools
from dataclasses import replace
from pathlib import Path

from backend.domain.models import (
    CalculationResult,
    Outcome,
    ParsedCastellQuery,
    PerformanceResult,
    ScoredCastell,
)


DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "taula_puntuacions_concurs_castells_2026.csv"


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


class CastellNormalizer:
    EXPLICIT_ALIASES = {
        "4de9net": "4de9sf",
        "2de8net": "2de8sf",
        "3de9net": "3de9sf",
        "pde7net": "Pde7sf",
        "4de9af": "4de9fa",
        "3de9af": "3de9fa",
    }

    def __init__(self, table: ScoreTable) -> None:
        self.table = table

    def normalize(self, notation: str) -> str | None:
        value = notation.strip().lower().replace(" ", "").replace("/", "de")
        if value.startswith("pd") and not value.startswith("pde"):
            value = "pde" + value[2:]
        elif value.startswith("p") and len(value) > 1 and value[1].isdigit():
            value = "pde" + value[1:]
        else:
            head, separator, tail = value.partition("d")
            if separator and not value.startswith("p") and not value.startswith(f"{head}de"):
                value = f"{head}de{tail}"

        value = self.EXPLICIT_ALIASES.get(value, value)
        canonical = "P" + value[1:] if value.startswith("pde") else value
        if self.table.contains(canonical):
            return canonical
        return None

    @staticmethod
    def structure_key(canonical: str) -> str:
        shared_structures = {
            "4de9f": "4de9",
            "4de9sf": "4de9",
            "2de8f": "2de8",
            "2de8sf": "2de8",
            "3de9f": "3de9",
            "3de9sf": "3de9",
            "Pde7f": "Pde7",
            "Pde7sf": "Pde7",
            "2de9fm": "2de9",
            "2de9sm": "2de9",
            "3de10fm": "3de10",
            "3de10sm": "3de10",
            "4de10fm": "4de10",
            "4de10sm": "4de10",
        }
        return shared_structures.get(canonical, canonical)


class ScoringEngine:
    def __init__(self, table: ScoreTable) -> None:
        self.table = table
        self.normalizer = CastellNormalizer(table)

    def calculate(self, query: ParsedCastellQuery) -> CalculationResult:
        if query.intent in {"clarification", "unsupported"} or not query.performances:
            reply = query.clarification or "No he pogut identificar cap castell. Me'l pots escriure amb una notació com 5d9f?"
            return CalculationResult(
                reply=reply,
                intent=query.intent,
                performances=[],
                winner_label=None,
                warnings=[],
                needs_clarification=True,
            )

        warnings: list[str] = []
        performance_results: list[PerformanceResult] = []
        has_unknown = False

        for performance in query.performances:
            scored: list[ScoredCastell] = []
            for parsed in performance.castells:
                canonical = self.normalizer.normalize(parsed.notation)
                if canonical is None:
                    has_unknown = True
                    warning = f"No reconec el castell «{parsed.notation}»."
                    warnings.append(warning)
                    scored.append(
                        ScoredCastell(
                            input=parsed.notation,
                            canonical=None,
                            outcome=parsed.outcome,
                            points=0,
                            reason="unknown_castell",
                        )
                    )
                    continue
                points = self.table.points(canonical, parsed.outcome)
                scored.append(
                    ScoredCastell(
                        input=parsed.notation,
                        canonical=canonical,
                        outcome=parsed.outcome,
                        points=points,
                        reason="attempt" if parsed.outcome is Outcome.ATTEMPT else None,
                    )
                )

            self._select_counted(scored)
            performance_results.append(
                PerformanceResult(
                    label=performance.label,
                    total=sum(item.points for item in scored if item.counted),
                    castells=scored,
                )
            )

        winner_label: str | None = None
        if not has_unknown and len(performance_results) > 1:
            best = max(result.total for result in performance_results)
            winners = [result.label for result in performance_results if result.total == best]
            if len(winners) == 1:
                winner_label = winners[0]

        reply = self._render_reply(performance_results, winner_label, warnings, has_unknown)
        return CalculationResult(
            reply=reply,
            intent=query.intent,
            performances=performance_results,
            winner_label=winner_label,
            warnings=warnings,
            needs_clarification=has_unknown,
        )

    def _select_counted(self, scored: list[ScoredCastell]) -> None:
        eligible = [item for item in scored if item.canonical is not None and item.outcome is not Outcome.ATTEMPT]

        best_by_structure: dict[str, ScoredCastell] = {}
        for item in eligible:
            assert item.canonical is not None
            key = self.normalizer.structure_key(item.canonical)
            current = best_by_structure.get(key)
            if current is None or item.points > current.points:
                if current is not None:
                    current.reason = "duplicate_structure"
                best_by_structure[key] = item
            else:
                item.reason = "duplicate_structure"

        candidates = list(best_by_structure.values())
        combinations: list[tuple[ScoredCastell, ...]] = []
        for size in range(1, min(3, len(candidates)) + 1):
            for candidate_group in itertools.combinations(candidates, size):
                loaded = sum(item.outcome is Outcome.LOADED for item in candidate_group)
                if loaded <= 2:
                    combinations.append(candidate_group)

        selected = max(combinations, key=lambda group: sum(item.points for item in group), default=())
        selected_ids = {id(item) for item in selected}
        loaded_selected = sum(item.outcome is Outcome.LOADED for item in selected)

        for item in candidates:
            if id(item) in selected_ids:
                item.counted = True
                item.reason = None
            elif item.reason is None:
                if item.outcome is Outcome.LOADED and loaded_selected >= 2:
                    item.reason = "loaded_limit"
                else:
                    item.reason = "outside_top_three"

    @staticmethod
    def _format_points(points: int) -> str:
        return f"{points:,}".replace(",", ".")

    def _render_reply(
        self,
        performances: list[PerformanceResult],
        winner_label: str | None,
        warnings: list[str],
        has_unknown: bool,
    ) -> str:
        parts: list[str] = []
        for performance in performances:
            counted = [item for item in performance.castells if item.counted]
            details = ", ".join(
                f"{item.canonical} {self._outcome_label(item.outcome)} ({self._format_points(item.points)} punts)"
                for item in counted
                if item.canonical
            )
            if len(performances) == 1 and len(counted) == 1:
                parts.append(f"El {details}.")
            else:
                parts.append(
                    f"{performance.label}: {details or 'cap castell computable'}. Total: {self._format_points(performance.total)} punts."
                )

        if has_unknown:
            parts.extend(warnings)
            parts.append("Aclareix aquesta notació i tornaré a fer el càlcul complet.")
        elif len(performances) > 1:
            totals = [performance.total for performance in performances]
            if len(set(totals)) == 1:
                parts.append(f"Hi ha un empat a {self._format_points(totals[0])} punts.")
            elif winner_label is not None:
                difference = max(totals) - sorted(totals, reverse=True)[1]
                parts.append(f"Guanya {winner_label} per {self._format_points(difference)} punts.")
        return " ".join(parts)

    @staticmethod
    def _outcome_label(outcome: Outcome) -> str:
        return {
            Outcome.LOADED: "carregat",
            Outcome.UNLOADED: "descarregat",
            Outcome.ATTEMPT: "intent",
        }[outcome]
