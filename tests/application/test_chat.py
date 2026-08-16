import asyncio

from backend.application.chat import ChatService
from backend.domain.calculator.models import (
    ChatTurn,
    Outcome,
    ParsedCastell,
    ParsedCastellQuery,
    ParsedPerformance,
)
from backend.domain.calculator.scoring import ScoringEngine
from backend.domain.calculator.table import ScoreTable
from backend.domain.contest.models import ContestKnowledgeQuery


class ContestChatModel:
    def __init__(self, resolution: ParsedCastellQuery) -> None:
        self.resolution = resolution
        self.resolution_calls: list[tuple[list[ChatTurn], str, str]] = []

    async def interpret(self, history: list[ChatTurn], message: str) -> ParsedCastellQuery:
        del history, message
        return ParsedCastellQuery(
            intent="contest_info",
            knowledge_query=ContestKnowledgeQuery(
                source="results",
                years=[2024],
                result_scope="classification",
            ),
        )

    async def resolve_contest(
        self,
        history: list[ChatTurn],
        message: str,
        context: str,
    ) -> ParsedCastellQuery:
        self.resolution_calls.append((history, message, context))
        return self.resolution


class RecordingContestRepository:
    def __init__(self) -> None:
        self.queries: list[ContestKnowledgeQuery] = []

    def retrieve(self, query: ContestKnowledgeQuery) -> str:
        self.queries.append(query)
        return "<coneixement_recuperat>2024 | 1 | Castellers de Vilafranca</coneixement_recuperat>"


class CalculationChatModel:
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
        raise AssertionError("Una consulta de càlcul no ha de fer una segona crida")


class UnexpectedContestRepository:
    def retrieve(self, query: ContestKnowledgeQuery) -> str:
        del query
        raise AssertionError("Una consulta de càlcul no ha de recuperar coneixement")


def _service(
    model: ContestChatModel,
    repository: RecordingContestRepository,
) -> ChatService:
    return ChatService(
        model,
        repository,
        ScoringEngine(ScoreTable.default()),
    )


def test_chat_service_retrieves_context_before_answering_contest_information() -> None:
    model = ContestChatModel(
        ParsedCastellQuery(
            intent="contest_info",
            answer="Els Castellers de Vilafranca van guanyar el Concurs 2024.",
        )
    )
    repository = RecordingContestRepository()

    result = asyncio.run(
        _service(model, repository).respond(
            [ChatTurn(role="user", content="Qui va guanyar el 2024?")]
        )
    )

    assert repository.queries[0].years == [2024]
    assert "Castellers de Vilafranca" in model.resolution_calls[0][2]
    assert result.reply == "Els Castellers de Vilafranca van guanyar el Concurs 2024."
    assert result.intent == "contest_info"
    assert result.performances == []
    assert result.winner_label is None
    assert result.warnings == []
    assert not result.needs_clarification


def test_chat_service_keeps_calculations_on_the_single_call_path() -> None:
    service = ChatService(
        CalculationChatModel(),
        UnexpectedContestRepository(),
        ScoringEngine(ScoreTable.default()),
    )

    result = asyncio.run(
        service.respond([ChatTurn(role="user", content="Què val més, 5d9f o 4d9fa?")])
    )

    assert result.intent == "comparison"
    assert result.winner_label == "Amb 4d9fa"


def test_chat_service_sends_historical_recalculation_to_the_scoring_engine() -> None:
    model = ContestChatModel(
        ParsedCastellQuery(
            intent="total",
            performances=[
                ParsedPerformance(
                    label="C. de Vilafranca",
                    castells=[
                        ParsedCastell("3d10fm"),
                        ParsedCastell("9d9f", Outcome.ATTEMPT),
                        ParsedCastell("4d9fa", Outcome.LOADED),
                        ParsedCastell("9d9f", Outcome.LOADED),
                        ParsedCastell("4d10fm", Outcome.LOADED),
                    ],
                )
            ],
        )
    )
    repository = RecordingContestRepository()

    result = asyncio.run(
        _service(model, repository).respond(
            [ChatTurn(role="user", content="Recalcula Vilafranca 2024 amb la taula 2026")]
        )
    )

    assert result.intent == "total"
    assert result.performances[0].total == 12_915
    assert "12.915 punts" in result.reply


def test_chat_service_rejects_an_unresolved_contest_route() -> None:
    model = ContestChatModel(ParsedCastellQuery(intent="contest_info"))
    repository = RecordingContestRepository()

    try:
        asyncio.run(
            _service(model, repository).respond(
                [ChatTurn(role="user", content="Qui va guanyar el 2024?")]
            )
        )
    except ValueError as error:
        assert "resposta informativa" in str(error)
    else:
        raise AssertionError("S'esperava un error per una resolució informativa buida")
