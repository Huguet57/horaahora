import json

from backend.domain.notifications.interest import InterestLevel
from scripts.evaluate_jev_news import DEFAULT_DATASET, evaluate_case, summarize


def test_editorial_fixture_is_complete_and_preserves_agreed_examples():
    cases = json.loads(DEFAULT_DATASET.read_text())["cases"]
    assert len(cases) == len({case["id"] for case in cases}) == 40
    for case in cases:
        assert case["title"] and case["summary"]
        assert InterestLevel(case["expected"])
        if content := case.get("content"):
            assert content["text"] and content["url"].startswith("https://")
            assert content["role"] in {"article_body", "linked_context"}
    expected = {case["id"]: case["expected"] for case in cases}
    assert expected["news-047"] == "medium"  # Seasonal results at Misericòrdia.
    assert expected["news-048"] == "medium"  # Euskadi's new rehearsal venue.
    assert expected["news-056"] == "medium"  # Accepted short Quarts Amunt announcement.
    assert expected["news-010"] == "high"  # Historic Santa Tecla performances.
    assert expected["news-077"] == "high"  # Announced first-ever attempts.


def test_evaluation_counts_errors_false_high_and_missed_high_separately():
    results = [
        {"expected": "medium", "runs": [{"level": "high"}, {"level": "medium"}]},
        {"expected": "high", "runs": [{"level": "medium"}, {"error": "TimeoutError"}]},
    ]
    metrics = summarize(results)
    assert metrics["cases"] == 2
    assert metrics["calls"] == 4
    assert metrics["correct"] == metrics["errors"] == 1
    assert metrics["false_high"] == metrics["missed_high"] == 1
    assert metrics["unstable_cases"] == 1
    assert metrics["confusion_expected_to_actual"]["high"]["medium"] == 1


def test_evaluation_records_provider_errors_without_exception_details():
    class FailingClassifier:
        def classify(self, *args, **kwargs):
            raise RuntimeError("Sensitive request details")

    case = {"id": "test", "title": "T", "summary": "S", "expected": "low"}
    result = evaluate_case(FailingClassifier(), case, [], 1)
    assert result["runs"][0]["error"] == "RuntimeError"
    assert "Sensitive" not in json.dumps(result)
