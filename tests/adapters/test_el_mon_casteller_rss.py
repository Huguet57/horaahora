from datetime import UTC, datetime
from pathlib import Path

import pytest

from backend.adapters.content.el_mon_casteller_rss import parse_feed

FIXTURE = Path(__file__).parents[1] / "fixtures" / "el_mon_casteller.xml"
FEED = FIXTURE.read_text(encoding="utf-8")
FETCHED_AT = datetime(2026, 9, 24, 10, tzinfo=UTC)


def test_parses_rss_metadata_and_links_to_the_original_article() -> None:
    items = parse_feed(FEED, fetched_at=FETCHED_AT)

    assert [item.title for item in items] == [
        "Una diada & una estrena",
        "Una entrevista ‘castellera’",
    ]
    assert items[0].created_at == items[0].updated_at == FETCHED_AT
    assert items[0].display_title == items[0].title
    assert items[0].summary == "Una estrena a plaça …"
    assert items[0].published_at.isoformat() == "2026-09-24T09:08:17+00:00"
    assert items[1].published_at.isoformat() == "2026-09-23T18:29:27+00:00"
    assert items[0].source_id == "el-mon-casteller"
    assert items[0].attribution == "El Món Casteller"
    assert items[0].article_url == "https://www.elmoncasteller.cat/una-diada/"
    assert items[0].action_url == items[0].article_url
    assert [item.source_order for item in items] == [0, 1]


def test_guid_keeps_identity_stable_when_title_or_permalink_changes() -> None:
    original = parse_feed(FEED, fetched_at=FETCHED_AT)[0]
    updated = parse_feed(
        FEED.replace("una-diada/", "diada-nova/").replace("estrena", "fita"), fetched_at=FETCHED_AT
    )[0]

    assert updated.id == original.id
    assert updated.external_id == original.external_id
    assert updated.article_url != original.article_url


@pytest.mark.parametrize("date", ["", "not-a-date"])
def test_missing_optional_metadata_does_not_invent_a_publication_date(date) -> None:
    feed = f"""<rss><channel><item><title>Opinió</title>
      <link>https://www.elmoncasteller.cat/opinio/</link><pubDate>{date}</pubDate>
    </item></channel></rss>"""
    item = parse_feed(feed, fetched_at=FETCHED_AT)[0]

    assert item.published_at is None
    assert item.summary == ""
    assert item.id == parse_feed(feed, fetched_at=FETCHED_AT)[0].id


@pytest.mark.parametrize("link", ["", "javascript:alert(1)", "https://"])
def test_skips_articles_without_a_usable_destination(link) -> None:
    feed = f"<rss><channel><item><title>Notícia</title><link>{link}</link></item></channel></rss>"
    assert parse_feed(feed, fetched_at=FETCHED_AT) == []


@pytest.mark.parametrize("feed", ["<html>Maintenance</html>", "<rss>"])
def test_rejects_invalid_feed_responses(feed) -> None:
    with pytest.raises(ValueError):
        parse_feed(feed, fetched_at=FETCHED_AT)


def test_accepts_an_empty_rss_channel() -> None:
    assert parse_feed("<rss><channel /></rss>", fetched_at=FETCHED_AT) == []
