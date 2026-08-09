import asyncio

from backend.application.chat import ChatService
from backend.domain.calculator.models import ChatTurn, ParsedCastellQuery
from backend.domain.calculator.scoring import ScoringEngine
from backend.domain.calculator.table import ScoreTable


class ContestInformationInterpreter:
    async def interpret(self, history: list[ChatTurn], message: str) -> ParsedCastellQuery:
        del history, message
        return ParsedCastellQuery(
            intent="contest_info",
            answer="Els Castellers de Vilafranca van guanyar el Concurs 2024.",
        )


def test_chat_service_returns_information_without_invoking_scoring() -> None:
    service = ChatService(
        ContestInformationInterpreter(),
        ScoringEngine(ScoreTable.default()),
    )

    result = asyncio.run(
        service.respond([ChatTurn(role="user", content="Qui va guanyar el 2024?")])
    )

    assert result.reply == "Els Castellers de Vilafranca van guanyar el Concurs 2024."
    assert result.intent == "contest_info"
    assert result.performances == []
    assert result.winner_label is None
    assert result.warnings == []
    assert not result.needs_clarification
