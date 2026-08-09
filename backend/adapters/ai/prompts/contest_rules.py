from __future__ import annotations

from backend.adapters.ai.prompts.contest_snapshot import load_contest_snapshot


def render_contest_rules_prompt() -> str:
    snapshot = load_contest_snapshot("rules.json")
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


CONTEST_RULES_PROMPT = render_contest_rules_prompt()
