from typing import Protocol

from backend.domain.calculator.models import ChatTurn, ParsedCastellQuery, ParsedPerformance


class ChatModel(Protocol):
    async def interpret(
        self,
        history: list[ChatTurn],
        message: str,
        *,
        scenario: list[ParsedPerformance] | None = None,
    ) -> ParsedCastellQuery: ...

    async def resolve_contest(
        self,
        history: list[ChatTurn],
        message: str,
        context: str,
        *,
        scenario: list[ParsedPerformance] | None = None,
    ) -> ParsedCastellQuery: ...
