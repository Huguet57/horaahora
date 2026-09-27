from collections.abc import Iterator
from datetime import UTC, datetime

import httpx

from backend.adapters.social.x_search import SEARCH_FIELDS, build_search_queries, parse_search_page
from backend.domain.social.models import SocialPost, SocialWatchlist

_HEADERS = {"User-Agent": "HoraAHoraApp/1.0 (+https://github.com/Huguet57/horaahora)"}


class XRecentSearchSource:
    """Popular posts from the official X API, billed per post read."""

    URL = "https://api.x.com/2/tweets/search/recent"

    def __init__(
        self,
        bearer_token: str,
        *,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 10,
        max_pages: int = 5,
    ) -> None:
        if not bearer_token:
            raise ValueError("X_BEARER_TOKEN és obligatori per llegir X")
        self.bearer_token = bearer_token
        self.transport = transport
        self.timeout = timeout
        self.max_pages = max_pages

    def search(self, watchlist: SocialWatchlist, *, since: datetime) -> list[SocialPost]:
        posts: dict[str, SocialPost] = {}
        headers = _HEADERS | {"Authorization": f"Bearer {self.bearer_token}"}
        with httpx.Client(
            transport=self.transport, timeout=self.timeout, headers=headers
        ) as client:
            for query in build_search_queries(watchlist):
                for post in self._pages(client, query, since):
                    posts.setdefault(post.post_id, post)
        return sorted(posts.values(), key=lambda post: post.published_at, reverse=True)

    def _pages(self, client: httpx.Client, query: str, since: datetime) -> Iterator[SocialPost]:
        params = {
            "query": query,
            "start_time": since.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "max_results": 100,
            **SEARCH_FIELDS,
        }
        # A bounded number of pages keeps an unexpectedly busy day from running up the bill.
        for _ in range(self.max_pages):
            response = client.get(self.URL, params=params)
            response.raise_for_status()
            page = parse_search_page(response.json())
            yield from page.posts
            if not page.next_token:
                return
            params = params | {"next_token": page.next_token}
