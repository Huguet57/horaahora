from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest


REPOSITORY_ROOT = Path(__file__).parents[1]
SCRIPT = REPOSITORY_ROOT / "scripts" / "deploy-testflight.sh"


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


def test_default_build_number_is_the_current_unix_timestamp() -> None:
    before = int(time.time())

    result = subprocess.run(
        [
            "bash",
            "-c",
            f"source {SCRIPT!s}; generate_build_number",
        ],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    after = int(time.time())
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().isdigit()
    assert before <= int(result.stdout.strip()) <= after


def test_dry_run_pins_the_requested_ref_and_build_number() -> None:
    expected_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    result = run_script(
        "--dry-run",
        "--skip-tests",
        "--ref",
        "HEAD",
        "--build-number",
        "1774400000",
    )

    assert result.returncode == 0, result.stderr
    assert f"Source commit: {expected_commit}" in result.stdout
    assert "Build number: 1774400000" in result.stdout
    assert "CURRENT_PROJECT_VERSION=1774400000" in result.stdout
    assert "No upload was performed." in result.stdout


def test_invalid_build_number_is_rejected_before_building() -> None:
    result = run_script(
        "--dry-run",
        "--ref",
        "HEAD",
        "--build-number",
        "2026-07-25",
    )

    assert result.returncode == 2
    assert "must be a positive integer" in result.stderr


@pytest.mark.skipif(sys.platform != "darwin", reason="TestFlight deploy requires macOS")
def test_deploy_archives_uploads_and_removes_its_temporary_worktree(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_xcodebuild = fake_bin / "xcodebuild"
    fake_xcodebuild.write_text(
        """#!/usr/bin/env python3
import pathlib
import plistlib
import sys

arguments = sys.argv[1:]
if "archive" in arguments:
    archive_path = pathlib.Path(arguments[arguments.index("-archivePath") + 1])
    build_number = next(
        argument.split("=", 1)[1]
        for argument in arguments
        if argument.startswith("CURRENT_PROJECT_VERSION=")
    )
    archive_path.mkdir(parents=True)
    with (archive_path / "Info.plist").open("wb") as plist:
        plistlib.dump(
            {
                "ApplicationProperties": {
                    "CFBundleIdentifier": "com.ahuguet.castellsenvena",
                    "CFBundleShortVersionString": "1.0",
                    "CFBundleVersion": build_number,
                }
            },
            plist,
        )
elif "-exportArchive" in arguments:
    print("** EXPORT SUCCEEDED **")
else:
    raise SystemExit(f"Unexpected xcodebuild arguments: {arguments}")
"""
    )
    fake_xcodebuild.chmod(0o755)
    environment = os.environ | {"PATH": f"{fake_bin}:{os.environ['PATH']}"}
    worktrees_before = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout

    result = run_script(
        "--skip-tests",
        "--ref",
        "HEAD",
        "--build-number",
        "1774400000",
        env=environment,
    )

    worktrees_after = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert result.returncode == 0, result.stderr
    assert "Uploading com.ahuguet.castellsenvena 1.0 (1774400000)" in result.stdout
    assert "Upload accepted for TestFlight" in result.stdout
    assert worktrees_after == worktrees_before


def test_deploy_script_is_documented() -> None:
    readme = (REPOSITORY_ROOT / "README.md").read_text()

    assert re.search(r"scripts/deploy-testflight\.sh", readme)
    assert "make deploy-testflight" in readme
    assert "--build-number" in readme


def test_make_target_delegates_to_the_deploy_script() -> None:
    result = subprocess.run(
        [
            "make",
            "deploy-testflight",
            "ARGS=--dry-run --skip-tests --ref HEAD --build-number 1774400000",
        ],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "Build number: 1774400000" in result.stdout
    assert "No upload was performed." in result.stdout
