from backend.adapters.content.group_directory import load_group_directory


def test_snapshot_is_non_empty_sorted_and_unique() -> None:
    directory = load_group_directory()

    assert len(directory.groups) > 80
    assert directory.groups == sorted(directory.groups, key=str.casefold)
    assert len(directory.groups) == len(set(directory.groups))
