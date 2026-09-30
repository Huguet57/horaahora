# Comparativa del xat amb conversa natural i continuïtat

Data: 30 de setembre de 2026. Implementació provada: `60f9ce2`.

## Resultat i decisió

La correcció resol els casos provats de resposta genèrica i de pèrdua d'actuacions amb
el model actual. Mantindria Gemini 3.7 Flash: Gemini 3.8 no millora els encerts en aquesta
mostra, Sonnet costa 3,83 vegades més i Luna introdueix errors de comprensió i factuals.
La PR no canvia el model configurat ni desplega a producció.

| Model d'OpenRouter | Torns correctes | Escenaris complets | Cost real dels 69 torns (USD) | Mediana del servei | p95 del servei |
|---|---:|---:|---:|---:|---:|
| `google/gemini-3.7-flash` | 69/69 | 60/60 | 0,391767 | 3,67 s | 6,67 s |
| `google/gemini-3.8-flash` | 69/69 | 60/60 | 0,390644 | 3,81 s | 17,28 s |
| `openai/gpt-6-luna` | 65/69 | 56/60 | 0,014688 | 3,52 s | 5,17 s |
| `anthropic/claude-sonnet-5.5` | 69/69 | 60/60 | 1,501534 | 2,62 s | 4,53 s |

No hi ha hagut errors de petició. Cada model ha fet 72 crides: les tres consultes
històriques tenen una crida d'encaminament i una altra de resolució amb fonts.
Els costos són `usage.cost` reportats per OpenRouter, amb el raonament i la memòria cau
efectivament facturats. No són una estimació de la factura mensual.

La memòria cau afavoreix especialment Luna en una bateria repetitiva: ha reutilitzat
417.296 de 433.350 tokens d'entrada (96,3%). Gemini 3.7 ha reutilitzat 96.211/497.581
(19,3%), Gemini 3.8 41.044/481.623 (8,5%) i Sonnet 0/663.042. No s'ha forçat un proveïdor:
OpenRouter ha resolt Gemini a Google/Google AI Studio, Luna a OpenAI i Sonnet a Azure.
S'han verificat els identificadors de model retornats a totes les crides.

## Què s'ha provat

20 escenaris sintètics, 23 torns per passada i tres passades per model: 276 torns i
240 escenaris en total. Tots han rebut els mateixos prompts i esquema estricte,
amb `reasoning.effort=low` i `provider.data_collection=deny`. El nivell de raonament
és la mateixa opció sol·licitada, però cada proveïdor la implementa de manera diferent.

| Categoria | Cobertura | Gemini 3.7 | Gemini 3.8 | Luna | Sonnet |
|---|---|---:|---:|---:|---:|
| Conversa | Identitat, salutació, frustració, capacitats, pronòstics, probabilitats i fora d'àmbit | 21/21 | 21/21 | 21/21 | 21/21 |
| Context | Edicions parcials, quatre colles, correccions encadenades, canvis globals, substitució, addició, reinici, ambigüitat i resum recent | 42/42 | 42/42 | 40/42 | 42/42 |
| Control | Càlcul independent i guanyador del Concurs de 2024 | 6/6 | 6/6 | 4/6 | 6/6 |

S'ha executat `ChatService` amb l'adaptador real d'OpenRouter, les instantànies de
coneixement i el motor de puntuació de la PR. Els torns encadenats reben la resposta
real anterior del mateix model. L'historial es limita als mateixos 12 missatges del
producte. La latència mesura el servei sencer, inclosa la segona crida quan cal recuperar
informació; exclou el trajecte del client fins a la Preview. El p95 usa el rang més
proper. Les peticions han estat intercalades entre models, amb concurrència màxima de 4.

L'execució s'ha fet en una Preview temporal protegida, sense connexió a la base de dades,
amb accés limitat als models i casos de la fixture. No conté exportacions de converses
reals, identificadors d'usuaris ni dades personals.

## Fallades observades

Les quatre fallades són de Luna:

- `append_does_not_drop_castells`, passada 1: conserva totes les colles i castells,
  però retorna `total` en lloc de `comparison`. És una fallada de contracte; el resultat
  visible i la puntuació són correctes.
- `only_recent_summary_available`, passada 1: retorna «Quan dius «4net», a quin castell
  et refereixes?» en una modificació de la Jove. No normalitza la referència i el càlcul
  es queda en aclariment, sense el resultat actualitzat.
- `grounded_history_control`, passades 2 i 3: atribueix el Concurs de 2024 a la Colla
  Vella amb 9.465 punts. El resultat correcte de la instantània és Castellers de
  Vilafranca. Aquesta prova recorre el servei complet; no aïlla si l'error s'origina en
  l'encaminament o en la síntesi final.

Exemples reals de Gemini 3.7 amb la correcció:

- «Ets una IA?» → «Sí, soc un assistent basat en intel·ligència artificial dissenyat
  per ajudar-te a consultar i calcular puntuacions de castells.»
- Una expressió de frustració rep «Cap problema, ho deixem aquí…», sense exigir un
  castell ni marcar la resposta com a aclariment.
- Les tres passades de correccions successives mantenen les quatre colles i els canvis
  de resultat anteriors. Es comparen tots els castells interpretats, inclosos els que
  no puntuen per quedar fora dels tres millors.

## Abast de les conclusions

És una bateria de regressió petita, repetida tres vegades; 69/69 no implica absència
d'errors en converses arbitràries. Les comprovacions de conversa revisen intent,
absència d'aclariment obligatori, resposta no genèrica i algunes expressions esperades;
no són una mesura general de qualitat de redacció. També s'han llegit exemples de les
set classes de conversa dels quatre models.

Una prova pilot anterior va servir per precisar les instruccions de `td9f` i referències
curtes com `3net`. Per tant, aquesta bateria és de desenvolupament i regressió, no una
mostra independent per ordenar la intel·ligència general dels models.

També es van executar cinc escenaris contra el codi anterior amb Gemini 3.7: fallaven
els tres de conversa per la resposta fixa; els dos escenaris simplificats de context
passaven. Aquesta comparació confirma la correcció de conversa, però no permet atribuir
un percentatge de millora general de context.

Després de l'execució s'ha corregit un fals negatiu del verificador: una consulta
independent sense nom de colla admet etiquetes generades equivalents, com «Actuació»
o «Amb 5d9f». S'han tornat a puntuar totes les respostes guardades, sense repetir ni
seleccionar inferències. Això elimina sis falsos negatius de Gemini, tres per model.
Les comparacions amb colles continuen exigint els noms exactes i tots els castells.
El registre conserva `initial_failures` on la puntuació ha canviat.

La continuïtat continua depenent del model i dels 12 missatges disponibles. No s'ha
afegit memòria persistent ni recuperació de castells que ja no consten a l'historial.
La PR conserva el càlcul determinista i les fonts per a consultes factuals.

## Reproducció i evidència

- [Escenaris i expectatives](../tests/fixtures/chat_conversation_cases.json).
- [Avaluador](../scripts/evaluate_chat_models.py), amb cost i ús de cada crida.
- [Registre complet de la comparativa](evaluations/chat-models-20260930.jsonl): primera
  línia de metadades i mètriques, seguida dels 240 escenaris amb respostes i ús.

Amb `OPENROUTER_API_KEY` definida:

```bash
uv run --frozen python -m scripts.evaluate_chat_models \
  --output /tmp/chat-evaluation.json --repetitions 3
```

Empremtes SHA-256:

- Prompts i esquemes: `a094b222d6b5ebd5e343e7f1559c9ffe203315d844ff40c849e2d6b57b23935a`.
- Fixture: `609d2b14cb6a871f6f9bcc71ab434cd8f3e52e72a0b07228ec32989846eb5a2d`.
- Avaluador final: `0c3ea37d8cecd62fef7304e4caf033b5541b945024cd958ea7ae012aacfb878a`.

Validació local: 361 proves passades, 6 proves PostgreSQL omeses per manca de base local,
Ruff i format correctes. Les proves d'integració s'executen al CI amb PostgreSQL.
La PR també actualitza exclusivament PyJWT 2.13.0 → 2.14.0 al lockfile per resoldre
les alertes de seguretat detectades pel CI en la dependència existent.


## Correcció posterior: estat complet fora de la finestra

Les mesures anteriors corresponen a la versió que només enviava text. La correcció
posterior afegeix `scenario` a la petició: colles, notacions i resultats de tots els
castells de l'últim càlcul, independentment dels 12 missatges. iOS i Android el
recuperen de les respostes completes ja persistides, també en reobrir la conversa.
Les respostes sense càlcul el conserven; el següent càlcul el substitueix. No es
reutilitzen punts ni indicadors de còmput: el motor els torna a calcular.

El camp és opcional per mantenir la compatibilitat amb apps antigues, que continuen
amb el seu historial de text. L'avaluador també envia aquest estat a partir d'ara;
els percentatges d'aquest informe no són una nova mesura amb aquesta correcció.
Les regressions locals cobreixen la finestra esgotada, intents, castells fora dels
tres millors, el límit de carregats, reobertura, substitució de l'escenari i separació
entre converses. Els tres adaptadors inclouen l'estat tant en la interpretació com
en la resolució amb fonts, sense elevar aquestes dades a instruccions de sistema.
