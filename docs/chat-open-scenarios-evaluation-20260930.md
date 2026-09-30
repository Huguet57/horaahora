# Preguntes obertes sobre opcions de puntuació

PR #71, sobre la PR #70. Implementació provada: `63265ce`.

El cas reportat era «Si la vella i la joves descarreguen 3d10fm vilafranca pot guanyar
amb alguna combinacio?». Abans exigia actuacions completes o rebutjava la pregunta com
una predicció. Ara recupera la taula de puntuacions i dona opcions parcials documentades.

Resposta real de Gemini 3.8 després del canvi:

> Segons la taula de puntuacions del 2026, el 3de10fm descarregat té un valor de 4.525
> punts. Per a superar aquest castell en una ronda individual, hi ha estructures
> superiors com el 4de10fm descarregat (4.930 punts) o el 9de9f descarregat (5.180 punts).
> Tanmateix, per determinar si Vilafranca pot guanyar l'actuació completa cal conèixer
> la resta de castells de cada colla, ja que el resultat final depèn de la suma dels
> tres millors castells.

## Resultats reals

| Versió | Model | Passades | Torns superats | Escenaris complets | Cost reportat USD | Mediana del servei |
|---|---|---:|---:|---:|---:|---:|
| Abans | Gemini 3.8 Flash | 1 | 11/17 | 6/12 | 0,109937 | 3,14 s |
| Final | Gemini 3.8 Flash | 3 | 51/51 | 36/36 | 0,348157 | 4,18 s |
| Final | Gemini 3.7 Flash | 3 | 51/51 | 36/36 | 0,443360 | 6,59 s |

La reproducció exacta amb els missatges anteriors fallava abans, amb:
«Quins altres castells completen l'actuació de cada colla o quina combinació concreta
de Vilafranca vols comparar?». Ara passa tres vegades per model.

La fixture conté 12 situacions i 17 torns: pregunta amb l'historial reportat, salutació
final amb les males respostes anteriors, seqüència completa des de zero, consulta aïllada,
referència carregada, rivals amb castells diferents, cap castell per sobre del màxim,
possibilitat per punts versus probabilitat real, comparació concreta, continuació de
la pregunta oberta cap a una comparació concreta i petició en castellà.

S'ha executat el servei complet amb OpenRouter, recuperació real de les instantànies,
esquemes estrictes, `reasoning.effort=low`, `data_collection=deny` i un màxim de quatre
escenaris simultanis. Cada torn rep les respostes reals anteriors del seu model i els
mateixos 12 missatges de context que l'app. Cap reintent substitueix una fallada.
La Preview temporal no connecta amb la base de producció. El cost inclou la memòria
cau de la prova; la latència inclou les crides d'encaminament i resolució.

## Desenvolupament i límits

Una prova intermèdia de Gemini 3.8 va donar 47/51: faltava el valor numèric de la
referència en una resposta i «Hola mates» es confonia amb matemàtiques en tres torns.
Es van reforçar les instruccions generals de salutació i de citar primer els punts
de referència. La prova final repeteix tota la bateria amb aquesta mateixa versió.
És una regressió de desenvolupament, no una mostra independent d'intel·ligència general.

El verificador exigeix intent informatiu, resposta sense aclariment obligatori, punts
de referència, alguna alternativa vàlida de la taula i qualificació de la conclusió
quan es pregunta per guanyar tota l'actuació. Les comparacions concretes comproven
castells, resultats i totals. Els casos de probabilitat rebutgen percentatges inventats.
Les respostes obertes també s'han inspeccionat, perquè comprovar fragments de text
no és una validació semàntica exhaustiva.

S'ha corregit una expectativa massa estricta abans de la prova final: quan la pregunta
ja es limita a superar un castell, no cal repetir la reserva sobre l'actuació sencera.
La base s'ha tornat a puntuar amb les mateixes expectatives finals; el registre conserva
la puntuació inicial on canvia. Els missatges no s'han modificat.

El canvi permet oferir exemples per punts a partir de la taula; no incorpora un
optimitzador de totes les combinacions ni fa pronòstics. Els totals i les comparacions
completes continuen al motor. No resol els errors de compatibilitats, àlies i memòria
documentats a la [bateria ampliada](gemini38-extended-evaluation-20260930.md).

## Reproducció

[Fixture](../tests/fixtures/chat_open_scenario_cases.json) ·
[Registre abans/després](evaluations/chat-open-scenarios-20260930.jsonl).

```bash
uv run --frozen python -m scripts.evaluate_chat_models \
  --dataset tests/fixtures/chat_open_scenario_cases.json \
  --models google/gemini-3.8-flash google/gemini-3.7-flash \
  --repetitions 3 --output /tmp/chat-open-scenarios.json
```

Requereix `OPENROUTER_API_KEY`. Empremta final de prompts/esquemes:
`16114f45283f4cd1078946ffe1823e28ed7986cc389629bf47c89287be38dcf7`.
Les empremtes de les fixtures i les dades d'ús de cada crida es conserven al registre.

Validació del codi: 363 proves locals passades, 6 d'integració PostgreSQL al CI,
Ruff i format correctes. El prompt d'interpretació continua per sota de 17.000 caràcters.
