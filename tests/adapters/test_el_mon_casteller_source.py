from pathlib import Path
from unittest.mock import Mock

import pytest
import requests

from backend.adapters.content.el_mon_casteller import ElMonCastellerRSSSource

FIXTURE = Path(__file__).parents[1] / "fixtures" / "el_mon_casteller.xml"
FEED = FIXTURE.read_text(encoding="utf-8")


def test_parses_rss_metadata_and_links_to_the_original_article() -> None:
    items = ElMonCastellerRSSSource().parse(FEED)

    assert [item.title for item in items] == [
        "Una diada & una estrena",
        "Una entrevista ‘castellera’",
    ]
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
    source = ElMonCastellerRSSSource()
    original = source.parse(FEED)[0]
    updated = source.parse(FEED.replace("una-diada/", "diada-nova/").replace("estrena", "fita"))[0]

    assert updated.id == original.id
    assert updated.external_id == original.external_id
    assert updated.article_url != original.article_url


@pytest.mark.parametrize("date", ["", "not-a-date"])
def test_missing_optional_metadata_does_not_invent_a_publication_date(date) -> None:
    feed = f"""<rss><channel><item><title>Opinió</title>
      <link>https://www.elmoncasteller.cat/opinio/</link><pubDate>{date}</pubDate>
    </item></channel></rss>"""
    source = ElMonCastellerRSSSource()
    item = source.parse(feed)[0]

    assert item.published_at is None
    assert item.summary == ""
    assert item.id == source.parse(feed)[0].id


@pytest.mark.parametrize("link", ["", "javascript:alert(1)", "https://"])
def test_skips_articles_without_a_usable_destination(link) -> None:
    feed = f"<rss><channel><item><title>Notícia</title><link>{link}</link></item></channel></rss>"
    assert ElMonCastellerRSSSource().parse(feed) == []


@pytest.mark.parametrize("feed", ["<html>Maintenance</html>", "<rss>"])
def test_rejects_invalid_feed_responses(feed) -> None:
    with pytest.raises(ValueError):
        ElMonCastellerRSSSource().parse(feed)


def test_accepts_an_empty_rss_channel() -> None:
    assert ElMonCastellerRSSSource().parse("<rss><channel /></rss>") == []


def test_fetches_all_four_categories_and_deduplicates_shared_articles(monkeypatch) -> None:
    response = Mock(content=FEED.encode())
    get = Mock(return_value=response)
    monkeypatch.setattr(requests, "get", get)

    items = ElMonCastellerRSSSource(timeout=7).fetch()

    assert {call.args[0] for call in get.call_args_list} == {
        f"https://www.elmoncasteller.cat/category/{category}/feed/"
        for category in ("noticies", "opinio", "entrevistes", "cronica")
    }
    assert all(call.kwargs["timeout"] == 7 for call in get.call_args_list)
    assert all(
        "HoraAHoraApp" in call.kwargs["headers"]["User-Agent"] for call in get.call_args_list
    )
    assert response.raise_for_status.call_count == 4
    assert len(items) == 2
    assert [item.source_order for item in items] == [0, 1]


def test_rejects_partial_category_fetch_to_avoid_initializing_an_incomplete_baseline(monkeypatch):
    def get(url, **kwargs):
        if "/opinio/" in url:
            raise requests.Timeout("opinio unavailable")
        return Mock(content=FEED.encode())

    monkeypatch.setattr(requests, "get", get)

    with pytest.raises(requests.Timeout):
        ElMonCastellerRSSSource().fetch()
