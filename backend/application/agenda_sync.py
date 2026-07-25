from dataclasses import dataclass
from datetime import date

from backend.application.agenda import months_between
from backend.domain.content.ports import AgendaRepository, AgendaSource


@dataclass(frozen=True, slots=True)
class AgendaSyncFailure:
    year_month: tuple[int, int]
    error: str


@dataclass(frozen=True, slots=True)
class AgendaSyncResult:
    succeeded: list[tuple[int, int]]
    failed: list[AgendaSyncFailure]


class AgendaSyncService:
    def __init__(self, repository: AgendaRepository, source: AgendaSource) -> None:
        self.repository = repository
        self.source = source

    def sync(self, date_from: date, date_to: date) -> AgendaSyncResult:
        if date_to < date_from:
            raise ValueError("La data final no pot ser anterior a la inicial")

        succeeded: list[tuple[int, int]] = []
        failed: list[AgendaSyncFailure] = []
        for year, month in months_between(date_from, date_to):
            try:
                items = self.source.fetch_month(year, month)
                self.repository.replace_agenda_month(self.source.source_id, year, month, items)
                succeeded.append((year, month))
            except Exception as error:
                failed.append(AgendaSyncFailure((year, month), str(error)))
        return AgendaSyncResult(succeeded=succeeded, failed=failed)
