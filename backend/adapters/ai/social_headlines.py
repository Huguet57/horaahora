import json

import httpx
from pydantic import Field, StrictBool, StrictStr, ValidationError

from backend.adapters.ai.openrouter import openrouter_schema
from backend.adapters.ai.prompts.social_headline import SOCIAL_HEADLINE_PROMPT
from backend.adapters.ai.schema import StrictPayloadModel
from backend.domain.social.models import SocialHeadline, SocialPost, SocialPostContext

_RELATIONS = {"quoted": "cita", "replied_to": "respon"}
_USAGE_FIELDS = {"prompt_tokens", "completion_tokens", "total_tokens", "cost"}


class SocialHeadlinePayload(StrictPayloadModel):
    publicable: StrictBool
    titular: StrictStr = Field(max_length=160)


class OpenRouterSocialHeadlineWriter:
    """Decide whether a popular post is worth publishing and write its headline."""

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str | None = None,
        *,
        reasoning_effort: str = "low",
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not api_key or not model:
            raise ValueError("AI_API_KEY i AI_MODEL són obligatoris per escriure titulars")
        self.api_key = api_key
        self.model = model
        self.base_url = (base_url or "https://openrouter.ai/api").rstrip("/")
        self.reasoning_effort = reasoning_effort
        self.transport = transport

    def write(self, post: SocialPost, *, timeout: float) -> SocialHeadline:
        request = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SOCIAL_HEADLINE_PROMPT},
                {"role": "user", "content": post_prompt(post)},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "titular_hora_a_hora",
                    "strict": True,
                    "schema": openrouter_schema(SocialHeadlinePayload.model_json_schema()),
                },
            },
            "provider": {"require_parameters": True, "data_collection": "deny"},
            "usage": {"include": True},
            "reasoning": {"effort": self.reasoning_effort},
        }
        with httpx.Client(
            transport=self.transport,
            timeout=timeout,
            headers={"Authorization": f"Bearer {self.api_key}"},
        ) as client:
            response = client.post(f"{self.base_url}/v1/chat/completions", json=request)
            response.raise_for_status()
            payload = response.json()
        try:
            content = payload["choices"][0]["message"]["content"]
            answer = SocialHeadlinePayload.model_validate_json(content)
        except (KeyError, IndexError, TypeError, ValidationError) as error:
            raise ValueError("El model no ha retornat un titular vàlid") from error
        headline = " ".join(answer.titular.split()) if answer.publicable else ""
        if answer.publicable and not headline:
            raise ValueError("Un post publicable necessita titular")
        usage = payload.get("usage") or {}
        return SocialHeadline(
            publishable=answer.publicable,
            headline=headline,
            model=payload.get("model") or self.model,
            usage={
                key: value
                for key, value in usage.items()
                if key in _USAGE_FIELDS and isinstance(value, int | float)
            },
        )


def post_prompt(post: SocialPost) -> str:
    return json.dumps(
        {
            "autor": {"nom": post.author.name, "usuari": f"@{post.author.username}"},
            "text": post.text,
            "context": [_context(context) for context in post.context],
        },
        ensure_ascii=False,
    )


def _context(context: SocialPostContext) -> dict[str, str]:
    item = {"relació": _RELATIONS.get(context.relation, context.relation)}
    if context.author is not None:
        item["autor"] = f"{context.author.name} (@{context.author.username})"
    item["text"] = context.text
    return item
