from backend.domain.calculator.models import Outcome
from backend.domain.calculator.table import ScoreTable
from scripts.export_score_table import OUTPUTS, build_score_table, castell_name, render


def test_export_keeps_the_official_order_groups_and_points() -> None:
    castells = build_score_table()["castells"]
    table = ScoreTable.default()

    assert [castell["notation"] for castell in castells] == list(table.scores)
    assert castells[0] == {
        "notation": "2de6",
        "name": "Torre de sis",
        "group": 1,
        "loaded": 250,
        "unloaded": 300,
    }
    assert castells[-1]["notation"] == "3de10sm"
    assert castells[-1]["group"] == 7
    for castell in castells:
        assert castell["loaded"] == table.points(castell["notation"], Outcome.LOADED)
        assert castell["unloaded"] == table.points(castell["notation"], Outcome.UNLOADED)


def test_names_read_the_notation_in_catalan() -> None:
    assert castell_name("Pde5") == "Pilar de cinc"
    assert castell_name("9de8") == "Nou de vuit"
    assert castell_name("4de7a") == "Quatre de set amb l'agulla"
    assert castell_name("3de8s") == "Tres de vuit aixecat per sota"
    assert castell_name("2de8f") == "Torre de vuit amb folre"
    assert castell_name("3de9fa") == "Tres de nou amb folre i l'agulla"
    assert castell_name("4de10fm") == "Quatre de deu amb folre i manilles"
    assert castell_name("Pde9fmp") == "Pilar de nou amb folre, manilles i puntals"
    assert castell_name("4de9sf") == "Quatre de nou sense folre"
    assert castell_name("2de9sm") == "Torre de nou sense manilles"


def test_bundled_copies_match_the_backend_table() -> None:
    expected = render(build_score_table())

    for output in OUTPUTS:
        assert output.read_text(encoding="utf-8") == expected, (
            f"{output} està desfasat: executa "
            "`uv run --frozen --no-sync python -m scripts.export_score_table`"
        )
