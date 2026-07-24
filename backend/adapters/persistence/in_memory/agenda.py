from datetime import UTC, date, datetime
from threading import Lock
import unicodedata

from backend.domain.content.models import CastellEvent


class InMemoryAgendaRepository:
    def __init__(self) -> None:
        self._agenda: dict[tuple[str, str], CastellEvent] = {}
        self._syncs: dict[tuple[str, int, int], datetime] = {}
        self._lock = Lock()

    def replace_agenda_month(
        self, source_id: str, year: int, month: int, items: list[CastellEvent]
    ) -> None:
        with self._lock:
            incoming = {(item.source_id, item.external_id): item for item in items}
            for key, item in list(self._agenda.items()):
                if (
                    item.source_id == source_id
                    and item.local_date.year == year
                    and item.local_date.month == month
                    and key not in incoming
                ):
                    del self._agenda[key]
            self._agenda.update(incoming)
            self._syncs[(source_id, year, month)] = datetime.now(UTC)

    def list_agenda(
        self,
        date_from: date,
        date_to: date,
        group: str | None,
        municipality: str | None,
        offset: int,
        limit: int,
    ) -> list[CastellEvent]:
        with self._lock:
            return self._filtered(date_from, date_to, group, municipality)[
                offset : offset + limit
            ]

    def count_agenda(
        self,
        date_from: date,
        date_to: date,
        group: str | None,
        municipality: str | None,
    ) -> int:
        with self._lock:
            return len(self._filtered(date_from, date_to, group, municipality))

    def latest_agenda_month_sync(self, source_id: str, year: int, month: int):
        with self._lock:
            return self._syncs.get((source_id, year, month))

    def _filtered(
        self, date_from: date, date_to: date, group: str | None, municipality: str | None
    ) -> list[CastellEvent]:
        group_key = _search_key(group) if group else None
        municipality_key = _search_key(municipality) if municipality else None
        values = [
            item
            for item in self._agenda.values()
            if date_from <= item.local_date <= date_to
            and (
                group_key is None
                or any(_search_key(value) == group_key for value in item.participating_groups)
            )
            and (
                municipality_key is None
                or _search_key(item.municipality) == municipality_key
            )
        ]
        return sorted(values, key=lambda item: (item.local_date, item.source_order, item.title))


def _search_key(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    without_accents = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    return " ".join(without_accents.split())
