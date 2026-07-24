from __future__ import annotations

import re

from backend.domain.calculator.models import (
    ChatTurn,
    Outcome,
    ParsedCastell,
    ParsedCastellQuery,
    ParsedPerformance,
)
from backend.domain.calculator.labels import meaningful_performance_labels


CASTELL_PATTERN = re.compile(
    r"\b(?:[pt](?:d|de)?\d{1,2}[a-z]*|\d+(?:d|de)\d{1,2}[a-z]*)\b",
    re.IGNORECASE,
)
SIDE_SEPARATOR = re.compile(r"\s+(?:vs\.?|contra)\s+", re.IGNORECASE)
LABEL_PATTERN = re.compile(
    r"\b(?:la|els|les)\s+([A-ZÀ-Ü][A-Za-zÀ-ÿ'·-]*(?:\s+[A-ZÀ-Ü][A-Za-zÀ-ÿ'·-]*){0,3})"
    r"(?=\s+(?:descarrega|descarreguen|carrega|carreguen|fa|fan|prova|proven|el|la)\b)"
)


class RegexQueryInterpreter:
    """Offline baseline adapter; external model adapters implement the same port."""

    async def interpret(self, history: list[ChatTurn], message: str) -> ParsedCastellQuery:
        del history
        text = message.strip()
        sides = SIDE_SEPARATOR.split(text, maxsplit=1)
        if len(sides) == 2:
            performances = [
                ParsedPerformance(label="A", castells=self._parse_castells(sides[0])),
                ParsedPerformance(label="B", castells=self._parse_castells(sides[1])),
            ]
            performances = self._with_meaningful_labels(performances)
            return self._validated("comparison", performances)

        named = self._parse_named_performances(text)
        if len(named) >= 2:
            return self._validated("comparison", named)

        matches = list(CASTELL_PATTERN.finditer(text))
        if len(matches) == 2 and re.search(r"\s+o\s+", text, re.IGNORECASE):
            performances = [
                ParsedPerformance(
                    label=f"Amb {match.group(0)}",
                    castells=[ParsedCastell(match.group(0), self._outcome(text[: match.start()]))],
                )
                for match in matches
            ]
            return self._validated("comparison", performances)

        castells = self._parse_castells(text)
        if castells:
            intent = "lookup" if len(castells) == 1 else "total"
            return ParsedCastellQuery(
                intent=intent,
                performances=[ParsedPerformance(label="Actuació", castells=castells)],
            )
        return ParsedCastellQuery(
            intent="clarification",
            clarification="Quin castell vols calcular?",
        )

    def _parse_named_performances(self, text: str) -> list[ParsedPerformance]:
        castle_matches = list(CASTELL_PATTERN.finditer(text))
        if not castle_matches:
            return []
        grouped: dict[str, list[ParsedCastell]] = {}
        order: list[str] = []
        previous_end = 0
        current_label: str | None = None
        for match in castle_matches:
            prefix = text[previous_end : match.start()]
            label_matches = list(LABEL_PATTERN.finditer(prefix))
            if label_matches:
                current_label = label_matches[-1].group(1).strip()
            if current_label is None:
                previous_end = match.end()
                continue
            if current_label not in grouped:
                grouped[current_label] = []
                order.append(current_label)
            grouped[current_label].append(ParsedCastell(match.group(0), self._outcome(prefix)))
            previous_end = match.end()
        return [ParsedPerformance(label=label, castells=grouped[label]) for label in order]

    @staticmethod
    def _with_meaningful_labels(
        performances: list[ParsedPerformance],
    ) -> list[ParsedPerformance]:
        labels = meaningful_performance_labels(performances)
        return [
            ParsedPerformance(label=label, castells=performance.castells)
            for label, performance in zip(labels, performances)
        ]

    def _parse_castells(self, text: str) -> list[ParsedCastell]:
        matches = list(CASTELL_PATTERN.finditer(text))
        result: list[ParsedCastell] = []
        previous_end = 0
        inherited_outcome: Outcome | None = None
        for match in matches:
            prefix = text[previous_end : match.start()]
            explicit = self._explicit_outcome(prefix)
            if explicit is not None:
                inherited_outcome = explicit
            result.append(ParsedCastell(match.group(0), explicit or inherited_outcome or Outcome.UNLOADED))
            previous_end = match.end()
        return result

    @staticmethod
    def _explicit_outcome(text: str) -> Outcome | None:
        lower = text.lower()
        if "intent" in lower or "prova" in lower:
            return Outcome.ATTEMPT
        if "descarreg" in lower or "complet" in lower:
            return Outcome.UNLOADED
        if "carreg" in lower or "coron" in lower:
            return Outcome.LOADED
        return None

    def _outcome(self, text: str) -> Outcome:
        return self._explicit_outcome(text) or Outcome.UNLOADED

    @staticmethod
    def _validated(intent: str, performances: list[ParsedPerformance]) -> ParsedCastellQuery:
        if any(not performance.castells for performance in performances):
            return ParsedCastellQuery(
                intent="clarification",
                clarification="Quin castell vols posar a l’altra opció?",
            )
        return ParsedCastellQuery(intent=intent, performances=performances)  # type: ignore[arg-type]
