from __future__ import annotations

from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime

import requests

from backend.adapters.content.el_mon_casteller_rss import parse_feed
from backend.domain.content.models import HourByHourItem


class ElMonCastellerRSSSource:
    FEED_URLS = tuple(
        f"https://www.elmoncasteller.cat/category/{category}/feed/"
        for category in ("noticies", "opinio", "entrevistes", "cronica")
    )

    def __init__(self, timeout: float = 15) -> None:
        self.timeout = timeout

    def fetch(self) -> list[HourByHourItem]:
        # All categories must succeed before establishing this publisher's baseline.
        # Concurrent requests keep a slow feed within the cron's time budget.
        with ThreadPoolExecutor(max_workers=len(self.FEED_URLS)) as executor:
            feeds = list(executor.map(self._fetch_feed, self.FEED_URLS))

        fetched_at = datetime.now(UTC)
        return _merge_categories(parse_feed(feed, fetched_at=fetched_at) for feed in feeds)

    def _fetch_feed(self, url: str) -> bytes:
        response = requests.get(
            url,
            timeout=self.timeout,
            headers={"User-Agent": "HoraAHoraApp/1.0 (+https://github.com/Huguet57/horaahora)"},
        )
        response.raise_for_status()
        return response.content


def _merge_categories(feeds: Iterable[list[HourByHourItem]]) -> list[HourByHourItem]:
    items: list[HourByHourItem] = []
    seen_ids: set[str] = set()
    seen_urls: set[str] = set()
    for feed in feeds:
        for item in feed:
            if item.external_id in seen_ids or item.article_url in seen_urls:
                continue
            seen_ids.add(item.external_id)
            seen_urls.add(item.article_url)
            items.append(replace(item, source_order=len(items)))
    return items
