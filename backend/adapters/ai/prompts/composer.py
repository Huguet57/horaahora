from dataclasses import dataclass

from backend.adapters.ai.prompts.calculator import CALCULATOR_PROMPT
from backend.adapters.ai.prompts.contest_router import CONTEST_ROUTER_PROMPT
from backend.adapters.ai.prompts.response_policy import RESPONSE_POLICY_PROMPT


@dataclass(frozen=True, slots=True)
class PromptModule:
    name: str
    content: str


INTERPRETATION_MODULES = (
    PromptModule("calculator", CALCULATOR_PROMPT),
    PromptModule("contest_router", CONTEST_ROUTER_PROMPT),
)

INTERPRETATION_PROMPT = "\n\n".join(module.content for module in INTERPRETATION_MODULES)


def compose_contest_resolution_prompt(retrieved_context: str) -> str:
    modules = (
        PromptModule("calculator", CALCULATOR_PROMPT),
        PromptModule("response_policy", RESPONSE_POLICY_PROMPT),
        PromptModule("retrieved_contest_context", retrieved_context),
    )
    return "\n\n".join(module.content for module in modules)
