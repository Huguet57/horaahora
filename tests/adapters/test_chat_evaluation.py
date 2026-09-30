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


def test_lookup_grader_ignores_generated_label_but_rejects_stale_participants():
    castell = {"canonical": "5de9f", "outcome": "unloaded"}
    expected = {"intents": ["lookup"], "performances": [{"label": "A", "castells": [castell]}]}
    result = {
        "intent": "lookup",
        "needs_clarification": False,
        "reply": "El 5de9f val 3.125 punts.",
        "performances": [{"label": "Amb 5d9f", "castells": [castell]}],
    }
    assert check_result(result, expected) == []
    result["performances"].append({"label": "Joves", "castells": [castell]})
    assert "scenario_state" in check_result(result, expected)


def test_extended_grader_checks_totals_counted_castells_and_ranking_rows():
    result = {
        "intent": "total",
        "needs_clarification": False,
        "reply": "Una actuació.",
        "performances": [
            {
                "label": "A",
                "total": 845,
                "castells": [
                    {"canonical": "4de8", "outcome": "unloaded", "counted": True},
                    {"canonical": "3de7", "outcome": "attempt", "counted": False},
                ],
            }
        ],
        "presentation": None,
    }
    expected = {
        "intents": ["total"],
        "totals": {"A": 845},
        "counted": {"A": [["4de8", "unloaded"]]},
    }
    assert check_result(result, expected) == []
    result["performances"][0]["total"] = 1260
    result["performances"][0]["castells"][1]["counted"] = True
    assert check_result(result, expected) == ["totals", "counted"]
    assert "presentation" in check_result(
        result,
        {"intents": ["total"], "presentation": {"outcome": "both", "notations": ["3de10sm"]}},
    )


def test_extended_grader_handles_unnamed_comparisons_and_forbidden_claims():
    result = {
        "intent": "comparison",
        "needs_clarification": False,
        "reply": "Un 80% segur.",
        "performances": [
            {"label": "Amb 4de8", "castells": [{"canonical": "4de8", "outcome": "unloaded"}]}
        ],
    }
    expected = {
        "intents": ["comparison"],
        "ignore_labels": True,
        "performances": [
            {"label": "A", "castells": [{"canonical": "4de8", "outcome": "unloaded"}]}
        ],
        "reply_forbids_patterns": [r"\d+\s*%"],
    }
    assert check_result(result, expected) == ["reply_forbidden_pattern"]
