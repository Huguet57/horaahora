from typing import Protocol

from backend.domain.calculator.models import ChatTurn, ParsedCastellQuery


class QueryInterpreter(Protocol):
    async def interpret(self, history: list[ChatTurn], message: str) -> ParsedCastellQuery: ...
