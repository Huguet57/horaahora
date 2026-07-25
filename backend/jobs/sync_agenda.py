from __future__ import annotations

import argparse
import json
import time
from collections.abc import Sequence
from datetime import date, datetime
from zoneinfo import ZoneInfo

from backend.application.agenda_sync import AgendaSyncService
from backend.composition.providers import (
    build_agenda_repository,
    build_agenda_source,
    build_database,
)
from backend.config import Settings


def month_start(value: date, offset: int = 0) -> date:
    month_index = value.year * 12 + value.month - 1 + offset
    return date(month_index // 12, month_index % 12 + 1, 1)


def parse_month(value: str) -> date:
    try:
        parsed = datetime.strptime(value, "%Y-%m").date()
    except ValueError as error:
        raise argparse.ArgumentTypeError("El mes ha de tenir format YYYY-MM") from error
    return parsed.replace(day=1)


def default_range(settings: Settings, today: date | None = None) -> tuple[date, date]:
    today = today or datetime.now(ZoneInfo("Europe/Madrid")).date()
    return (
        month_start(today, -settings.agenda_sync_months_back),
        month_start(today, settings.agenda_sync_months_ahead),
    )


def sync_once(settings: Settings, date_from: date, date_to: date) -> int:
    source = build_agenda_source(settings)
    if source is None:
        raise RuntimeError("AGENDA_SOURCE ha d'estar activa per sincronitzar l'agenda")

    repository = build_agenda_repository(build_database(settings))
    result = AgendaSyncService(repository, source).sync(date_from, date_to)
    print(
        json.dumps(
            {
                "event": "agenda_sync_finished",
                "source_id": source.source_id,
                "from": date_from.strftime("%Y-%m"),
                "to": date_to.strftime("%Y-%m"),
                "succeeded": [f"{year:04d}-{month:02d}" for year, month in result.succeeded],
                "failed": [
                    {
                        "month": f"{failure.year_month[0]:04d}-{failure.year_month[1]:02d}",
                        "error": failure.error,
                    }
                    for failure in result.failed
                ],
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return 1 if result.failed else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prefetch de l'agenda de la CCCC cap a la base de dades pròpia."
    )
    parser.add_argument("--from-month", type=parse_month, help="Primer mes (YYYY-MM)")
    parser.add_argument("--to-month", type=parse_month, help="Últim mes (YYYY-MM)")
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Repeteix la sincronització segons AGENDA_SYNC_INTERVAL_SECONDS.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = Settings.from_env()
    default_from, default_to = default_range(settings)
    date_from = args.from_month or default_from
    date_to = args.to_month or default_to
    if date_to < date_from:
        raise SystemExit("--to-month no pot ser anterior a --from-month")

    while True:
        exit_code = sync_once(settings, date_from, date_to)
        if not args.daemon:
            return exit_code
        time.sleep(settings.agenda_sync_interval_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
