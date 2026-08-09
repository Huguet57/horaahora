from __future__ import annotations

from typing import Any

from backend.adapters.ai.prompts.contest_snapshot import load_contest_snapshot

RESULT_LABELS = {
    "descarregat": "descarregat",
    "carregat": "carregat",
    "intent": "intent",
    "intent_desmuntat": "intent desmuntat",
    "sense_actuació": "sense actuació",
    "desconegut": "resultat no identificat",
}


def _round_label(round_result: dict[str, Any]) -> str:
    details = [RESULT_LABELS[round_result["result"]]]
    if round_result["counted"]:
        details.append("computat")
    if round_result["penalty"]:
        details.append("penalitzat")
    return f"{round_result['notation']} [{', '.join(details)}]"


def render_contest_results_prompt() -> str:
    snapshot = load_contest_snapshot("previous_results.json")
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


CONTEST_RESULTS_PROMPT = render_contest_results_prompt()
