from __future__ import annotations

import tomllib
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).parents[1]


def read(relative_path: str) -> str:
    return (REPOSITORY_ROOT / relative_path).read_text()


def test_ruff_has_an_explicit_stable_policy() -> None:
    pyproject = tomllib.loads(read("pyproject.toml"))
    ruff = pyproject["tool"]["ruff"]

    assert ruff["line-length"] == 100
    assert ruff["lint"]["select"] == ["E4", "E7", "E9", "F", "I", "B", "UP"]
    assert set(ruff["lint"]["flake8-bugbear"]["extend-immutable-calls"]) == {
        "fastapi.Depends",
        "fastapi.Header",
        "fastapi.Query",
    }


def test_backend_ci_gates_format_lint_and_migration_drift() -> None:
    workflow = read(".github/workflows/check.yml")

    assert "astral-sh/ruff-action@v4.1.0" in workflow
    assert 'args: "check"' in workflow
    assert 'args: "format --check"' in workflow
    assert workflow.count('src: "."') == 2
    assert "alembic upgrade head" in workflow
    assert "alembic check" in workflow


def test_codeql_scans_python_and_path_filtered_swift() -> None:
    python_workflow = read(".github/workflows/codeql-python.yml")
    swift_workflow = read(".github/workflows/codeql-swift.yml")

    for workflow in (python_workflow, swift_workflow):
        assert "security-events: write" in workflow
        assert "github/codeql-action/init@v4.37.3" in workflow
        assert "github/codeql-action/analyze@v4.37.3" in workflow

    assert "languages: python" in python_workflow
    assert "languages: swift" in swift_workflow
    assert "build-mode: manual" in swift_workflow
    assert '"HoraAHoraApp/**"' in swift_workflow
    assert "CODE_SIGNING_ALLOWED=NO" in swift_workflow


def test_trivy_blocks_dependency_and_dockerfile_findings() -> None:
    workflow = read(".github/workflows/security.yml")
    dockerfile = read("Dockerfile")

    assert "aquasecurity/trivy-action@v0.36.0" in workflow
    assert 'version: "v0.72.0"' in workflow
    assert 'scan-type: "fs"' in workflow
    assert 'scanners: "vuln,misconfig"' in workflow
    assert 'severity: "HIGH,CRITICAL"' in workflow
    assert 'exit-code: "1"' in workflow
    assert "USER app" in dockerfile
