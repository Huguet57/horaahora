import asyncio
import json

import httpx
import pytest

from backend.adapters.ai.anthropic import AnthropicChatModel
from backend.adapters.ai.openai import OpenAIChatModel
from backend.adapters.ai.openrouter import OpenRouterChatModel
from backend.domain.calculator.models import ChatTurn, Outcome, ParsedCastell, ParsedPerformance


@pytest.mark.parametrize("adapter", [OpenRouterChatModel, OpenAIChatModel, AnthropicChatModel])
@pytest.mark.parametrize("resolve", [False, True])
def test_scenario_is_sent_with_current_turn_after_history_trimming(adapter, resolve):
    requests = []
    answer = {
        "intent": "conversa",
        "actuacions": [],
        "aclariment": None,
        "resposta": "Hola!",
    }
    if not resolve:
        answer["consulta_concurs"] = None

    def handler(request):
        body = json.loads(request.content)
        requests.append(body)
        if adapter is AnthropicChatModel:
            payload = {
                "content": [{"type": "tool_use", "name": body["tools"][0]["name"], "input": answer}]
            }
        elif adapter is OpenAIChatModel:
            payload = {
                "output": [{"content": [{"type": "output_text", "text": json.dumps(answer)}]}]
            }
        else:
            payload = {"choices": [{"message": {"content": json.dumps(answer)}}]}
        return httpx.Response(200, json=payload)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    model = adapter("test-key", "test-model", client=client)
    history = [ChatTurn("user", "original discarded")] + [ChatTurn("assistant", "Hola!")] * 15
    scenario = [ParsedPerformance("Vella", [ParsedCastell("5de9f", Outcome.ATTEMPT)])]
    if resolve:
        asyncio.run(
            model.resolve_contest(history, "I descarregat?", "Normativa", scenario=scenario)
        )
    else:
        asyncio.run(model.interpret(history, "I descarregat?", scenario=scenario))
    asyncio.run(client.aclose())

    body = requests[0]
    messages = body["input"] if adapter is OpenAIChatModel else body["messages"]
    assert "original discarded" not in json.dumps(messages)
    content = json.loads(messages[-1]["content"])
    assert content == {
        "escenari_vigent": [
            {"nom": "Vella", "castells": [{"notació": "5de9f", "resultat": "intent"}]}
        ],
        "missatge_actual": "I descarregat?",
    }
    assert messages[-1]["role"] == "user"
