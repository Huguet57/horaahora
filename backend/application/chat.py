from backend.domain.calculator.models import CalculationResult, ChatTurn
from backend.domain.calculator.ports import QueryInterpreter
from backend.domain.calculator.scoring import ScoringEngine


class ChatService:
    def __init__(self, interpreter: QueryInterpreter, scoring_engine: ScoringEngine) -> None:
        self.interpreter = interpreter
        self.scoring_engine = scoring_engine

    async def respond(self, history: list[ChatTurn]) -> CalculationResult:
        if not history or history[-1].role != "user":
            raise ValueError("L'últim missatge ha de ser de l'usuari")
        current = history[-1]
        query = await self.interpreter.interpret(history[:-1], current.content)
        return self.scoring_engine.calculate(query)
