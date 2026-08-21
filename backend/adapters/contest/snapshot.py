from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from backend.domain.calculator.models import Outcome
from backend.domain.calculator.normalization import CastellNormalizer
from backend.domain.calculator.table import ScoreTable
from backend.domain.contest.models import (
    ContestKnowledgeQuery,
    ScorePresentation,
    ScoreRankingRow,
)

DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data" / "contest"

RESULT_LABELS = {
    "descarregat": "descarregat",
    "carregat": "carregat",
    "intent": "intent",
    "intent_desmuntat": "intent desmuntat",
    "sense_actuació": "sense actuació",
    "desconegut": "resultat no identificat",
}


class SnapshotContestKnowledgeRepository:
    def __init__(
        self,
        rules: dict[str, Any],
        results: dict[str, Any],
        score_table: ScoreTable,
    ) -> None:
        self.rules = rules
        self.results = results
        self.score_table = score_table
        self.normalizer = CastellNormalizer(score_table)

    @classmethod
    def default(cls) -> SnapshotContestKnowledgeRepository:
        return cls(
            rules=_load_snapshot("rules.json"),
            results=_load_snapshot("previous_results.json"),
            score_table=ScoreTable.default(),
        )

    def retrieve(self, query: ContestKnowledgeQuery) -> str:
        if query.source == "rules":
            return self._render_rules()
        if query.source == "results":
            return self._render_results(query)
        return self._render_score_ranking(query)

    def _render_rules(self) -> str:
        lines = [
            "<coneixement_recuperat>",
            "Tipus: normativa del Concurs de Castells.",
            f"Instantània verificada el {self.rules['verified_at']}.",
            "Precedència: canvis confirmats 2026 → normativa completa 2024 → no confirmable.",
        ]
        for source in self.rules["sources"]:
            lines.extend(
                [
                    f"<{source['id']}>",
                    f"Font: {source['title']} ({source['year']}) — {source['source_url']}",
                    source["text"],
                    f"</{source['id']}>",
                ]
            )
        lines.append("</coneixement_recuperat>")
        return "\n".join(lines)

    def _render_results(self, query: ContestKnowledgeQuery) -> str:
        editions = self.results["editions"]
        if query.years:
            requested_years = set(query.years)
            editions = [edition for edition in editions if edition["year"] in requested_years]

        lines = [
            "<coneixement_recuperat>",
            "Tipus: resultats històrics registrats; no són una recalculació amb la taula 2026.",
            f"Instantània verificada el {self.results['verified_at']}.",
            f"Índex oficial: {self.results['source_index']}",
        ]

        if not editions:
            return self._render_no_matches(lines, query)

        scope = query.result_scope or "classification"
        if scope == "editions" and not query.groups:
            lines.append("Edicions publicades:")
            for edition in editions:
                status = "celebrat" if edition["status"] == "held" else "no celebrat"
                lines.append(
                    f"{edition['year']} | {edition['title']} | {status} | {edition['source_url']}"
                )
                if edition["status"] == "cancelled":
                    lines.append(edition["note"])
            lines.append("</coneixement_recuperat>")
            return "\n".join(lines)

        if scope == "winners" and not query.groups:
            lines.append("Guanyadors de les edicions celebrades:")
            for edition in editions:
                if edition["status"] == "cancelled":
                    lines.append(f"{edition['year']} | no celebrat | {edition['note']}")
                    continue
                classification = edition["classification"]
                if classification:
                    lines.append(f"{edition['year']} | {_render_winner(classification[0])}")
            lines.append("</coneixement_recuperat>")
            return "\n".join(lines)

        matching_rows = 0
        for edition in editions:
            rows = edition["classification"]
            if query.groups:
                rows = [row for row in rows if _matches_any_group(_row_group(row), query.groups)]
            if edition["status"] == "cancelled":
                if not query.groups:
                    lines.extend(
                        [
                            f"\n## {edition['title']} ({edition['year']}) — {edition['source_url']}",
                            edition["note"],
                        ]
                    )
                continue
            if not rows:
                continue
            matching_rows += len(rows)
            lines.append(f"\n## {edition['title']} ({edition['year']}) — {edition['source_url']}")
            lines.append("Columnes: " + " | ".join(edition["columns"]))
            lines.extend(_render_row(row) for row in rows)

        if matching_rows == 0 and (
            query.groups or all(e["status"] != "cancelled" for e in editions)
        ):
            return self._render_no_matches(lines[:4], query)
        lines.append("</coneixement_recuperat>")
        return "\n".join(lines)

    def _render_score_ranking(self, query: ContestKnowledgeQuery) -> str:
        presentation = self.score_presentation(query)
        if presentation is None:
            return "\n".join(
                [
                    "<coneixement_recuperat>",
                    "No hi ha cap castell coincident al rànquing de puntuacions 2026.",
                    "No completis aquesta absència amb coneixement extern ni dades inventades.",
                    "</coneixement_recuperat>",
                ]
            )
        score_outcome = presentation.outcome
        sort_outcome = Outcome.LOADED if score_outcome == "loaded" else Outcome.UNLOADED
        outcome_label = "carregat" if sort_outcome is Outcome.LOADED else "descarregat"
        lines = [
            "<coneixement_recuperat>",
            "Tipus: rànquing de puntuacions; no són totals històrics d'una actuació.",
            "Rànquing de puntuacions del Concurs de Castells 2026.",
            "Font: taula_puntuacions_concurs_castells_2026.csv.",
            f"Ordre: de més a menys punts {outcome_label}.",
        ]
        if score_outcome == "both":
            lines.append("Posició | Castell | Punts carregat | Punts descarregat")
            lines.extend(
                f"{row.position} | {row.notation} | {row.loaded_points} | {row.unloaded_points}"
                for row in presentation.rows
            )
        else:
            lines.append(f"Posició | Castell | Punts {outcome_label}")
            lines.extend(
                f"{row.position} | {row.notation} | "
                f"{row.loaded_points if sort_outcome is Outcome.LOADED else row.unloaded_points}"
                for row in presentation.rows
            )
        lines.append("</coneixement_recuperat>")
        return "\n".join(lines)

    def score_presentation(self, query: ContestKnowledgeQuery) -> ScorePresentation | None:
        if query.source != "scores":
            return None
        rows = self._selected_score_rows(query)
        if not rows:
            return None
        selection = query.ranking_selection or "full"
        is_card = selection in {"position", "neighbors"} or len(rows) == 1
        focus_notation = None
        if is_card:
            focus_notation = (
                self.normalizer.normalize(query.ranking_notation or "") or rows[0].notation
            )
            focus_row = next(
                (row for row in rows if row.notation == focus_notation),
                rows[0],
            )
            title = f"{focus_row.notation} · {focus_row.position}a posició"
        else:
            title = "Rànquing de puntuacions 2026"
        return ScorePresentation(
            kind="score_card" if is_card else "score_ranking",
            title=title,
            outcome=query.score_outcome or "both",
            rows=rows,
            focus_notation=focus_notation,
        )

    def _selected_score_rows(self, query: ContestKnowledgeQuery) -> list[ScoreRankingRow]:
        score_outcome = query.score_outcome or "both"
        sort_outcome = Outcome.LOADED if score_outcome == "loaded" else Outcome.UNLOADED
        sorted_scores = sorted(
            self.score_table.scores.items(),
            key=lambda item: item[1][sort_outcome],
            reverse=True,
        )
        rows = [
            ScoreRankingRow(
                position=position,
                notation=notation,
                loaded_points=scores[Outcome.LOADED],
                unloaded_points=scores[Outcome.UNLOADED],
            )
            for position, (notation, scores) in enumerate(sorted_scores, start=1)
        ]
        selection = query.ranking_selection or "full"
        if selection == "top":
            return rows[: query.ranking_limit or 1]
        if selection == "bottom":
            return rows[-(query.ranking_limit or 1) :]
        if selection in {"position", "neighbors"}:
            canonical = self.normalizer.normalize(query.ranking_notation or "")
            if canonical is None:
                return []
            index = next(
                (index for index, row in enumerate(rows) if row.notation == canonical),
                None,
            )
            if index is None:
                return []
            if selection == "position":
                return [rows[index]]
            return rows[max(0, index - 1) : min(len(rows), index + 2)]
        return rows

    @staticmethod
    def _render_no_matches(lines: list[str], query: ContestKnowledgeQuery) -> str:
        years = ", ".join(str(year) for year in query.years) or "qualsevol any"
        groups = ", ".join(query.groups) or "qualsevol colla"
        lines.extend(
            [
                f"No hi ha cap dada coincident per als anys [{years}] i les colles [{groups}].",
                "No completis aquesta absència amb coneixement extern ni dades inventades.",
                "</coneixement_recuperat>",
            ]
        )
        return "\n".join(lines)


def _load_snapshot(filename: str) -> dict[str, Any]:
    return json.loads((DATA_DIRECTORY / filename).read_text(encoding="utf-8"))


def _render_row(row: dict[str, Any]) -> str:
    if "rounds" not in row:
        return " | ".join(row["cells"])
    rounds = "; ".join(_render_round(round_result) for round_result in row["rounds"])
    return f"{row['position']} | {row['group']} | {rounds} | {row['points']} punts"


def _render_winner(row: dict[str, Any]) -> str:
    if "rounds" not in row:
        cells = row["cells"]
        return f"{cells[0]} | {cells[1]} | {cells[-1]} punts"
    return f"{row['position']} | {row['group']} | {row['points']} punts"


def _render_round(round_result: dict[str, Any]) -> str:
    details = [RESULT_LABELS[round_result["result"]]]
    if round_result["counted"]:
        details.append("computat")
    if round_result["penalty"]:
        details.append("penalitzat")
    return f"{round_result['notation']} [{', '.join(details)}]"


def _row_group(row: dict[str, Any]) -> str:
    return row.get("group") or row["cells"][1]


def _matches_any_group(candidate: str, requested_groups: list[str]) -> bool:
    candidate_tokens = _group_tokens(candidate)
    for requested in requested_groups:
        requested_tokens = _group_tokens(requested)
        if requested_tokens and (
            requested_tokens.issubset(candidate_tokens)
            or candidate_tokens.issubset(requested_tokens)
        ):
            return True
    return False


def _group_tokens(value: str) -> set[str]:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    tokens = {
        token
        for token in re.findall(r"[a-z0-9]+", normalized.lower())
        if len(token) > 1 and token.isalpha()
    }
    return tokens - {"c", "colla", "castellers", "de", "del", "dels", "la", "els"}
