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


def test_trailing_c_marks_a_glued_castell_as_loaded() -> None:
    # Shared conversations wrote «9d9fc» and «4d10fmc» for carregat and got a clarification.
    result = make_engine().calculate(
        ParsedCastellQuery(
            intent="total",
            performances=[
                performance(
                    "Verds",
                    ("9d9fc", Outcome.UNLOADED),
                    ("4d10fmc", Outcome.UNLOADED),
                    ("3d10fm", Outcome.UNLOADED),
                ),
            ],
        )
    )

    assert not result.needs_clarification
    castells = result.performances[0].castells
    assert [item.canonical for item in castells] == ["9de9f", "4de10fm", "3de10fm"]
    assert [item.outcome for item in castells] == [
        Outcome.LOADED,
        Outcome.LOADED,
        Outcome.UNLOADED,
    ]
    assert result.performances[0].total == 4295 + 4095 + 4525


def test_ranks_three_or_more_performances_by_total() -> None:
    # A shared conversation asked to «ordena la meva porra» and got the colles in input order.
    result = make_engine().calculate(
        ParsedCastellQuery(
            intent="comparison",
            performances=[
                performance("Reus", ("4d9f", Outcome.UNLOADED)),
                performance("Vella", ("4d10fm", Outcome.UNLOADED)),
                performance("Moixis", ("4d9f", Outcome.UNLOADED)),
                performance("Joves", ("4d9sf", Outcome.UNLOADED)),
            ],
        )
    )

    # Ties keep the order the user wrote them in.
    assert [item.label for item in result.performances] == ["Vella", "Joves", "Reus", "Moixis"]
    assert result.reply.startswith("Vella:")
    assert result.winner_label == "Vella"


def test_two_performances_keep_the_order_they_were_written_in() -> None:
    result = make_engine().calculate(
        ParsedCastellQuery(
            intent="comparison",
            performances=[
                performance("Joves", ("4d9sf", Outcome.UNLOADED)),
                performance("Vella", ("4d10fm", Outcome.UNLOADED)),
            ],
        )
    )

    assert [item.label for item in result.performances] == ["Joves", "Vella"]


def test_a_twelve_colla_porra_is_calculated() -> None:
    result = make_engine().calculate(
        ParsedCastellQuery(
            intent="comparison",
            performances=[performance(f"Colla {n}", ("5d8", Outcome.UNLOADED)) for n in range(12)],
        )
    )

    assert not result.needs_clarification
    assert len(result.performances) == 12


def test_more_performances_than_the_limit_ask_to_split_them() -> None:
    # A 12-colla porra used to fail with a provider error on every turn.
    result = make_engine().calculate(
        ParsedCastellQuery(
            intent="comparison",
            performances=[performance(f"Colla {n}", ("5d8", Outcome.UNLOADED)) for n in range(17)],
        )
    )

    assert result.needs_clarification
    assert result.performances == []
    assert "fins a 16" in result.reply
    assert "17" in result.reply


def variants_of_5d8_7d8_2d8f(*loaded: str) -> list[tuple[str, Outcome]]:
    return [
        (notation, Outcome.LOADED if notation in loaded else Outcome.UNLOADED)
        for notation in ("5d8", "7d8", "td8f")
    ]


def reference(label: str, *castells: tuple[str, Outcome]) -> ParsedPerformance:
    return ParsedPerformance(
        label=label,
        castells=[
            ParsedCastell(notation=notation, outcome=outcome) for notation, outcome in castells
        ],
        reference=True,
    )


BASE_3610 = (("7d8", Outcome.UNLOADED), ("td8f", Outcome.UNLOADED), ("4d8a", Outcome.LOADED))


def test_variants_against_a_reference_say_which_ones_beat_it() -> None:
    # Shared 2026-10-02: «what can stay loaded and still beat it?» got six full
    # performances and «Guanya B: tot descarregat», which ranks the variants instead.
    result = make_engine().calculate(
        ParsedCastellQuery(
            intent="comparison",
            performances=[
                reference("Actuació base", *BASE_3610),
                performance("B: tot descarregat", *variants_of_5d8_7d8_2d8f()),
                performance("B: 7d8 carregat", *variants_of_5d8_7d8_2d8f("7d8")),
                performance("B: 2d8f carregat", *variants_of_5d8_7d8_2d8f("td8f")),
                performance("B: 5d8 carregat", *variants_of_5d8_7d8_2d8f("5d8")),
                performance("B: tot carregat", *variants_of_5d8_7d8_2d8f("5d8", "7d8", "td8f")),
            ],
        )
    )

    assert [item.total for item in result.performances] == [3685, 3610, 3500, 3480, 3450, 2155]
    assert result.winner_label == "B: tot descarregat"
    assert result.reply == (
        "Per superar «Actuació base» (3.610 punts) només serveix «B: tot descarregat»: "
        "3.685 punts, 75 més. Per sota hi queden «B: 7d8 carregat» 3.500 punts (−110), "
        "«B: 2d8f carregat» 3.480 punts (−130), «B: 5d8 carregat» 3.450 punts (−160) i "
        "«B: tot carregat» 2.155 punts (−1.455)."
    )


def test_no_variant_beats_the_reference() -> None:
    result = make_engine().calculate(
        ParsedCastellQuery(
            intent="comparison",
            performances=[
                reference("Actuació base", *BASE_3610),
                performance("7d8 carregat", *variants_of_5d8_7d8_2d8f("7d8")),
                performance("5d8 carregat", *variants_of_5d8_7d8_2d8f("5d8")),
            ],
        )
    )

    assert result.reply == (
        "Cap variant supera «Actuació base» (3.610 punts): «7d8 carregat» 3.500 punts (−110) "
        "i «5d8 carregat» 3.450 punts (−160)."
    )


def test_every_variant_beats_the_reference() -> None:
    result = make_engine().calculate(
        ParsedCastellQuery(
            intent="comparison",
            performances=[
                reference("Rival", ("5d8", Outcome.LOADED), ("7d8", Outcome.LOADED)),
                performance("Tot descarregat", *variants_of_5d8_7d8_2d8f()),
                performance("7d8 carregat", *variants_of_5d8_7d8_2d8f("7d8")),
            ],
        )
    )

    assert result.reply == (
        "Totes les variants superen «Rival» (2.055 punts): «Tot descarregat» 3.685 punts "
        "(+1.630) i «7d8 carregat» 3.500 punts (+1.445)."
    )


def test_several_variants_beat_the_reference_and_one_ties() -> None:
    result = make_engine().calculate(
        ParsedCastellQuery(
            intent="comparison",
            performances=[
                reference("Rival", ("5d8", Outcome.UNLOADED), ("7d8", Outcome.LOADED)),
                performance("Tot descarregat", *variants_of_5d8_7d8_2d8f()),
                performance("2d8f carregat", *variants_of_5d8_7d8_2d8f("td8f")),
                performance("Igual", ("7d8", Outcome.LOADED), ("5d8", Outcome.UNLOADED)),
            ],
        )
    )

    assert result.reply == (
        "Per superar «Rival» (2.290 punts) serveixen «Tot descarregat» 3.685 punts (+1.395) "
        "i «2d8f carregat» 3.480 punts (+1.190). «Igual» hi empata a 2.290 punts."
    )


def test_a_reference_against_a_single_variant_is_a_plain_comparison() -> None:
    result = make_engine().calculate(
        ParsedCastellQuery(
            intent="comparison",
            performances=[
                reference("Actuació base", *BASE_3610),
                performance("7d8 carregat", *variants_of_5d8_7d8_2d8f("7d8")),
            ],
        )
    )

    assert result.reply.endswith("Guanya Actuació base per 110 punts.")


def test_variants_with_the_same_name_are_told_apart_by_what_they_load() -> None:
    # Production 2026-10-03: the model named every variant «Nosaltres».
    result = make_engine().calculate(
        ParsedCastellQuery(
            intent="comparison",
            performances=[
                reference("Rival", *BASE_3610),
                performance("Nosaltres", *variants_of_5d8_7d8_2d8f()),
                performance("Nosaltres", *variants_of_5d8_7d8_2d8f("7d8")),
                performance("Nosaltres", *variants_of_5d8_7d8_2d8f("5d8", "td8f")),
            ],
        )
    )

    assert [item.label for item in result.performances] == [
        "Nosaltres: tot descarregat",
        "Rival",
        "Nosaltres: 7d8 carregat",
        "Nosaltres: 5d8 i td8f carregats",
    ]
    assert result.reply.startswith(
        "Per superar «Rival» (3.610 punts) només serveix «Nosaltres: tot descarregat»"
    )


def test_same_named_performances_with_different_castells_keep_a_distinct_label() -> None:
    result = make_engine().calculate(
        ParsedCastellQuery(
            intent="comparison",
            performances=[
                performance("Vella", ("4d10fm", Outcome.UNLOADED)),
                performance("Vella", ("3d10fm", Outcome.UNLOADED)),
            ],
        )
    )

    assert [item.label for item in result.performances] == [
        "Vella amb 4d10fm",
        "Vella amb 3d10fm",
    ]
