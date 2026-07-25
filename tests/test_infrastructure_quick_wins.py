from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
DIGEST = r"sha256:[0-9a-f]{64}"


def test_runtime_images_are_pinned_by_digest() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text()
    compose = (ROOT / "compose.yaml").read_text()
    workflow = (ROOT / ".github/workflows/check.yml").read_text()

    assert re.search(rf"FROM ghcr\.io/astral-sh/uv:0\.11\.32@{DIGEST}", dockerfile)
    assert re.search(rf"FROM python:3\.12-slim@{DIGEST}", dockerfile)
    assert re.search(rf"image: postgres:17-alpine@{DIGEST}", compose)
    assert re.search(rf"image: postgres:17-alpine@{DIGEST}", workflow)


def test_xcode_personal_state_is_ignored_and_not_versioned() -> None:
    gitignore = (ROOT / ".gitignore").read_text().splitlines()

    assert "xcuserdata/" in gitignore
    assert "*.xcuserstate" in gitignore
    assert not list((ROOT / "HoraAHoraApp").glob("**/xcuserdata/**/*"))
