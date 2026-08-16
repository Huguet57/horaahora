from __future__ import annotations

import json
from pathlib import Path

from scripts.update_contest_rules import extract_rule_page

REPOSITORY_ROOT = Path(__file__).parents[2]
SNAPSHOT_PATH = REPOSITORY_ROOT / "backend/data/contest/rules.json"


def test_rule_extractor_keeps_headings_articles_and_lists() -> None:
    html = """
    <div class="col-md-8 body clearfix generica">
      <h1 class="title">Normes bàsiques 2024</h1>
      <div class="body mb20">
        <h2>Capítol primer</h2>
        <p><strong>Article 1</strong></p>
        <ul><li>Primera regla</li><li>Segona regla</li></ul>
      </div>
    </div>
    """

    source = extract_rule_page(
        source_id="normativa_completa_2024",
        year=2024,
        source_url="https://www.concursdecastells.cat/normes-basiques-2024-cdc",
        html=html,
    )

    assert source["title"] == "Normes bàsiques 2024"
    assert source["text"].splitlines() == [
        "Capítol primer",
        "Article 1",
        "- Primera regla",
        "- Segona regla",
    ]


def test_versioned_rules_snapshot_separates_2026_overrides_from_2024_baseline() -> None:
    snapshot = json.loads(SNAPSHOT_PATH.read_text())
    sources = {source["id"]: source for source in snapshot["sources"]}

    assert snapshot["verified_at"] == "2026-08-09"
    assert list(sources) == [
        "canvis_confirmats_2026",
        "normativa_completa_2024",
        "protocol_placa_2024",
    ]
    assert "màxim dos castells carregats" in sources["canvis_confirmats_2026"]["text"]
    assert "Classificació final" in sources["normativa_completa_2024"]["text"]
    assert "carregada" in sources["protocol_placa_2024"]["text"]
    assert all(source["source_url"].startswith("https://") for source in sources.values())
