from backend.adapters.ai.local import RegexQueryInterpreter
from backend.adapters.persistence.in_memory.agenda import InMemoryAgendaRepository
from backend.adapters.persistence.in_memory.hour_by_hour import InMemoryHourByHourRepository
from backend.adapters.rate_limit.memory import InMemoryRateLimiter
from backend.composition.container import ApplicationOverrides


def application_overrides(**values) -> ApplicationOverrides:
    defaults = {
        "interpreter": RegexQueryInterpreter(),
        "hour_by_hour_repository": InMemoryHourByHourRepository(),
        "agenda_repository": InMemoryAgendaRepository(),
        "rate_limiter": InMemoryRateLimiter(max_requests=100, window_seconds=60),
    }
    defaults.update(values)
    return ApplicationOverrides(**defaults)
