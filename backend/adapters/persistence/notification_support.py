import hashlib

from backend.domain.content.models import HourByHourItem


def collapse_id(external_id: str) -> str:
    value = f"hour-by-hour:{external_id}"
    if len(value.encode("utf-8")) <= 64:
        return value
    return f"hour-by-hour:{hashlib.sha256(external_id.encode()).hexdigest()[:40]}"


def content_hash(items: list[HourByHourItem]) -> str:
    identifiers = "\n".join(sorted(item.external_id for item in items))
    return hashlib.sha256(identifiers.encode("utf-8")).hexdigest()


def revoked_token(subscription_id: str) -> str:
    return f"revoked:{subscription_id}"
