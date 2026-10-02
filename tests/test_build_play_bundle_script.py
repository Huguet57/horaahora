from __future__ import annotations

import os
import re
import subprocess
import time
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).parents[1]
SCRIPT = REPOSITORY_ROOT / "scripts" / "build-play-bundle.sh"


def run_script(
    *arguments: str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPT), *arguments],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


def committed_version() -> str:
    version_file = subprocess.run(
        ["git", "show", "HEAD:Version.xcconfig"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return re.search(r"^MARKETING_VERSION = (\S+)$", version_file, re.MULTILINE).group(1)


def test_default_version_code_is_the_current_unix_timestamp() -> None:
    before = int(time.time())

    result = subprocess.run(
        ["bash", "-c", f"source {SCRIPT!s}; generate_version_code"],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    after = int(time.time())
    assert result.returncode == 0, result.stderr
    assert before <= int(result.stdout.strip()) <= after


def test_dry_run_builds_the_public_bundle_with_the_committed_version(tmp_path: Path) -> None:
    version = committed_version()

    result = run_script(
        "--dry-run",
        "--ref",
        "HEAD",
        "--version-code",
        "1790941076",
        "--output-dir",
        str(tmp_path),
    )

    assert result.returncode == 0, result.stderr
    assert f"Version: {version}\n" in result.stdout
    assert "Version code: 1790941076\n" in result.stdout
    assert "-Pcastells.buildProfile=public" in result.stdout
    assert "-Pcastells.versionCode=1790941076" in result.stdout
    assert ":app:bundleRelease" in result.stdout
    assert f"{tmp_path}/castells-en-vena-{version}-1790941076.aab" in result.stdout
    assert "No bundle was built." in result.stdout


@pytest.mark.parametrize("version_code", ["0", "2026-10-02", "2100000001"])
def test_invalid_version_codes_are_rejected_before_building(version_code: str) -> None:
    result = run_script("--dry-run", "--ref", "HEAD", "--version-code", version_code)

    assert result.returncode == 2
    assert "version code must be an integer from 1 to 2100000000" in result.stderr


@pytest.mark.parametrize("command", ["script", "make"])
def test_the_internal_app_never_gets_a_play_bundle(command: str) -> None:
    environment = os.environ | {"CASTELLS_BUILD_PROFILE": "internal"}
    arguments = ["--dry-run", "--ref", "HEAD", "--version-code", "1790941076"]

    if command == "script":
        result = run_script(*arguments, env=environment)
    else:
        result = subprocess.run(
            ["make", "play-bundle", f"ARGS={' '.join(arguments)}"],
            cwd=REPOSITORY_ROOT,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )

    assert result.returncode != 0
    assert (
        "Error: Google Play only receives the public app; CASTELLS_BUILD_PROFILE is internal."
        in result.stderr
    )


def test_make_target_delegates_to_the_script() -> None:
    result = subprocess.run(
        ["make", "play-bundle", "ARGS=--dry-run --ref HEAD --version-code 1790941076"],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "Version code: 1790941076" in result.stdout


def test_play_bundle_is_documented() -> None:
    readme = (REPOSITORY_ROOT / "README.md").read_text()

    assert "make play-bundle" in readme
    assert "Version.xcconfig" in readme
