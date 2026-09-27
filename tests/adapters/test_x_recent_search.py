from datetime import UTC, datetime

import httpx
import pytest

from backend.adapters.social.x_recent_search import XRecentSearchSource
from backend.domain.social.models import SocialWatchlist, WatchedAccount

SINCE = datetime(2026, 9, 26, 22, 30, 15, tzinfo=UTC)
WATCHLIST = SocialWatchlist(min_likes=10, hashtags=("castells",))


def post(post_id: str, created_at: str = "2026-09-27T08:00:00Z") -> dict:
    return {
        "id": post_id,
        "text": f"Opinió {post_id}",
        "author_id": "11",
        "created_at": created_at,
        "public_metrics": {"like_count": 12},
    }


def page(*posts: dict, next_token: str | None = None) -> dict:
    meta = {"result_count": len(posts)} | ({"next_token": next_token} if next_token else {})
    return {
        "data": list(posts),
        "includes": {"users": [{"id": "11", "name": "Nom", "username": "Compte"}]},
        "meta": meta,
    }


def test_each_query_is_paged_with_the_bearer_token_and_the_required_fields() -> None:
    requests: list[httpx.Request] = []
    pages = [
        page(post("1", "2026-09-27T08:00:00Z"), next_token="next"),
        page(post("2", "2026-09-27T09:00:00Z")),
    ]

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=pages[len(requests) - 1])

    source = XRecentSearchSource("token", transport=httpx.MockTransport(handle))
    posts = source.search(WATCHLIST, since=SINCE)

    assert [item.post_id for item in posts] == ["2", "1"]
    assert len(requests) == 2
    first = requests[0]
    assert first.headers["Authorization"] == "Bearer token"
    assert first.url.copy_with(query=None) == "https://api.x.com/2/tweets/search/recent"
    assert first.url.params["query"] == "(#castells) min_likes:10 -is:retweet"
    assert first.url.params["start_time"] == "2026-09-26T22:30:15Z"
    assert first.url.params["max_results"] == "100"
    assert "public_metrics" in first.url.params["tweet.fields"]
    assert first.url.params["expansions"].startswith("author_id")
    assert "next_token" not in first.url.params
    assert requests[1].url.params["next_token"] == "next"


def test_paging_stops_at_the_configured_limit() -> None:
    requests: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=page(post(str(len(requests))), next_token="more"))

    source = XRecentSearchSource("token", transport=httpx.MockTransport(handle), max_pages=2)

    assert len(source.search(WATCHLIST, since=SINCE)) == 2
    assert len(requests) == 2


def test_a_post_matched_by_several_queries_is_returned_once() -> None:
    accounts = tuple(WatchedAccount(f"compte_{index:07d}") for index in range(40))
    watchlist = SocialWatchlist(min_likes=10, accounts=accounts, hashtags=("castells",))
    queries: list[str] = []

    def handle(request: httpx.Request) -> httpx.Response:
        queries.append(request.url.params["query"])
        return httpx.Response(200, json=page(post("same")))

    posts = XRecentSearchSource("token", transport=httpx.MockTransport(handle)).search(
        watchlist, since=SINCE
    )

    assert len(queries) > 1
    assert [item.post_id for item in posts] == ["same"]


def test_provider_errors_are_raised_without_retrying() -> None:
    requests: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(429)

    source = XRecentSearchSource("token", transport=httpx.MockTransport(handle))

    with pytest.raises(httpx.HTTPStatusError):
        source.search(WATCHLIST, since=SINCE)
    assert len(requests) == 1


def test_a_bearer_token_is_required() -> None:
    with pytest.raises(ValueError, match="X_BEARER_TOKEN"):
        XRecentSearchSource("")
