from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from backend.domain.models import Outcome, ParsedCastell, ParsedCastellQuery, ParsedPerformance


class ParsedCastellPayload(BaseModel):
    notation: str = Field(min_length=1, max_length=32)
    outcome: Literal["loaded", "unloaded", "attempt"] = "unloaded"


class ParsedPerformancePayload(BaseModel):
    label: str = Field(min_length=1, max_length=100)
    castells: list[ParsedCastellPayload] = Field(default_factory=list, max_length=12)


class ParsedQueryPayload(BaseModel):
    intent: Literal["lookup", "comparison", "total", "clarification", "unsupported"]
    performances: list[ParsedPerformancePayload] = Field(default_factory=list, max_length=8)
    clarification: str | None = Field(default=None, max_length=500)

    def to_domain(self) -> ParsedCastellQuery:
        return ParsedCastellQuery(
            intent=self.intent,
            performances=[
                ParsedPerformance(
                    label=performance.label,
                    castells=[
                        ParsedCastell(notation=castell.notation, outcome=Outcome(castell.outcome))
                        for castell in performance.castells
                    ],
                )
                for performance in self.performances
            ],
            clarification=self.clarification,
        )


SYSTEM_PROMPT = """Ets un intèrpret de consultes sobre puntuacions castelleres.
Extreu participants, castells i estat, però no calculis punts ni decideixis el guanyador.
Mantén la notació escrita per l'usuari. Si no indica l'estat, usa unloaded.
loaded significa carregat; unloaded significa descarregat; attempt significa intent o intent desmuntat.
Quan hi ha 'vs' o 'contra', crea una actuació per cada costat. Conserva els noms de colla.
Si falta una dada imprescindible, retorna intent clarification i explica què falta.
Respon exclusivament amb l'estructura sol·licitada."""
