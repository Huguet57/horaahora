from __future__ import annotations

import json
from pathlib import Path

from scripts.update_contest_results import parse_edition_page

REPOSITORY_ROOT = Path(__file__).parents[2]
SNAPSHOT_PATH = REPOSITORY_ROOT / "backend/data/contest/previous_results.json"


def test_parser_preserves_modern_round_outcomes_counting_and_penalties() -> None:
    html = """
    <div class="col-md-8 body clearfix generica">
      <h1 class="title">Concurs 2024</h1>
      <div class="body mb20">
        <p>Consulta la classificació.</p>
        <div id="j_resultats">
          <table></table>
          <table><tbody><tr>
            <td><span>1</span></td>
            <td><span>C. de Vilafranca (6/10)</span></td>
            <td class="bg-black td-datos"><span class="bg-verde">3de10fm</span></td>
            <td class="td-datos"><span class="bg-rojo">9de9f</span></td>
            <td class="td-datos"><span class="bg-naranja">4de9fa</span></td>
            <td class="bg-black td-datos"><span class="bg-naranja"><a
              class="penalizado" title="Penalitzacions: 2|Dues rondes">9de9f*</a></span></td>
            <td class="total"><span>9465</span></td>
          </tr></tbody></table>
        </div>
      </div>
    </div>
    """

    edition = parse_edition_page(
        year=2024,
        source_url="https://www.concursdecastells.cat/concurs-2024-cdc",
        html=html,
    )

    assert edition["status"] == "held"
    assert edition["classification"][0] == {
        "position": "1",
        "group": "C. de Vilafranca (6/10)",
        "rounds": [
            {
                "notation": "3de10fm",
                "result": "descarregat",
                "counted": True,
                "penalty": None,
            },
            {
                "notation": "9de9f",
                "result": "intent_desmuntat",
                "counted": False,
                "penalty": None,
            },
            {
                "notation": "4de9fa",
                "result": "carregat",
                "counted": False,
                "penalty": None,
            },
            {
                "notation": "9de9f*",
                "result": "carregat",
                "counted": True,
                "penalty": "Penalitzacions: 2|Dues rondes",
            },
        ],
        "points": "9465",
    }


def test_parser_preserves_historical_headers_and_marks() -> None:
    html = """
    <div class="col-md-8 body clearfix generica">
      <h1 class="title">Concurs 1932</h1>
      <div class="body mb20">
        <table>
          <tr><th>Pos.</th><th>Colla</th><th>1a ronda</th><th>Punts</th></tr>
          <tr><td>1</td><td>Colla Vella dels Xiquets de Valls</td><td>3 de 7</td><td>149</td></tr>
        </table>
      </div>
    </div>
    """

    edition = parse_edition_page(
        year=1932,
        source_url="https://www.concursdecastells.cat/concurs-1932-cdc",
        html=html,
    )

    assert edition["columns"] == ["Pos.", "Colla", "1a ronda", "Punts"]
    assert edition["classification"][0]["cells"] == [
        "1",
        "Colla Vella dels Xiquets de Valls",
        "3 de 7",
        "149",
    ]


def test_parser_records_cancelled_2020_without_a_classification() -> None:
    html = """
    <div class="col-md-8 body clearfix generica">
      <h1 class="title">Concurs 2020</h1>
      <div class="body mb20">
        <p>L'any 2020 no es va celebrar el Concurs de Castells a causa de la pandèmia.</p>
      </div>
    </div>
    """

    edition = parse_edition_page(
        year=2020,
        source_url="https://www.concursdecastells.cat/concurs-2020-cdc",
        html=html,
    )

    assert edition["status"] == "cancelled"
    assert edition["classification"] == []
    assert "pandèmia" in edition["note"]


def test_versioned_snapshot_contains_every_official_edition_once() -> None:
    snapshot = json.loads(SNAPSHOT_PATH.read_text())
    editions = snapshot["editions"]
    years = [edition["year"] for edition in editions]

    assert len(editions) == 30
    assert len(years) == len(set(years))
    assert years == sorted(years, reverse=True)
    assert snapshot["verified_at"] == "2026-08-09"
    assert snapshot["source_index"].endswith("/edicions-anteriors-cdc")

    by_year = {edition["year"]: edition for edition in editions}
    assert by_year[2020]["status"] == "cancelled"
    assert by_year[2024]["classification"][0]["group"] == "C. de Vilafranca (6/10)"
    assert by_year[1932]["classification"][0]["cells"][1] == ("Colla Vella dels Xiquets de Valls")
