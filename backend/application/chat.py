from backend.domain.calculator.app_prompts import app_prompt_query
from backend.domain.calculator.models import CalculationResult, ChatTurn, ParsedPerformance
from backend.domain.calculator.ports import ChatModel
from backend.domain.calculator.scoring import ScoringEngine
from backend.domain.contest.ports import ContestKnowledgeRepository


class ChatService:
    def __init__(
        self,
        chat_model: ChatModel,
        contest_repository: ContestKnowledgeRepository,
        scoring_engine: ScoringEngine,
    ) -> None:
        self.chat_model = chat_model
        self.contest_repository = contest_repository
        self.scoring_engine = scoring_engine

    async def respond(
        self, history: list[ChatTurn], *, scenario: list[ParsedPerformance] | None = None
    ) -> CalculationResult:
        if not history or history[-1].role != "user":
            raise ValueError("L'últim missatge ha de ser de l'usuari")
        spell_out = self.scoring_engine.normalizer.spell_out_loaded_markers
        history = [
            ChatTurn(turn.role, spell_out(turn.content)) if turn.role == "user" else turn
            for turn in history
        ]
        current = history[-1]
        # An app suggestion that opens a conversation has a fixed interpretation.
        query = app_prompt_query(current.content) if len(history) == 1 and not scenario else None
        if query is None:
            query = await self.chat_model.interpret(
                history[:-1], current.content, scenario=scenario
            )
        presentation = None
        if query.intent == "contest_info":
            if query.knowledge_query is None:
                raise ValueError("La consulta informativa del Concurs és buida")
            knowledge_query = query.knowledge_query
            context = self.contest_repository.retrieve(knowledge_query)
            presentation = (
                self.contest_repository.score_presentation(knowledge_query)
                if knowledge_query.source == "scores"
                else None
            )
            query = await self.chat_model.resolve_contest(
                history[:-1],
                current.content,
                context,
                scenario=scenario,
            )
        if query.intent in {"contest_info", "conversation", "unsupported"}:
            if not query.answer or not query.answer.strip():
                raise ValueError("La resposta informativa o conversacional és buida")
            return CalculationResult(
                reply=query.answer,
                intent=query.intent,
                performances=[],
                winner_label=None,
                warnings=[],
                needs_clarification=False,
                presentation=presentation if query.intent == "contest_info" else None,
            )
        return self.scoring_engine.calculate(query)
