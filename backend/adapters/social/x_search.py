"""Translate X recent search queries and responses without network or clock access."""

import html
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urlsplit

from backend.domain.social.models import (
    SocialAuthor,
    SocialPost,
    SocialPostContext,
    SocialWatchlist,
)

NETWORK = "x"
MAX_QUERY_LENGTH = 512
SEARCH_FIELDS = {
    "tweet.fields": "author_id,created_at,entities,note_tweet,public_metrics,referenced_tweets",
    # Quoted and replied posts give the headline its context; authors avoid guessing names.
    "expansions": "author_id,referenced_tweets.id,referenced_tweets.id.author_id",
    "user.fields": "name,username",
}
_CONTEXT_RELATIONS = ("quoted", "replied_to")


@dataclass(frozen=True, slots=True)
class SearchPage:
    posts: list[SocialPost]
    next_token: str | None


def build_search_queries(
    watchlist: SocialWatchlist, *, max_length: int = MAX_QUERY_LENGTH
) -> list[str]:
    suffix = f" min_likes:{watchlist.search_min_likes} -is:retweet"
    terms = [f"from:{account.username}" for account in watchlist.accounts]
    terms += [f"#{hashtag}" for hashtag in watchlist.hashtags]
    queries: list[str] = []
    group: list[str] = []
    for term in terms:
        if group and len(_query([*group, term], suffix)) > max_length:
            queries.append(_query(group, suffix))
            group = []
        group.append(term)
    if group:
        queries.append(_query(group, suffix))
    return queries


def _query(terms: list[str], suffix: str) -> str:
    return f"({' OR '.join(terms)}){suffix}"


def parse_search_page(payload: dict) -> SearchPage:
    includes = payload.get("includes") or {}
    authors = {user["id"]: _author(user) for user in includes.get("users") or []}
    # X is renaming tweets to posts; read both names so the rename cannot hide data.
    referenced = {
        post["id"]: post for post in includes.get("tweets") or includes.get("posts") or []
    }
    posts = []
    for item in payload.get("data") or []:
        if not item.get("author_id") or not item.get("created_at"):
            raise ValueError("X no ha retornat author_id i created_at: revisa tweet.fields")
        author = authors.get(item["author_id"])
        references = _references(item)
        if author is None or any(reference.get("type") == "retweeted" for reference in references):
            continue
        posts.append(
            SocialPost(
                network=NETWORK,
                post_id=item["id"],
                author=author,
                text=display_text(item),
                url=f"https://x.com/{author.username}/status/{item['id']}",
                published_at=_datetime(item["created_at"]),
                like_count=int((item.get("public_metrics") or {}).get("like_count", 0)),
                context=tuple(_contexts(references, referenced, authors)),
            )
        )
    return SearchPage(posts=posts, next_token=(payload.get("meta") or {}).get("next_token"))


def display_text(post: dict) -> str:
    """Return the full post text with media and quoted-post links removed."""
    note = post.get("note_tweet") or post.get("note_post") or {}
    text = note.get("text") or post.get("text", "")
    entities = (note if note.get("text") else post).get("entities") or {}
    referenced_ids = {reference.get("id") for reference in _references(post)}
    for link in entities.get("urls") or []:
        if link.get("url"):
            text = text.replace(link["url"], _link_text(link, referenced_ids))
    return " ".join(html.unescape(text).split())


def _link_text(link: dict, referenced_ids: set[str | None]) -> str:
    display_url = link.get("display_url", "")
    if link.get("media_key") or display_url.startswith(("pic.x.com", "pic.twitter.com")):
        return ""
    if _status_id(link.get("expanded_url", "")) in referenced_ids:
        return ""
    return display_url or link.get("expanded_url") or link["url"]


def _status_id(url: str) -> str | None:
    parts = urlsplit(url).path.strip("/").split("/")
    if len(parts) >= 3 and parts[1] == "status":
        return parts[2]
    return None


def _references(post: dict) -> list[dict]:
    return post.get("referenced_tweets") or post.get("referenced_posts") or []


def _contexts(
    references: list[dict], referenced: dict[str, dict], authors: dict[str, SocialAuthor]
) -> Iterator[SocialPostContext]:
    for reference in references:
        post = referenced.get(reference.get("id", ""))
        # Deleted or protected posts are missing from includes: keep only what is public.
        if reference.get("type") not in _CONTEXT_RELATIONS or post is None:
            continue
        yield SocialPostContext(
            relation=reference["type"],
            text=display_text(post),
            author=authors.get(post.get("author_id", "")),
        )


def _author(user: dict) -> SocialAuthor:
    name = " ".join(str(user.get("name") or "").split()) or user["username"]
    return SocialAuthor(user_id=user["id"], username=user["username"], name=name)


def _datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
