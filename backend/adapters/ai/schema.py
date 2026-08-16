from __future__ import annotations

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.domain.calculator.models import (
    Outcome,
    ParsedCastell,
    ParsedCastellQuery,
    ParsedPerformance,
)
from backend.domain.contest.models import ContestKnowledgeQuery


class StrictPayloadModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ParsedCastellPayload(StrictPayloadModel):
    notació: str = Field(min_length=1, max_length=32)
    resultat: Literal["carregat", "descarregat", "intent"]


class ParsedPerformancePayload(StrictPayloadModel):
    nom: str = Field(min_length=1, max_length=100)
    castells: list[ParsedCastellPayload] = Field(max_length=12)


class ContestKnowledgeQueryPayload(StrictPayloadModel):
    font: Literal["normativa", "resultats"]
    anys: list[int] = Field(max_length=30)
    colles: list[str] = Field(max_length=20)
    abast_resultats: Literal["edicions", "guanyadors", "classificació"] | None

    @model_validator(mode="after")
    def validate_source(self) -> Self:
        if self.font == "normativa" and self.abast_resultats is not None:
            raise ValueError("abast_resultats només es permet per a resultats")
        if self.font == "resultats" and self.abast_resultats is None:
            raise ValueError("resultats exigeix abast_resultats")
        return self

    def to_domain(self) -> ContestKnowledgeQuery:
        scopes = {
            "edicions": "editions",
            "guanyadors": "winners",
            "classificació": "classification",
        }
        return ContestKnowledgeQuery(
            source="rules" if self.font == "normativa" else "results",
            years=self.anys,
            groups=self.colles,
            result_scope=scopes[self.abast_resultats] if self.abast_resultats else None,  # type: ignore[arg-type]
        )


class QueryRoutingPayload(StrictPayloadModel):
    intent: Literal[
        "consulta",
        "comparació",
        "total",
        "informació_concurs",
        "aclariment",
        "no_compatible",
    ]
    actuacions: list[ParsedPerformancePayload] = Field(max_length=8)
    aclariment: str | None = Field(max_length=500)
    consulta_concurs: ContestKnowledgeQueryPayload | None

    @model_validator(mode="after")
    def validate_intent_payload(self) -> Self:
        if self.intent == "informació_concurs":
            if self.consulta_concurs is None or self.actuacions or self.aclariment is not None:
                raise ValueError(
                    "informació_concurs exigeix consulta_concurs, actuacions buides i cap aclariment"
                )
            return self
        if self.consulta_concurs is not None:
            raise ValueError("consulta_concurs només es permet per a informació_concurs")
        if self.intent == "aclariment" and (self.actuacions or not self.aclariment):
            raise ValueError("aclariment exigeix una pregunta i actuacions buides")
        return self

    def to_domain(self) -> ParsedCastellQuery:
        return _to_domain(
            intent=self.intent,
            performances=self.actuacions,
            clarification=self.aclariment,
            knowledge_query=(
                self.consulta_concurs.to_domain() if self.consulta_concurs is not None else None
            ),
        )


class ResolvedQueryPayload(StrictPayloadModel):
    intent: Literal[
        "consulta",
        "comparació",
        "total",
        "informació_concurs",
        "aclariment",
        "no_compatible",
    ]
    actuacions: list[ParsedPerformancePayload] = Field(max_length=8)
    aclariment: str | None = Field(max_length=500)
    resposta: str | None = Field(max_length=1_500)

    @model_validator(mode="after")
    def validate_intent_payload(self) -> Self:
        if self.intent == "informació_concurs":
            if not self.resposta or self.actuacions or self.aclariment is not None:
                raise ValueError(
                    "informació_concurs exigeix resposta, actuacions buides i cap aclariment"
                )
            return self
        if self.resposta is not None:
            raise ValueError("resposta només es permet per a informació_concurs")
        if self.intent == "aclariment" and (self.actuacions or not self.aclariment):
            raise ValueError("aclariment exigeix una pregunta i actuacions buides")
        return self

    def to_domain(self) -> ParsedCastellQuery:
        return _to_domain(
            intent=self.intent,
            performances=self.actuacions,
            clarification=self.aclariment,
            answer=self.resposta,
        )


def _to_domain(
    *,
    intent: str,
    performances: list[ParsedPerformancePayload],
    clarification: str | None,
    answer: str | None = None,
    knowledge_query: ContestKnowledgeQuery | None = None,
) -> ParsedCastellQuery:
    intents = {
        "consulta": "lookup",
        "comparació": "comparison",
        "total": "total",
        "informació_concurs": "contest_info",
        "aclariment": "clarification",
        "no_compatible": "unsupported",
    }
    outcomes = {
        "carregat": Outcome.LOADED,
        "descarregat": Outcome.UNLOADED,
        "intent": Outcome.ATTEMPT,
    }
    return ParsedCastellQuery(
        intent=intents[intent],  # type: ignore[arg-type]
        performances=[
            ParsedPerformance(
                label=performance.nom,
                castells=[
                    ParsedCastell(
                        notation=castell.notació,
                        outcome=outcomes[castell.resultat],
                    )
                    for castell in performance.castells
                ],
            )
            for performance in performances
        ],
        clarification=clarification,
        answer=answer,
        knowledge_query=knowledge_query,
    )
