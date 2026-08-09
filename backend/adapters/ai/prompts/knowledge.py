from __future__ import annotations

import json
from pathlib import Path

DATA_ROOT = Path(__file__).resolve().parents[3] / "data" / "contest"


def _load_json(filename: str) -> dict:
    return json.loads((DATA_ROOT / filename).read_text(encoding="utf-8"))


def _render_rules() -> str:
    snapshot = _load_json("rules.json")
    sections = [
        "<coneixement_normatiu>",
        f"Instantània verificada el {snapshot['verified_at']}.",
    ]
    for source in snapshot["sources"]:
        sections.extend(
            [
                f"<{source['id']}>",
                f"Font: {source['title']} ({source['year']}) — {source['source_url']}",
                source["text"],
                f"</{source['id']}>",
            ]
        )
    sections.append("</coneixement_normatiu>")
    return "\n".join(sections)


def _round_label(round_result: dict) -> str:
    results = {
        "descarregat": "descarregat",
        "carregat": "carregat",
        "intent": "intent",
        "intent_desmuntat": "intent desmuntat",
        "sense_actuació": "sense actuació",
        "desconegut": "resultat no identificat",
    }
    details = [results[round_result["result"]]]
    if round_result["counted"]:
        details.append("computat")
    if round_result["penalty"]:
        details.append("penalitzat")
    return f"{round_result['notation']} [{', '.join(details)}]"


def _render_results() -> str:
    snapshot = _load_json("previous_results.json")
    lines = [
        "<resultats_anteriors>",
        f"Instantània verificada el {snapshot['verified_at']}.",
        f"Índex oficial: {snapshot['source_index']}",
        "En les edicions modernes, cada ronda indica resultat, si va computar i si consta "
        "penalització. En les edicions històriques es conserva literalment la notació de la "
        "taula oficial; `c`, `i` i `id` poden aparèixer com a marques històriques.",
    ]
    for edition in snapshot["editions"]:
        lines.append(f"\n## {edition['title']} ({edition['year']}) — {edition['source_url']}")
        if edition["status"] == "cancelled":
            lines.append(edition["note"])
            continue
        lines.append("Columnes: " + " | ".join(edition["columns"]))
        for row in edition["classification"]:
            if "rounds" in row:
                rounds = "; ".join(_round_label(item) for item in row["rounds"])
                lines.append(
                    f"{row['position']} | {row['group']} | {rounds} | {row['points']} punts"
                )
            else:
                lines.append(" | ".join(row["cells"]))
    lines.append("</resultats_anteriors>")
    return "\n".join(lines)


CONTEST_RULES_PROMPT = _render_rules()
CONTEST_RESULTS_PROMPT = _render_results()
