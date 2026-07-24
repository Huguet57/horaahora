from backend.domain.calculator.normalization import CastellNormalizer
from backend.domain.calculator.table import ScoreTable


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
