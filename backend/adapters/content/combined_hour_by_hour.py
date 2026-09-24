from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor

from backend.domain.content.models import HourByHourItem
from backend.domain.content.ports import HourByHourSource

logger = logging.getLogger(__name__)


class CombinedHourByHourSource:
    def __init__(self, sources: list[HourByHourSource]) -> None:
        self.sources = sources

    def fetch(self) -> list[HourByHourItem]:
        items: list[HourByHourItem] = []
        successful_sources = 0
        with ThreadPoolExecutor(max_workers=max(1, len(self.sources))) as executor:
            futures = [(source, executor.submit(source.fetch)) for source in self.sources]
            for source, future in futures:
                try:
                    items.extend(future.result())
                    successful_sources += 1
                except Exception:
                    logger.warning(
                        "No s'ha pogut actualitzar la font %s",
                        type(source).__name__,
                        exc_info=True,
                    )
        if not successful_sources:
            raise RuntimeError("No s'ha pogut actualitzar cap font de l'Hora a Hora")
        return items
