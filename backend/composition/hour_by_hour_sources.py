"""The Hora a Hora sources that HOUR_BY_HOUR_SOURCES switches on and off."""

from collections.abc import Callable

from backend.adapters.content.el_mon_casteller import ElMonCastellerRSSSource
from backend.adapters.content.revista_castells import RevistaCastellsHTMLSource
from backend.config import Settings
from backend.domain.content.ports import HourByHourSource

SOURCES: dict[str, Callable[[Settings], HourByHourSource]] = {
    RevistaCastellsHTMLSource.SOURCE_ID: lambda settings: RevistaCastellsHTMLSource(
        settings.revista_castells_url
    ),
    ElMonCastellerRSSSource.SOURCE_ID: lambda _: ElMonCastellerRSSSource(),
}


def enabled_sources(settings: Settings) -> list[HourByHourSource]:
    unknown = sorted(set(settings.hour_by_hour_sources) - SOURCES.keys())
    if unknown:
        raise RuntimeError(f"HOUR_BY_HOUR_SOURCES no suportades: {', '.join(unknown)}")
    return [SOURCES[source_id](settings) for source_id in settings.hour_by_hour_sources]


def disabled_source_ids(settings: Settings) -> frozenset[str]:
    return frozenset(SOURCES.keys() - set(settings.hour_by_hour_sources))
