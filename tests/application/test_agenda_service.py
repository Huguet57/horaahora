from datetime import UTC, date, datetime

from backend.adapters.persistence.in_memory.agenda import InMemoryAgendaRepository
from backend.application.agenda import AgendaService
from backend.application.agenda_sync import AgendaSyncService
from backend.domain.content.models import CastellEvent


class RecordingAgendaSource:
    source_id = "cccc"

    def __init__(self) -> None:
        self.calls: list[tuple[int, int]] = []
        self.should_fail = False

    def fetch_month(self, year: int, month: int) -> list[CastellEvent]:
        self.calls.append((year, month))
        if self.should_fail:
            raise RuntimeError("source unavailable")
        day = date(year, month, 1)
        return [event(f"{year}-{month:02d}", day)]


def event(external_id: str, day: date) -> CastellEvent:
    return CastellEvent(
        id=external_id,
        source_id="cccc",
        external_id=external_id,
        title=f"Diada {external_id}",
        local_date=day,
        starts_at=None,
        time_label="Matí",
        timezone="Europe/Madrid",
        venue="Plaça",
        municipality="Valls",
        participating_groups=["Colla A"],
        notes="",
        source_url="https://castellscat.cat/ca/agenda",
        source_order=0,
        attribution="Font: Coordinadora de Colles Castelleres de Catalunya (CCCC)",
        revision="r1",
        updated_at=datetime.now(UTC),
    )


def test_fetches_each_month_once_and_uses_sync_cache_afterwards() -> None:
    source = RecordingAgendaSource()
    service = AgendaService(InMemoryAgendaRepository(), source, refresh_seconds=1_800)

    first = service.list(date(2026, 7, 1), date(2026, 8, 1), None, None, None, 50)
    second = service.list(date(2026, 7, 1), date(2026, 8, 1), None, None, None, 50)

    assert source.calls == [(2026, 7), (2026, 8)]
    assert [item.external_id for item in first.items] == ["2026-07", "2026-08"]
    assert first.from_cache is False
    assert second.from_cache is True


def test_refresh_failure_returns_previous_snapshot_without_deleting_it() -> None:
    source = RecordingAgendaSource()
    service = AgendaService(InMemoryAgendaRepository(), source, refresh_seconds=1_800)
    service.list(date(2026, 7, 1), date(2026, 7, 1), None, None, None, 50)
    source.should_fail = True

    page = service.list(
        date(2026, 7, 1),
        date(2026, 7, 1),
        None,
        None,
        None,
        50,
        force_refresh=True,
    )

    assert [item.external_id for item in page.items] == ["2026-07"]
    assert page.from_cache is True


def test_read_service_does_not_contact_source_when_on_demand_refresh_is_disabled() -> None:
    source = RecordingAgendaSource()
    repository = InMemoryAgendaRepository()
    AgendaSyncService(repository, source).sync(date(2026, 7, 1), date(2026, 7, 31))
    source.calls.clear()
    service = AgendaService(
        repository,
        source,
        refresh_seconds=1_800,
        refresh_on_request=False,
    )

    page = service.list(date(2026, 7, 1), date(2026, 7, 31), None, None, None, 50)

    assert source.calls == []
    assert [item.external_id for item in page.items] == ["2026-07"]
    assert page.from_cache is True
    assert page.source_status == "active"


def test_sync_service_replaces_successful_months_and_preserves_failed_months() -> None:
    source = RecordingAgendaSource()
    repository = InMemoryAgendaRepository()
    sync = AgendaSyncService(repository, source)
    first = sync.sync(date(2026, 7, 1), date(2026, 8, 31))
    source.should_fail = True

    second = sync.sync(date(2026, 7, 1), date(2026, 8, 31))

    assert first.succeeded == [(2026, 7), (2026, 8)]
    assert first.failed == []
    assert second.succeeded == []
    assert [failure.year_month for failure in second.failed] == [(2026, 7), (2026, 8)]
    assert repository.count_agenda(date(2026, 7, 1), date(2026, 8, 31), None, None) == 2
