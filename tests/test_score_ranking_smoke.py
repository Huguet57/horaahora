import json
import subprocess

import pytest

from scripts import smoke_score_ranking_api
from scripts.smoke_score_ranking_api import SmokeCase, _post_question, _validate


def test_smoke_validation_accepts_localized_point_separators() -> None:
    case = SmokeCase(
        "highest",
        "Quin és el castell que dona més punts?",
        "contest_info",
        ("3de10sm", "6205", "7475"),
    )

    reply = _validate(
        case,
        {
            "intent": "contest_info",
            "reply": "El 3de10sm: 6.205 carregat i 7.475 descarregat.",
        },
    )

    assert reply.startswith("El 3de10sm")


def test_smoke_validation_rejects_an_unrequested_outcome() -> None:
    case = SmokeCase(
        "loaded-ranking",
        "Quin és el castell més puntuat si només queda carregat?",
        "contest_info",
        ("3de10sm", "6205"),
        ("7475",),
    )

    with pytest.raises(AssertionError, match=r"forbidden=\['7475'\]"):
        _validate(
            case,
            {
                "intent": "contest_info",
                "reply": "El 3de10sm dona 6.205 carregat i 7.475 descarregat.",
            },
        )


def test_smoke_request_can_use_the_authenticated_vercel_transport(monkeypatch) -> None:
    case = SmokeCase("highest", "Quin dona més punts?", "contest_info", ("3de10sm",))
    captured: list[str] = []

    def fake_run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        captured.extend(command)
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps({"intent": "contest_info", "reply": "3de10sm"}),
            stderr="",
        )

    monkeypatch.setattr(smoke_score_ranking_api.subprocess, "run", fake_run)

    response = _post_question("https://preview.example", case, vercel_auth=True)

    assert response["reply"] == "3de10sm"
    assert captured[:5] == [
        "vercel",
        "curl",
        "/v1/chat",
        "--deployment",
        "https://preview.example",
    ]
