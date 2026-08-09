from backend.domain.calculator.models import (
    ChatTurn,
    ParsedCastell,
    ParsedCastellQuery,
    ParsedPerformance,
)


class CalculatorQueryInterpreterStub:
    async def interpret(self, history: list[ChatTurn], message: str) -> ParsedCastellQuery:
        del history, message
        return ParsedCastellQuery(
            intent="comparison",
            performances=[
                ParsedPerformance("Amb 5d9f", [ParsedCastell("5d9f")]),
                ParsedPerformance("Amb 4d9fa", [ParsedCastell("4d9fa")]),
            ],
        )
