import json
from datetime import UTC, date, datetime

from backend.adapters.persistence.memory import InMemoryContentRepository
from backend.config import Settings
from backend.domain.models import CastellEvent
from backend.jobs import sync_agenda


class RecordingAgendaSource:
    source_id = "cccc"

    def __init__(self) -> None:
        self.calls: list[tuple[int, int]] = []

    def fetch_month(self, year: int, month: int) -> list[CastellEvent]:
        self.calls.append((year, month))
        local_date = date(year, month, 1)
        external_id = f"{year:04d}-{month:02d}"
        return [
            CastellEvent(
                id=external_id,
                source_id=self.source_id,
                external_id=external_id,
                title="Diada",
                local_date=local_date,
                starts_at=None,
                time_label="Matí",
                timezone="Europe/Madrid",
                venue="Plaça",
                municipality="Valls",
                participating_groups=["Colla A"],
                notes="",
                source_url="https://castellscat.cat/public/ca/agenda",
                source_order=0,
                attribution="Font: CCCC",
                revision="r1",
                updated_at=datetime.now(UTC),
            )
        ]


def test_default_range_uses_configured_month_window() -> None:
    settings = Settings(agenda_sync_months_back=1, agenda_sync_months_ahead=3)

    date_from, date_to = sync_agenda.default_range(settings, today=date(2026, 1, 15))

    assert date_from == date(2025, 12, 1)
    assert date_to == date(2026, 4, 1)


def test_manual_job_prefetches_complete_months_and_reports_result(
    monkeypatch, capsys
) -> None:
    source = RecordingAgendaSource()
    repository = InMemoryContentRepository()
    monkeypatch.setattr(sync_agenda, "build_agenda_source", lambda settings: source)
    monkeypatch.setattr(sync_agenda, "build_content_repository", lambda settings: repository)

    exit_code = sync_agenda.sync_once(
        Settings(agenda_source="cccc_html", cccc_agenda_authorized=True),
        date(2026, 7, 1),
        date(2026, 8, 1),
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert source.calls == [(2026, 7), (2026, 8)]
    assert payload["succeeded"] == ["2026-07", "2026-08"]
    assert repository.count_agenda(date(2026, 7, 1), date(2026, 8, 31), None, None) == 2
