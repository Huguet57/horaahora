import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, delete, select, update
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from backend.adapters.persistence.database import Database
from backend.adapters.persistence.models import HourByHourRecord, SocialPostRecord
from backend.adapters.persistence.notification_withdrawal import cancel_undelivered_notifications
from backend.adapters.persistence.repository_support import (
    database_datetime,
    domain_datetime,
    resolve_engine,
)
from backend.domain.social.models import (
    HeadlinedPost,
    SocialAuthor,
    SocialHeadline,
    SocialPost,
    SocialPostContext,
)

PENDING = "pending"
ACCEPTED = "accepted"
REJECTED = "rejected"
FAILED = "failed"
HIDDEN = "hidden"


class SQLAlchemySocialPostRepository:
    def __init__(self, database: Database | Engine | str) -> None:
        self.database, self.engine = resolve_engine(database)

    def save_candidates(self, posts: list[SocialPost], *, seen_at: datetime) -> int:
        discovered = 0
        seen = database_datetime(seen_at)
        with Session(self.engine) as session, session.begin():
            for post in posts:
                record = session.scalar(_select(post))
                if record is None:
                    session.add(_new_record(post, seen))
                    discovered += 1
                    continue
                # Text and context stay as discovered: the headline was written from them.
                record.like_count = post.like_count
                record.updated_at = seen
        return discovered

    def pending_headlines(self, limit: int) -> list[SocialPost]:
        with Session(self.engine) as session:
            records = session.scalars(
                select(SocialPostRecord)
                .where(SocialPostRecord.status == PENDING)
                .order_by(SocialPostRecord.published_at.desc(), SocialPostRecord.post_id.desc())
                .limit(limit)
            ).all()
            return [_post(record) for record in records]

    def record_headline(
        self, post: SocialPost, headline: SocialHeadline, *, decided_at: datetime
    ) -> None:
        with Session(self.engine) as session, session.begin():
            session.execute(
                update(SocialPostRecord)
                .where(
                    SocialPostRecord.network == post.network,
                    SocialPostRecord.post_id == post.post_id,
                    SocialPostRecord.status == PENDING,
                )
                .values(
                    status=ACCEPTED if headline.publishable else REJECTED,
                    headline=headline.headline,
                    model=headline.model[:100],
                    error="",
                    decided_at=database_datetime(decided_at),
                )
            )

    def record_headline_failure(self, post: SocialPost, reason: str, *, max_attempts: int) -> bool:
        with Session(self.engine) as session, session.begin():
            record = session.scalar(_select(post).where(SocialPostRecord.status == PENDING))
            if record is None:
                return False
            record.attempts += 1
            record.error = reason[:100]
            if record.attempts < max_attempts:
                return False
            record.status = FAILED
            return True

    def accepted_since(self, since: datetime, limit: int) -> list[HeadlinedPost]:
        with Session(self.engine) as session:
            records = session.scalars(
                select(SocialPostRecord)
                .where(
                    SocialPostRecord.status == ACCEPTED,
                    SocialPostRecord.published_at >= database_datetime(since),
                )
                .order_by(SocialPostRecord.published_at.desc(), SocialPostRecord.post_id.desc())
                .limit(limit)
            ).all()
            return [
                HeadlinedPost(post=_post(record), headline=record.headline) for record in records
            ]

    def hide(self, network: str, post_id: str) -> bool:
        """Withdraw a post and its unsent notifications, and keep it from coming back."""
        with Session(self.engine) as session, session.begin():
            hidden = session.execute(
                update(SocialPostRecord)
                .where(SocialPostRecord.network == network, SocialPostRecord.post_id == post_id)
                .values(status=HIDDEN)
            ).rowcount
            session.execute(
                delete(HourByHourRecord).where(
                    HourByHourRecord.source_id == network, HourByHourRecord.external_id == post_id
                )
            )
            cancel_undelivered_notifications(
                session,
                source_id=network,
                external_id=post_id,
                reason="Hidden",
                now=database_datetime(datetime.now(UTC)),
            )
            return hidden == 1


def _select(post: SocialPost) -> Select[tuple[SocialPostRecord]]:
    return select(SocialPostRecord).where(
        SocialPostRecord.network == post.network,
        SocialPostRecord.post_id == post.post_id,
    )


def _new_record(post: SocialPost, seen: datetime) -> SocialPostRecord:
    return SocialPostRecord(
        id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{post.network}:{post.post_id}")),
        network=post.network,
        post_id=post.post_id,
        author_id=post.author.user_id,
        author_username=post.author.username,
        author_name=post.author.name[:200],
        text=post.text,
        context=[_context_json(context) for context in post.context],
        url=post.url,
        like_count=post.like_count,
        published_at=database_datetime(post.published_at),
        status=PENDING,
        attempts=0,
        headline="",
        model="",
        error="",
        first_seen_at=seen,
        updated_at=seen,
        decided_at=None,
    )


def _post(record: SocialPostRecord) -> SocialPost:
    return SocialPost(
        network=record.network,
        post_id=record.post_id,
        author=SocialAuthor(record.author_id, record.author_username, record.author_name),
        text=record.text,
        url=record.url,
        published_at=domain_datetime(record.published_at),
        like_count=record.like_count,
        context=tuple(_context(item) for item in record.context),
    )


def _context_json(context: SocialPostContext) -> dict:
    author = context.author
    return {
        "relation": context.relation,
        "text": context.text,
        "author": None
        if author is None
        else {"user_id": author.user_id, "username": author.username, "name": author.name},
    }


def _context(item: dict) -> SocialPostContext:
    author = item.get("author")
    return SocialPostContext(
        relation=item["relation"],
        text=item["text"],
        author=None
        if author is None
        else SocialAuthor(author["user_id"], author["username"], author["name"]),
    )
