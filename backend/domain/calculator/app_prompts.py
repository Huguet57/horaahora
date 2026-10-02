"""Interpretations of the prompts the apps suggest, so they need no model call.

Only the interpretation is fixed: the scoring engine still computes every answer,
so a change to the score table reaches these replies too.
"""

from backend.domain.calculator.models import (
    Outcome,
    ParsedCastell,
    ParsedCastellQuery,
    ParsedPerformance,
)


def _performance(label: str, *notations: str) -> ParsedPerformance:
    return ParsedPerformance(
        label=label,
        castells=[
            ParsedCastell(notation=notation, outcome=Outcome.UNLOADED) for notation in notations
        ],
    )


# Keep in sync with PromptSuggestions (iOS) and CalculatorPrompts (Android); a test checks it.
APP_PROMPT_QUERIES: dict[str, ParsedCastellQuery] = {
    "Què guanya, el 5d9f o el 4d9fa?": ParsedCastellQuery(
        intent="comparison",
        performances=[_performance("5d9f", "5d9f"), _performance("4d9fa", "4d9fa")],
    ),
    "Si la Vella descarrega el 4d10fm i la Joves el 4d9net, qui guanya?": ParsedCastellQuery(
        intent="comparison",
        performances=[_performance("Vella", "4d10fm"), _performance("Joves", "4d9net")],
    ),
    "5d9f, 4d9fa, 3d10fm vs 3d10fm, 4d10fm i 3d9fa": ParsedCastellQuery(
        intent="comparison",
        performances=[
            _performance("A", "5d9f", "4d9fa", "3d10fm"),
            _performance("B", "3d10fm", "4d10fm", "3d9fa"),
        ],
    ),
}

_BY_COMPACT_TEXT = {" ".join(prompt.split()): query for prompt, query in APP_PROMPT_QUERIES.items()}


def app_prompt_query(message: str) -> ParsedCastellQuery | None:
    return _BY_COMPACT_TEXT.get(" ".join(message.split()))
