from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.domain.models import Outcome, ParsedCastell, ParsedCastellQuery, ParsedPerformance


class StrictPayloadModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ParsedCastellPayload(StrictPayloadModel):
    notació: str = Field(min_length=1, max_length=32)
    resultat: Literal["carregat", "descarregat", "intent"]


class ParsedPerformancePayload(StrictPayloadModel):
    nom: str = Field(min_length=1, max_length=100)
    castells: list[ParsedCastellPayload] = Field(max_length=12)


class ParsedQueryPayload(StrictPayloadModel):
    intent: Literal["consulta", "comparació", "total", "aclariment", "no_compatible"]
    actuacions: list[ParsedPerformancePayload] = Field(max_length=8)
    aclariment: str | None = Field(max_length=500)

    def to_domain(self) -> ParsedCastellQuery:
        intents = {
            "consulta": "lookup",
            "comparació": "comparison",
            "total": "total",
            "aclariment": "clarification",
            "no_compatible": "unsupported",
        }
        resultats = {
            "carregat": Outcome.LOADED,
            "descarregat": Outcome.UNLOADED,
            "intent": Outcome.ATTEMPT,
        }
        return ParsedCastellQuery(
            intent=intents[self.intent],
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
        )


SYSTEM_PROMPT = """Ets un intèrpret de consultes sobre puntuacions castelleres.
Extreu els participants, els castells i el resultat, però no calculis punts ni decideixis el guanyador.
Mantén la notació escrita per l'usuari. Si no indica el resultat, usa «descarregat».
Aplica literalment aquestes equivalències:
- descarrega, descarregat, descarregada o completat: «descarregat»;
- carrega, carregat, carregada o coronat: «carregat»;
- intent o intent desmuntat: «intent».
No confonguis mai el verb «descarrega» amb «carregat».
Quan hi ha «vs» o «contra», crea una actuació per cada costat. Conserva els noms de colla si hi són; si no hi ha noms, usa «costat 1» i «costat 2» i no demanis cap aclariment.
Usa l'intent «consulta» per un sol castell, «comparació» per comparar actuacions, «total» per sumar-ne una, «aclariment» si falta una dada imprescindible i «no_compatible» si la petició queda fora de l'àmbit.
Inclou sempre «actuacions» i «aclariment», encara que siguin [] i null.
Respon exclusivament amb l'estructura sol·licitada."""
