import unicodedata
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal


class InterestLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @property
    def rank(self) -> int:
        return list(InterestLevel).index(self)


def group_key(name: str) -> str:
    for apostrophe in ("’", "‘", "ʼ"):
        name = name.replace(apostrophe, "'")
    folded = unicodedata.normalize("NFKD", name).casefold()
    return " ".join("".join(c for c in folded if not unicodedata.combining(c)).split())


@dataclass(frozen=True, slots=True)
class GroupSelection:
    mode: str = "all"
    keys: frozenset[str] = frozenset()

    def to_json(self) -> dict:
        return {"mode": self.mode, "keys": sorted(self.keys) if self.mode == "custom" else []}

    @classmethod
    def from_json(cls, value: dict) -> "GroupSelection":
        return cls(value.get("mode", "all"), frozenset(value.get("keys", [])))


def effective_interest(
    base: InterestLevel, groups: set[str] | frozenset[str], selection: GroupSelection
) -> InterestLevel:
    boost = selection.mode == "custom" and not selection.keys.isdisjoint(groups)
    return list(InterestLevel)[min(2, base.rank + int(boost))]


def qualifies(
    base: InterestLevel,
    groups: set[str] | frozenset[str],
    minimum: InterestLevel,
    selection: GroupSelection,
) -> bool:
    return effective_interest(base, groups, selection).rank >= minimum.rank


@dataclass(frozen=True, slots=True)
class InterestClassification:
    level: InterestLevel
    group_keys: frozenset[str]
    model: str
    criteria_version: str
    probabilities: dict
    confidence: float
    usage: dict = field(default_factory=dict)
    input_metadata: dict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class NewsContent:
    text: str
    url: str
    role: Literal["article_body", "linked_context"]


@dataclass(frozen=True, slots=True)
class ClassificationCandidate:
    id: str
    title: str
    summary: str
    url: str
    article_url: str = ""

    def content_for_classification(self, text: str) -> NewsContent | None:
        if not text:
            return None
        # Separate links (and legacy rows with unknown provenance) are context.
        role = (
            "article_body"
            if self.article_url and self.article_url == self.url
            else "linked_context"
        )
        return NewsContent(text, self.url, role)
