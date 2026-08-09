from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

DATA_DIRECTORY = Path(__file__).resolve().parents[3] / "data" / "contest"
SnapshotFilename = Literal["previous_results.json", "rules.json"]


def load_contest_snapshot(filename: SnapshotFilename) -> dict[str, Any]:
    return json.loads((DATA_DIRECTORY / filename).read_text(encoding="utf-8"))
