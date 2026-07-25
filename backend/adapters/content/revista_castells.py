from __future__ import annotations

import hashlib
import re
import uuid
from datetime import UTC, datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from backend.domain.content.models import HourByHourItem


_EDITORIAL_TITLE_PREFIX = re.compile(
    r"^\s*(?:dilluns|dimarts|dimecres|dijous|divendres|dissabte|diumenge)"
    r"\s*,?\s*\d{1,2}\s*,\s*\d{1,2}(?:[.:]\d{1,2})?\s*h(?:\s*[.·:–—-])?\s*",
    flags=re.IGNORECASE,
)


def clean_hour_by_hour_display_title(title: str) -> str:
    """Remove Revista Castells' redundant date/time prefix for list presentation."""
    display_title = _EDITORIAL_TITLE_PREFIX.sub("", title, count=1).strip()
    return display_title or title


class RevistaCastellsHTMLSource:
    SOURCE_ID = "revista-castells"
    ATTRIBUTION = "Revista Castells"
    URL = "https://revistacastells.cat/castells-hora-a-hora/"

    def __init__(self, url: str | None = None, timeout: float = 30) -> None:
        self.url = url or self.URL
        self.timeout = timeout

    def fetch(self) -> list[HourByHourItem]:
        response = requests.get(
            self.url,
            timeout=self.timeout,
            headers={"User-Agent": "HoraAHoraApp/1.0 (+https://github.com/Huguet57/horaahora)"},
        )
        response.raise_for_status()
        return self.parse(response.text)

    def parse(self, html: str) -> list[HourByHourItem]:
        soup = BeautifulSoup(html, "html.parser")
        container = soup.select_one(".castells-hora-a-hora")
        if container is None:
            raise ValueError("No s'ha trobat el contenidor .castells-hora-a-hora")

        now = datetime.now(UTC)
        items: list[HourByHourItem] = []
        for source_order, module in enumerate(container.select(".td_module_wrap")):
            title_element = module.select_one("h3.entry-title a")
            if title_element is None:
                continue
            excerpt_element = module.select_one(".td-excerpt")
            time_element = module.select_one("time.entry-date")
            article_href = str(title_element.get("href", "")).strip()
            article_url = urljoin(self.url, article_href) if article_href else ""
            embedded = excerpt_element.select_one("a[href]") if excerpt_element else None
            embedded_href = str(embedded.get("href", "")).strip() if embedded else ""
            action_url = urljoin(self.url, embedded_href) if embedded_href else None
            title = title_element.get_text(" ", strip=True)
            published_at = self._parse_datetime(str(time_element.get("datetime", ""))) if time_element else None
            external_id = hashlib.sha256((article_url or title).encode("utf-8")).hexdigest()
            item_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{self.SOURCE_ID}:{external_id}"))
            items.append(
                HourByHourItem(
                    id=item_id,
                    source_id=self.SOURCE_ID,
                    external_id=external_id,
                    title=title,
                    display_title=clean_hour_by_hour_display_title(title),
                    summary=excerpt_element.get_text(" ", strip=True) if excerpt_element else "",
                    published_at=published_at,
                    source_order=source_order,
                    article_url=article_url,
                    action_url=action_url,
                    attribution=self.ATTRIBUTION,
                    created_at=now,
                    updated_at=now,
                )
            )
        return items

    @staticmethod
    def _parse_datetime(value: str) -> datetime | None:
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
        except ValueError:
            return None
