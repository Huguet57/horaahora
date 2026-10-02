# La calculadora de l'Aleta

App nativa per a iOS i Android centrada en una calculadora castellera conversacional i en la
taula de puntuacions del Concurs de Castells 2026. Té quatre pestanyes: Calculadora,
Comparador, Puntuacions i Ajustos.
El backend és una aplicació ASGI portable i no exposa cap proveïdor d'IA ni infraestructura
concreta al domini o al contracte HTTP.

El nom visible de l'app és **La calculadora de l'Aleta** (abans, Castells en vena). El
Bundle ID d'iOS i l'`applicationId` d'Android es mantenen: `com.ahuguet.castellsenvena`.

Hora a Hora, l'Agenda i els avisos de notícies, que abans eren a l'app interna d'aquest
repositori, són ara una app separada amb el seu propi backend:
[Huguet57/hora-a-hora](https://github.com/Huguet57/hora-a-hora).

## Estructura

- `HoraAHoraApp/HoraAHoraApp`: entrada de l'app iOS, configuració, arrencada, navegació i dependències.
- `HoraAHoraApp/Packages/CastellsKit`: paquet Swift local amb domini, dades i features independents.
- `android`: app Android nativa (Kotlin i Jetpack Compose) amb mòduls `core` i `feature`; vegeu `android/README.md`.
- `backend/domain`: models, ports i motor de puntuació determinista.
- `backend/application`: casos d'ús.
- `backend/adapters`: IA, coneixement del Concurs, persistència i rate limiting.
- `backend/api`: routers i esquemes HTTP separats per contracte.
- `tests`: proves del domini, contractes d'IA i API.
- `docs/architecture.md`: límits modulars i dependències permeses.
- `docs/testflight-readiness.md`: estat tècnic i passos manuals necessaris per distribuir la beta.

## Backend local

Amb Python 3.12 i [uv](https://docs.astral.sh/uv/):

```bash
uv sync --frozen
cp .env.example .env
docker compose up -d db
set -a && source .env && set +a
uv run --frozen alembic upgrade head
uv run --frozen uvicorn api.index:app --reload
```

`pyproject.toml` és l'única font de dependències i `uv.lock` fixa tota la resolució
transitiva. Després de modificar dependències, executa `uv lock`; CI rebutja qualsevol
lockfile desactualitzat.

O amb infraestructura local completa:

```bash
cp .env.example .env
docker compose up --build
```

L'API queda disponible a `http://127.0.0.1:8000` i la documentació interactiva a `/docs`. Compose aporta PostgreSQL 17; tot l'estat compartit del backend viu en aquesta base i no hi ha cap fallback SQLite o en memòria al runtime.

### Interpretació de consultes

La calculadora requereix un proveïdor de model explícit: `AI_PROVIDER=openrouter`,
`AI_PROVIDER=openai` o `AI_PROVIDER=anthropic`. La configuració de producció recomanada és
OpenRouter amb `AI_MODEL=anthropic/claude-sonnet-5.5`, `AI_BASE_URL=https://openrouter.ai/api`
i raonament baix. El prompt és deliberadament curt: descriu la situació, el coneixement
casteller que el motor no pot deduir i el contracte de sortida, i confia la resta al model.
Un error reportat s'afegeix primer a les bateries d'avaluació; només arriba al prompt si hi
falta coneixement del domini. El model, la clau i l'endpoint es configuren amb `AI_MODEL`, `AI_API_KEY`
i `AI_BASE_URL`. No hi ha cap intèrpret alternatiu ni cap degradació silenciosa: una
configuració absent o desconeguda impedeix arrencar el servei de xat.

Els adaptadors amb model també poden respondre preguntes sobre la normativa i els resultats
històrics del Concurs. Les instantànies versionades contenen totes les edicions oficials
publicades i l'última normativa completa disponible, però no s'injecten senceres al prompt.
Les preguntes sobre l'ordre, les posicions o els veïns del rànquing recuperen sota demanda
la taula de puntuacions 2026, ordenada determinísticament des del CSV versionat.
Aquestes respostes inclouen també una presentació tipada (`score_ranking`)
perquè els clients puguin mostrar files, posicions i punts sense analitzar la prosa; el camp
`reply` es conserva com a fallback compatible.
No es consulta cap web durant una petició de xat. Els canvis confirmats del 2026 tenen
prioritat; quan una regla només consta als documents del 2024, la resposta n'indica
explícitament l'any.

La composició és explícita i té un únic recorregut en dues fases quan cal coneixement:

- `calculator.py`: interpretació de llenguatge casteller i consultes de càlcul;
- `aleta.py`: context públic de l'app de gestió Aleta, verificat el 30/09/2026;
- `contest_router.py`: consulta estructurada per font, anys, colles i abast;
- `response_policy.py`: límits, atribució temporal i prohibició d'inventar dades;
- `adapters/contest/snapshot.py`: selecció local de la porció rellevant de normativa o
  resultats i composició del rànquing de puntuacions;
- `composer.py`: prompt base d'interpretació i prompt de resolució amb el context recuperat.

OpenAI i Anthropic consumeixen els mateixos contractes. L'adaptador directe d'Anthropic
(`AI_PROVIDER=anthropic`, per exemple amb `AI_MODEL=claude-sonnet-5-5`) demana la sortida
estructurada amb `output_config.format` i esforç baix, sense forçar cap eina: els models
actuals de Claude rebutgen `tool_choice` forçat. Una consulta de càlcul fa una sola
petició estructurada i passa directament al motor determinista. Una consulta del Concurs fa
una primera petició d'encaminament, recupera només les edicions, colles o fonts necessàries i
fa una segona petició de resolució. Una resposta que no compleix l'esquema falla de manera
explícita: no es reintenta amb un prompt alternatiu ni s'accepten formats antics del proveïdor.

Les salutacions, les preguntes sobre l'assistent i la frustració tenen un intent
`conversation` amb una resposta redactada pel model en la primera crida, sense files de
càlcul ni un aclariment obligatori. Les peticions fora d'àmbit també reben una explicació
pertinent. Les respostes factuals del Concurs continuen exigint les fonts recuperades i
els punts els continua calculant exclusivament el motor determinista.

En una conversa de càlcul, les modificacions parteixen de l'últim escenari vigent i
conserven les colles, els castells i els resultats no modificats. Una consulta independent
o un reinici explícit inicia un escenari nou. Aquesta interpretació es basa en els darrers
12 missatges que envia el client; no afegeix persistència de converses ni memòria fora
d'aquest historial.

Les preguntes obertes com «si les altres colles fan un 3d10fm, quines opcions tinc per
superar-lo?» consulten la taula i reben exemples amb punts abans de demanar actuacions
completes. La resposta distingeix superar el castell indicat de guanyar tota l'actuació.
No estima probabilitats ni optimitza combinacions: les comparacions concretes continuen
passant pel motor de càlcul.
El perfil del creador és al mòdul `backend/adapters/ai/prompts/creator.py`: el xat pot
explicar qui és Andreu Huguet («Mates») i la seva trajectòria, mantenint la seva pròpia
identitat com a assistent d'IA.

El context d'Aleta resumeix les funcionalitats, l'accés, les tarifes, la demo i el suport
de [la web oficial](https://aleta.castellera.cat). Aquestes preguntes aprofiten l'intent
`conversation` i es responen en una sola crida, sense recuperar dades del Concurs ni
calcular punts. Les tarifes i subvencions s'atribueixen a la data de verificació i remeten
a la web per confirmar les condicions; el xat no accedeix a dades privades de les colles
ni fa gestions a Aleta. El mòdul només s'inclou en el prompt d'interpretació.

La comparativa de models usa escenaris sintètics de conversa, modificacions successives
i controls de càlcul i consulta històrica. Executa el mateix servei del xat, sense base de
dades ni registre de converses; els torns successius reben les respostes reals del model.
Amb `OPENROUTER_API_KEY` disponible a l'entorn:

```bash
uv run --frozen python -m scripts.evaluate_chat_models \
  --output /tmp/chat-evaluation.json --repetitions 3
```

Compara Gemini 3.7 Flash, Gemini 3.8 Flash, GPT-6 Luna i Claude Sonnet 5.5 amb el mateix
raonament `low`, l'esquema estricte i la política `data_collection=deny` de producció.
El resultat inclou les respostes, errors, latència, ús i cost reportat per OpenRouter,
i empremtes dels prompts, esquemes i dades de prova. Les comprovacions automàtiques de
resposta conversacional són bàsiques: la qualitat de la prosa també s'ha de revisar.

La [comparativa del 30/09/2026](docs/chat-model-evaluation-20260930.md) inclou resultats,
costos, limitacions i el registre complet de les tres passades dels quatre models.
La [bateria ampliada de Gemini 3.8](docs/gemini38-extended-evaluation-20260930.md) prova
100 situacions i 363 torns, amb diagnòstic separat dels errors del model i del producte.
La [regressió de preguntes obertes](docs/chat-open-scenarios-evaluation-20260930.md)
comprova les opcions parcials de puntuació i la conversa reportada amb Gemini 3.7 i 3.8.

Abans de fusionar un canvi del rànquing, la bateria end-to-end es pot executar contra la URL
real d'una Preview amb:

```bash
uv run --frozen python scripts/smoke_score_ranking_api.py \
  https://preview.example --vercel-auth
```

Les instantànies es poden regenerar manualment, després de revisar les fonts, amb:

```bash
uv run --frozen --no-sync python scripts/update_contest_results.py --verified-at YYYY-MM-DD
uv run --frozen --no-sync python scripts/update_contest_rules.py --verified-at YYYY-MM-DD
```

## App iOS

Obre `HoraAHoraApp/HoraAHoraApp.xcodeproj` i tria l'esquema `HoraAHoraApp`. El projecte referencia el paquet local `Packages/CastellsKit`
i admet iPhone amb iOS 17 o posterior.

La URL del backend es resol en aquest ordre:

1. variable de procés `CASTELLS_API_BASE_URL`, per exemple a l'esquema d'Xcode;
2. clau `CastellsAPIBaseURL` de l'Info.plist, que pren el valor de la build setting
   `CASTELLS_API_BASE_URL`;
3. `https://castells-superapp-poc.vercel.app` com a fallback del codi.

Les builds Release (TestFlight i App Store) apunten sempre a producció,
`https://castells-superapp-poc.vercel.app`, i `make deploy-testflight` atura la pujada si
l'arxiu apunta a una altra URL. Les builds Debug apunten al backend local,
`http://127.0.0.1:8000`, perquè les proves no es barregin amb l'ús real: el simulador hi
arriba quan el backend corre en aquest Mac (vegeu [Backend local](#backend-local)).

Per canviar el backend de les builds Debug en un Mac, crea
`HoraAHoraApp/HoraAHoraApp/Configuration/Debug.local.xcconfig`, que no es versiona, amb una
línia com aquestes. La primera serveix per provar en un iPhone físic contra el backend local
arrencat amb `--host 0.0.0.0`; la segona apunta explícitament a producció:

```
CASTELLS_API_BASE_URL = http:/$()/nom-del-mac.local:8000
CASTELLS_API_BASE_URL = https:/$()/castells-superapp-poc.vercel.app
```

Des de la línia d'ordres també es pot passar `CASTELLS_API_BASE_URL=...` a `xcodebuild`.

Les converses es desen amb SwiftData al dispositiu; el backend rep com a màxim els darrers 12 missatges. Amb «Millora la calculadora» activada (opció per defecte d'Ajustos), l'app marca `share_for_improvement` a les converses començades després de veure l'avís de la calculadora i el backend en desa els missatges i la resposta a `shared_conversations` durant 90 dies, sense identificador d'instal·lació ni IP. El cron diari de manteniment elimina les files caducades.

La política de privacitat es publica a `/privacy` en català, amb selector cap a `/privacy/ca`, `/privacy/es` i `/privacy/en`; són pàgines HTML estàtiques sense JavaScript, cookies ni analítica. Ajustos manté l'enllaç a `/privacy` i concentra el contacte de suport, l'identificador tècnic de la instal·lació, les fonts, els crèdits i la versió de l'app. El correu de suport és editable i mostra versió, build i identificador abans que l'usuari l'enviï manualment; no exporta converses.

### TestFlight

`make deploy-testflight` arxiva l'esquema `HoraAHoraApp` i s'atura si l'arxiu no és `com.ahuguet.castellsenvena`. L'app no té l'entitlement `aps-environment`. El projecte inclou App Icon, privacy manifest i declaració d'exempció de xifrat. Consulta [la checklist de TestFlight](docs/testflight-readiness.md) abans de crear l'archive signat. Els textos suggerits per a la beta són a [testflight-metadata-ca.md](docs/testflight-metadata-ca.md), la [política de privacitat](docs/privacy-policy-ca.md) es publica des del backend i els [canvis futurs de privacitat de l'app](docs/privacy-app-followups.md) queden documentats separadament.

### Versions

La versió visible de les dues apps (CFBundleShortVersionString a iOS, `versionName` a Android)
només és a `Version.xcconfig`, a l'arrel del repositori. L'Xcode la llegeix com a configuració
base del projecte i el Gradle la llegeix del mateix fitxer. Per publicar una versió nova, canvia
`MARKETING_VERSION` en aquest fitxer i fusiona-ho a `main`; els dos scripts de publicació la
prenen del commit que publiquen.

El número de build no es versiona: els dos scripts fan servir els segons Unix UTC, que sempre
creixen. Així iOS (`CURRENT_PROJECT_VERSION`) i Android (`versionCode`) no repeteixen mai un
número que la botiga ja tingui.

Per provar, arxivar i pujar l'últim `origin/main` a TestFlight:

```bash
make deploy-testflight
```

El script actualitza `origin/main`, crea un worktree temporal del commit exacte, arxiva amb la
versió de `Version.xcconfig` i el build Unix i atura la pujada si l'arxiu no coincideix.
Requereix el compte Apple configurat a Xcode. El target de `make` delega a
`scripts/deploy-testflight.sh` i permet passar-li opcions amb `ARGS`. Per inspeccionar el pla,
ometre proves o fixar excepcionalment el build:

```bash
make deploy-testflight ARGS="--dry-run"
make deploy-testflight ARGS="--skip-tests"
make deploy-testflight ARGS="--build-number 1774400000"
```

### Google Play

Per generar l'AAB signat de l'últim `origin/main`:

```bash
make play-bundle
```

El script crea un worktree temporal del commit exacte i compila `:app:bundleRelease` de l'app
amb la versió de `Version.xcconfig` i els segons Unix UTC com a `versionCode`. Comprova
el paquet, la versió i la signatura, i deixa `castells-en-vena-<versió>-<versionCode>.aab` a
`~/Downloads`; després cal pujar-lo a la Play Console. Necessita `bundletool`
(`brew install bundletool`), el SDK d'Android (`ANDROID_HOME`, per defecte
`~/Library/Android/sdk`) i la clau de pujada a `~/.gradle/gradle.properties`
(`castells.signing.storeFile`, `storePassword`, `keyAlias` i `keyPassword`). Opcions:
`--ref`, `--version-code`, `--output-dir` i `--dry-run`.

### Desplegament a Vercel i Supabase

`api/index.py` és un adaptador de lliurament prim que exposa la mateixa aplicació ASGI.
`cdg1` és la regió principal de la funció, però això no implica processament exclusiu dins
la UE. Supabase PostgreSQL a París és la font d'estat de producció del backend: rate limiting
amb identificadors HMAC i converses compartides per millorar la calculadora.

El runtime prioritza `SUPABASE_DATABASE_URL` i conserva `DATABASE_URL` només com a fallback
de rollback. Alembic prioritza `SUPABASE_MIGRATION_DATABASE_URL`, després la connexió de
runtime i finalment el fallback. La connexió de runtime utilitza el pooler de sessió de
Supabase (port `5432`); totes les connexions exigeixen TLS.

Passos de preparació de producció:

1. Crea un projecte Supabase a la mateixa regió que Vercel, o tan a prop com sigui possible.
   Utilitza un projecte diferent per a Preview. Si el límit del pla no ho permet, no defineixis
   `SUPABASE_DATABASE_URL` a Preview: mai no apuntis una Preview a la base de producció.
2. Configura `SUPABASE_DATABASE_URL` només a Production amb la cadena del pooler de sessió.
   Desa també una connexió de sessió o directa com a `SUPABASE_MIGRATION_DATABASE_URL` al
   gestor de secrets des del qual s'executin les migracions.
3. Configura `RATE_LIMIT_HASH_SECRET`, `CRON_SECRET` i les variables `AI_*` com a secrets.
4. Executa les migracions abans de desplegar codi que depengui del nou esquema:

```bash
SUPABASE_MIGRATION_DATABASE_URL='postgresql://…' uv run --frozen alembic upgrade head
SUPABASE_MIGRATION_DATABASE_URL='postgresql://…' uv run --frozen alembic current
```

Per validar una migració en una Preview concreta, aplica-la de manera controlada al projecte
Supabase de Preview abans de provar el codi dependent:

```bash
SUPABASE_MIGRATION_DATABASE_URL='postgresql://…' uv run --frozen alembic upgrade head
```

5. Desplega i comprova `/health/ready`.

Vercel invoca `/internal/cron/maintenance` diàriament, amb el `Bearer CRON_SECRET`: elimina
els comptadors de rate limiting caducats i les converses compartides de més de 90 dies.

## Proves

```bash
uv sync --frozen
uvx ruff==0.16.0 check .
uvx ruff==0.16.0 format --check .
uv run --frozen --no-sync python -m pytest -q
cd HoraAHoraApp/Packages/CastellsKit
swift test
```

El CI crea PostgreSQL 17 i defineix `TEST_DATABASE_URL`; així valida les dues rutes
d'Alembic, els `ON CONFLICT`, la concurrència del rate limiter, els advisory locks i
`FOR UPDATE SKIP LOCKED` amb PostgreSQL real. Sense aquesta variable, aquestes quatre
proves d'integració se salten i la resta de la bateria continua sent local.

La taula oficial versionada és `backend/data/taula_puntuacions_concurs_castells_2026.csv`. El motor aplica tres millors castells, màxim dos carregats, intents, estructures repetides i àlies explícits com `4d9net -> 4de9sf`.

La pestanya Puntuacions de l'app porta una còpia en JSON d'aquesta taula, amb el nom de cada
castell en català per als lectors de pantalla. Després de canviar el CSV, regenera-la; una prova
comprova que no quedi desfasada:

```bash
uv run --frozen --no-sync python -m scripts.export_score_table
```
