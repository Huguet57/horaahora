from datetime import UTC, datetime

from backend.domain.content.models import HourByHourItem


def hour_item(
    external_id: str, title: str | None = None, *, source_id: str = "revista-castells"
) -> HourByHourItem:
    now = datetime.now(UTC)
    return HourByHourItem(
        id=external_id,
        source_id=source_id,
        external_id=external_id,
        title=title or f"Dimecres 22, 10h. Notícia {external_id}",
        display_title=f"Notícia {external_id}",
        summary=f"Resum {external_id}",
        published_at=now,
        source_order=0,
        article_url=f"https://example.com/{external_id}",
        action_url=f"https://example.com/{external_id}/directe",
        attribution="Revista Castells",
        created_at=now,
        updated_at=now,
    )
