from backend.domain.models import Outcome, ParsedCastell, ParsedCastellQuery, ParsedPerformance
from backend.domain.scoring import CastellNormalizer, ScoringEngine, ScoreTable


def make_engine() -> ScoringEngine:
    return ScoringEngine(ScoreTable.default())


def performance(label: str, *castells: tuple[str, Outcome]) -> ParsedPerformance:
    return ParsedPerformance(
        label=label,
        castells=[ParsedCastell(notation=notation, outcome=outcome) for notation, outcome in castells],
    )


def test_normalizes_common_notation_and_explicit_net_alias() -> None:
    normalizer = CastellNormalizer(ScoreTable.default())

    assert normalizer.normalize("5d9f") == "5de9f"
    assert normalizer.normalize("pd8fm") == "Pde8fm"
    assert normalizer.normalize("4d9net") == "4de9sf"
    assert normalizer.normalize("4de9af") == "4de9fa"


def test_normalizes_conventional_omissions_but_preserves_explicit_rare_variants() -> None:
    normalizer = CastellNormalizer(ScoreTable.default())

    assert normalizer.normalize("4d10") == "4de10fm"
    assert normalizer.normalize("3d10") == "3de10fm"
    assert normalizer.normalize("2d9") == "2de9fm"
    assert normalizer.normalize("pd8") == "Pde8fm"
    assert normalizer.normalize("2d8") == "2de8f"
    assert normalizer.normalize("pd7") == "Pde7f"
    assert normalizer.normalize("4d10f") == "4de10sm"
    assert normalizer.normalize("4d10sm") == "4de10sm"


def test_normalizes_pilar_and_agulla_suffixes_for_every_scored_structure() -> None:
    table = ScoreTable.default()
    normalizer = CastellNormalizer(table)

    for canonical in table.scores:
        lower = canonical.lower()
        if lower.endswith("fa"):
            stem = lower[:-2]
            for suffix in ("fp", "af", "pf"):
                assert normalizer.normalize(stem + suffix) == canonical
        elif lower.endswith("a"):
            assert normalizer.normalize(lower[:-1] + "p") == canonical


def test_normalizes_torre_net_and_common_separator_aliases() -> None:
    normalizer = CastellNormalizer(ScoreTable.default())

    assert normalizer.normalize("td8sf") == "2de8sf"
    assert normalizer.normalize("t8n") == "2de8sf"
    assert normalizer.normalize("4/9fp") == "4de9fa"
    assert normalizer.normalize("3x9pf") == "3de9fa"
    assert normalizer.normalize("4×8p") == "4de8a"


def test_common_notation_families_cover_every_scored_castell() -> None:
    table = ScoreTable.default()
    normalizer = CastellNormalizer(table)

    for canonical in table.scores:
        lower = canonical.lower()
        if lower.startswith("pde"):
            tail = lower[3:]
            assert normalizer.normalize("pd" + tail) == canonical
            assert normalizer.normalize("p" + tail) == canonical
        else:
            width, height_and_suffix = lower.split("de", maxsplit=1)
            for separator in ("d", "/", "x", "×"):
                assert normalizer.normalize(width + separator + height_and_suffix) == canonical

            if width == "2":
                assert normalizer.normalize("td" + height_and_suffix) == canonical
                assert normalizer.normalize("t" + height_and_suffix) == canonical

        if lower.endswith("sf"):
            stem = lower[:-2]
            assert normalizer.normalize(stem + "net") == canonical
            assert normalizer.normalize(stem + "n") == canonical


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
    assert next(item for item in castells if item.canonical == "4de9f").reason == "duplicate_structure"


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
        "No acabo d’identificar «10d10» ni «torrevolada». "
        "A quins castells et refereixes?"
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
