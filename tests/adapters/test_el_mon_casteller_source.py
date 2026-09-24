from pathlib import Path
from unittest.mock import Mock

import pytest
import requests

from backend.adapters.content.el_mon_casteller import ElMonCastellerRSSSource

FIXTURE = Path(__file__).parents[1] / "fixtures" / "el_mon_casteller.xml"
FEED = FIXTURE.read_text(encoding="utf-8")


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


def test_fetch_preserves_unique_articles_from_every_category_in_a_stable_order(monkeypatch):
    categories = ("noticies", "opinio", "entrevistes", "cronica")

    def get(url, **kwargs):
        category = url.split("/")[-3]
        feed = FEED.replace("?p=123", f"?p={category}").replace("una-diada/", f"{category}/")
        return Mock(content=feed.encode())

    monkeypatch.setattr(requests, "get", get)

    items = ElMonCastellerRSSSource().fetch()

    assert [item.article_url for item in items] == [
        "https://www.elmoncasteller.cat/noticies/",
        "https://www.elmoncasteller.cat/una-entrevista/",
        "https://www.elmoncasteller.cat/opinio/",
        "https://www.elmoncasteller.cat/entrevistes/",
        "https://www.elmoncasteller.cat/cronica/",
    ]
    assert [item.source_order for item in items] == list(range(len(categories) + 1))


@pytest.mark.parametrize("changed_field", ["guid", "link"])
def test_fetch_deduplicates_by_both_guid_and_permalink(monkeypatch, changed_field):
    def get(url, **kwargs):
        feed = FEED
        if "/opinio/" in url:
            feed = (
                feed.replace("?p=123", "?p=456")
                if changed_field == "guid"
                else feed.replace("una-diada/", "nou-enllac/")
            )
        return Mock(content=feed.encode())

    monkeypatch.setattr(requests, "get", get)

    assert len(ElMonCastellerRSSSource().fetch()) == 2
