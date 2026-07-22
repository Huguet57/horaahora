from __future__ import annotations

from datetime import UTC, date, datetime
import unicodedata

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    select,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from backend.adapters.persistence.database import Database
from backend.domain.models import CastellEvent, HourByHourItem


class Base(DeclarativeBase):
    pass


class HourByHourRecord(Base):
    __tablename__ = "hour_by_hour_items"
    __table_args__ = (UniqueConstraint("source_id", "external_id", name="uq_hour_by_hour_source_external"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_id: Mapped[str] = mapped_column(String(100), index=True)
    external_id: Mapped[str] = mapped_column(String(128))
    title: Mapped[str] = mapped_column(Text)
    display_title: Mapped[str] = mapped_column(Text)
    summary: Mapped[str] = mapped_column(Text, default="")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    source_order: Mapped[int] = mapped_column(Integer)
    article_url: Mapped[str] = mapped_column(Text)
    action_url: Mapped[str] = mapped_column(Text)
    attribution: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class AgendaEventRecord(Base):
    __tablename__ = "agenda_events"
    __table_args__ = (UniqueConstraint("source_id", "external_id", name="uq_agenda_source_external"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_id: Mapped[str] = mapped_column(String(100), index=True)
    external_id: Mapped[str] = mapped_column(String(128))
    title: Mapped[str] = mapped_column(Text)
    local_date: Mapped[date] = mapped_column(Date, index=True)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    time_label: Mapped[str] = mapped_column(String(50))
    timezone: Mapped[str] = mapped_column(String(100))
    venue: Mapped[str] = mapped_column(Text)
    municipality: Mapped[str] = mapped_column(String(200), index=True)
    participating_groups: Mapped[list[str]] = mapped_column(JSON)
    notes: Mapped[str] = mapped_column(Text)
    source_url: Mapped[str] = mapped_column(Text)
    source_order: Mapped[int] = mapped_column(Integer)
    attribution: Mapped[str] = mapped_column(String(250))
    revision: Mapped[str] = mapped_column(String(128))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class AgendaSyncRecord(Base):
    __tablename__ = "agenda_syncs"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    source_id: Mapped[str] = mapped_column(String(100), index=True)
    year: Mapped[int] = mapped_column(Integer)
    month: Mapped[int] = mapped_column(Integer)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class PushSubscriptionRecord(Base):
    __tablename__ = "push_subscriptions"
    __table_args__ = (
        UniqueConstraint(
            "installation_id", "environment", "topic", name="uq_push_installation_environment_topic"
        ),
        UniqueConstraint(
            "device_token", "environment", "topic", name="uq_push_token_environment_topic"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    installation_id: Mapped[str] = mapped_column(String(128), index=True)
    device_token: Mapped[str] = mapped_column(Text)
    environment: Mapped[str] = mapped_column(String(20), index=True)
    topic: Mapped[str] = mapped_column(String(200))
    hour_by_hour_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    app_version: Mapped[str] = mapped_column(String(64), default="")
    locale: Mapped[str] = mapped_column(String(16), default="ca-ES")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    invalidated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class NotificationSyncStateRecord(Base):
    __tablename__ = "notification_sync_state"

    source_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    initialized_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    last_content_hash: Mapped[str] = mapped_column(String(64))


class NotificationOutboxRecord(Base):
    __tablename__ = "notification_outbox"
    __table_args__ = (
        UniqueConstraint(
            "event_type", "source_id", "external_id", name="uq_notification_outbox_event"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(50), index=True)
    source_id: Mapped[str] = mapped_column(String(100), index=True)
    external_id: Mapped[str] = mapped_column(String(128))
    title: Mapped[str] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text, default="")
    collapse_id: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class NotificationDeliveryRecord(Base):
    __tablename__ = "notification_deliveries"
    __table_args__ = (
        UniqueConstraint("outbox_id", "subscription_id", name="uq_notification_delivery_target"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    outbox_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("notification_outbox.id", ondelete="CASCADE"), index=True
    )
    subscription_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("push_subscriptions.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(String(20), index=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class RateLimitBucketRecord(Base):
    __tablename__ = "rate_limit_buckets"

    identifier_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    window_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    request_count: Mapped[int] = mapped_column(Integer)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class SQLAlchemyContentRepository:
    def __init__(self, database: Database | Engine | str) -> None:
        if isinstance(database, Database):
            self.database = database
        elif isinstance(database, Engine):
            self.database = None
            self.engine = database
            return
        else:
            self.database = Database(database)
        self.engine = self.database.engine
        if self.engine.dialect.name == "sqlite":
            # SQLite is retained solely as a lightweight unit-test adapter.
            Base.metadata.create_all(self.engine)

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
                        created_at=self._database_datetime(item.created_at),
                    )
                    session.add(record)
                record.title = item.title
                record.display_title = item.display_title
                record.summary = item.summary
                record.published_at = (
                    self._database_datetime(item.published_at) if item.published_at else None
                )
                record.source_order = item.source_order
                record.article_url = item.article_url
                record.action_url = item.action_url or ""
                record.attribution = item.attribution
                record.updated_at = self._database_datetime(item.updated_at)
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
            return [self._to_domain(record) for record in records]

    def count_hour_by_hour(self) -> int:
        with Session(self.engine) as session:
            return int(session.scalar(select(func.count()).select_from(HourByHourRecord)) or 0)

    def latest_hour_by_hour_update(self) -> datetime | None:
        with Session(self.engine) as session:
            return session.scalar(select(func.max(HourByHourRecord.updated_at)))

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
                        updated_at=self._database_datetime(item.updated_at),
                    )
                    session.add(record)
                revision_changed = record.revision != item.revision
                record.title = item.title
                record.local_date = item.local_date
                record.starts_at = (
                    self._database_datetime(item.starts_at) if item.starts_at else None
                )
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
                    record.updated_at = self._database_datetime(item.updated_at)

            sync_id = f"{source_id}:{year:04d}-{month:02d}"
            sync = session.get(AgendaSyncRecord, sync_id)
            if sync is None:
                sync = AgendaSyncRecord(
                    id=sync_id,
                    source_id=source_id,
                    year=year,
                    month=month,
                    synced_at=datetime.now(UTC),
                )
                session.add(sync)
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
            with Session(self.engine) as session:
                records = session.scalars(
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
                    .limit(limit)
                ).all()
            return [self._agenda_to_domain(record) for record in records]

        records = self._agenda_records(date_from, date_to, group, municipality)
        return [self._agenda_to_domain(record) for record in records[offset : offset + limit]]

    def count_agenda(
        self,
        date_from: date,
        date_to: date,
        group: str | None,
        municipality: str | None,
    ) -> int:
        if group is None and municipality is None:
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

        return len(self._agenda_records(date_from, date_to, group, municipality))

    def latest_agenda_month_sync(self, source_id: str, year: int, month: int) -> datetime | None:
        sync_id = f"{source_id}:{year:04d}-{month:02d}"
        with Session(self.engine) as session:
            value = session.scalar(
                select(AgendaSyncRecord.synced_at).where(AgendaSyncRecord.id == sync_id)
            )
            return self._domain_datetime(value) if value else None

    def _agenda_records(
        self, date_from: date, date_to: date, group: str | None, municipality: str | None
    ) -> list[AgendaEventRecord]:
        with Session(self.engine) as session:
            records = session.scalars(
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
            ).all()
            group_key = _search_key(group) if group else None
            municipality_key = _search_key(municipality) if municipality else None
            return [
                record
                for record in records
                if (
                    group_key is None
                    or any(
                        _search_key(value) == group_key
                        for value in (record.participating_groups or [])
                    )
                )
                and (
                    municipality_key is None
                    or _search_key(record.municipality) == municipality_key
                )
            ]

    @staticmethod
    def _to_domain(record: HourByHourRecord) -> HourByHourItem:
        return HourByHourItem(
            id=record.id,
            source_id=record.source_id,
            external_id=record.external_id,
            title=record.title,
            display_title=record.display_title,
            summary=record.summary,
            published_at=(
                SQLAlchemyContentRepository._domain_datetime(record.published_at)
                if record.published_at
                else None
            ),
            source_order=record.source_order,
            article_url=record.article_url,
            action_url=record.action_url or None,
            attribution=record.attribution,
            created_at=SQLAlchemyContentRepository._domain_datetime(record.created_at),
            updated_at=SQLAlchemyContentRepository._domain_datetime(record.updated_at),
        )

    @staticmethod
    def _agenda_to_domain(record: AgendaEventRecord) -> CastellEvent:
        return CastellEvent(
            id=record.id,
            source_id=record.source_id,
            external_id=record.external_id,
            title=record.title,
            local_date=record.local_date,
            starts_at=(
                SQLAlchemyContentRepository._domain_datetime(record.starts_at)
                if record.starts_at
                else None
            ),
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
            updated_at=SQLAlchemyContentRepository._domain_datetime(record.updated_at),
        )

    @staticmethod
    def _database_datetime(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @staticmethod
    def _domain_datetime(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


def _next_month(year: int, month: int) -> date:
    if month == 12:
        return date(year + 1, 1, 1)
    return date(year, month + 1, 1)


def _search_key(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    without_accents = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    return " ".join(without_accents.split())
