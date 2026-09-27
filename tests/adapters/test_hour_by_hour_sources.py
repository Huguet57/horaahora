from pathlib import Path
from unittest.mock import Mock

import pytest
import requests

from backend.adapters.content.el_mon_casteller import ElMonCastellerRSSSource
from backend.adapters.content.revista_castells import RevistaCastellsHTMLSource
from backend.composition.providers import build_hour_by_hour_source
from backend.config import Settings

FIXTURES = Path(__file__).parents[1] / "fixtures"
REVISTA_HTML = (FIXTURES / "revista_hour_by_hour.html").read_text()
ELMON_FEED = (FIXTURES / "el_mon_casteller.xml").read_bytes()
REVISTA_URLS = [RevistaCastellsHTMLSource.URL]
ELMON_URLS = sorted(ElMonCastellerRSSSource.FEED_URLS)


@pytest.mark.parametrize(
    ("source_ids", "expected_urls"),
    [
        (("el-mon-casteller",), ELMON_URLS),
        (("revista-castells",), REVISTA_URLS),
        (("revista-castells", "el-mon-casteller"), sorted(REVISTA_URLS + ELMON_URLS)),
        ((), []),
    ],
)
def test_only_the_configured_sources_are_read(monkeypatch, source_ids, expected_urls) -> None:
    requested_urls = []

    def get(url, **kwargs):
        requested_urls.append(url)
        return Mock(text=REVISTA_HTML, content=ELMON_FEED)

    monkeypatch.setattr(requests, "get", get)

    items = build_hour_by_hour_source(Settings(hour_by_hour_sources=source_ids)).fetch()

    assert sorted(requested_urls) == expected_urls
    assert {item.source_id for item in items} == set(source_ids)


def test_an_unknown_source_stops_the_configuration() -> None:
    settings = Settings(hour_by_hour_sources=("el-mon-casteller", "diari-inventat"))

    with pytest.raises(RuntimeError, match="HOUR_BY_HOUR_SOURCES"):
        build_hour_by_hour_source(settings)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, ("el-mon-casteller",)),
        (
            " Revista-Castells, el-mon-casteller,revista-castells ",
            ("revista-castells", "el-mon-casteller"),
        ),
        ("", ()),
    ],
)
def test_the_environment_lists_the_sources(monkeypatch, value, expected) -> None:
    monkeypatch.setenv("SUPABASE_DATABASE_URL", "postgresql://user:secret@db.example/app")
    monkeypatch.setenv("RATE_LIMIT_HASH_SECRET", "test-secret")
    if value is None:
        monkeypatch.delenv("HOUR_BY_HOUR_SOURCES", raising=False)
    else:
        monkeypatch.setenv("HOUR_BY_HOUR_SOURCES", value)

    assert Settings.from_env().hour_by_hour_sources == expected
