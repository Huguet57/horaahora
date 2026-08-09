from __future__ import annotations

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.domain.calculator.models import (
    Outcome,
    ParsedCastell,
    ParsedCastellQuery,
    ParsedPerformance,
)


class StrictPayloadModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ParsedCastellPayload(StrictPayloadModel):
    notació: str = Field(min_length=1, max_length=32)
    resultat: Literal["carregat", "descarregat", "intent"]


class ParsedPerformancePayload(StrictPayloadModel):
    nom: str = Field(min_length=1, max_length=100)
    castells: list[ParsedCastellPayload] = Field(max_length=12)


class ParsedQueryPayload(StrictPayloadModel):
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
        intents = {
            "consulta": "lookup",
            "comparació": "comparison",
            "total": "total",
            "informació_concurs": "contest_info",
            "aclariment": "clarification",
            "no_compatible": "unsupported",
        }
        resultats = {
            "carregat": Outcome.LOADED,
            "descarregat": Outcome.UNLOADED,
            "intent": Outcome.ATTEMPT,
        }
        return ParsedCastellQuery(
            intent=intents[self.intent],  # type: ignore[arg-type]
            performances=[
                ParsedPerformance(
                    label=performance.nom,
                    castells=[
                        ParsedCastell(
                            notation=castell.notació,
                            outcome=resultats[castell.resultat],
                        )
                        for castell in performance.castells
                    ],
                )
                for performance in self.actuacions
            ],
            clarification=self.aclariment,
            answer=self.resposta,
        )
