from pathlib import Path

import pytest

from backend.adapters.ai.openrouter import OpenRouterChatModel
from backend.composition.providers import build_chat_model
from backend.config import Settings

REPOSITORY_ROOT = Path(__file__).parents[2]


@pytest.mark.parametrize("provider", ["", "local"])
def test_calculator_rejects_missing_or_removed_ai_providers(provider: str) -> None:
    settings = Settings(
        ai_provider=provider,
        ai_model="model",
        ai_api_key="key",
    )

    with pytest.raises(RuntimeError, match="AI_PROVIDER ha de ser openai, anthropic o openrouter"):
        build_chat_model(settings)


def test_calculator_builds_openrouter_with_gemini_defaults() -> None:
    settings = Settings(
        ai_provider="openrouter",
        ai_model="google/gemini-3.7-flash",
        ai_api_key="key",
    )

    model = build_chat_model(settings)

    assert isinstance(model, OpenRouterChatModel)
    assert model.model == "google/gemini-3.7-flash"
    assert model.base_url == "https://openrouter.ai/api"
    assert model.reasoning_effort == "low"


def test_local_compose_requires_an_explicit_model_provider_and_credentials() -> None:
    compose = (REPOSITORY_ROOT / "compose.yaml").read_text()
    example_environment = (REPOSITORY_ROOT / ".env.example").read_text()

    assert "${AI_PROVIDER:?" in compose
    assert "${AI_MODEL:?" in compose
    assert "${AI_API_KEY:?" in compose
    assert "AI_PROVIDER=openrouter" in example_environment
    assert "AI_MODEL=google/gemini-3.7-flash" in example_environment
    assert "AI_BASE_URL=https://openrouter.ai/api" in example_environment
    assert "AI_PROVIDER=local" not in example_environment
