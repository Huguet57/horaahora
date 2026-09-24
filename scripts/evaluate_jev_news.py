"""Evaluate fixed public-news cases with Jev, without database access or push delivery.

Run: uv run --env-file .env.jev.local python -m scripts.evaluate_jev_news \
    --output /tmp/jev-evaluation.json --repetitions 3
"""

import argparse
import hashlib
import json
import os
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

from backend.adapters.ai.jev import CRITERIA_VERSION, JevNewsInterestClassifier
from backend.adapters.content.group_directory import load_group_directory
from backend.domain.notifications.interest import NewsContent

DEFAULT_DATASET = Path(__file__).parents[1] / "tests/fixtures/jev_editorial_cases.json"


def evaluate_case(classifier, case, groups, repetitions):
    content = NewsContent(**case["content"]) if case.get("content") else None
    runs = []
    for _ in range(repetitions):
        started = time.monotonic()
        try:
            result = classifier.classify(
                case["title"], case["summary"], groups, content=content, timeout=8
            )
            run = {
                "level": result.level.value,
                "group_keys": sorted(result.group_keys),
                "probabilities": result.probabilities,
                "input": result.input_metadata,
                "model": result.model,
                "usage": result.usage,
            }
        except Exception as error:
            # Deliberate repetitions are independent observations, never retries.
            run = {"error": type(error).__name__}
        run["latency_ms"] = round((time.monotonic() - started) * 1000)
        runs.append(run)
    return {"id": case["id"], "title": case["title"], "expected": case["expected"], "runs": runs}


def summarize(results):
    levels = ("low", "medium", "high")
    all_runs = [(case, run) for case in results for run in case["runs"]]
    valid = [(case, run) for case, run in all_runs if "level" in run]
    confusion = {level: dict.fromkeys(levels, 0) for level in levels}
    for case, run in valid:
        confusion[case["expected"]][run["level"]] += 1
    return {
        "cases": len(results),
        "calls": len(all_runs),
        "errors": len(all_runs) - len(valid),
        "correct": sum(case["expected"] == run["level"] for case, run in valid),
        "false_high": sum(
            case["expected"] != "high" and run["level"] == "high" for case, run in valid
        ),
        "missed_high": sum(
            case["expected"] == "high" and run["level"] != "high" for case, run in valid
        ),
        "unstable_cases": sum(
            len({r["level"] for r in case["runs"] if "level" in r}) > 1 for case in results
        ),
        "counts": dict(Counter(run["level"] for _, run in valid)),
        "confusion_expected_to_actual": confusion,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, choices=range(1, 6), default=1)
    args = parser.parse_args()
    raw = args.dataset.read_bytes()
    dataset = json.loads(raw)
    classifier = JevNewsInterestClassifier(os.environ["JEV_API_KEY"], "jev-1.13.0")
    groups = load_group_directory().groups
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(
            pool.map(
                lambda case: evaluate_case(classifier, case, groups, args.repetitions),
                dataset["cases"],
            )
        )
    metrics = summarize(results)
    report = {
        "evaluated_at": datetime.now(UTC).isoformat(),
        "model": classifier.model,
        "criteria_version": CRITERIA_VERSION,
        "dataset_version": dataset["version"],
        "dataset_sha256": hashlib.sha256(raw).hexdigest(),
        "metrics": metrics,
        "cases": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    print(args.output)
    # Evaluation mismatches stay visible; this is a live diagnostic, not a CI test.
    return int(metrics["correct"] != metrics["calls"])


if __name__ == "__main__":
    raise SystemExit(main())
