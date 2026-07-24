from dataclasses import replace
from datetime import UTC, date, datetime, timedelta, timezone

from backend.adapters.persistence.agenda_repository import SQLAlchemyAgendaRepository
from backend.adapters.persistence.hour_by_hour_repository import (
    SQLAlchemyHourByHourRepository,
)
from backend.domain.content.models import CastellEvent, HourByHourItem


def item(external_id: str, published_at: datetime, title: str) -> HourByHourItem:
    return HourByHourItem(
        id=external_id,
        source_id="source",
        external_id=external_id,
        title=title,
        display_title=title,
        summary="",
        published_at=published_at,
        source_order=0,
        article_url=f"https://example.com/{external_id}",
        action_url=f"https://example.com/{external_id}",
        attribution="Source",
        created_at=published_at,
        updated_at=published_at,
    )


def test_sql_repository_upserts_and_orders_newest_first() -> None:
    repository = SQLAlchemyHourByHourRepository("sqlite+pysqlite:///:memory:")
    now = datetime.now(UTC)

    repository.upsert_hour_by_hour(
        [item("old", now - timedelta(hours=1), "Old"), item("new", now, "New")]
    )
    repository.upsert_hour_by_hour([item("old", now - timedelta(hours=1), "Old updated")])

    assert repository.count_hour_by_hour() == 2
    assert [value.title for value in repository.list_hour_by_hour(0, 10)] == ["New", "Old updated"]
    assert [value.display_title for value in repository.list_hour_by_hour(0, 10)] == ["New", "Old updated"]


def test_sqlite_repository_preserves_the_instant_of_offset_dates() -> None:
    repository = SQLAlchemyHourByHourRepository("sqlite+pysqlite:///:memory:")
    local_time = datetime(2026, 7, 20, 14, 45, tzinfo=timezone(timedelta(hours=2)))

    repository.upsert_hour_by_hour([item("offset", local_time, "Offset")])

    stored = repository.list_hour_by_hour(0, 1)[0].published_at
    assert stored is not None
    assert stored.tzinfo is not None
    assert stored.astimezone(UTC) == datetime(2026, 7, 20, 12, 45, tzinfo=UTC)


def test_sql_repository_preserves_missing_associated_link() -> None:
    repository = SQLAlchemyHourByHourRepository("sqlite+pysqlite:///:memory:")
    now = datetime.now(UTC)
    value = replace(item("without-link", now, "Sense enllaç"), action_url=None)

    repository.upsert_hour_by_hour([value])

    assert repository.list_hour_by_hour(0, 1)[0].action_url is None


def agenda_event(external_id: str, day: date, revision: str = "r1") -> CastellEvent:
    return CastellEvent(
        id=external_id,
        source_id="cccc",
        external_id=external_id,
        title=f"Diada {external_id}",
        local_date=day,
        starts_at=datetime(day.year, day.month, day.day, 12, tzinfo=timezone(timedelta(hours=2))),
        time_label="12:00",
        timezone="Europe/Madrid",
        venue="Plaça",
        municipality="Valls",
        participating_groups=["Colla A"],
        notes="",
        source_url="https://castellscat.cat/ca/agenda",
        source_order=0,
        attribution="Font: Coordinadora de Colles Castelleres de Catalunya (CCCC)",
        revision=revision,
        updated_at=datetime.now(UTC),
    )


def test_agenda_month_snapshot_propagates_updates_and_deletions() -> None:
    repository = SQLAlchemyAgendaRepository("sqlite+pysqlite:///:memory:")
    day = date(2026, 7, 21)

    repository.replace_agenda_month(
        "cccc", 2026, 7, [agenda_event("one", day), agenda_event("two", day)]
    )
    repository.replace_agenda_month(
        "cccc", 2026, 7, [agenda_event("one", day, revision="r2")]
    )

    events = repository.list_agenda(day, day, None, None, 0, 50)
    assert [(event.external_id, event.revision) for event in events] == [("one", "r2")]
    assert repository.count_agenda(day, day, None, None) == 1
    assert repository.latest_agenda_month_sync("cccc", 2026, 7) is not None


def test_agenda_filters_names_without_case_or_accent_sensitivity() -> None:
    repository = SQLAlchemyAgendaRepository("sqlite+pysqlite:///:memory:")
    day = date(2026, 7, 21)
    event = agenda_event("one", day)
    repository.replace_agenda_month("cccc", 2026, 7, [event])

    assert repository.count_agenda(day, day, "colla a", "vàlls") == 1
    assert repository.count_agenda(day, day, "Colla inexistent", None) == 0


def test_agenda_unfiltered_pagination_is_applied_in_database_order() -> None:
    repository = SQLAlchemyAgendaRepository("sqlite+pysqlite:///:memory:")
    day = date(2026, 7, 21)
    repository.replace_agenda_month(
        "cccc",
        2026,
        7,
        [
            agenda_event("one", day),
            agenda_event("two", day),
            agenda_event("three", day),
        ],
    )

    all_items = repository.list_agenda(day, day, None, None, 0, 3)
    second_page = repository.list_agenda(day, day, None, None, 1, 1)

    assert len(all_items) == 3
    assert second_page == [all_items[1]]
    assert repository.count_agenda(day, day, None, None) == 3
