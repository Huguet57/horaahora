from datetime import UTC, datetime

from backend.domain.social.models import SocialAuthor, SocialPost, SocialWatchlist, WatchedAccount


def post(username: str, likes: int) -> SocialPost:
    return SocialPost(
        network="x",
        post_id=f"{username}-{likes}",
        author=SocialAuthor(user_id="1", username=username, name=username),
        text="Text",
        url="https://x.com/status/1",
        published_at=datetime(2026, 9, 27, tzinfo=UTC),
        like_count=likes,
    )


def test_accounts_can_raise_or_lower_the_global_like_threshold() -> None:
    watchlist = SocialWatchlist(
        min_likes=10,
        accounts=(
            WatchedAccount("Gran", min_likes=50),
            WatchedAccount("Petit", min_likes=5),
            WatchedAccount("Normal"),
        ),
        hashtags=("castells",),
    )

    # One server-side filter must still return posts for the most permissive account.
    assert watchlist.search_min_likes == 5
    assert watchlist.threshold_for("gran") == 50
    assert watchlist.threshold_for("Desconegut") == 10
    assert watchlist.qualifies(post("Petit", 5))
    assert watchlist.qualifies(post("Normal", 10))
    assert watchlist.qualifies(post("hashtag_author", 10))
    assert not watchlist.qualifies(post("GRAN", 49))
    assert not watchlist.qualifies(post("Normal", 9))


def test_a_watchlist_without_accounts_or_hashtags_is_empty() -> None:
    assert SocialWatchlist(min_likes=10).is_empty
    assert not SocialWatchlist(min_likes=10, hashtags=("castells",)).is_empty
    assert not SocialWatchlist(min_likes=10, accounts=(WatchedAccount("Compte"),)).is_empty
