from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CastellerGroupDirectory:
    groups: list[str]
    revision: str
    official_url: str
