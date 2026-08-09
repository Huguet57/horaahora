from backend.domain.calculator.models import (
    ChatTurn,
    ParsedCastell,
    ParsedCastellQuery,
    ParsedPerformance,
)


class CalculatorChatModelStub:
    async def interpret(self, history: list[ChatTurn], message: str) -> ParsedCastellQuery:
        del history, message
        return ParsedCastellQuery(
            intent="comparison",
            performances=[
                ParsedPerformance("Amb 5d9f", [ParsedCastell("5d9f")]),
                ParsedPerformance("Amb 4d9fa", [ParsedCastell("4d9fa")]),
            ],
        )

    async def resolve_contest(
        self,
        history: list[ChatTurn],
        message: str,
        context: str,
    ) -> ParsedCastellQuery:
        del history, message, context
        raise AssertionError("El flux de càlcul no ha de resoldre coneixement del Concurs")
