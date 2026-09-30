import json

from backend.adapters.ai.schema import written_text
from backend.domain.calculator.models import ChatTurn, ParsedPerformance

HISTORY_TURNS = 11


def history_messages(history: list[ChatTurn]) -> list[dict[str, str]]:
    """Send the latest turns, with earlier replies cleaned as the apps now store them.

    Conversations saved before replies were cleaned can still hold a stray tail, and a tail
    in the history leads the model to repeat it.
    """
    return [
        {
            "role": turn.role,
            "content": written_text(turn.content) if turn.role == "assistant" else turn.content,
        }
        for turn in history[-HISTORY_TURNS:]
    ]


def message_with_scenario(message: str, scenario: list[ParsedPerformance] | None) -> str:
    """Attach calculation inputs to the current turn so history trimming cannot drop them.

    Keep client-provided data at user priority, outside the system instructions. No scores
    or counted flags are reused: the scoring engine derives them again after each edit.
    """
    if not scenario:
        return message
    state = [
        {
            "nom": performance.label,
            "castells": [
                {
                    "notació": castell.notation,
                    "resultat": {
                        "unloaded": "descarregat",
                        "loaded": "carregat",
                        "attempt": "intent",
                    }[castell.outcome.value],
                }
                for castell in performance.castells
            ],
        }
        for performance in scenario
    ]
    return json.dumps(
        {"escenari_vigent": state, "missatge_actual": message},
        ensure_ascii=False,
        separators=(",", ":"),
    )
