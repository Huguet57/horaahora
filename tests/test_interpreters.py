import asyncio

from backend.adapters.ai.local import RegexQueryInterpreter
from backend.domain.models import Outcome


def test_interprets_or_comparison() -> None:
    query = asyncio.run(RegexQueryInterpreter().interpret([], "Què guanya el 5d9f o el 4d9fa?"))

    assert [performance.label for performance in query.performances] == ["Amb 5d9f", "Amb 4d9fa"]
    assert [performance.castells[0].notation for performance in query.performances] == ["5d9f", "4d9fa"]
    assert all(performance.castells[0].outcome is Outcome.UNLOADED for performance in query.performances)


def test_interprets_named_groups() -> None:
    query = asyncio.run(
        RegexQueryInterpreter().interpret(
            [],
            "Si la Vella descarrega el 4d10fm i la Joves el 4d9net, qui guanya",
        )
    )

    assert [performance.label for performance in query.performances] == ["Vella", "Joves"]
    assert [performance.castells[0].notation for performance in query.performances] == ["4d10fm", "4d9net"]


def test_interprets_vs_lists() -> None:
    query = asyncio.run(
        RegexQueryInterpreter().interpret(
            [],
            "5d9f, 4d9fa, 3d10fm vs 3d10fm, 4d10fm i 3d9fa",
        )
    )

    assert [len(performance.castells) for performance in query.performances] == [3, 3]
    assert [performance.label for performance in query.performances] == ["Amb 5d9f", "Amb 4d10fm"]


def test_interprets_t_as_torre_notation() -> None:
    query = asyncio.run(RegexQueryInterpreter().interpret([], "td8sf o 4d9fp?"))

    assert [performance.castells[0].notation for performance in query.performances] == [
        "td8sf",
        "4d9fp",
    ]
