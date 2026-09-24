# Super-app castellera

Primera fase d'una app iOS modular amb quatre seccions natives: Hora a Hora, Agenda, una calculadora conversacional i Ajustos. El backend és una aplicació ASGI portable i no exposa cap proveïdor d'IA ni infraestructura concreta al domini o al contracte HTTP.

El nom visible i definitiu de l'app és **Castells en vena** i el Bundle ID de distribució és `com.ahuguet.castellsenvena`.

## Estructura

- `HoraAHoraApp/HoraAHoraApp`: composició, navegació, notificacions i configuració iOS.
- `HoraAHoraApp/Packages/CastellsKit`: paquet Swift local amb domini, dades i features independents.
- `backend/domain`: models, ports i motor de puntuació determinista.
- `backend/application`: casos d'ús.
- `backend/adapters`: IA, Revista Castells, El Món Casteller, persistència i rate limiting.
- `backend/api`: routers i esquemes HTTP separats per contracte.
- `tests`: proves del domini, ingesta, contractes d'IA i API.
- `openapi/partner-api.yaml`: contracte reduït per a clients i reunions amb socis.
- `docs/architecture.md`: límits modulars i dependències permeses.
- `docs/integracio-socis.md`: proposta de col·laboració amb Revista Castells i la CCCC.
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
docker compose --profile ingestion up --build
```

L'API queda disponible a `http://127.0.0.1:8000` i la documentació interactiva a `/docs`. Compose aporta PostgreSQL 17; tot l'estat compartit del backend viu en aquesta base i no hi ha cap fallback SQLite o en memòria al runtime. Les fonts de l'Hora a Hora es poden desactivar amb `HOUR_BY_HOUR_SOURCE_ENABLED=false`.

### Fonts de l'Hora a Hora

La sincronització combina l'HTML de Revista Castells amb els feeds RSS públics d'El Món
Casteller de [notícies](https://www.elmoncasteller.cat/category/noticies/feed/),
[opinió](https://www.elmoncasteller.cat/category/opinio/feed/),
[entrevistes](https://www.elmoncasteller.cat/category/entrevistes/feed/) i
[cròniques](https://www.elmoncasteller.cat/category/cronica/feed/). Cada article conserva
el titular, el resum publicat al feed, la data, l'atribució i l'enllaç al web original.
Els articles compartits entre categories només apareixen una vegada i la llista combina
les fonts per data de publicació. Es carreguen les entrades disponibles als feeds;
no es recorre tot l'arxiu històric.

El job manual `python -m backend.jobs.sync_hour_by_hour` i el cron utilitzen les mateixes
fonts. La primera ingesta de cada mitjà crea una base sense avisos antics; les següents
només notifiquen articles nous. Si falla un mitjà, es conserva el contingut desat i
s'actualitza l'altre, deixant constància de l'error al log. Les quatre categories d'El Món
Casteller es carreguen conjuntament per evitar inicialitzar una base incompleta.

### Agenda de la CCCC

`AGENDA_SOURCE` selecciona un adaptador intercanviable:

- `fixture`: dades simulades locals, identificades com a no oficials, per al simulador i les proves;
- `cccc_snapshot`: instantània oficial autoritzada per sembrar la base de dades de la POC;
- `disabled`: integració desactivada, valor segur per defecte fora de Compose;
- `cccc_html`: consulta mensual de l'HTML de la CCCC, només després d'obtenir autorització escrita.

El mode real exigeix també `CCCC_AGENDA_AUTHORIZED=true`; si no, el backend falla a l'arrencada per evitar una activació accidental. Per a aquesta POC hi ha permís explícit de la CCCC. La font real conserva atribució i enllaç de retorn, i l'app desa també una cache SwiftData per consultar els dies carregats sense connexió.

L'API no consulta la CCCC quan un usuari obre l'agenda (`AGENDA_REFRESH_ON_REQUEST=false`). La sincronització automàtica queda desactivada mentre la font bloquegi clients automatitzats. El servei local `agenda-sync`, disponible només amb el perfil opcional `ingestion`, permet provar un pre-fetch seqüencial; una fallada no elimina l'última còpia vàlida. La sincronització també es pot executar manualment:

```bash
AGENDA_SOURCE=cccc_html CCCC_AGENDA_AUTHORIZED=true \
python -m backend.jobs.sync_agenda --from-month 2026-07 --to-month 2027-07
```

Cloudflare respon actualment amb un repte als clients HTTP automatitzats. Cal que la CCCC habiliti el client autoritzat (whitelist, token o feed) perquè el job diari pugui refrescar directament. Mentrestant, la POC es pot sembrar amb la instantània oficial capturada el 21 de juliol de 2026, sense dades inventades:

```bash
AGENDA_SOURCE=cccc_snapshot CCCC_AGENDA_AUTHORIZED=true \
python -m backend.jobs.sync_agenda --from-month 2026-07 --to-month 2026-07
```

`GET /v1/groups` serveix un snapshot versionat dels noms del directori públic de colles,
incloses les categories actives, discontínues, en formació, universitàries i de l'exterior.
No consulta la web de la CCCC en temps d'execució. L'app en conserva una còpia a
`UserDefaults`, la combina amb les colles observades a l'agenda i aplica el filtre només al
dispositiu; les preferències de seguiment se sincronitzen amb el backend quan les notificacions estan actives.

### Interpretació de consultes

La calculadora requereix un proveïdor de model explícit: `AI_PROVIDER=openrouter`,
`AI_PROVIDER=openai` o `AI_PROVIDER=anthropic`. La configuració de producció recomanada és
OpenRouter amb `AI_MODEL=google/gemini-3.7-flash`, `AI_BASE_URL=https://openrouter.ai/api`
i raonament baix. El model, la clau i l'endpoint es configuren amb `AI_MODEL`, `AI_API_KEY`
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
- `contest_router.py`: consulta estructurada per font, anys, colles i abast;
- `response_policy.py`: límits, atribució temporal i prohibició d'inventar dades;
- `adapters/contest/snapshot.py`: selecció local de la porció rellevant de normativa o
  resultats i composició del rànquing de puntuacions;
- `composer.py`: prompt base d'interpretació i prompt de resolució amb el context recuperat.

OpenAI i Anthropic consumeixen els mateixos contractes. Una consulta de càlcul fa una sola
petició estructurada i passa directament al motor determinista. Una consulta del Concurs fa
una primera petició d'encaminament, recupera només les edicions, colles o fonts necessàries i
fa una segona petició de resolució. Una resposta que no compleix l'esquema falla de manera
explícita: no es reintenta amb un prompt alternatiu ni s'accepten formats antics del proveïdor.

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

Obre `HoraAHoraApp/HoraAHoraApp.xcodeproj`. El projecte referencia el paquet local `Packages/CastellsKit` i admet iPhone amb iOS 17 o posterior.

La URL del backend es resol en aquest ordre:

1. variable de procés `CASTELLS_API_BASE_URL`;
2. clau `CastellsAPIBaseURL` de l'Info.plist generat;
3. `https://castells-superapp-poc.vercel.app` com a fallback del codi.

Les configuracions Debug i Release apunten per defecte al backend POC desplegat a
`https://castells-superapp-poc.vercel.app`. Per treballar contra el backend local al
simulador, defineix `CASTELLS_API_BASE_URL=http://127.0.0.1:8000` a l'esquema d'Xcode.

En un iPhone físic cal indicar una URL accessible des del dispositiu. Les converses i les còpies de l'Hora a Hora i l'Agenda es desen només amb SwiftData al dispositiu; el backend rep com a màxim els darrers 12 missatges i no persisteix cap conversa.

Les notificacions de l'Hora a Hora no demanen permís en arrencar l'app. En una instal·lació nova, la secció mostra un onboarding descartable; «Configura-ho» obre la pestanya Ajustos. Des d'allà es poden activar o desactivar els avisos; si el permís s'havia denegat a iOS, l'app obre directament els ajustos del sistema per recuperar-lo. Quan APNs lliura o rota el token, l'app el registra al backend amb l'identificador aleatori d'instal·lació; en desactivar els avisos, en demana la revocació i reintenta si estava sense connexió. Les compilacions Debug indiquen l'entorn APNs `development`; TestFlight i Release indiquen `production`.

La política de privacitat es publica a `/privacy` en català, amb selector cap a `/privacy/ca`, `/privacy/es` i `/privacy/en`; són pàgines HTML estàtiques sense JavaScript, cookies ni analítica. Ajustos manté l'enllaç a `/privacy` i concentra el contacte de suport, l'identificador tècnic de la instal·lació, les fonts, els crèdits i la versió de l'app. El correu de suport és editable i mostra versió, build i identificador abans que l'usuari l'enviï manualment; no exporta converses.

### TestFlight

El projecte inclou App Icon, privacy manifest, declaració d'exempció de xifrat i configuració APNs diferenciada entre Debug i Release. Consulta [la checklist de TestFlight](docs/testflight-readiness.md) abans de crear l'archive signat. Els textos suggerits per a la beta són a [testflight-metadata-ca.md](docs/testflight-metadata-ca.md), la [política de privacitat](docs/privacy-policy-ca.md) es publica des del backend i els [canvis futurs de privacitat de l'app](docs/privacy-app-followups.md) queden documentats separadament.

Per provar, arxivar i pujar l'últim `origin/main` amb una versió de màrqueting explícita
i un número de build únic:

```bash
make deploy-testflight ARGS="--marketing-version 1.1"
```

El script actualitza `origin/main`, crea un worktree temporal del commit exacte i utilitza
els segons Unix UTC com a `CURRENT_PROJECT_VERSION`; així el build creix sense modificar
el projecte ni crear un commit només per canviar-ne el número. Requereix el compte Apple
configurat a Xcode. El target de `make` delega a `scripts/deploy-testflight.sh` i permet
passar-li opcions amb `ARGS`. `--marketing-version` permet obrir una train nova quan
App Store Connect tanca la versió que ja s'ha aprovat per a producció. Per inspeccionar
el pla, ometre proves o fixar excepcionalment el build:

```bash
make deploy-testflight ARGS="--dry-run --marketing-version 1.1"
make deploy-testflight ARGS="--skip-tests --marketing-version 1.1"
make deploy-testflight ARGS="--marketing-version 1.1 --build-number 1774400000"
```

### Desplegament a Vercel i Supabase

`api/index.py` és un adaptador de lliurament prim que exposa la mateixa aplicació ASGI.
`cdg1` és la regió principal de la funció, però això no implica processament exclusiu dins
la UE. Supabase PostgreSQL a París és la font d'estat de producció del backend: contingut,
agenda, sincronitzacions, rate limiting amb identificadors HMAC, subscripcions push, outbox
i entregues.

El runtime prioritza `SUPABASE_DATABASE_URL` i conserva `DATABASE_URL` només com a fallback
de rollback. Alembic prioritza `SUPABASE_MIGRATION_DATABASE_URL`, després la connexió de
runtime i finalment el fallback. La connexió de runtime utilitza el pooler de sessió de
Supabase (port `5432`) perquè els jobs fan servir advisory locks de sessió; totes les
connexions exigeixen TLS.

Passos de preparació de producció:

1. Crea un projecte Supabase a la mateixa regió que Vercel, o tan a prop com sigui possible.
   Utilitza un projecte diferent per a Preview. Si el límit del pla no ho permet, no defineixis
   `SUPABASE_DATABASE_URL` a Preview: mai no apuntis una Preview a la base de producció.
2. Configura `SUPABASE_DATABASE_URL` només a Production amb la cadena del pooler de sessió.
   Desa també una connexió de sessió o directa com a `SUPABASE_MIGRATION_DATABASE_URL` al
   gestor de secrets des del qual s'executin les migracions.
3. Configura `RATE_LIMIT_HASH_SECRET`, `CRON_SECRET`, `APNS_KEY_P8`, `APNS_KEY_ID`,
   `APNS_TEAM_ID` i `APNS_BUNDLE_ID` com a secrets. Mantén `PUSH_DELIVERY_ENABLED=false`
   al primer desplegament i sempre a Preview.
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

5. Sembra l'estat inicial de l'Hora a Hora sense enviar notificacions antigues i carrega
   l'instantània autoritzada de l'agenda:

```bash
vercel env run -e production -- \
  uv run --frozen python -m backend.jobs.sync_hour_by_hour
vercel env run -e production -- \
  env AGENDA_SOURCE=cccc_snapshot CCCC_AGENDA_AUTHORIZED=true \
  uv run --frozen python -m backend.jobs.sync_agenda \
  --from-month 2026-07 --to-month 2026-07
```

6. Desplega, comprova `/health/ready`, publica la beta que registra tokens i fes una prova
   dirigida abans d'activar `PUSH_DELIVERY_ENABLED=true`.

Vercel Pro invoca `/internal/cron/hour-by-hour` cada minut i `/internal/cron/maintenance`
diàriament. Tots dos exigeixen el `Bearer CRON_SECRET`; l'outbox, les restriccions úniques
i l'advisory lock de PostgreSQL fan que execucions duplicades siguin idempotents.

## Notificacions personalitzades amb Jev

El servidor classifica cada notícia nova una vegada amb Jev (`jev-1.13.0`), tant de Revista
Castells com d'El Món Casteller. La rellevància general és Low (rutinària), Medium
(interessant) o High (breaking news). Una coincidència amb les colles seguides a l'Agenda
puja un nivell, amb màxim High; «Totes» i una selecció buida no apliquen cap pujada.
L'app ofereix el selector a Ajustos, amb High per a noves activacions i Low per als
usuaris que ja tenien avisos actius. Els destacats de l'Agenda no afecten la regla.

Configura `JEV_API_KEY` només al servidor i `JEV_MODEL=jev-1.13.0`. La clau és independent
de `AI_API_KEY`. El contracte `PUT /v1/push-subscriptions/{installation_id}` accepta
`minimum_interest` (`low`, `medium`, `high`) i `group_selection`
(`{"mode":"custom","keys":["castellers de vilafranca"]}` o `{"mode":"all","keys":[]}`).
Les peticions antigues preserven els valors existents, amb Low i totes com a defaults.

L'outbox conserva l'estat de classificació i el resultat, amb model, criteris i probabilitats.
Les preferències de l'audiència es capturen en detectar la novetat i es buiden en acabar.
El cron revalida la preferència actual abans de reclamar les entregues. Les pujades de
llindar poden suprimir avisos pendents; abaixar-lo o seguir colles no recupera avisos antics.
Els errors de Jev són omissions definitives; els errors transitoris d'APNs es reintenten.
Si s'esgota el pressupost, les classificacions no iniciades queden per al següent cron.
Un intent interromput es marca omès en recuperar el bloqueig. Les crides Jev no mantenen
cap transacció d'escriptura oberta i les dues rutes d'ingesta comparteixen l'advisory lock.

Per validar el model en català sense escriure a la base de dades ni enviar avisos:

```bash
uv run --env-file .env.jev.local python -m scripts.smoke_jev_news --live-count 5
```

El fitxer local amb la clau ha de quedar fora de Git i Vercel. El smoke mostra nivells,
colles, latència i consum, sense mostrar credencials. Els logs de classificació i el cron
exposen `classified` i `classification_skipped` per diagnosticar omissions.

Desplegament: configurar el secret, aplicar Alembic (`20260924_06`), desplegar el backend
compatible i verificar-lo; després publicar l'app iOS. No reclassificar ni notificar
l'històric. Els outboxes previs a la migració només mantenen entregues ja pendents per a
subscripcions Low. Un rollback de codi pot mantenir les columnes additives; no rebaixar
l'esquema mentre hi hagi instàncies del backend nou en execució.

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
