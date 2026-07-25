from __future__ import annotations

import itertools

from backend.domain.calculator.labels import meaningful_performance_labels
from backend.domain.calculator.models import (
    CalculationResult,
    Outcome,
    ParsedCastellQuery,
    PerformanceResult,
    ScoredCastell,
)
from backend.domain.calculator.normalization import CastellNormalizer
from backend.domain.calculator.table import ScoreTable


class ScoringEngine:
    def __init__(self, table: ScoreTable) -> None:
        self.table = table
        self.normalizer = CastellNormalizer(table)

    def calculate(self, query: ParsedCastellQuery) -> CalculationResult:
        if query.intent in {"clarification", "unsupported"} or not query.performances:
            return CalculationResult(
                reply=query.clarification or "Quin castell vols calcular?",
                intent=query.intent,
                performances=[],
                winner_label=None,
                warnings=[],
                needs_clarification=True,
            )

        warnings: list[str] = []
        unknown_notations: list[str] = []
        performance_results: list[PerformanceResult] = []
        performance_labels = meaningful_performance_labels(query.performances)
        for performance, performance_label in zip(query.performances, performance_labels):
            scored: list[ScoredCastell] = []
            for parsed in performance.castells:
                canonical = self.normalizer.normalize(parsed.notation)
                if canonical is None:
                    if parsed.notation not in unknown_notations:
                        unknown_notations.append(parsed.notation)
                    warnings.append(f"No reconec el castell «{parsed.notation}».")
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
                scored.append(
                    ScoredCastell(
                        input=parsed.notation,
                        canonical=canonical,
                        outcome=parsed.outcome,
                        points=self.table.points(canonical, parsed.outcome),
                        reason="attempt" if parsed.outcome is Outcome.ATTEMPT else None,
                    )
                )
            self._select_counted(scored)
            performance_results.append(
                PerformanceResult(
                    label=performance_label,
                    total=sum(item.points for item in scored if item.counted),
                    castells=scored,
                )
            )

        if unknown_notations:
            return CalculationResult(
                reply=self._clarification_for_unknown(unknown_notations),
                intent=query.intent,
                performances=[],
                winner_label=None,
                warnings=warnings,
                needs_clarification=True,
            )

        winner_label: str | None = None
        if len(performance_results) > 1:
            best = max(result.total for result in performance_results)
            winners = [result.label for result in performance_results if result.total == best]
            if len(winners) == 1:
                winner_label = winners[0]
        return CalculationResult(
            reply=self._render_reply(performance_results, winner_label),
            intent=query.intent,
            performances=performance_results,
            winner_label=winner_label,
            warnings=warnings,
            needs_clarification=False,
        )

    @staticmethod
    def _clarification_for_unknown(notations: list[str]) -> str:
        if len(notations) == 1:
            return f"Quan dius «{notations[0]}», a quin castell et refereixes?"
        quoted = [f"«{notation}»" for notation in notations]
        names = " ni ".join(quoted) if len(quoted) == 2 else ", ".join(quoted[:-1]) + f" ni {quoted[-1]}"
        return f"No acabo d’identificar {names}. A quins castells et refereixes?"

    def _select_counted(self, scored: list[ScoredCastell]) -> None:
        eligible = [
            item
            for item in scored
            if item.canonical is not None and item.outcome is not Outcome.ATTEMPT
        ]
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
        combinations = [
            group
            for size in range(1, min(3, len(candidates)) + 1)
            for group in itertools.combinations(candidates, size)
            if sum(item.outcome is Outcome.LOADED for item in group) <= 2
        ]
        selected = max(combinations, key=lambda group: sum(item.points for item in group), default=())
        selected_ids = {id(item) for item in selected}
        loaded_selected = sum(item.outcome is Outcome.LOADED for item in selected)
        for item in candidates:
            if id(item) in selected_ids:
                item.counted = True
                item.reason = None
            elif item.reason is None:
                item.reason = (
                    "loaded_limit"
                    if item.outcome is Outcome.LOADED and loaded_selected >= 2
                    else "outside_top_three"
                )

    @staticmethod
    def _format_points(points: int) -> str:
        return f"{points:,}".replace(",", ".")

    def _render_reply(
        self, performances: list[PerformanceResult], winner_label: str | None
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
                    f"{performance.label}: {details or 'cap castell computable'}. "
                    f"Total: {self._format_points(performance.total)} punts."
                )
        if len(performances) > 1:
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
