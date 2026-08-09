from pathlib import Path

import pytest

from backend.composition.providers import build_interpreter
from backend.config import Settings

REPOSITORY_ROOT = Path(__file__).parents[2]


@pytest.mark.parametrize("provider", ["", "local"])
def test_calculator_rejects_missing_or_removed_ai_providers(provider: str) -> None:
    settings = Settings(
        ai_provider=provider,
        ai_model="model",
        ai_api_key="key",
    )

    with pytest.raises(RuntimeError, match="AI_PROVIDER ha de ser openai o anthropic"):
        build_interpreter(settings)


def test_local_compose_requires_an_explicit_model_provider_and_credentials() -> None:
    compose = (REPOSITORY_ROOT / "compose.yaml").read_text()
    example_environment = (REPOSITORY_ROOT / ".env.example").read_text()

    assert "${AI_PROVIDER:?" in compose
    assert "${AI_MODEL:?" in compose
    assert "${AI_API_KEY:?" in compose
    assert "AI_PROVIDER=openai" in example_environment
    assert "AI_PROVIDER=local" not in example_environment
