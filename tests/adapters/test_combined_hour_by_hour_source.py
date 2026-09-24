from unittest.mock import Mock

import pytest

from backend.adapters.content.combined_hour_by_hour import CombinedHourByHourSource
from tests.support.hour_by_hour import hour_item


def test_combines_publishers_without_changing_their_identity() -> None:
    first = [hour_item("shared-id", source_id="publisher-a")]
    second = [hour_item("shared-id", source_id="publisher-b")]
    source = CombinedHourByHourSource(
        [Mock(fetch=Mock(return_value=first)), Mock(fetch=Mock(return_value=second))]
    )

    assert source.fetch() == first + second


@pytest.mark.parametrize("failed_first", [True, False])
def test_one_publisher_failure_does_not_block_the_other(failed_first, caplog) -> None:
    items = [hour_item("one")]
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


def test_an_empty_successful_publisher_is_not_treated_as_a_failure() -> None:
    source = CombinedHourByHourSource(
        [Mock(fetch=Mock(side_effect=ValueError("bad feed"))), Mock(fetch=Mock(return_value=[]))]
    )

    assert source.fetch() == []
