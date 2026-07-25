from backend.domain.calculator.models import (
    Outcome,
    ParsedCastell,
    ParsedCastellQuery,
    ParsedPerformance,
)
from backend.domain.calculator.scoring import ScoringEngine
from backend.domain.calculator.table import ScoreTable


def make_engine() -> ScoringEngine:
    return ScoringEngine(ScoreTable.default())


def performance(label: str, *castells: tuple[str, Outcome]) -> ParsedPerformance:
    return ParsedPerformance(
        label=label,
        castells=[
            ParsedCastell(notation=notation, outcome=outcome) for notation, outcome in castells
        ],
    )


def test_compares_two_unloaded_castells() -> None:
    result = make_engine().calculate(
        ParsedCastellQuery(
            intent="comparison",
            performances=[
                performance("5d9f", ("5d9f", Outcome.UNLOADED)),
                performance("4d9fa", ("4d9fa", Outcome.UNLOADED)),
            ],
        )
    )

    assert [item.total for item in result.performances] == [3125, 3285]
    assert [item.label for item in result.performances] == ["Amb 5d9f", "Amb 4d9fa"]
    assert result.winner_label == "Amb 4d9fa"
    assert "160 punts" in result.reply


def test_compares_named_groups_and_net_alias() -> None:
    result = make_engine().calculate(
        ParsedCastellQuery(
            intent="comparison",
            performances=[
                performance("Vella", ("4d10fm", Outcome.UNLOADED)),
                performance("Joves", ("4d9net", Outcome.UNLOADED)),
            ],
        )
    )

    assert [item.total for item in result.performances] == [4930, 4105]
    assert result.winner_label == "Vella"


def test_compares_three_castell_performances() -> None:
    result = make_engine().calculate(
        ParsedCastellQuery(
            intent="comparison",
            performances=[
                performance(
                    "Opció A",
                    ("5d9f", Outcome.UNLOADED),
                    ("4d9fa", Outcome.UNLOADED),
                    ("3d10fm", Outcome.UNLOADED),
                ),
                performance(
                    "Opció B",
                    ("3d10fm", Outcome.UNLOADED),
                    ("4d10fm", Outcome.UNLOADED),
                    ("3d9fa", Outcome.UNLOADED),
                ),
            ],
        )
    )

    assert [item.total for item in result.performances] == [10935, 12900]
    assert [item.label for item in result.performances] == ["Amb 5d9f", "Amb 4d10fm"]
    assert result.winner_label == "Amb 4d10fm"
    assert "1.965 punts" in result.reply


def test_falls_back_to_letters_when_unnamed_sides_have_no_distinctive_castell() -> None:
    result = make_engine().calculate(
        ParsedCastellQuery(
            intent="comparison",
            performances=[
                performance("costat 1", ("5d9f", Outcome.UNLOADED)),
                performance("costat 2", ("5d9f", Outcome.UNLOADED)),
            ],
        )
    )

    assert [item.label for item in result.performances] == ["A", "B"]


def test_keeps_top_three_with_at_most_two_loaded() -> None:
    result = make_engine().calculate(
        ParsedCastellQuery(
            intent="total",
            performances=[
                performance(
                    "Colla",
                    ("3d10sm", Outcome.LOADED),
                    ("4d10sm", Outcome.LOADED),
                    ("2d10fmp", Outcome.LOADED),
                    ("5d9f", Outcome.UNLOADED),
                )
            ],
        )
    )

    counted = [item for item in result.performances[0].castells if item.counted]
    assert len(counted) == 3
    assert sum(item.outcome is Outcome.LOADED for item in counted) == 2
    assert any(item.reason == "loaded_limit" for item in result.performances[0].castells)


def test_only_best_result_for_same_structure_counts() -> None:
    result = make_engine().calculate(
        ParsedCastellQuery(
            intent="total",
            performances=[
                performance(
                    "Colla",
                    ("4d9f", Outcome.UNLOADED),
                    ("4d9net", Outcome.UNLOADED),
                    ("5d9f", Outcome.UNLOADED),
                )
            ],
        )
    )

    castells = result.performances[0].castells
    assert next(item for item in castells if item.canonical == "4de9sf").counted
    assert (
        next(item for item in castells if item.canonical == "4de9f").reason == "duplicate_structure"
    )


def test_attempt_scores_zero_and_unknown_prevents_a_winner() -> None:
    result = make_engine().calculate(
        ParsedCastellQuery(
            intent="comparison",
            performances=[
                performance("A", ("5d9f", Outcome.ATTEMPT)),
                performance("B", ("10d10", Outcome.UNLOADED)),
            ],
        )
    )

    assert result.winner_label is None
    assert result.needs_clarification
    assert any("10d10" in warning for warning in result.warnings)
    assert result.performances == []
    assert result.reply == "Quan dius «10d10», a quin castell et refereixes?"
    assert "0 punts" not in result.reply
    assert "cap castell computable" not in result.reply


def test_multiple_unknown_castells_ask_one_short_natural_follow_up() -> None:
    result = make_engine().calculate(
        ParsedCastellQuery(
            intent="comparison",
            performances=[
                performance("A", ("10d10", Outcome.UNLOADED)),
                performance("B", ("torrevolada", Outcome.UNLOADED)),
            ],
        )
    )

    assert result.needs_clarification
    assert result.performances == []
    assert result.reply == (
        "No acabo d’identificar «10d10» ni «torrevolada». A quins castells et refereixes?"
    )


def test_equal_performances_are_reported_as_a_tie() -> None:
    result = make_engine().calculate(
        ParsedCastellQuery(
            intent="comparison",
            performances=[
                performance("A", ("5d9f", Outcome.UNLOADED)),
                performance("B", ("5d9f", Outcome.UNLOADED)),
            ],
        )
    )

    assert result.winner_label is None
    assert "empat a 3.125 punts" in result.reply
