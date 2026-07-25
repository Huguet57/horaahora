from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).parents[1]
DETECT_IOS_CHANGES = REPOSITORY_ROOT / ".github/scripts/detect-ios-changes.sh"
MAIN_RULESET = REPOSITORY_ROOT / ".github/rulesets/main.json"


def git(repository: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def commit_file(repository: Path, relative_path: str, content: str) -> str:
    path = repository / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    git(repository, "add", relative_path)
    git(repository, "commit", "-m", f"Update {relative_path}")
    return git(repository, "rev-parse", "HEAD")


def detect_ios_changes(
    repository: Path,
    output_file: Path,
    base: str,
    head: str,
) -> str:
    environment = os.environ | {"GITHUB_OUTPUT": str(output_file)}
    subprocess.run(
        ["bash", str(DETECT_IOS_CHANGES), base, head],
        cwd=repository,
        env=environment,
        check=True,
    )
    return output_file.read_text().strip()


def initialized_repository(tmp_path: Path) -> tuple[Path, str]:
    repository = tmp_path / "repository"
    repository.mkdir()
    git(repository, "init")
    git(repository, "config", "user.name", "Infrastructure Tests")
    git(repository, "config", "user.email", "infra-tests@example.com")
    initial_commit = commit_file(repository, "README.md", "initial\n")
    return repository, initial_commit


def test_ios_change_detector_skips_unrelated_changes(tmp_path: Path) -> None:
    repository, base = initialized_repository(tmp_path)
    head = commit_file(repository, "docs/architecture.md", "documentation\n")

    result = detect_ios_changes(repository, tmp_path / "output", base, head)

    assert result == "ios=false"


def test_ios_change_detector_selects_app_and_workflow_changes(tmp_path: Path) -> None:
    repository, base = initialized_repository(tmp_path)
    app_head = commit_file(repository, "HoraAHoraApp/App.swift", "app\n")

    app_result = detect_ios_changes(repository, tmp_path / "app-output", base, app_head)

    assert app_result == "ios=true"

    workflow_head = commit_file(
        repository,
        ".github/workflows/ios.yml",
        "name: iOS\n",
    )
    workflow_result = detect_ios_changes(
        repository,
        tmp_path / "workflow-output",
        app_head,
        workflow_head,
    )

    assert workflow_result == "ios=true"


def test_ios_change_detector_fails_open_when_the_base_is_unavailable(tmp_path: Path) -> None:
    repository, head = initialized_repository(tmp_path)

    result = detect_ios_changes(repository, tmp_path / "output", "", head)

    assert result == "ios=true"


def test_main_ruleset_requires_pull_requests_and_stable_ci_checks() -> None:
    ruleset = json.loads(MAIN_RULESET.read_text())
    rules = {rule["type"]: rule for rule in ruleset["rules"]}

    assert ruleset["enforcement"] == "active"
    assert ruleset["conditions"]["ref_name"] == {
        "include": ["~DEFAULT_BRANCH"],
        "exclude": [],
    }
    assert ruleset["bypass_actors"] == []
    assert {"deletion", "non_fast_forward", "pull_request"} <= rules.keys()

    pull_requests = rules["pull_request"]["parameters"]
    assert pull_requests["required_review_thread_resolution"] is True

    status_checks = rules["required_status_checks"]["parameters"]
    assert status_checks["strict_required_status_checks_policy"] is True
    assert {
        check["context"] for check in status_checks["required_status_checks"]
    } == {"Backend required", "iOS required"}


def test_required_checks_have_stable_names_and_ios_runs_for_every_pull_request() -> None:
    backend_workflow = (REPOSITORY_ROOT / ".github/workflows/check.yml").read_text()
    ios_workflow = (REPOSITORY_ROOT / ".github/workflows/ios.yml").read_text()
    pull_request = re.search(
        r"(?m)^  pull_request:\s*$\n(?P<body>(?: {4}.*\n)*)",
        ios_workflow,
    )

    assert "name: Backend required" in backend_workflow
    assert "name: iOS required" in ios_workflow
    assert "if: always()" in ios_workflow
    assert pull_request is not None
    assert "paths:" not in pull_request.group("body")
