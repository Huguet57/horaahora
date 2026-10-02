from __future__ import annotations

import re
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
    font: Literal["normativa", "resultats", "puntuacions"]
    anys: list[int] = Field(max_length=30)
    colles: list[str] = Field(max_length=20)
    abast_resultats: Literal["edicions", "guanyadors", "classificació"] | None
    abast_puntuacions: Literal["rànquing"] | None
    resultat_puntuacions: Literal["carregat", "descarregat", "tots_dos"] | None
    selecció_rànquing: Literal["primers", "últims", "posició", "veïns", "complet"] | None
    límit_rànquing: int | None = Field(ge=1, le=47)
    castell_rànquing: str | None = Field(min_length=1, max_length=32)

    @model_validator(mode="after")
    def validate_source(self) -> Self:
        if self.font == "normativa":
            if (
                self.abast_resultats is not None
                or self.abast_puntuacions is not None
                or self.resultat_puntuacions is not None
                or self.selecció_rànquing is not None
                or self.límit_rànquing is not None
                or self.castell_rànquing is not None
            ):
                raise ValueError("normativa no permet abasts de resultats ni de puntuacions")
        elif self.font == "resultats":
            if self.abast_resultats is None:
                raise ValueError("resultats exigeix abast_resultats")
            if (
                self.abast_puntuacions is not None
                or self.resultat_puntuacions is not None
                or self.selecció_rànquing is not None
                or self.límit_rànquing is not None
                or self.castell_rànquing is not None
            ):
                raise ValueError("els filtres de puntuacions només es permeten per a puntuacions")
        elif (
            self.abast_resultats is not None
            or self.abast_puntuacions != "rànquing"
            or self.resultat_puntuacions is None
            or self.selecció_rànquing is None
            or self.anys
            or self.colles
        ):
            raise ValueError(
                "puntuacions exigeix el rànquing, un resultat i cap filtre d'any o colla"
            )
        elif self.selecció_rànquing in {"primers", "últims"}:
            if self.límit_rànquing is None or self.castell_rànquing is not None:
                raise ValueError("primers i últims exigeixen límit i no permeten castell")
        elif self.selecció_rànquing in {"posició", "veïns"}:
            if self.castell_rànquing is None or self.límit_rànquing is not None:
                raise ValueError("posició i veïns exigeixen castell i no permeten límit")
        elif self.límit_rànquing is not None or self.castell_rànquing is not None:
            raise ValueError("el rànquing complet no permet límit ni castell")
        return self

    def to_domain(self) -> ContestKnowledgeQuery:
        scopes = {
            "edicions": "editions",
            "guanyadors": "winners",
            "classificació": "classification",
        }
        sources = {
            "normativa": "rules",
            "resultats": "results",
            "puntuacions": "scores",
        }
        score_outcomes = {
            "carregat": "loaded",
            "descarregat": "unloaded",
            "tots_dos": "both",
        }
        ranking_selections = {
            "primers": "top",
            "últims": "bottom",
            "posició": "position",
            "veïns": "neighbors",
            "complet": "full",
        }
        return ContestKnowledgeQuery(
            source=sources[self.font],  # type: ignore[arg-type]
            years=self.anys,
            groups=self.colles,
            result_scope=scopes[self.abast_resultats] if self.abast_resultats else None,  # type: ignore[arg-type]
            score_scope="ranking" if self.abast_puntuacions else None,
            score_outcome=(
                score_outcomes[self.resultat_puntuacions]
                if self.resultat_puntuacions is not None
                else None
            ),  # type: ignore[arg-type]
            ranking_selection=(
                ranking_selections[self.selecció_rànquing]
                if self.selecció_rànquing is not None
                else None
            ),  # type: ignore[arg-type]
            ranking_limit=self.límit_rànquing,
            ranking_notation=self.castell_rànquing,
        )


class QueryRoutingPayload(StrictPayloadModel):
    intent: Literal[
        "consulta",
        "comparació",
        "total",
        "informació_concurs",
        "conversa",
        "aclariment",
        "no_compatible",
    ]
    # The scoring engine enforces MAX_PERFORMANCES with a readable reply.
    actuacions: list[ParsedPerformancePayload]
    aclariment: str | None = Field(max_length=500)
    consulta_concurs: ContestKnowledgeQueryPayload | None
    resposta: str | None = Field(max_length=1_500)

    @model_validator(mode="after")
    def validate_intent_payload(self) -> Self:
        if self.intent in {"conversa", "no_compatible"}:
            if (
                not self.resposta
                or not self.resposta.strip()
                or self.actuacions
                or self.aclariment is not None
                or self.consulta_concurs is not None
            ):
                raise ValueError("conversa i no_compatible exigeixen només una resposta")
            return self
        if self.resposta is not None:
            raise ValueError("resposta només es permet per a conversa o no_compatible")
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
            answer=self.resposta,
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
        "conversa",
        "aclariment",
        "no_compatible",
    ]
    # The scoring engine enforces MAX_PERFORMANCES with a readable reply.
    actuacions: list[ParsedPerformancePayload]
    aclariment: str | None = Field(max_length=500)
    resposta: str | None = Field(max_length=1_500)

    @model_validator(mode="after")
    def validate_intent_payload(self) -> Self:
        if self.intent in {"informació_concurs", "conversa", "no_compatible"}:
            if (
                not self.resposta
                or not self.resposta.strip()
                or self.actuacions
                or self.aclariment is not None
            ):
                raise ValueError(
                    "una resposta informativa o conversacional exigeix resposta, "
                    "actuacions buides i cap aclariment"
                )
            return self
        if self.resposta is not None:
            raise ValueError("resposta només es permet per a informació_concurs o conversa")
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


# Under a strict JSON schema some models close a sentence and then emit stray closing
# punctuation (`}`, `'}`, `',`) before the string really ends. A lone `"` or `”` is kept:
# it can close a quotation.
_STRAY_TAIL = re.compile(r"(?<=[.!?»)])[\s'\"”`}\],]*[}\],'`][\s'\"”`}\],]*$")


def _written_text(text: str | None) -> str | None:
    if text is None:
        return None
    return _STRAY_TAIL.sub("", text.strip())


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
        "conversa": "conversation",
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
        clarification=_written_text(clarification),
        answer=_written_text(answer),
        knowledge_query=knowledge_query,
    )
