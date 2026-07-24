from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from backend.adapters.persistence.database import Database
from backend.adapters.persistence.models import HourByHourRecord
from backend.adapters.persistence.repository_support import (
    database_datetime,
    domain_datetime,
    resolve_engine,
)
from backend.domain.content.models import HourByHourItem


class SQLAlchemyHourByHourRepository:
    def __init__(self, database: Database | Engine | str) -> None:
        self.database, self.engine = resolve_engine(database)

    def upsert_hour_by_hour(self, items: list[HourByHourItem]) -> None:
        with Session(self.engine) as session:
            for item in items:
                record = session.scalar(
                    select(HourByHourRecord).where(
                        HourByHourRecord.source_id == item.source_id,
                        HourByHourRecord.external_id == item.external_id,
                    )
                )
                if record is None:
                    record = HourByHourRecord(
                        id=item.id,
                        source_id=item.source_id,
                        external_id=item.external_id,
                        created_at=database_datetime(item.created_at),
                    )
                    session.add(record)
                update_hour_by_hour_record(record, item)
            session.commit()

    def list_hour_by_hour(self, offset: int, limit: int) -> list[HourByHourItem]:
        with Session(self.engine) as session:
            records = session.scalars(
                select(HourByHourRecord)
                .order_by(
                    HourByHourRecord.published_at.desc().nullslast(),
                    HourByHourRecord.source_order.asc(),
                    HourByHourRecord.updated_at.desc(),
                )
                .offset(offset)
                .limit(limit)
            ).all()
            return [to_domain(record) for record in records]

    def count_hour_by_hour(self) -> int:
        with Session(self.engine) as session:
            return int(session.scalar(select(func.count()).select_from(HourByHourRecord)) or 0)

    def latest_hour_by_hour_update(self):
        with Session(self.engine) as session:
            return session.scalar(select(func.max(HourByHourRecord.updated_at)))


def update_hour_by_hour_record(record: HourByHourRecord, item: HourByHourItem) -> None:
    record.title = item.title
    record.display_title = item.display_title
    record.summary = item.summary
    record.published_at = database_datetime(item.published_at) if item.published_at else None
    record.source_order = item.source_order
    record.article_url = item.article_url
    record.action_url = item.action_url or ""
    record.attribution = item.attribution
    record.updated_at = database_datetime(item.updated_at)


def to_domain(record: HourByHourRecord) -> HourByHourItem:
    return HourByHourItem(
        id=record.id,
        source_id=record.source_id,
        external_id=record.external_id,
        title=record.title,
        display_title=record.display_title,
        summary=record.summary,
        published_at=domain_datetime(record.published_at) if record.published_at else None,
        source_order=record.source_order,
        article_url=record.article_url,
        action_url=record.action_url or None,
        attribution=record.attribution,
        created_at=domain_datetime(record.created_at),
        updated_at=domain_datetime(record.updated_at),
    )
