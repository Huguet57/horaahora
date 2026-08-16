from backend.domain.calculator.models import CalculationResult, ChatTurn
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

    async def respond(self, history: list[ChatTurn]) -> CalculationResult:
        if not history or history[-1].role != "user":
            raise ValueError("L'últim missatge ha de ser de l'usuari")
        current = history[-1]
        query = await self.chat_model.interpret(history[:-1], current.content)
        if query.intent == "contest_info":
            if query.knowledge_query is None:
                raise ValueError("La consulta informativa del Concurs és buida")
            context = self.contest_repository.retrieve(query.knowledge_query)
            query = await self.chat_model.resolve_contest(
                history[:-1],
                current.content,
                context,
            )
            if query.intent == "contest_info":
                if not query.answer:
                    raise ValueError("La resposta informativa del Concurs és buida")
                return CalculationResult(
                    reply=query.answer,
                    intent=query.intent,
                    performances=[],
                    winner_label=None,
                    warnings=[],
                    needs_clarification=False,
                )
        return self.scoring_engine.calculate(query)
