import json
from unittest.mock import Mock

import pytest

from backend.config import Settings
from backend.jobs import hide_x_post


@pytest.mark.parametrize(
    "reference",
    [
        "1970000000000000001",
        "https://x.com/JoanQuijorna/status/1970000000000000001",
        "https://twitter.com/JoanQuijorna/status/1970000000000000001/?s=20",
    ],
)
def test_posts_can_be_referenced_by_id_or_link(reference: str) -> None:
    assert hide_x_post.post_id_from(reference) == "1970000000000000001"


@pytest.mark.parametrize("reference", ["https://x.com/JoanQuijorna", "https://x.com/user123", ""])
def test_other_references_are_rejected(reference: str) -> None:
    with pytest.raises(ValueError, match="post de X"):
        hide_x_post.post_id_from(reference)


@pytest.mark.parametrize(("hidden", "exit_code"), [(True, 0), (False, 1)])
def test_the_job_hides_the_post_and_reports_whether_it_existed(
    monkeypatch, capsys, hidden: bool, exit_code: int
) -> None:
    repository = Mock(hide=Mock(return_value=hidden))
    monkeypatch.setattr(hide_x_post, "build_database", lambda _: object())
    monkeypatch.setattr(hide_x_post, "build_social_post_repository", lambda _: repository)

    assert hide_x_post.hide_once(Settings(), "https://x.com/u/status/42") == exit_code

    repository.hide.assert_called_once_with("x", "42")
    assert json.loads(capsys.readouterr().out) == {
        "event": "x_post_hidden",
        "post_id": "42",
        "hidden": hidden,
    }
