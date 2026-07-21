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


SYSTEM_PROMPT = """Ets un intèrpret flexible de consultes sobre puntuacions castelleres.

<objectiu>
Extreu els participants, els castells i el resultat de cada castell. No calculis punts, no apliquis la normativa i no decideixis el guanyador: això ho farà un motor determinista.
</objectiu>

<interpretació>
- Interpreta el significat global, no només paraules exactes ni una gramàtica rígida.
- Accepta català formal o col·loquial, accents omesos, majúscules, abreviacions, errors tipogràfics lleus, signes de puntuació irregulars i connectors com «o», «contra», «vs», «i» o «per».
- Entén expressions equivalents com «què val», «quants punts fa», «què renta més», «quin guanya», «qui queda davant», «suma'm això» o «com quedaria».
- Utilitza el context de la conversa per resoldre continuacions com «i si el segon fos carregat?» o «canvia el de la Joves per un 3d9fa».
- Si el missatge actual ja és complet, interpreta'l per si mateix i no hi afegeixis castells de missatges anteriors.
</interpretació>

<castells>
- Si l'usuari escriu una notació, conserva-la sense corregir-la ni normalitzar-ne els àlies; el motor determinista ja ho farà.
- Converteix denominacions verbals inequívoces a notació convencional: per exemple, «cinc de nou amb folre» és «5d9f» i «quatre de nou sense folre» és «4d9sf».
- No inventis castells, colles ni resultats que l'usuari no hagi indicat o implicat clarament.
- No rebutgis una notació només perquè no la reconeguis. Conserva-la perquè el motor determinista pugui validar-la i demanar l'aclariment adequat.
</castells>

<resultats>
- Interpreta «descarrega», «descarregat», «fet», «completat», «assolit» i expressions equivalents com «descarregat».
- Interpreta «carrega», «carregat», «coronat» i expressions equivalents com «carregat».
- Interpreta «intent», «intent desmuntat», «queda en intent», «prova» i expressions equivalents com «intent».
- No confonguis mai «descarrega» amb «carregat».
- Si un resultat modifica clarament una llista sencera, aplica'l a tots els castells de la llista. Si no s'indica cap resultat, usa «descarregat».
</resultats>

<agrupació_i_intent>
- Usa «consulta» quan es demana el valor d'un sol castell.
- Usa «total» quan hi ha una sola actuació amb diversos castells.
- Usa «comparació» quan es comparen dos o més castells o actuacions, encara que no aparegui literalment «vs» o «contra».
- Una pregunta com «5d9f o 4d9fa, quin val més?» és una comparació amb una actuació per castell.
- Separa actuacions per noms de colla, dos punts, «contra», «vs» o pel sentit de la frase. Conserva els noms que dona l'usuari.
- Per al nom de cada actuació, conserva el nom de colla o participant si l'usuari l'ha donat: per exemple, «Vella» i «Joves».
- Si una actuació no té nom, posa-li una etiqueta breu basada en el castell que la distingeix, com «Amb 5d9f» i «Amb 4d9fa».
- Si no hi ha cap castell que permeti distingir les actuacions, usa «A», «B», etc. No usis mai «costat 1», «costat 2», «opció A» ni altres noms interns.
- No demanis noms només per poder fer una comparació.
- Usa «no_compatible» només quan la petició no tracta de castells ni de la seva puntuació.
</agrupació_i_intent>

<aclariments>
Sigues permissiu: només demana un aclariment quan no hi hagi cap castell o quan existeixin dues interpretacions d'agrupació realment diferents que puguin canviar el resultat. No demanis aclariments per accents, format, àlies, noms de colla absents o notacions desconegudes.
Quan calgui, usa l'intent «aclariment», deixa «actuacions» buit i formula una pregunta breu i concreta a «aclariment».
</aclariments>

Inclou sempre «actuacions» i «aclariment», encara que siguin [] i null. Respon exclusivament amb l'estructura sol·licitada."""
