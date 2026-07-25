from __future__ import annotations

import tomllib
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).parents[1]


def read(relative_path: str) -> str:
    return (REPOSITORY_ROOT / relative_path).read_text()


def test_pyproject_is_the_only_python_dependency_manifest() -> None:
    pyproject = tomllib.loads(read("pyproject.toml"))

    assert pyproject["project"]["requires-python"] == ">=3.12,<3.13"
    assert pyproject["dependency-groups"]["dev"] == ["pytest>=8,<10"]
    assert not (REPOSITORY_ROOT / "requirements.txt").exists()
    assert not (REPOSITORY_ROOT / "requirements-dev.txt").exists()


def test_python_runtime_and_resolved_dependencies_are_locked() -> None:
    lock = tomllib.loads(read("uv.lock"))

    assert read(".python-version").strip() == "3.12"
    assert lock["requires-python"] == "==3.12.*"
    assert any(package["name"] == "horaahora" for package in lock["package"])


def test_ci_uses_the_frozen_uv_environment() -> None:
    workflow = read(".github/workflows/check.yml")

    assert "astral-sh/setup-uv@v9.0.0" in workflow
    assert "uv lock --check" in workflow
    assert "uv sync --frozen" in workflow
    assert "uv run --frozen --no-sync python -m pytest -q" in workflow
    assert "pip install" not in workflow
    assert "requirements" not in workflow


def test_container_uses_only_locked_runtime_dependencies() -> None:
    dockerfile = read("Dockerfile")

    assert "COPY pyproject.toml uv.lock .python-version ./" in dockerfile
    assert "uv sync --frozen --no-dev --no-install-project" in dockerfile
    assert 'PATH="/app/.venv/bin:$PATH"' in dockerfile
    assert "requirements" not in dockerfile
