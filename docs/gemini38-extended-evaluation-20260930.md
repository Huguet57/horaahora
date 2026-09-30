# Gemini 3.8 Flash: bateria ampliada

30/09/2026, sobre la implementació de conversa i continuïtat de la PR #70 (`fe6ffb5`).
Mateix prompt que la comparativa inicial; no s'ha ajustat durant aquesta prova.

**351/363 torns superats (96,7%). 95/100 situacions diferents passen les tres vegades.**
S'han completat 300 execucions d'escenari; 288 passen íntegrament. Hi ha una resposta
invàlida del proveïdor i onze torns amb resultat incorrecte o incomplet.

## Cobertura

100 situacions: les 20 de regressió anteriors i 80 de noves. 121 torns per passada,
tres passades, amb `google/gemini-3.8-flash`, raonament `low` i l'esquema de producció.
Els 69 torns de regressió passen; dels nous, en passen 282/294 (95,9%).

| Àmbit | Torns superats |
|---|---:|
| Conversa, frustració, identitat, peticions fora d'àmbit i probabilitats | 45/45 |
| Notacions, sobrenoms de castells, errors tipogràfics i castellà | 48/48 |
| Modificacions de comparacions i converses llargues | 147/150 |
| Ambigüitats i dades insuficients | 18/18 |
| Càlcul i selecció dels castells que computen, inclòs el control bàsic | 21/27 |
| Historial, edicions inexistents i àlies de colles, inclòs el control anterior | 31/33 |
| Normativa | 18/18 |
| Rànquing, extrems, veïns i taula completa | 23/24 |

Les converses llargues inclouen vuit modificacions successives, tornar al càlcul després
d'una consulta històrica, frustració, desfer un canvi, colles amb noms semblants, afegir,
eliminar i reanomenar participants. Els vuit canvis seguits passen les tres vegades.

## Fallades reproduïdes

| Situació | Fallades | Diagnòstic |
|---|---:|---|
| `3d8 + 3d9f + 4d8` descarregats | 3/3 | El motor suma 3.725 punts; hauria de comptar només el millor dels dos tresos i donar 2.755. |
| `2d9fm + 2d9sm + 4d9f` descarregats | 3/3 | El motor elimina una torre compatible: dona 7.465 en lloc de 10.195. |
| Reprendre la comparació després de sis torns de conversa | 3/3 | L'escenari ha sortit dels 12 missatges enviats al model; demana reconstruir-lo. |
| Punts dels «Verds» al Concurs de 2024 | 2/3 | Quan el model passa literalment «Verds» al filtre de recuperació, no troba Castellers de Vilafranca. |
| Taula completa amb carregats i descarregats | 1/3 | El model genera 2.233 caràcters a `resposta`, que té un màxim de 1.500, i la validació falla. |

En les dues fallades de puntuació la interpretació de castells i resultats és correcta.
Són errors del motor determinista. A més, les preguntes normatives sobre aquelles mateixes
compatibilitats reben respostes correctes: el producte es contradiu entre explicació i suma.

La prova d'historial també inclou un castell no computat que desapareix del resum, però
al torn final ha desaparegut **tot** l'escenari de la finestra disponible. El resultat
prova el límit d'historial; no aïlla la pèrdua d'aquell castell. El model demana dades
en lloc d'inventar-les, però la tasca de l'usuari queda sense resoldre.

Amb «Verds», la primera passada funciona perquè el model envia «Castellers de Vilafranca»;
les altres dues envien «Verds». La recuperació d'àlies hauria de ser estable al programa.

## Cost, metodologia i límits

- 441 crides reals; cost reportat total **2,369577 USD**, inclosa la resposta que no
  passa la validació. Mediana del servei: **3,17 s**; p95: **10,54 s** (rang més proper).
- Cost amb la memòria cau real de la bateria. No és una previsió de factura mensual.
  L'agregat conservador `total_cost_usd` és null si hi ha errors; `recorded_cost_usd`
  suma els costos presents de totes les 441 crides, inclòs l'error de validació facturat.
- S'ha executat `ChatService`, el model real, les instantànies versionades i el motor
  de puntuació en una Preview temporal protegida, sense base de producció. Concurrència
  màxima 4, sense reintents per reemplaçar fallades. Els torns encadenats reben les
  respostes reals anteriors del model, amb el límit de 12 missatges.
- Les expectatives de càlcul comproven interpretació, totals i castells computats;
  les de rànquing comproven també les files estructurades. Les expectatives de text
  són comprovacions parcials de contingut, no un judici exhaustiu de totes les frases.
  S'han revisat les fallades i les respostes històriques i normatives de la primera passada.
- Es compten els errors del producte complet, no només els atribuïbles al model.
  No s'han comparat els altres models en aquests 80 casos nous.
- La pregunta oberta «si Vella i Joves descarreguen 3d10fm, Vilafranca pot guanyar amb
  alguna combinació?» no formava part d'aquestes 100 situacions. Requereix una regressió
  específica i no es pot considerar coberta per aquests percentatges.

S'han corregit dues expectatives després d'iniciar l'execució, sense canviar cap missatge
enviat al model: la suma d'estructures incompatibles es va contrastar amb el protocol
en lloc d'acceptar el motor com a referència, i el guanyador de 1998 es va corregir a
Vilafranca segons la primera fila de la instantània. Es tornen a puntuar totes les
respostes guardades; no es repeteixen selectivament inferències. Les correccions, les
expectatives originals i `initial_failures` es conserven al registre. Les dues correccions
es compensen numèricament: el total de torns aprovats no canvia.

## Reproducció

[Fixture](../tests/fixtures/chat_extended_cases.json) ·
[Avaluador](../scripts/evaluate_chat_models.py) ·
[Registre complet](evaluations/gemini38-extended-20260930.jsonl).

Amb `OPENROUTER_API_KEY` definida:

```bash
uv run --frozen python -m scripts.evaluate_chat_models \
  --dataset tests/fixtures/chat_extended_cases.json \
  --models google/gemini-3.8-flash --repetitions 3 \
  --output /tmp/gemini38-extended.json
```

SHA-256 del prompt/esquema: `a094b222d6b5ebd5e343e7f1559c9ffe203315d844ff40c849e2d6b57b23935a`.
Fixture final: `50218c4082a41146ff0abc3446c6942f6770860c601275920c0322a1f680c7ac`.
Entrades al model sense expectatives: `3a2cc3fdee160d1ff3a0e032efcb4758a3a457bb790dbb960c9f0027165db03a`.

Les millores de l'avaluador tenen proves pròpies: 363 proves locals passades i 6 de
PostgreSQL reservades al CI. Aquesta ampliació no modifica el comportament del xat.
