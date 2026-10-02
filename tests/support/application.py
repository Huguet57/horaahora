from fastapi.testclient import TestClient

from backend.adapters.rate_limit.memory import InMemoryRateLimiter
from backend.app import create_app
from backend.composition.container import ApplicationOverrides
from backend.config import Settings
from tests.support.interpreters import CalculatorChatModelStub


def application_overrides(**values) -> ApplicationOverrides:
    defaults = {
        "chat_model": CalculatorChatModelStub(),
        "rate_limiter": InMemoryRateLimiter(max_requests=100, window_seconds=60),
    }
    defaults.update(values)
    return ApplicationOverrides(**defaults)


def make_test_client(
    *,
    settings: Settings | None = None,
    **override_values,
) -> TestClient:
    resolved_settings = settings or Settings(
        database_url="sqlite://",
        rate_limit_max_requests=100,
    )
    return TestClient(
        create_app(
            settings=resolved_settings,
            overrides=application_overrides(**override_values),
        )
    )
