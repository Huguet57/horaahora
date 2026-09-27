"""Exports the 2026 score table that the apps bundle for their «Puntuacions» tab.

The backend CSV stays the only source of the points. The export adds the name of each castell
in Catalan, which the apps read out to screen readers instead of the notation.

    uv run --frozen --no-sync python -m scripts.export_score_table
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

from backend.domain.calculator.table import DATA_FILE

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = (
    REPOSITORY_ROOT
    / "HoraAHoraApp/Packages/CastellsKit/Sources/FeatureScoreTable/Resources/score-table-2026.json",
)

NOTATION = re.compile(r"(?P<structure>P|\d)de(?P<height>\d+)(?P<features>[a-z]*)")
STRUCTURES = {
    "P": "Pilar",
    "2": "Torre",
    "3": "Tres",
    "4": "Quatre",
    "5": "Cinc",
    "7": "Set",
    "9": "Nou",
}
HEIGHTS = {"5": "cinc", "6": "sis", "7": "set", "8": "vuit", "9": "nou", "10": "deu"}
FEATURES = {
    "": "",
    "a": "amb l'agulla",
    "s": "aixecat per sota",
    "f": "amb folre",
    "fa": "amb folre i l'agulla",
    "fm": "amb folre i manilles",
    "fmp": "amb folre, manilles i puntals",
    "sf": "sense folre",
    "sm": "sense manilles",
}


def castell_name(notation: str) -> str:
    structure, height, features = _parts(notation)
    words = [STRUCTURES[structure], "de", HEIGHTS[height], FEATURES[features]]
    return " ".join(word for word in words if word)


def build_score_table(path: Path = DATA_FILE) -> dict[str, Any]:
    with path.open(newline="", encoding="utf-8") as file:
        castells = [
            {
                "notation": row["castell"],
                "name": castell_name(row["castell"]),
                "group": int(row["grup"]),
                "loaded": int(row["punts_carregat"]),
                "unloaded": int(row["punts_descarregat"]),
            }
            for row in csv.DictReader(file)
        ]
    return {"castells": castells}


def render(score_table: dict[str, Any]) -> str:
    """One castell per line, so that a change in the table reads well in a diff."""
    rows = ",\n".join(
        f"    {json.dumps(castell, ensure_ascii=False)}" for castell in score_table["castells"]
    )
    return f'{{\n  "castells": [\n{rows}\n  ]\n}}\n'


def main() -> None:
    content = render(build_score_table())
    for output in OUTPUTS:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
        print(output.relative_to(REPOSITORY_ROOT))


def _parts(notation: str) -> tuple[str, str, str]:
    match = NOTATION.fullmatch(notation)
    if match is None or match["features"] not in FEATURES or match["height"] not in HEIGHTS:
        raise ValueError(f"No es pot anomenar el castell {notation!r}")
    return match["structure"], match["height"], match["features"]


if __name__ == "__main__":
    main()
