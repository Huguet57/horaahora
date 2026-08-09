from dataclasses import dataclass

from backend.adapters.ai.prompts.calculator import CALCULATOR_PROMPT
from backend.adapters.ai.prompts.contest_results import CONTEST_RESULTS_PROMPT
from backend.adapters.ai.prompts.contest_rules import CONTEST_RULES_PROMPT
from backend.adapters.ai.prompts.response_policy import RESPONSE_POLICY_PROMPT


@dataclass(frozen=True, slots=True)
class PromptModule:
    name: str
    content: str


PROMPT_MODULES = (
    PromptModule("calculator", CALCULATOR_PROMPT),
    PromptModule("contest_rules", CONTEST_RULES_PROMPT),
    PromptModule("contest_results", CONTEST_RESULTS_PROMPT),
    PromptModule("response_policy", RESPONSE_POLICY_PROMPT),
)

SYSTEM_PROMPT = "\n\n".join(module.content for module in PROMPT_MODULES)
