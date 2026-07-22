# Super-app castellera

Primera fase d'una app iOS modular amb quatre seccions natives: Hora a Hora, Agenda, una calculadora conversacional i Ajustos. El backend és una aplicació ASGI portable i no exposa cap proveïdor d'IA ni infraestructura concreta al domini o al contracte HTTP.

El nom visible i definitiu de l'app és **Castells en vena** i el Bundle ID de distribució és `com.ahuguet.castellsenvena`.

## Estructura

- `HoraAHoraApp/HoraAHoraApp`: composició, navegació, notificacions i configuració iOS.
- `HoraAHoraApp/Packages/CastellsKit`: paquet Swift local amb domini, dades i features independents.
- `backend/domain`: models, ports i motor de puntuació determinista.
- `backend/application`: casos d'ús.
- `backend/adapters`: IA, Revista Castells, persistència i rate limiting.
- `backend/api`: esquemes HTTP neutrals.
- `tests`: proves del domini, ingesta, contractes d'IA i API.
- `openapi/partner-api.yaml`: contracte reduït per a clients i reunions amb socis.
- `docs/integracio-socis.md`: proposta de col·laboració amb Revista Castells i la CCCC.
- `docs/testflight-readiness.md`: estat tècnic i passos manuals necessaris per distribuir la beta.

## Backend local

Amb Python 3.11 o posterior:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
docker compose up -d db
set -a && source .env && set +a
alembic upgrade head
uvicorn api.index:app --reload
```

O amb infraestructura local completa:

```bash
cp .env.example .env
docker compose --profile ingestion up --build
```

L'API queda disponible a `http://127.0.0.1:8000` i la documentació interactiva a `/docs`. Compose aporta PostgreSQL 17; tot l'estat compartit del backend viu en aquesta base i no hi ha cap fallback SQLite o en memòria al runtime. L'adaptador HTML es pot desactivar amb `HOUR_BY_HOUR_SOURCE_ENABLED=false`.

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

### Interpretació de consultes

`AI_PROVIDER=local` usa l'intèrpret determinista inclòs, sense claus externes. També hi ha adaptadors desacoblats per `openai` i `anthropic`; el model, la clau i un endpoint compatible es configuren amb `AI_MODEL`, `AI_API_KEY` i `AI_BASE_URL`. Tots validen la mateixa sortida estructurada abans d'invocar el motor de puntuació.

## App iOS

Obre `HoraAHoraApp/HoraAHoraApp.xcodeproj`. El projecte referencia el paquet local `Packages/CastellsKit` i admet iPhone i iPad amb iOS 17 o posterior.

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

### Desplegament a Vercel i Neon

`api/index.py` és un adaptador de lliurament prim que exposa la mateixa aplicació ASGI.
`cdg1` és la regió principal de la funció, però això no implica processament exclusiu dins
la UE. Neon PostgreSQL, vinculat des del Marketplace de Vercel, és l'única font d'estat
del backend: contingut, agenda, sincronitzacions, rate limiting amb identificadors HMAC,
subscripcions push, outbox i entregues.

Passos de preparació de producció:

1. Instal·la Neon des del Marketplace de Vercel, amb la branca principal per a Production i branques aïllades per a Preview.
2. Configura `RATE_LIMIT_HASH_SECRET`, `CRON_SECRET`, `APNS_KEY_P8`, `APNS_KEY_ID`, `APNS_TEAM_ID` i `APNS_BUNDLE_ID` com a secrets. Mantén `PUSH_DELIVERY_ENABLED=false` al primer desplegament i sempre a Preview.
3. Executa les migracions abans de desplegar codi que depengui del nou esquema:

```bash
vercel env run -e production -- alembic upgrade head
vercel env run -e production -- alembic current
```

Per validar una migració en una Preview concreta, aplica-la de manera controlada a la
branca Neon que la integració hagi creat, abans de provar el codi dependent:

```bash
vercel env run -e preview --git-branch nom-de-la-branca -- alembic upgrade head
```

4. Sembra l'estat inicial de l'Hora a Hora sense enviar notificacions antigues i carrega l'instantània autoritzada de l'agenda:

```bash
vercel env run -e production -- python -m backend.jobs.sync_hour_by_hour
vercel env run -e production -- \
  env AGENDA_SOURCE=cccc_snapshot CCCC_AGENDA_AUTHORIZED=true \
  python -m backend.jobs.sync_agenda --from-month 2026-07 --to-month 2026-07
```

5. Desplega, comprova `/health/ready`, publica la beta que registra tokens i fes una prova dirigida abans d'activar `PUSH_DELIVERY_ENABLED=true`.

Vercel Pro invoca `/internal/cron/hour-by-hour` cada minut i `/internal/cron/maintenance`
diàriament. Tots dos exigeixen el `Bearer CRON_SECRET`; l'outbox, les restriccions úniques
i l'advisory lock de PostgreSQL fan que execucions duplicades siguin idempotents.

## Proves

```bash
python3 -m pytest -q
cd HoraAHoraApp/Packages/CastellsKit
swift test
```

El CI crea PostgreSQL 17 i defineix `TEST_DATABASE_URL`; així valida les dues rutes
d'Alembic, els `ON CONFLICT`, la concurrència del rate limiter, els advisory locks i
`FOR UPDATE SKIP LOCKED` amb PostgreSQL real. Sense aquesta variable, aquestes quatre
proves d'integració se salten i la resta de la bateria continua sent local.

La taula oficial versionada és `backend/data/taula_puntuacions_concurs_castells_2026.csv`. El motor aplica tres millors castells, màxim dos carregats, intents, estructures repetides i àlies explícits com `4d9net -> 4de9sf`.
