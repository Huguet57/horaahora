import httpx
import pytest

from backend.adapters.ai.jev import JevNewsInterestClassifier
from backend.domain.notifications.interest import InterestLevel


def response():
    return {
        "model": "jev-1.13.0",
        "answers": {
            "interest": {
                "type": "choice",
                "choice": "medium",
                "confidence": 0.9,
                "probabilities": {"low": 0.05, "medium": 0.9, "high": 0.05},
            },
            "group_0": {"type": "noul", "noul": 0.8},
            "group_1": {"type": "noul", "noul": 0.79},
        },
        "usage": {"input_tokens": 100, "output_tokens": 20},
    }


def test_sends_one_typed_request_and_uses_inclusive_group_threshold():
    requests = []

    def handle(request):
        import json

        requests.append(json.loads(request.content))
        assert request.headers["Authorization"] == "Bearer test-secret"
        assert str(request.url) == "https://api.typesafe.ai/v1/systemone"
        return httpx.Response(200, json=response())

    classifier = JevNewsInterestClassifier("test-secret", transport=httpx.MockTransport(handle))
    result = classifier.classify(
        "Els Verds estrenen castell",
        "Resultats destacats",
        ["Castellers de Vilafranca", "Minyons de Terrassa"],
        timeout=2,
    )
    assert result.level is InterestLevel.MEDIUM
    assert result.group_keys == frozenset({"castellers de vilafranca"})
    assert result.usage["input_tokens"] == 100
    assert len(requests) == 1
    assert requests[0]["model"] == "jev-1.13.0"
    assert "Verds" in str(requests[0]["questions"]["group_0"])
    assert set(requests[0]["state"]) == {"title", "summary"}


@pytest.mark.parametrize(
    "mutation",
    [
        lambda r: r["answers"].pop("group_1"),
        lambda r: r["answers"]["interest"].update(choice="urgent"),
        lambda r: r["answers"]["group_0"].update(noul=1.1),
        lambda r: r["answers"]["interest"].update(confidence=float("nan")),
    ],
)
def test_malformed_responses_are_rejected(mutation):
    payload = response()
    mutation(payload)
    transport = httpx.MockTransport(
        lambda _: httpx.Response(200, content=__import__("json").dumps(payload))
    )
    with pytest.raises(ValueError):
        JevNewsInterestClassifier("key", transport=transport).classify(
            "T", "S", ["a", "b"], timeout=1
        )


def test_provider_failure_is_not_retried():
    calls = []

    def handle(request):
        calls.append(request)
        return httpx.Response(429)

    with pytest.raises(httpx.HTTPStatusError):
        JevNewsInterestClassifier("key", transport=httpx.MockTransport(handle)).classify(
            "T", "S", [], timeout=1
        )
    assert len(calls) == 1
