"""Translate El Món Casteller RSS into content items without network or clock access."""

import hashlib
import uuid
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit
from xml.etree import ElementTree

from bs4 import BeautifulSoup

from backend.domain.content.models import HourByHourItem

SOURCE_ID = "el-mon-casteller"
ATTRIBUTION = "El Món Casteller"


def parse_feed(xml: str | bytes, *, fetched_at: datetime) -> list[HourByHourItem]:
    try:
        root = ElementTree.fromstring(xml)
    except ElementTree.ParseError as error:
        raise ValueError("El feed d'El Món Casteller no és XML vàlid") from error
    channel = root.find("channel")
    if root.tag != "rss" or channel is None:
        raise ValueError("No s'ha trobat el canal RSS d'El Món Casteller")

    items: list[HourByHourItem] = []
    for entry in channel.findall("item"):
        title = _plain_text(entry.findtext("title", ""))
        article_url = entry.findtext("link", "").strip()
        parsed_url = urlsplit(article_url)
        if not title or parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            continue
        identity = entry.findtext("guid", "").strip() or article_url
        external_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()
        item_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{SOURCE_ID}:{external_id}"))
        items.append(
            HourByHourItem(
                id=item_id,
                source_id=SOURCE_ID,
                external_id=external_id,
                title=title,
                display_title=title,
                summary=_summary(entry.findtext("description", ""), article_url),
                published_at=_published_at(entry.findtext("pubDate", "")),
                source_order=len(items),
                article_url=article_url,
                action_url=article_url,
                attribution=ATTRIBUTION,
                created_at=fetched_at,
                updated_at=fetched_at,
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
