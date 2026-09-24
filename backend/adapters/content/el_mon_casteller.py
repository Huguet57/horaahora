from __future__ import annotations

import hashlib
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit
from xml.etree import ElementTree

import requests
from bs4 import BeautifulSoup

from backend.domain.content.models import HourByHourItem


class ElMonCastellerRSSSource:
    SOURCE_ID = "el-mon-casteller"
    ATTRIBUTION = "El Món Casteller"
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

    def _fetch_feed(self, url: str) -> list[HourByHourItem]:
        response = requests.get(
            url,
            timeout=self.timeout,
            headers={"User-Agent": "HoraAHoraApp/1.0 (+https://github.com/Huguet57/horaahora)"},
        )
        response.raise_for_status()
        return self.parse(response.content)

    def parse(self, xml: str | bytes) -> list[HourByHourItem]:
        try:
            root = ElementTree.fromstring(xml)
        except ElementTree.ParseError as error:
            raise ValueError("El feed d'El Món Casteller no és XML vàlid") from error
        channel = root.find("channel")
        if root.tag != "rss" or channel is None:
            raise ValueError("No s'ha trobat el canal RSS d'El Món Casteller")

        now = datetime.now(UTC)
        items: list[HourByHourItem] = []
        for entry in channel.findall("item"):
            title = _plain_text(entry.findtext("title", ""))
            article_url = entry.findtext("link", "").strip()
            parsed_url = urlsplit(article_url)
            if not title or parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
                continue
            identity = entry.findtext("guid", "").strip() or article_url
            external_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()
            item_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{self.SOURCE_ID}:{external_id}"))
            items.append(
                HourByHourItem(
                    id=item_id,
                    source_id=self.SOURCE_ID,
                    external_id=external_id,
                    title=title,
                    display_title=title,
                    summary=_summary(entry.findtext("description", ""), article_url),
                    published_at=_published_at(entry.findtext("pubDate", "")),
                    source_order=len(items),
                    article_url=article_url,
                    action_url=article_url,
                    attribution=self.ATTRIBUTION,
                    created_at=now,
                    updated_at=now,
                )
            )
        return items


def _plain_text(html: str) -> str:
    return " ".join(BeautifulSoup(html, "html.parser").get_text(" ", strip=True).split())


def _summary(html: str, article_url: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    # WordPress appends a redundant "Font" backlink to the supplied excerpt.
    for link in soup.select("a[href]"):
        if link.get("href") == article_url and link.get_text(strip=True) == "Font":
            link.decompose()
    return " ".join(soup.get_text(" ", strip=True).split())


def _published_at(value: str) -> datetime | None:
    try:
        parsed = parsedate_to_datetime(value)
    except (ValueError, TypeError, OverflowError):
        return None
    return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)
