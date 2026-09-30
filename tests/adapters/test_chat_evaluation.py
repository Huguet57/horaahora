from copy import deepcopy

from scripts.evaluate_chat_models import check_result, summarize


def test_context_grader_detects_lost_groups_castells_and_outcomes_including_uncounted():
    performances = [
        {
            "label": "Jove",
            "castells": [
                {"canonical": "3de10fm", "outcome": "loaded", "counted": True},
                {"canonical": "5de9f", "outcome": "unloaded", "counted": False},
            ],
        },
        {"label": "Joves", "castells": [{"canonical": "4de9sf", "outcome": "unloaded"}]},
    ]
    expected = {"intents": ["comparison"], "performances": performances}
    result = {
        "intent": "comparison",
        "performances": deepcopy(performances),
        "needs_clarification": False,
        "reply": "Un resultat de càlcul.",
    }
    assert check_result(result, expected) == []
    for change in ("group", "castell", "outcome"):
        broken = deepcopy(result)
        if change == "group":
            broken["performances"].pop()
        elif change == "castell":
            broken["performances"][0]["castells"].pop()
        else:
            broken["performances"][0]["castells"][0]["outcome"] = "unloaded"
        assert "scenario_state" in check_result(broken, expected)


def test_unfinished_scenario_does_not_pass_and_missing_cost_is_not_zero():
    run = {
        "expected_turns": 2,
        "turns": [
            {"failures": ["request_error"], "error": "ReadTimeout", "latency_s": 180, "calls": []}
        ],
    }
    summary = summarize([run])
    assert summary["passed_scenarios"] == 0
    assert summary["expected_turns"] == 2
    assert summary["passed_turns"] == 0
    assert summary["errors"] == 1
    assert summary["total_cost_usd"] is None
