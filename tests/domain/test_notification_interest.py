import pytest

from backend.domain.notifications.interest import (
    GroupSelection,
    InterestLevel,
    effective_interest,
    group_key,
    qualifies,
)


@pytest.mark.parametrize(
    "base,matched,expected",
    [
        ("low", False, "low"),
        ("low", True, "medium"),
        ("medium", False, "medium"),
        ("medium", True, "high"),
        ("high", False, "high"),
        ("high", True, "high"),
    ],
)
def test_personalized_interest_matrix(base, matched, expected):
    selection = GroupSelection("custom", frozenset({"a", "b"}))
    groups = {"a", "b"} if matched else {"c"}
    assert effective_interest(InterestLevel(base), groups, selection).value == expected
    for minimum in InterestLevel:
        assert qualifies(InterestLevel(base), groups, minimum, selection) == (
            InterestLevel(expected).rank >= minimum.rank
        )


@pytest.mark.parametrize("selection", [GroupSelection(), GroupSelection("custom")])
def test_all_or_empty_selection_does_not_promote(selection):
    assert effective_interest(InterestLevel.LOW, {"a"}, selection) is InterestLevel.LOW


def test_group_keys_match_agenda_normalization():
    assert group_key("  COLLA  d’Al·lots  ") == "colla d'al·lots"
    assert group_key("Ｍｉｎｙｏｎｓ de Terrássa") == "minyons de terrassa"
