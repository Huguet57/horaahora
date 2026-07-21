from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import UTC, date, datetime
from pathlib import Path
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

from backend.domain.models import CastellEvent


class CCCCAgendaHTMLSource:
    source_id = "cccc"
    ATTRIBUTION = "Font: Coordinadora de Colles Castelleres de Catalunya (CCCC)"
    URL = "https://castellscat.cat/ca/agenda"
    TIMEZONE = "Europe/Madrid"
    _DATE_PATTERN = re.compile(r"^\d{2}/\d{2}/\d{4}$")
    _TIME_PATTERN = re.compile(r"^(?P<hour>\d{1,2})[:.](?P<minute>\d{2})(?:\s*h)?$", re.IGNORECASE)

    def __init__(self, url: str | None = None, timeout: float = 30) -> None:
        self.url = url or self.URL
        self.timeout = timeout

    def fetch_month(self, year: int, month: int) -> list[CastellEvent]:
        response = requests.get(
            self.url,
            params={"a": str(year), "m": f"{month:02d}"},
            timeout=self.timeout,
            headers={
                "User-Agent": "CastellsSuperApp/1.0 (+https://github.com/Huguet57/horaahora)",
                "Accept-Language": "ca,en;q=0.8",
            },
        )
        response.raise_for_status()
        return self.parse(response.text, year=year, month=month)

    def parse(self, html: str, *, year: int, month: int) -> list[CastellEvent]:
        soup = BeautifulSoup(html, "html.parser")
        container = soup.select_one("#agenda")
        if container is None:
            raise ValueError("No s'ha trobat el contenidor de l'agenda de la CCCC")

        now = datetime.now(UTC)
        events: list[CastellEvent] = []
        for source_order, element in enumerate(container.select(".element")):
            header = element.select_one(".element-header")
            body = element.select_one(".element-body")
            cells = body.select(".divTableCell") if body else []
            if header is None or len(cells) < 2:
                continue

            title = self._title(header)
            municipality_element = cells[0].select_one(".cityname")
            municipality = (
                municipality_element.get_text(" ", strip=True) if municipality_element else ""
            )
            detail_lines = [value.strip() for value in cells[0].stripped_strings if value.strip()]
            date_index = next(
                (index for index, value in enumerate(detail_lines) if self._DATE_PATTERN.match(value)),
                None,
            )
            if date_index is None or date_index + 1 >= len(detail_lines):
                continue
            local_date = datetime.strptime(detail_lines[date_index], "%d/%m/%Y").date()
            if local_date.year != year or local_date.month != month:
                continue
            time_label = detail_lines[date_index + 1]
            venue_parts = [
                value
                for value in detail_lines[date_index + 2 :]
                if not municipality or value != municipality
            ]
            venue = " · ".join(venue_parts)
            groups = self._groups(cells[1])
            notes_element = body.select_one(".pt-1") if body else None
            notes = notes_element.get_text(" ", strip=True) if notes_element else ""
            if notes == "-":
                notes = ""

            source_url = f"{self.url}?{urlencode({'a': year, 'm': f'{month:02d}'})}"
            external_payload = "|".join(
                [local_date.isoformat(), self._normal(title), self._normal(municipality)]
            )
            external_id = hashlib.sha256(external_payload.encode("utf-8")).hexdigest()
            starts_at = self._starts_at(local_date, time_label)
            revision_payload = json.dumps(
                {
                    "title": title,
                    "local_date": local_date.isoformat(),
                    "time_label": time_label,
                    "venue": venue,
                    "municipality": municipality,
                    "groups": groups,
                    "notes": notes,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
            revision = hashlib.sha256(revision_payload.encode("utf-8")).hexdigest()
            item_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{self.source_id}:{external_id}"))
            events.append(
                CastellEvent(
                    id=item_id,
                    source_id=self.source_id,
                    external_id=external_id,
                    title=title,
                    local_date=local_date,
                    starts_at=starts_at,
                    time_label=time_label,
                    timezone=self.TIMEZONE,
                    venue=venue,
                    municipality=municipality,
                    participating_groups=groups,
                    notes=notes,
                    source_url=source_url,
                    source_order=source_order,
                    attribution=self.ATTRIBUTION,
                    revision=revision,
                    updated_at=now,
                )
            )
        return events

    @classmethod
    def _starts_at(cls, local_date: date, time_label: str) -> datetime | None:
        match = cls._TIME_PATTERN.match(time_label.strip())
        if match is None:
            return None
        hour = int(match.group("hour"))
        minute = int(match.group("minute"))
        if hour > 23 or minute > 59:
            return None
        return datetime(
            local_date.year,
            local_date.month,
            local_date.day,
            hour,
            minute,
            tzinfo=ZoneInfo(cls.TIMEZONE),
        )

    @staticmethod
    def _groups(cell: object) -> list[str]:
        strings = getattr(cell, "stripped_strings", [])
        groups: list[str] = []
        for value in strings:
            cleaned = str(value).strip().lstrip("-–— ").strip()
            if cleaned and cleaned not in groups:
                groups.append(cleaned)
        return groups

    @staticmethod
    def _title(header: object) -> str:
        select_one = getattr(header, "select_one", None)
        desktop = select_one(".d-none.d-md-block") if select_one else None
        if desktop is not None:
            return desktop.get_text(" ", strip=True)
        get_text = getattr(header, "get_text")
        return get_text(" ", strip=True)

    @staticmethod
    def _normal(value: str) -> str:
        return " ".join(value.casefold().split())


class CCCCAgendaFixtureSource(CCCCAgendaHTMLSource):
    source_id = "cccc-fixture"
    ATTRIBUTION = "Dades de demostració — no oficials"

    def __init__(self, fixture_path: str | Path) -> None:
        super().__init__()
        self.fixture_path = Path(fixture_path)

    def fetch_month(self, year: int, month: int) -> list[CastellEvent]:
        return self.parse(self.fixture_path.read_text(encoding="utf-8"), year=year, month=month)
