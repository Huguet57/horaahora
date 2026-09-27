from datetime import UTC, datetime

from backend.domain.social.models import SocialAuthor, SocialPost, SocialPostContext


def social_post(
    post_id: str,
    *,
    username: str = "JoanQuijorna",
    likes: int = 10,
    published_at: datetime | None = None,
    context: tuple[SocialPostContext, ...] = (),
) -> SocialPost:
    return SocialPost(
        network="x",
        post_id=post_id,
        author=SocialAuthor(user_id=f"id-{username}", username=username, name=f"Nom {username}"),
        text=f"Opinió castellera {post_id}",
        url=f"https://x.com/{username}/status/{post_id}",
        published_at=published_at or datetime(2026, 9, 27, 10, tzinfo=UTC),
        like_count=likes,
        context=context,
    )
