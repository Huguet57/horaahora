from pathlib import Path
from unittest.mock import Mock

import pytest

from backend.adapters.content.combined_hour_by_hour import CombinedHourByHourSource
from backend.adapters.content.el_mon_casteller import ElMonCastellerRSSSource
from backend.adapters.content.revista_castells import RevistaCastellsHTMLSource

FIXTURES = Path(__file__).parents[1] / "fixtures"


def test_combines_publishers_without_changing_their_identity() -> None:
    revista = RevistaCastellsHTMLSource().parse(
        (FIXTURES / "revista_hour_by_hour.html").read_text()
    )
    elmon = ElMonCastellerRSSSource().parse((FIXTURES / "el_mon_casteller.xml").read_text())
    source = CombinedHourByHourSource(
        [Mock(fetch=Mock(return_value=revista)), Mock(fetch=Mock(return_value=elmon))]
    )

    assert source.fetch() == revista + elmon


@pytest.mark.parametrize("failed_first", [True, False])
def test_one_publisher_failure_does_not_block_the_other(failed_first, caplog) -> None:
    items = ElMonCastellerRSSSource().parse((FIXTURES / "el_mon_casteller.xml").read_text())
    sources = [
        Mock(fetch=Mock(side_effect=ValueError("bad feed"))),
        Mock(fetch=Mock(return_value=items)),
    ]
    source = CombinedHourByHourSource(sources if failed_first else sources[::-1])

    assert source.fetch() == items
    assert "bad feed" in caplog.text


def test_all_publisher_failures_raise_instead_of_reporting_a_successful_sync() -> None:
    source = CombinedHourByHourSource([Mock(fetch=Mock(side_effect=ValueError("bad feed")))])

    with pytest.raises(RuntimeError):
        source.fetch()
