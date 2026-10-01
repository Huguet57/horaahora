import ast
import asyncio
import re
from pathlib import Path

import pytest

from backend.application.chat import ChatService
from backend.domain.calculator.app_prompts import APP_PROMPT_QUERIES
from backend.domain.calculator.models import (
    ChatTurn,
    Outcome,
    ParsedCastell,
    ParsedCastellQuery,
    ParsedPerformance,
)
from backend.domain.calculator.scoring import ScoringEngine
from backend.domain.calculator.table import ScoreTable

ROOT = Path(__file__).resolve().parents[2]
IOS_PROMPTS = (
    ROOT
    / "HoraAHoraApp/Packages/CastellsKit/Sources/FeatureCalculator/Views/CalculatorSupportingViews.swift"
)
ANDROID_PROMPTS = (
    ROOT
    / "android/feature/calculator/presentation/src/main/kotlin/com/ahuguet/castellsenvena"
    / "feature/calculator/presentation/CalculationPresentation.kt"
)


class UnusedModel:
    async def interpret(self, history, message, *, scenario=None):
        raise AssertionError("Un exemple de l'app no necessita el model")


class RecordingModel:
    def __init__(self) -> None:
        self.messages: list[str] = []

    async def interpret(self, history, message, *, scenario=None) -> ParsedCastellQuery:
        self.messages.append(message)
        return ParsedCastellQuery(
            intent="total",
            performances=[
                ParsedPerformance(
                    label="Actuació",
                    castells=[ParsedCastell(notation="5d9f", outcome=Outcome.UNLOADED)],
                )
            ],
        )


def make_service(model) -> ChatService:
    return ChatService(model, object(), ScoringEngine(ScoreTable.default()))


def app_prompts(path: Path, start: str) -> list[str]:
    block = path.read_text().split(start, 1)[1].split(")" if "listOf" in start else "]", 1)[0]
    return [ast.literal_eval(f'"{item}"') for item in re.findall(r'"((?:[^"\\]|\\.)*)"', block)]


def test_backend_answers_exactly_the_prompts_both_apps_suggest() -> None:
    expected = set(APP_PROMPT_QUERIES)

    assert set(app_prompts(IOS_PROMPTS, "private let prompts = [")) == expected
    assert set(app_prompts(ANDROID_PROMPTS, "val suggestions = listOf(")) == expected


@pytest.mark.parametrize(
    ("prompt", "labels", "totals"),
    [
        ("Què guanya, el 5d9f o el 4d9fa?", ["Amb 5d9f", "Amb 4d9fa"], [3125, 3285]),
        (
            "Si la Vella descarrega el 4d10fm i la Joves el 4d9net, qui guanya?",
            ["Vella", "Joves"],
            [4930, 4105],
        ),
        (
            "5d9f, 4d9fa, 3d10fm vs 3d10fm, 4d10fm i 3d9fa",
            ["Amb 5d9f", "Amb 4d10fm"],
            [10935, 12900],
        ),
    ],
)
def test_app_prompt_opening_a_conversation_skips_the_model(
    prompt: str, labels: list[str], totals: list[int]
) -> None:
    result = asyncio.run(make_service(UnusedModel()).respond([ChatTurn("user", prompt)]))

    assert result.intent == "comparison"
    assert [performance.label for performance in result.performances] == labels
    assert [performance.total for performance in result.performances] == totals


def test_app_prompt_tolerates_surrounding_whitespace() -> None:
    result = asyncio.run(
        make_service(UnusedModel()).respond(
            [ChatTurn("user", "  Què guanya, el 5d9f  o el 4d9fa? ")]
        )
    )

    assert [performance.total for performance in result.performances] == [3125, 3285]


def test_app_prompt_later_in_a_conversation_still_asks_the_model() -> None:
    model = RecordingModel()
    history = [
        ChatTurn("user", "Quant val el 5d9f?"),
        ChatTurn("assistant", "El 5de9f descarregat (3.125 punts)."),
        ChatTurn("user", "Què guanya, el 5d9f o el 4d9fa?"),
    ]

    asyncio.run(make_service(model).respond(history))

    assert model.messages == ["Què guanya, el 5d9f o el 4d9fa?"]


def test_app_prompt_with_a_scenario_still_asks_the_model() -> None:
    model = RecordingModel()
    scenario = [
        ParsedPerformance(
            label="Vella",
            castells=[ParsedCastell(notation="3d9sf", outcome=Outcome.LOADED)],
        )
    ]

    asyncio.run(
        make_service(model).respond(
            [ChatTurn("user", "Què guanya, el 5d9f o el 4d9fa?")], scenario=scenario
        )
    )

    assert model.messages == ["Què guanya, el 5d9f o el 4d9fa?"]


def test_edited_app_prompt_asks_the_model() -> None:
    model = RecordingModel()

    asyncio.run(make_service(model).respond([ChatTurn("user", "Què guanya, el 5d9f o el 4d9f?")]))

    assert model.messages == ["Què guanya, el 5d9f o el 4d9f?"]
