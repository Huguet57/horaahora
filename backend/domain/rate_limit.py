from typing import Protocol


class RateLimiter(Protocol):
    def allow(self, identifier: str) -> tuple[bool, int]: ...
