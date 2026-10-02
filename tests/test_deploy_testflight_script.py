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


def committed_version() -> str:
    version_file = subprocess.run(
        ["git", "show", "HEAD:Version.xcconfig"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return re.search(r"^MARKETING_VERSION = (\S+)$", version_file, re.MULTILINE).group(1)


def test_dry_run_takes_the_marketing_version_from_the_deployed_commit() -> None:
    version = committed_version()

    result = run_script(
        "--dry-run", "--skip-tests", "--ref", "HEAD", "--build-number", "1774400000"
    )

    assert result.returncode == 0, result.stderr
    assert f"Marketing version: {version}\n" in result.stdout
    assert f"MARKETING_VERSION={version}" in result.stdout


def test_dry_run_uses_the_frozen_python_environment() -> None:
    result = run_script(
        "--dry-run",
        "--ref",
        "HEAD",
        "--build-number",
        "1774400000",
    )

    assert result.returncode == 0, result.stderr
    assert "+ uv sync --frozen" in result.stdout
    assert "+ uv run --frozen --no-sync python -m pytest -q" in result.stdout


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


def fake_xcodebuild_environment(
    tmp_path: Path,
    api_base_url: str,
    bundle_identifier: str = "com.ahuguet.castellsenvena",
) -> dict[str, str]:
    """Put an xcodebuild on PATH that archives an app pointing at api_base_url."""
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_xcodebuild = fake_bin / "xcodebuild"
    fake_xcodebuild.write_text(
        "#!/usr/bin/env python3\n"
        f"API_BASE_URL = {api_base_url!r}\n"
        f"BUNDLE_IDENTIFIER = {bundle_identifier!r}\n"
        f"EXPORT_MARKER = {str(tmp_path / 'exported')!r}\n"
        """import pathlib
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
    marketing_version = next(
        argument.split("=", 1)[1]
        for argument in arguments
        if argument.startswith("MARKETING_VERSION=")
    )
    application = archive_path / "Products" / "Applications" / "HoraAHoraApp.app"
    application.mkdir(parents=True)
    with (archive_path / "Info.plist").open("wb") as plist:
        plistlib.dump(
            {
                "ApplicationProperties": {
                    "ApplicationPath": "Applications/HoraAHoraApp.app",
                    "CFBundleIdentifier": BUNDLE_IDENTIFIER,
                    "CFBundleShortVersionString": marketing_version,
                    "CFBundleVersion": build_number,
                }
            },
            plist,
        )
    with (application / "Info.plist").open("wb") as plist:
        plistlib.dump({"CastellsAPIBaseURL": API_BASE_URL}, plist)
elif "-exportArchive" in arguments:
    pathlib.Path(EXPORT_MARKER).touch()
    print("** EXPORT SUCCEEDED **")
else:
    raise SystemExit(f"Unexpected xcodebuild arguments: {arguments}")
"""
    )
    fake_xcodebuild.chmod(0o755)
    return os.environ | {"PATH": f"{fake_bin}:{os.environ['PATH']}"}


def run_fake_deploy(environment: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return run_script(
        "--skip-tests",
        "--ref",
        "HEAD",
        "--build-number",
        "1774400000",
        env=environment,
    )


@pytest.mark.skipif(sys.platform != "darwin", reason="TestFlight deploy requires macOS")
def test_deploy_archives_uploads_and_removes_its_temporary_worktree(tmp_path: Path) -> None:
    environment = fake_xcodebuild_environment(tmp_path, "https://castells-superapp-poc.vercel.app")
    worktrees_before = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout

    result = run_fake_deploy(environment)

    worktrees_after = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert result.returncode == 0, result.stderr
    assert (
        f"Uploading com.ahuguet.castellsenvena {committed_version()} (1774400000)" in result.stdout
    )
    assert "Upload accepted for TestFlight" in result.stdout
    assert (tmp_path / "exported").exists()
    assert worktrees_after == worktrees_before


@pytest.mark.skipif(sys.platform != "darwin", reason="TestFlight deploy requires macOS")
def test_deploy_refuses_an_archive_that_does_not_use_the_production_backend(
    tmp_path: Path,
) -> None:
    environment = fake_xcodebuild_environment(tmp_path, "http://127.0.0.1:8000")

    result = run_fake_deploy(environment)

    errors = [line for line in result.stderr.splitlines() if line.startswith("Error:")]
    assert result.returncode != 0
    assert errors == [
        "Error: the archived app talks to http://127.0.0.1:8000; "
        "TestFlight builds must use https://castells-superapp-poc.vercel.app."
    ]
    assert not (tmp_path / "exported").exists()


@pytest.mark.skipif(sys.platform != "darwin", reason="TestFlight deploy requires macOS")
def test_deploy_refuses_an_archive_of_the_internal_app(tmp_path: Path) -> None:
    environment = fake_xcodebuild_environment(
        tmp_path,
        "https://castells-superapp-poc.vercel.app",
        bundle_identifier="com.ahuguet.castellsenvena.internal",
    )

    result = run_fake_deploy(environment)

    errors = [line for line in result.stderr.splitlines() if line.startswith("Error:")]
    assert result.returncode != 0
    assert errors == [
        "Error: the archive is com.ahuguet.castellsenvena.internal; "
        "TestFlight only receives com.ahuguet.castellsenvena."
    ]
    assert not (tmp_path / "exported").exists()


@pytest.mark.parametrize("command", ["script", "make"])
def test_the_internal_app_is_never_deployed(command: str) -> None:
    environment = os.environ | {"CASTELLS_BUILD_PROFILE": "internal"}
    arguments = ["--dry-run", "--skip-tests", "--ref", "HEAD", "--build-number", "1774400000"]

    if command == "script":
        result = run_script(*arguments, env=environment)
    else:
        result = subprocess.run(
            ["make", "deploy-testflight", f"ARGS={' '.join(arguments)}"],
            cwd=REPOSITORY_ROOT,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )

    assert result.returncode != 0
    assert (
        "Error: TestFlight only receives the public app; CASTELLS_BUILD_PROFILE is internal."
        in result.stderr
    )
    assert "Source commit" not in result.stdout


def test_the_dry_run_archives_the_public_scheme() -> None:
    result = run_script(
        "--dry-run",
        "--skip-tests",
        "--ref",
        "HEAD",
        "--build-number",
        "1774400000",
        env=os.environ | {"CASTELLS_BUILD_PROFILE": "public"},
    )

    assert result.returncode == 0, result.stderr
    assert "-scheme HoraAHoraApp " in result.stdout


def test_deploy_script_is_documented() -> None:
    readme = (REPOSITORY_ROOT / "README.md").read_text()
    readiness = (REPOSITORY_ROOT / "docs" / "testflight-readiness.md").read_text()
    recommended_upload = readiness.split("## Pujada recomanada", 1)[1].split("\n## ", 1)[0]

    assert re.search(r"scripts/deploy-testflight\.sh", readme)
    assert "make deploy-testflight" in readme
    assert "--build-number" in readme
    assert "make deploy-testflight" in recommended_upload


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
