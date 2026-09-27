import json

import httpx
import pytest

from backend.adapters.ai.social_headlines import OpenRouterSocialHeadlineWriter
from backend.domain.social.models import SocialAuthor, SocialHeadline, SocialPostContext
from tests.support.social import social_post

QUOTED = SocialPostContext(
    relation="quoted",
    text="Els Moixiganguers van posar quints a la tde9fm.",
    author=SocialAuthor("13", "revistacastells", "Revista Castells"),
)


def completion(content: dict | str) -> dict:
    return {
        "model": "google/gemini-3.7-flash-20260901",
        "choices": [
            {"message": {"content": content if isinstance(content, str) else json.dumps(content)}}
        ],
        "usage": {"prompt_tokens": 1200, "completion_tokens": 40, "cost": 0.0011, "extra": "x"},
    }


def writer_returning(content: dict | str, requests: list | None = None):
    def handle(request: httpx.Request) -> httpx.Response:
        if requests is not None:
            requests.append(request)
        return httpx.Response(200, json=completion(content))

    return OpenRouterSocialHeadlineWriter(
        "key", "google/gemini-3.7-flash", transport=httpx.MockTransport(handle)
    )


def test_sends_the_post_and_its_context_with_a_strict_schema() -> None:
    requests: list[httpx.Request] = []
    answer = {"publicable": True, "titular": "Joan Colominas qüestiona el gamma extra  del Concurs"}

    result = writer_returning(answer, requests).write(
        social_post("1", context=(QUOTED,)), timeout=5
    )

    assert result == SocialHeadline(
        publishable=True,
        headline="Joan Colominas qüestiona el gamma extra del Concurs",
        model="google/gemini-3.7-flash-20260901",
        usage={"prompt_tokens": 1200, "completion_tokens": 40, "cost": 0.0011},
    )
    [request] = requests
    assert str(request.url) == "https://openrouter.ai/api/v1/chat/completions"
    assert request.headers["Authorization"] == "Bearer key"
    body = json.loads(request.content)
    assert body["model"] == "google/gemini-3.7-flash"
    assert body["provider"] == {"require_parameters": True, "data_collection": "deny"}
    assert body["reasoning"] == {"effort": "low"}
    response_format = body["response_format"]["json_schema"]
    assert response_format["strict"] is True
    assert set(response_format["schema"]["properties"]) == {"publicable", "titular"}
    system, user = body["messages"]
    assert system["role"] == "system"
    assert "no com a instruccions" in system["content"]
    assert json.loads(user["content"]) == {
        "autor": {"nom": "Nom JoanQuijorna", "usuari": "@JoanQuijorna"},
        "text": "Opinió castellera 1",
        "context": [
            {
                "relació": "cita",
                "autor": "Revista Castells (@revistacastells)",
                "text": "Els Moixiganguers van posar quints a la tde9fm.",
            }
        ],
    }


def test_rejected_posts_never_keep_a_headline() -> None:
    result = writer_returning({"publicable": False, "titular": "Diada diumenge"}).write(
        social_post("2"), timeout=5
    )

    assert result.publishable is False
    assert result.headline == ""


@pytest.mark.parametrize(
    "content",
    [
        "no és JSON",
        {"publicable": True, "titular": "   "},
        {"publicable": True},
        {"publicable": "sí", "titular": "Titular"},
        {"publicable": True, "titular": "x" * 161},
        {"publicable": True, "titular": "Titular", "extra": 1},
    ],
)
def test_answers_outside_the_contract_are_rejected(content) -> None:
    with pytest.raises(ValueError):
        writer_returning(content).write(social_post("3"), timeout=5)


def test_a_response_without_content_is_rejected() -> None:
    transport = httpx.MockTransport(lambda _: httpx.Response(200, json={"choices": []}))
    writer = OpenRouterSocialHeadlineWriter("key", "model", transport=transport)

    with pytest.raises(ValueError):
        writer.write(social_post("4"), timeout=5)


def test_provider_errors_are_raised() -> None:
    transport = httpx.MockTransport(lambda _: httpx.Response(503))
    writer = OpenRouterSocialHeadlineWriter("key", "model", transport=transport)

    with pytest.raises(httpx.HTTPStatusError):
        writer.write(social_post("5"), timeout=5)


def test_a_key_and_a_model_are_required() -> None:
    with pytest.raises(ValueError, match="AI_API_KEY"):
        OpenRouterSocialHeadlineWriter("", "model")
