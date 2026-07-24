from datetime import date, datetime

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
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class HourByHourRecord(Base):
    __tablename__ = "hour_by_hour_items"
    __table_args__ = (
        UniqueConstraint("source_id", "external_id", name="uq_hour_by_hour_source_external"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_id: Mapped[str] = mapped_column(String(100), index=True)
    external_id: Mapped[str] = mapped_column(String(128))
    title: Mapped[str] = mapped_column(Text)
    display_title: Mapped[str] = mapped_column(Text)
    summary: Mapped[str] = mapped_column(Text, default="")
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    source_order: Mapped[int] = mapped_column(Integer)
    article_url: Mapped[str] = mapped_column(Text)
    action_url: Mapped[str] = mapped_column(Text)
    attribution: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class AgendaEventRecord(Base):
    __tablename__ = "agenda_events"
    __table_args__ = (
        UniqueConstraint("source_id", "external_id", name="uq_agenda_source_external"),
    )

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
