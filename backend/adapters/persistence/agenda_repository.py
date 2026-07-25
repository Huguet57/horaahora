from __future__ import annotations

import unicodedata
from datetime import UTC, date, datetime

from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from backend.adapters.persistence.database import Database
from backend.adapters.persistence.models import AgendaEventRecord, AgendaSyncRecord
from backend.adapters.persistence.repository_support import (
    database_datetime,
    domain_datetime,
    resolve_engine,
)
from backend.domain.content.models import CastellEvent


class SQLAlchemyAgendaRepository:
    def __init__(self, database: Database | Engine | str) -> None:
        self.database, self.engine = resolve_engine(database)

    def replace_agenda_month(
        self, source_id: str, year: int, month: int, items: list[CastellEvent]
    ) -> None:
        with Session(self.engine) as session:
            current = session.scalars(
                select(AgendaEventRecord).where(
                    AgendaEventRecord.source_id == source_id,
                    AgendaEventRecord.local_date >= date(year, month, 1),
                    AgendaEventRecord.local_date < _next_month(year, month),
                )
            ).all()
            by_external_id = {record.external_id: record for record in current}
            incoming_ids = {item.external_id for item in items}
            for external_id, record in by_external_id.items():
                if external_id not in incoming_ids:
                    session.delete(record)

            for item in items:
                record = by_external_id.get(item.external_id)
                if record is None:
                    record = AgendaEventRecord(
                        id=item.id,
                        source_id=item.source_id,
                        external_id=item.external_id,
                        updated_at=database_datetime(item.updated_at),
                    )
                    session.add(record)
                revision_changed = record.revision != item.revision
                record.title = item.title
                record.local_date = item.local_date
                record.starts_at = database_datetime(item.starts_at) if item.starts_at else None
                record.time_label = item.time_label
                record.timezone = item.timezone
                record.venue = item.venue
                record.municipality = item.municipality
                record.participating_groups = item.participating_groups
                record.notes = item.notes
                record.source_url = item.source_url
                record.source_order = item.source_order
                record.attribution = item.attribution
                record.revision = item.revision
                if revision_changed:
                    record.updated_at = database_datetime(item.updated_at)

            sync_id = f"{source_id}:{year:04d}-{month:02d}"
            sync = session.get(AgendaSyncRecord, sync_id)
            if sync is None:
                session.add(
                    AgendaSyncRecord(
                        id=sync_id,
                        source_id=source_id,
                        year=year,
                        month=month,
                        synced_at=datetime.now(UTC),
                    )
                )
            else:
                sync.synced_at = datetime.now(UTC)
            session.commit()

    def list_agenda(
        self,
        date_from: date,
        date_to: date,
        group: str | None,
        municipality: str | None,
        offset: int,
        limit: int,
    ) -> list[CastellEvent]:
        if group is None and municipality is None:
            records = self._ordered_records(date_from, date_to, offset, limit)
        else:
            records = self._filtered_records(date_from, date_to, group, municipality)[
                offset : offset + limit
            ]
        return [_to_domain(record) for record in records]

    def count_agenda(
        self,
        date_from: date,
        date_to: date,
        group: str | None,
        municipality: str | None,
    ) -> int:
        if group is not None or municipality is not None:
            return len(self._filtered_records(date_from, date_to, group, municipality))
        with Session(self.engine) as session:
            return int(
                session.scalar(
                    select(func.count())
                    .select_from(AgendaEventRecord)
                    .where(
                        AgendaEventRecord.local_date >= date_from,
                        AgendaEventRecord.local_date <= date_to,
                    )
                )
                or 0
            )

    def latest_agenda_month_sync(self, source_id: str, year: int, month: int):
        sync_id = f"{source_id}:{year:04d}-{month:02d}"
        with Session(self.engine) as session:
            value = session.scalar(
                select(AgendaSyncRecord.synced_at).where(AgendaSyncRecord.id == sync_id)
            )
            return domain_datetime(value) if value else None

    def _ordered_records(
        self, date_from: date, date_to: date, offset: int = 0, limit: int | None = None
    ) -> list[AgendaEventRecord]:
        query = (
            select(AgendaEventRecord)
            .where(
                AgendaEventRecord.local_date >= date_from,
                AgendaEventRecord.local_date <= date_to,
            )
            .order_by(
                AgendaEventRecord.local_date.asc(),
                AgendaEventRecord.source_order.asc(),
                AgendaEventRecord.title.asc(),
            )
            .offset(offset)
        )
        if limit is not None:
            query = query.limit(limit)
        with Session(self.engine) as session:
            return list(session.scalars(query).all())

    def _filtered_records(
        self, date_from: date, date_to: date, group: str | None, municipality: str | None
    ) -> list[AgendaEventRecord]:
        records = self._ordered_records(date_from, date_to)
        group_key = _search_key(group) if group else None
        municipality_key = _search_key(municipality) if municipality else None
        return [
            record
            for record in records
            if (
                group_key is None
                or any(
                    _search_key(value) == group_key for value in record.participating_groups or []
                )
            )
            and (municipality_key is None or _search_key(record.municipality) == municipality_key)
        ]


def _to_domain(record: AgendaEventRecord) -> CastellEvent:
    return CastellEvent(
        id=record.id,
        source_id=record.source_id,
        external_id=record.external_id,
        title=record.title,
        local_date=record.local_date,
        starts_at=domain_datetime(record.starts_at) if record.starts_at else None,
        time_label=record.time_label,
        timezone=record.timezone,
        venue=record.venue,
        municipality=record.municipality,
        participating_groups=list(record.participating_groups or []),
        notes=record.notes,
        source_url=record.source_url,
        source_order=record.source_order,
        attribution=record.attribution,
        revision=record.revision,
        updated_at=domain_datetime(record.updated_at),
    )


def _next_month(year: int, month: int) -> date:
    return date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)


def _search_key(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    without_accents = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    return " ".join(without_accents.split())
