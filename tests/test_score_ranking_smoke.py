import pytest

from scripts.smoke_score_ranking_api import SmokeCase, _validate


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
