from __future__ import annotations

import json
from pathlib import Path

from backend.domain.content.models import CastellerGroupDirectory


DEFAULT_DIRECTORY_PATH = (
    Path(__file__).parents[2] / "data" / "cccc_group_directory_2026_07_25.json"
)


def load_group_directory(path: Path = DEFAULT_DIRECTORY_PATH) -> CastellerGroupDirectory:
    payload = json.loads(path.read_text(encoding="utf-8"))
    groups = payload.get("groups")
    revision = payload.get("revision")
    official_url = payload.get("official_url")
    if not isinstance(groups, list) or not groups:
        raise ValueError("El directori de colles no pot estar buit")
    if not isinstance(revision, str) or not revision.strip():
        raise ValueError("El directori de colles necessita una revisió")
    if not isinstance(official_url, str) or not official_url.startswith("https://"):
        raise ValueError("El directori de colles necessita una URL oficial")

    cleaned = [value.strip() for value in groups if isinstance(value, str) and value.strip()]
    if len(cleaned) != len(groups):
        raise ValueError("El directori de colles conté noms invàlids")
    if len(set(cleaned)) != len(cleaned):
        raise ValueError("El directori de colles conté duplicats")

    return CastellerGroupDirectory(
        groups=sorted(cleaned, key=str.casefold),
        revision=revision,
        official_url=official_url,
    )
