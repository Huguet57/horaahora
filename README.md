# Super-app castellera

Primera fase d'una app iOS modular amb quatre seccions natives: Hora a Hora, Agenda, una calculadora conversacional i Ajustos. El backend és una aplicació ASGI portable i no exposa cap proveïdor d'IA ni infraestructura concreta al domini o al contracte HTTP.

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
AGENDA_SOURCE=cccc_html CCCC_AGENDA_AUTHORIZED=true uvicorn backend.app:app --reload
```

O amb infraestructura local completa:

```bash
cp .env.example .env
docker compose --profile ingestion up --build
```

L'API queda disponible a `http://127.0.0.1:8000` i la documentació interactiva a `/docs`. Compose aporta PostgreSQL i Redis. L'adaptador HTML es pot desactivar amb `HOUR_BY_HOUR_SOURCE_ENABLED=false`.

### Agenda de la CCCC

`AGENDA_SOURCE` selecciona un adaptador intercanviable:

- `fixture`: dades simulades locals, identificades com a no oficials, per al simulador i les proves;
- `cccc_snapshot`: instantània oficial autoritzada per sembrar la base de dades de la POC;
- `disabled`: integració desactivada, valor segur per defecte fora de Compose;
- `cccc_html`: consulta mensual de l'HTML de la CCCC, només després d'obtenir autorització escrita.

El mode real exigeix també `CCCC_AGENDA_AUTHORIZED=true`; si no, el backend falla a l'arrencada per evitar una activació accidental. Per a aquesta POC hi ha permís explícit de la CCCC. La font real conserva atribució i enllaç de retorn, i l'app desa també una cache SwiftData per consultar els dies carregats sense connexió.

L'API no consulta la CCCC quan un usuari obre l'agenda (`AGENDA_REFRESH_ON_REQUEST=false`). El servei `agenda-sync` fa el pre-fetch seqüencial de mesos complets, els valida i els substitueix atòmicament a PostgreSQL cada 24 hores. Una fallada no elimina l'última còpia vàlida. La sincronització també es pot executar manualment:

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

Les notificacions de l'Hora a Hora no demanen permís en arrencar l'app. En una instal·lació nova, la secció mostra un onboarding descartable; «Configura-ho» obre la pestanya Ajustos. Des d'allà es poden activar o desactivar els avisos; si el permís s'havia denegat a iOS, l'app obre directament els ajustos del sistema per recuperar-lo.

La política de privacitat es publica a `/privacy` en català, castellà i anglès. Ajustos també concentra el correu de suport revisable, l'identificador tècnic de la instal·lació, les fonts i els crèdits, i la versió de l'app.

### TestFlight

El projecte inclou App Icon, privacy manifest, declaració d'exempció de xifrat i configuració APNs diferenciada entre Debug i Release. Consulta [la checklist de TestFlight](docs/testflight-readiness.md) abans de crear l'archive signat. Els textos suggerits per a la beta són a [testflight-metadata-ca.md](docs/testflight-metadata-ca.md) i hi ha un [esborrany de política de privacitat](docs/privacy-policy-draft-ca.md) que s'ha de completar i publicar abans d'una beta externa.

### Desplegament POC a Vercel

`api/index.py` és un adaptador de lliurament prim que exposa la mateixa aplicació ASGI.
La configuració de Vercel selecciona OpenAI amb `AI_PROVIDER` i `AI_MODEL`, però la clau
només existeix com a variable sensible del projecte. La font HTML autoritzada de la CCCC
es consulta amb refresc a demanda i cache en una base
SQLite temporal. Aquesta configuració és adequada per a la prova de concepte; abans de
producció cal substituir-la per PostgreSQL i una sincronització programada.

## Proves

```bash
python3 -m pytest -q
cd HoraAHoraApp/Packages/CastellsKit
swift test
```

La taula oficial versionada és `backend/data/taula_puntuacions_concurs_castells_2026.csv`. El motor aplica tres millors castells, màxim dos carregats, intents, estructures repetides i àlies explícits com `4d9net -> 4de9sf`.
