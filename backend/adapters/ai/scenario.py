import json

from backend.domain.calculator.models import ParsedPerformance


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
