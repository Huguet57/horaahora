from fastapi.testclient import TestClient

from backend.adapters.persistence.in_memory.agenda import InMemoryAgendaRepository
from backend.adapters.persistence.in_memory.hour_by_hour import InMemoryHourByHourRepository
from backend.adapters.rate_limit.memory import InMemoryRateLimiter
from backend.app import create_app
from backend.composition.container import ApplicationOverrides
from backend.config import Settings
from tests.support.interpreters import CalculatorQueryInterpreterStub


def application_overrides(**values) -> ApplicationOverrides:
    defaults = {
        "interpreter": CalculatorQueryInterpreterStub(),
        "hour_by_hour_repository": InMemoryHourByHourRepository(),
        "agenda_repository": InMemoryAgendaRepository(),
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
        hour_by_hour_source_enabled=False,
        rate_limit_max_requests=100,
    )
    return TestClient(
        create_app(
            settings=resolved_settings,
            overrides=application_overrides(**override_values),
        )
    )
