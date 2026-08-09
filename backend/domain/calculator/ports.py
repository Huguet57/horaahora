from typing import Protocol

from backend.domain.calculator.models import ChatTurn, ParsedCastellQuery


class ChatModel(Protocol):
    async def interpret(self, history: list[ChatTurn], message: str) -> ParsedCastellQuery: ...

    async def resolve_contest(
        self,
        history: list[ChatTurn],
        message: str,
        context: str,
    ) -> ParsedCastellQuery: ...
