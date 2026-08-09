from backend.adapters.ai.prompts.calculator import CALCULATOR_PROMPT
from backend.adapters.ai.prompts.knowledge import (
    CONTEST_RESULTS_PROMPT,
    CONTEST_RULES_PROMPT,
)
from backend.adapters.ai.prompts.policy import RESPONSE_POLICY_PROMPT

PROMPT_MODULES = (
    CALCULATOR_PROMPT,
    CONTEST_RULES_PROMPT,
    CONTEST_RESULTS_PROMPT,
    RESPONSE_POLICY_PROMPT,
)
SYSTEM_PROMPT = "\n\n".join(PROMPT_MODULES)

__all__ = [
    "CALCULATOR_PROMPT",
    "CONTEST_RESULTS_PROMPT",
    "CONTEST_RULES_PROMPT",
    "PROMPT_MODULES",
    "RESPONSE_POLICY_PROMPT",
    "SYSTEM_PROMPT",
]
