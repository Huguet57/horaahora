from datetime import UTC, datetime

import pytest

from backend.adapters.social.x_search import build_search_queries, parse_search_page
from backend.domain.social.models import (
    SocialAuthor,
    SocialPostContext,
    SocialWatchlist,
    WatchedAccount,
)

QUIJO = {"id": "11", "name": 'Joan "Quijo" Colominas', "username": "JoanQuijorna"}
MANEL = {"id": "12", "name": "Manel Urbano", "username": "Manelcv"}
REVISTA = {"id": "13", "name": "Revista Castells", "username": "revistacastells"}


def quote_post() -> dict:
    return {
        "id": "1970000000000000001",
        "text": (
            "Potser seré una mica crític amb això &amp; ho dic amb carinyo #castells "
            "https://t.co/quote"
        ),
        "author_id": "11",
        "created_at": "2026-09-27T08:00:00.000Z",
        "public_metrics": {"like_count": 10, "reply_count": 1},
        "entities": {
            "urls": [
                {
                    "url": "https://t.co/quote",
                    "expanded_url": "https://twitter.com/revistacastells/status/1969999999999999999",
                    "display_url": "x.com/revistacastell…",
                }
            ]
        },
        "referenced_tweets": [{"type": "quoted", "id": "1969999999999999999"}],
    }


def page(*posts: dict, includes: dict | None = None, next_token: str | None = None) -> dict:
    payload = {
        "data": list(posts),
        "includes": includes
        or {
            "users": [QUIJO, MANEL, REVISTA],
            "tweets": [
                {
                    "id": "1969999999999999999",
                    "text": "Els @moixiganguers van posar ahir quints a la tde9fm. https://t.co/video",
                    "author_id": "13",
                    "entities": {
                        "urls": [
                            {
                                "url": "https://t.co/video",
                                "expanded_url": "https://x.com/revistacastells/status/1/video/1",
                                "display_url": "pic.x.com/video",
                                "media_key": "7_1",
                            }
                        ]
                    },
                }
            ],
        },
        "meta": {"result_count": len(posts)},
    }
    if next_token:
        payload["meta"]["next_token"] = next_token
    return payload


def test_builds_one_query_with_accounts_hashtags_and_the_lowest_threshold() -> None:
    watchlist = SocialWatchlist(
        min_likes=10,
        accounts=(WatchedAccount("JoanQuijorna"), WatchedAccount("Manelcv", min_likes=5)),
        hashtags=("castells",),
    )

    assert build_search_queries(watchlist) == [
        "(from:JoanQuijorna OR from:Manelcv OR #castells) min_likes:5 -is:retweet"
    ]


def test_long_watchlists_are_split_into_queries_within_the_length_limit() -> None:
    accounts = tuple(WatchedAccount(f"compte_{index:07d}") for index in range(40))
    watchlist = SocialWatchlist(min_likes=10, accounts=accounts, hashtags=("castells",))

    queries = build_search_queries(watchlist, max_length=200)

    assert len(queries) > 1
    assert all(len(query) <= 200 for query in queries)
    assert all(query.endswith(") min_likes:10 -is:retweet") for query in queries)
    terms = [term for query in queries for term in query.split(")")[0][1:].split(" OR ")]
    assert terms == [f"from:{account.username}" for account in accounts] + ["#castells"]


def test_posts_keep_their_author_readable_text_and_quoted_context() -> None:
    result = parse_search_page(page(quote_post(), next_token="page-2"))

    assert result.next_token == "page-2"
    [post] = result.posts
    assert post.network == "x"
    assert post.post_id == "1970000000000000001"
    assert post.author == SocialAuthor("11", "JoanQuijorna", 'Joan "Quijo" Colominas')
    # The link to the quoted post is redundant: the quote travels as context.
    assert post.text == "Potser seré una mica crític amb això & ho dic amb carinyo #castells"
    assert post.url == "https://x.com/JoanQuijorna/status/1970000000000000001"
    assert post.published_at == datetime(2026, 9, 27, 8, tzinfo=UTC)
    assert post.like_count == 10
    assert post.context == (
        SocialPostContext(
            relation="quoted",
            text="Els @moixiganguers van posar ahir quints a la tde9fm.",
            author=SocialAuthor("13", "revistacastells", "Revista Castells"),
        ),
    )


def test_media_links_are_dropped_and_other_links_are_shown_readably() -> None:
    post = {
        "id": "2",
        "text": "Poc se'n parla dels castells nets https://t.co/foto https://t.co/web",
        "author_id": "12",
        "created_at": "2026-09-21T18:00:00Z",
        "public_metrics": {"like_count": 268},
        "entities": {
            "urls": [
                {
                    "url": "https://t.co/foto",
                    "expanded_url": "https://x.com/Manelcv/status/2/photo/1",
                    "display_url": "pic.x.com/foto",
                    "media_key": "3_1",
                },
                {
                    "url": "https://t.co/web",
                    "expanded_url": "https://www.revistacastells.cat/article",
                    "display_url": "revistacastells.cat/article",
                },
            ]
        },
    }

    [parsed] = parse_search_page(page(post)).posts

    assert parsed.text == "Poc se'n parla dels castells nets revistacastells.cat/article"
    assert parsed.context == ()


def test_long_posts_use_the_full_note_text() -> None:
    post = quote_post() | {
        "text": "Inici truncat…",
        "note_tweet": {"text": "Inici truncat i la resta del text llarg", "entities": {}},
    }

    [parsed] = parse_search_page(page(post)).posts

    assert parsed.text == "Inici truncat i la resta del text llarg"


def test_retweets_and_posts_without_a_known_author_are_skipped() -> None:
    retweet = quote_post() | {
        "id": "3",
        "referenced_tweets": [{"type": "retweeted", "id": "1969999999999999999"}],
    }
    unknown_author = quote_post() | {"id": "4", "author_id": "999"}

    assert parse_search_page(page(retweet, unknown_author)).posts == []


def test_replies_carry_the_post_they_answer_when_it_is_available() -> None:
    reply = quote_post() | {
        "id": "5",
        "entities": {},
        "referenced_tweets": [
            {"type": "replied_to", "id": "1969999999999999999"},
            {"type": "quoted", "id": "deleted-post"},
        ],
    }

    [parsed] = parse_search_page(page(reply)).posts

    assert [context.relation for context in parsed.context] == ["replied_to"]


def test_the_renamed_post_fields_are_also_read() -> None:
    post = quote_post()
    post["referenced_posts"] = post.pop("referenced_tweets")
    post["note_post"] = {"text": "Text complet", "entities": {}}
    includes = page().get("includes")
    includes["posts"] = includes.pop("tweets")

    [parsed] = parse_search_page(page(post, includes=includes)).posts

    assert parsed.text == "Text complet"
    assert parsed.context[0].author.username == "revistacastells"


def test_an_empty_page_has_no_posts_or_next_token() -> None:
    result = parse_search_page({"meta": {"result_count": 0}})

    assert result.posts == []
    assert result.next_token is None


@pytest.mark.parametrize("field", ["author_id", "created_at"])
def test_posts_without_the_requested_fields_fail_loudly(field: str) -> None:
    # X is renaming its fields: an ignored field list must not look like an empty search.
    post = quote_post()
    del post[field]

    with pytest.raises(ValueError, match="tweet.fields"):
        parse_search_page(page(post))
