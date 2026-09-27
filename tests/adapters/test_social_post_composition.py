import pytest

from backend.adapters.content.combined_hour_by_hour import CombinedHourByHourSource
from backend.adapters.persistence.database import Database
from backend.adapters.persistence.in_memory.hour_by_hour import InMemoryHourByHourRepository
from backend.application.social_publication import SocialFeedPublisher, SocialHourByHourSource
from backend.composition.providers import (
    build_hour_by_hour_source,
    build_social_post_sync,
    build_x_watchlist,
)
from backend.config import Settings


def settings(**values) -> Settings:
    defaults = {
        "database_url": "sqlite://",
        "ai_provider": "openrouter",
        "ai_model": "google/gemini-3.7-flash",
        "ai_api_key": "key",
        "x_bearer_token": "token",
    }
    return Settings(**(defaults | values))


def build(configured: Settings):
    return build_social_post_sync(
        configured, Database("sqlite+pysqlite:///:memory:"), InMemoryHourByHourRepository()
    )


def test_x_posts_are_disabled_by_default() -> None:
    assert Settings().x_posts_mode == "disabled"
    assert build(Settings()) is None


@pytest.mark.parametrize(
    ("mode", "publishes"), [("shadow", False), ("feed", True), ("notify", False)]
)
def test_only_the_feed_mode_publishes_from_the_x_cron(mode: str, publishes: bool) -> None:
    sync = build(settings(x_posts_mode=mode))

    assert isinstance(sync.publisher, SocialFeedPublisher) is publishes


@pytest.mark.parametrize(
    ("mode", "included"),
    [("disabled", False), ("shadow", False), ("feed", False), ("notify", True)],
)
def test_only_the_notify_mode_hands_x_posts_to_the_notifying_ingestion(
    mode: str, included: bool
) -> None:
    source = build_hour_by_hour_source(
        settings(x_posts_mode=mode), Database("sqlite+pysqlite:///:memory:")
    )

    assert isinstance(source, CombinedHourByHourSource)
    assert any(isinstance(item, SocialHourByHourSource) for item in source.sources) is included


@pytest.mark.parametrize(
    ("values", "message"),
    [
        ({"x_posts_mode": "sometimes"}, "X_POSTS_MODE"),
        ({"x_posts_mode": "shadow", "x_bearer_token": ""}, "X_BEARER_TOKEN"),
        ({"x_posts_mode": "shadow", "ai_provider": "openai"}, "AI_PROVIDER=openrouter"),
        (
            {"x_posts_mode": "shadow", "x_watchlist_json": '{"accounts": []}'},
            "comptes ni etiquetes",
        ),
    ],
)
def test_enabled_x_posts_fail_fast_when_misconfigured(values: dict, message: str) -> None:
    with pytest.raises(RuntimeError, match=message):
        build(settings(**values))


def test_the_versioned_watchlist_is_used_by_default() -> None:
    watchlist = build_x_watchlist(settings())

    assert watchlist.hashtags == ("castells", "castellers")


def test_a_private_watchlist_replaces_the_versioned_one() -> None:
    watchlist = build_x_watchlist(settings(x_watchlist_json='{"accounts": ["JoanQuijorna"]}'))

    assert [account.username for account in watchlist.accounts] == ["JoanQuijorna"]
    assert watchlist.hashtags == ()


def test_x_settings_are_read_from_the_environment(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:password@localhost:5432/horaahora")
    monkeypatch.setenv("RATE_LIMIT_HASH_SECRET", "secret")
    monkeypatch.setenv("X_POSTS_MODE", " Shadow ")
    monkeypatch.setenv("X_BEARER_TOKEN", "token")
    monkeypatch.setenv("X_WATCHLIST_PATH", "/tmp/watchlist.json")
    monkeypatch.setenv("X_WATCHLIST_JSON", '{"hashtags": ["castells"]}')

    configured = Settings.from_env()

    assert configured.x_posts_mode == "shadow"
    assert configured.x_bearer_token == "token"
    assert configured.x_watchlist_path == "/tmp/watchlist.json"
    assert configured.x_watchlist_json == '{"hashtags": ["castells"]}'
