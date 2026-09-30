"""The scenario is independent of the bounded, lossy prose history."""

from copy import deepcopy

import pytest

from backend.domain.calculator.models import ParsedCastellQuery
from backend.domain.contest.models import ContestKnowledgeQuery
from tests.support.application import make_test_client

SCENARIO = [
    {
        "label": "Vella",
        "castells": [
            {"notation": "3de10fm", "outcome": "loaded"},
            {"notation": "4de9fa", "outcome": "loaded"},
            {"notation": "5de9f", "outcome": "loaded"},
            {"notation": "4de8", "outcome": "unloaded"},
            {"notation": "3de8", "outcome": "unloaded"},
            {"notation": "9de9f", "outcome": "attempt"},
        ],
    },
    {"label": "Joves", "castells": [{"notation": "2de8sf", "outcome": "unloaded"}]},
]


def request_body():
    return {
        "conversation_id": "3a35386d-f0e4-49cc-86d2-18fac079645c",
        "installation_id": "scenario-test",
        "messages": [
            {"role": "assistant" if i % 2 == 0 else "user", "content": "Hola!"} for i in range(11)
        ]
        + [{"role": "user", "content": "I si el 4d9fa de la Vella és descarregat?"}],
        "scenario": deepcopy(SCENARIO),
    }


class ScenarioChatModel:
    def __init__(self, retrieve=False):
        self.retrieve = retrieve
        self.scenarios = []

    async def interpret(self, history, message, *, scenario=None):
        assert len(history) == 11
        assert all(turn.content == "Hola!" for turn in history)
        self.scenarios.append(scenario)
        if self.retrieve:
            return ParsedCastellQuery(
                intent="contest_info",
                knowledge_query=ContestKnowledgeQuery(source="rules"),
            )
        return ParsedCastellQuery(intent="total", performances=scenario or [])

    async def resolve_contest(self, history, message, context, *, scenario=None):
        self.scenarios.append(scenario)
        return ParsedCastellQuery(intent="total", performances=scenario or [])


@pytest.mark.parametrize("retrieve", [False, True])
def test_complete_scenario_reaches_both_model_stages_without_original_messages(retrieve):
    model = ScenarioChatModel(retrieve)
    response = make_test_client(chat_model=model).post("/v1/chat", json=request_body())
    assert response.status_code == 200
    assert model.scenarios[0] is not None
    assert len(model.scenarios) == (2 if retrieve else 1)
    assert all(scenario == model.scenarios[0] for scenario in model.scenarios)
    result = response.json()
    assert [p["label"] for p in result["performances"]] == ["Vella", "Joves"]
    castells = result["performances"][0]["castells"]
    assert [(c["canonical"], c["outcome"]) for c in castells] == [
        (c["notation"], c["outcome"]) for c in SCENARIO[0]["castells"]
    ]
    # All three kinds of omitted detail remain in structured results.
    assert {c["reason"] for c in castells if not c["counted"]} == {
        "loaded_limit",
        "outside_top_three",
        "attempt",
    }


@pytest.mark.parametrize(
    "invalid",
    [
        SCENARIO * 5,
        [{"label": "A", "castells": SCENARIO[0]["castells"] * 3}],
        [{"label": "A" * 101, "castells": []}],
        [{"label": "A", "castells": [{"notation": "x" * 33, "outcome": "unloaded"}]}],
        [{"label": "A", "castells": [{"notation": "3d8", "outcome": "invented"}]}],
    ],
)
def test_scenario_input_is_bounded_and_validated(invalid):
    body = request_body()
    body["scenario"] = invalid
    assert make_test_client().post("/v1/chat", json=body).status_code == 422
