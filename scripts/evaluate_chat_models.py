"""Run fixed chat regressions through the real application service and OpenRouter.

Usage: OPENROUTER_API_KEY=... python -m scripts.evaluate_chat_models \
    --output /tmp/chat-evaluation.json --repetitions 3

Uses synthetic fixtures, no database, no production endpoint and no conversation sharing.
Each scenario starts afresh; subsequent turns receive the model's actual replies and
the complete last calculation, matching the mobile clients.
"""

import argparse
import asyncio
import hashlib
import json
import os
import re
import statistics
import time
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import httpx

from backend.adapters.ai.openrouter import OpenRouterChatModel
from backend.adapters.ai.prompts import INTERPRETATION_PROMPT, compose_contest_resolution_prompt
from backend.adapters.ai.schema import QueryRoutingPayload, ResolvedQueryPayload
from backend.adapters.contest.snapshot import SnapshotContestKnowledgeRepository
from backend.application.chat import ChatService
from backend.domain.calculator.models import ChatTurn, ParsedCastell, ParsedPerformance
from backend.domain.calculator.scoring import ScoringEngine
from backend.domain.calculator.table import ScoreTable

MODELS = (
    "google/gemini-3.7-flash",
    "google/gemini-3.8-flash",
    "openai/gpt-6-luna",
    "anthropic/claude-sonnet-5.5",
)
DATASET = Path(__file__).resolve().parents[1] / "tests/fixtures/chat_conversation_cases.json"


def signature(performances: list[dict]) -> dict:
    """Compare every interpreted castell, including those the scoring engine excludes."""
    return {
        p["label"].casefold().strip(): sorted((c["canonical"], c["outcome"]) for c in p["castells"])
        for p in performances
    }


def check_result(result: dict, expected: dict) -> list[str]:
    failures = []
    if result["intent"] not in expected["intents"]:
        failures.append("intent")
    if result["needs_clarification"] != expected.get("needs_clarification", False):
        failures.append("clarification")
    if "performances" in expected:
        actual_state = signature(result["performances"])
        expected_state = signature(expected["performances"])
        # An independent single-castell lookup has no user-supplied participant name.
        # The generated label is not part of its meaning; named comparisons stay exact.
        if expected["intents"] == ["lookup"] or expected.get("ignore_labels", False):
            matches = sorted(actual_state.values()) == sorted(expected_state.values())
        else:
            matches = actual_state == expected_state
        if not matches:
            failures.append("scenario_state")
    if "totals" in expected:
        actual = {p["label"].casefold(): p["total"] for p in result["performances"]}
        wanted = {label.casefold(): total for label, total in expected["totals"].items()}
        if actual != wanted:
            failures.append("totals")
    if "counted" in expected:
        actual = {
            p["label"].casefold(): sorted(
                [c["canonical"], c["outcome"]] for c in p["castells"] if c["counted"]
            )
            for p in result["performances"]
        }
        wanted = {
            label.casefold(): sorted(castells) for label, castells in expected["counted"].items()
        }
        if actual != wanted:
            failures.append("counted")
    if "presentation" in expected:
        presentation = result.get("presentation")
        wanted = expected["presentation"]
        if (
            not presentation
            or presentation["outcome"] != wanted["outcome"]
            or [row["notation"] for row in presentation["rows"]] != wanted["notations"]
        ):
            failures.append("presentation")
    if not result["reply"].strip() or result["reply"] == "Quin castell vols calcular?":
        failures.append("generic_reply")
    reply = result["reply"].casefold()
    for alternatives in expected.get("reply_contains_any", []):
        if not any(term.casefold() in reply for term in alternatives):
            failures.append("reply_content")
    for term in expected.get("reply_excludes", []):
        if term.casefold() in reply:
            failures.append("reply_forbidden")
    for pattern in expected.get("reply_forbids_patterns", []):
        if re.search(pattern, reply):
            failures.append("reply_forbidden_pattern")
    return failures


def fingerprint() -> str:
    inputs = [
        INTERPRETATION_PROMPT,
        compose_contest_resolution_prompt(""),
        json.dumps(QueryRoutingPayload.model_json_schema(), sort_keys=True),
        json.dumps(ResolvedQueryPayload.model_json_schema(), sort_keys=True),
    ]
    return hashlib.sha256("\n".join(inputs).encode()).hexdigest()


async def evaluate_scenario(model_name: str, scenario: dict, *, effort: str = "low") -> dict:
    calls = []

    async def record_usage(response: httpx.Response) -> None:
        await response.aread()
        if not response.is_success:
            calls.append({"status": response.status_code})
            return
        payload = response.json()
        calls.append(
            {
                "model": payload.get("model"),
                "provider": payload.get("provider"),
                "usage": payload.get("usage"),
                "finish_reasons": [c.get("finish_reason") for c in payload.get("choices", [])],
                "response_content": [
                    c.get("message", {}).get("content") for c in payload.get("choices", [])
                ],
            }
        )

    key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("AI_API_KEY")
    if not key:
        raise ValueError("OPENROUTER_API_KEY or AI_API_KEY is required")
    async with httpx.AsyncClient(
        headers={"Authorization": f"Bearer {key}"},
        timeout=180,
        event_hooks={"response": [record_usage]},
    ) as client:
        model = OpenRouterChatModel(key, model_name, client=client, reasoning_effort=effort)
        service = ChatService(
            model, SnapshotContestKnowledgeRepository.default(), ScoringEngine(ScoreTable.default())
        )
        history = [ChatTurn(**turn) for turn in scenario.get("history", [])]
        saved_scenario = []
        turns = []
        for step in scenario["steps"]:
            history.append(ChatTurn("user", step["message"]))
            start = time.monotonic()
            call_offset = len(calls)
            try:
                response = await service.respond(history[-12:], scenario=saved_scenario)
                if response.performances:
                    saved_scenario = [
                        ParsedPerformance(
                            p.label,
                            [ParsedCastell(c.canonical or c.input, c.outcome) for c in p.castells],
                        )
                        for p in response.performances
                    ]
                result = asdict(response)
                failures = check_result(result, step["expected"])
                history.append(ChatTurn("assistant", response.reply))
                turn = {"result": result, "failures": failures}
            except Exception as error:
                turn = {"error": type(error).__name__, "failures": ["request_error"]}
                # An unavailable or invalid answer cannot supply context for the next turn.
                turns.append(
                    dict(
                        turn,
                        message=step["message"],
                        latency_s=time.monotonic() - start,
                        calls=calls[call_offset:],
                    )
                )
                break
            turns.append(
                dict(
                    turn,
                    message=step["message"],
                    latency_s=time.monotonic() - start,
                    calls=calls[call_offset:],
                )
            )
    return {
        "id": scenario["id"],
        "category": scenario["category"],
        "turns": turns,
        "expected_turns": len(scenario["steps"]),
    }


def summarize(runs: list[dict]) -> dict:
    turns = [turn for run in runs for turn in run["turns"]]
    costs = [
        call.get("usage", {}).get("cost")
        for turn in turns
        for call in turn["calls"]
        if call.get("usage")
    ]
    return {
        "scenarios": len(runs),
        "passed_scenarios": sum(
            len(run["turns"]) == run["expected_turns"]
            and all(not turn["failures"] for turn in run["turns"])
            for run in runs
        ),
        "expected_turns": sum(run["expected_turns"] for run in runs),
        "completed_turns": len(turns),
        "passed_turns": sum(not turn["failures"] for turn in turns),
        "errors": sum("error" in turn for turn in turns),
        "median_latency_s": statistics.median(t["latency_s"] for t in turns) if turns else None,
        "total_cost_usd": (
            sum(costs)
            if costs
            and len(costs) == sum(len(t["calls"]) for t in turns)
            and all(c is not None for c in costs)
            and not any("error" in t for t in turns)
            else None
        ),
        "calls": sum(len(t["calls"]) for t in turns),
    }


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, default=DATASET)
    parser.add_argument("--repetitions", type=int, choices=range(1, 6), default=3)
    parser.add_argument("--models", nargs="+", choices=MODELS, default=list(MODELS))
    parser.add_argument("--effort", choices=["low", "medium", "high"], default="low")
    args = parser.parse_args()
    raw = args.dataset.read_bytes()
    dataset = json.loads(raw)
    gate = asyncio.Semaphore(4)

    async def run(model, scenario, repetition):
        async with gate:
            result = await evaluate_scenario(model, scenario, effort=args.effort)
            return {"model": model, "repetition": repetition, **result}

    runs = await asyncio.gather(
        *[
            run(model, scenario, repetition)
            for repetition in range(args.repetitions)
            for scenario in dataset["scenarios"]
            for model in args.models
        ]
    )
    report = {
        "evaluated_at": datetime.now(UTC).isoformat(),
        "effort": args.effort,
        "prompt_schema_sha256": fingerprint(),
        "dataset_sha256": hashlib.sha256(raw).hexdigest(),
        "metrics": {
            model: summarize([r for r in runs if r["model"] == model]) for model in args.models
        },
        "runs": runs,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report["metrics"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
