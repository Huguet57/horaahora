# La calculadora de l'Aleta

App nativa per a iOS i Android centrada en una calculadora castellera conversacional i en la
taula de puntuacions del Concurs de Castells 2026. L'app pública té tres pestanyes: Calculadora,
Puntuacions i Ajustos. Hora a Hora, Agenda, els seus ajustos i els avisos de notícies només són a
l'app interna de desenvolupament (vegeu [App pública i app interna](#app-pública-i-app-interna)).
El backend és una aplicació ASGI portable i no exposa cap proveïdor d'IA ni infraestructura
concreta al domini o al contracte HTTP.

El nom visible de l'app pública és **La calculadora de l'Aleta** (abans, Castells en vena). El
Bundle ID d'iOS i l'`applicationId` d'Android es mantenen: `com.ahuguet.castellsenvena`.

## Estructura

- `HoraAHoraApp/HoraAHoraApp`: codi compartit de les dues apps iOS (configuració, arrencada,
  navegació i dependències comunes); `Public/` i `Internal/` en tenen l'entrada i la composició.
- `HoraAHoraApp/Packages/CastellsKit`: paquet Swift local amb domini, dades i features independents.
- `android`: app Android nativa (Kotlin i Jetpack Compose) amb mòduls `core` i `feature`; vegeu `android/README.md`.
- `backend/domain`: models, ports i motor de puntuació determinista.
- `backend/application`: casos d'ús.
- `backend/adapters`: IA, Revista Castells, El Món Casteller, persistència i rate limiting.
- `backend/api`: routers i esquemes HTTP separats per contracte.
- `tests`: proves del domini, ingesta, contractes d'IA i API.
- `openapi/partner-api.yaml`: contracte reduït per a clients i reunions amb socis.
- `docs/architecture.md`: límits modulars i dependències permeses.
- `docs/integracio-socis.md`: proposta de col·laboració amb Revista Castells i la CCCC.
- `docs/testflight-readiness.md`: estat tècnic i passos manuals necessaris per distribuir la beta.

## App pública i app interna

El perfil de compilació tria quina app es genera. És `public` per defecte i no es pot canviar
remotament ni des de l'app instal·lada:

| | App pública (`public`) | App interna (`internal`) |
| --- | --- | --- |
| Per a | App Store, TestFlight i Google Play | Desenvolupament; mai no es puja a les botigues |
| Identificador | `com.ahuguet.castellsenvena` | `com.ahuguet.castellsenvena.internal` |
| Nom i icona | «La calculadora de l'Aleta» | «Aleta interna», icona fosca (a iOS, amb la franja «INTERNA») |
| Seccions | Calculadora, Puntuacions i Ajustos | Les mateixes, més Hora a Hora i Agenda, ocultes fins al gest secret |
| Avisos de notícies | Cap: sense permís, entitlement `aps-environment`, Firebase ni deep links | Com fins ara |
| iOS | Target i esquema `HoraAHoraApp` | Target i esquema `HoraAHoraAppInternal` |
| Android | Flavor `public` | Flavor `internal`, versió amb el sufix `-internal` |

Les dues apps comparteixen la calculadora, la taula de puntuacions i els ajustos de la
calculadora. L'app pública no enllaça els mòduls d'Hora a Hora, Agenda ni els ajustos interns, i
no conté cap punt d'entrada cap a ells. Conserva, però, l'esquema complet de la base de dades
local, amb les còpies d'Hora a Hora i Agenda de les versions anteriors, perquè les
actualitzacions mantinguin les converses sense cap migració. Per això la capa de dades compartida
(`CastellsData` i `:core:data`) encara conté el codi de dades d'aquestes seccions, que l'app
interna fa servir i l'app pública no crida enlloc.

Les ordres de `make` fan servir `CASTELLS_BUILD_PROFILE=public|internal` (també com a variable
d'entorn); qualsevol altre valor atura la compilació:

```bash
make ios-build ios-verify                                  # app pública, Release sense signar
make ios-build ios-verify CASTELLS_BUILD_PROFILE=internal  # app interna
make android-build android-lint android-verify             # APK públics de depuració i publicació
make android-install CASTELLS_BUILD_PROFILE=internal       # app interna al dispositiu connectat
```

`ios-verify` i `android-verify` inspeccionen el que s'acaba de compilar amb el paquet
`scripts/app_profiles`: l'app pública no pot contenir els mòduls interns, els avisos ni
Firebase, i l'app interna els ha de conservar amb el seu identificador. A Xcode, tria l'esquema
`HoraAHoraApp` o `HoraAHoraAppInternal`. A Gradle i Android Studio, les variants que existeixen són
les del perfil triat: passa `-Pcastells.buildProfile=internal`, defineix
`CASTELLS_BUILD_PROFILE=internal` o afegeix `castells.buildProfile=internal` a
`~/.gradle/gradle.properties`.

Quan una instal·lació que tenia avisos de notícies passa a l'app pública, l'app els retira la
primera vegada que s'obre: els treu del sistema (a iOS deixa de registrar-se a APNs i elimina les
notificacions lliurades; a Android esborra el canal «Avisos de notícies») i dona de baixa la
subscripció al backend. Si no hi ha connexió, ho torna a provar en cada arrencada i en tornar a
primer pla fins que el backend ho confirma. No torna a subscriure mai, encara que quedin les
preferències antigues o el permís del sistema. Les instal·lacions noves no fan cap petició.

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

`HOUR_BY_HOUR_SOURCES` tria quines d'aquestes fonts es llegeixen, separades per comes:
`el-mon-casteller` i `revista-castells`. Ara totes dues estan donades de baixa i la
llista és buida per defecte: el cron no llegeix cap web, però continua enviant els avisos
pendents. Per donar de baixa una font o tornar-la a donar d'alta, canvia la llista a
l'entorn de producció (o al `.env` en local) i torna a desplegar. Les notícies ja desades
d'una font donada de baixa continuen a la llista amb la seva atribució.
Mentre una font està donada de baixa, cada sincronització n'oblida la base d'avisos.
Així, la primera lectura després de tornar-la a donar d'alta crea una base nova: les
notícies publicades entretant apareixen a la llista sense avisos i només es notifiquen
les posteriors.

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

Obre `HoraAHoraApp/HoraAHoraApp.xcodeproj` i tria l'esquema `HoraAHoraApp` (app pública) o
`HoraAHoraAppInternal` (app interna). El projecte referencia el paquet local `Packages/CastellsKit`
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

Les converses i les còpies de l'Hora a Hora i l'Agenda es desen amb SwiftData al dispositiu; el backend rep com a màxim els darrers 12 missatges. Amb «Millora la calculadora» activada (opció per defecte d'Ajustos), l'app marca `share_for_improvement` a les converses començades després de veure l'avís de la calculadora i el backend en desa els missatges i la resposta a `shared_conversations` durant 90 dies, sense identificador d'instal·lació ni IP. El cron diari de manteniment elimina les files caducades.

A l'app interna, les notificacions de l'Hora a Hora no demanen permís en arrencar. En una instal·lació nova, la secció mostra un onboarding descartable; «Configura-ho» obre la pestanya Ajustos. Des d'allà es poden activar o desactivar els avisos; si el permís s'havia denegat a iOS, l'app obre directament els ajustos del sistema per recuperar-lo. Quan APNs lliura o rota el token, l'app el registra al backend amb l'identificador aleatori d'instal·lació; en desactivar els avisos, en demana la revocació i reintenta si estava sense connexió. Les compilacions Debug indiquen l'entorn APNs `development`; TestFlight i Release indiquen `production`.

La política de privacitat es publica a `/privacy` en català, amb selector cap a `/privacy/ca`, `/privacy/es` i `/privacy/en`; són pàgines HTML estàtiques sense JavaScript, cookies ni analítica. Ajustos manté l'enllaç a `/privacy` i concentra el contacte de suport, l'identificador tècnic de la instal·lació, les fonts, els crèdits i la versió de l'app. El correu de suport és editable i mostra versió, build i identificador abans que l'usuari l'enviï manualment; no exporta converses.

### TestFlight

TestFlight i l'App Store només reben l'app pública: `make deploy-testflight` arxiva l'esquema `HoraAHoraApp` i s'atura si `CASTELLS_BUILD_PROFILE` no és `public` o si l'arxiu no és `com.ahuguet.castellsenvena`. L'app pública no té l'entitlement `aps-environment`. El projecte inclou App Icon, privacy manifest i declaració d'exempció de xifrat, i l'app interna té la configuració APNs diferenciada entre Debug i Release. Consulta [la checklist de TestFlight](docs/testflight-readiness.md) abans de crear l'archive signat. Els textos suggerits per a la beta són a [testflight-metadata-ca.md](docs/testflight-metadata-ca.md), la [política de privacitat](docs/privacy-policy-ca.md) es publica des del backend i els [canvis futurs de privacitat de l'app](docs/privacy-app-followups.md) queden documentats separadament.

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
   `APNS_TEAM_ID` i `APNS_BUNDLE_ID` com a secrets. Per als avisos d'Android, afegeix
   `FCM_SERVICE_ACCOUNT_JSON` (la clau JSON d'un compte de servei del projecte Firebase amb
   permís per enviar missatges) i, si cal, `ANDROID_PACKAGE_NAME`. Sense aquesta clau, les
   entregues d'Android es marquen `PushServiceNotConfigured` i iOS continua funcionant.
   Mantén `PUSH_DELIVERY_ENABLED=false` al primer desplegament i sempre a Preview.
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
(interessant) o High (fites històriques i breaking news). Una coincidència amb les colles
seguides a l'Agenda puja un nivell, amb màxim High; «Totes» i una selecció buida no
apliquen cap pujada.
L'app interna ofereix el selector a Ajustos, amb High per a noves activacions i Low per als
usuaris que ja tenien avisos actius. Els destacats de l'Agenda no afecten la regla.

Els criteris són tres definicions generals, sense excepcions per notícia o colla:
Low per informació rutinària, Medium per actualitat interessant i High per fets
excepcionals, diades històriques i castells inèdits d'una colla, tant anunciats com
assolits. La fita es valora a escala de cada colla. Jev utilitza el títol, el resum i
el cos públic de l’article quan està disponible, i no ha d’inventar el context
històric que hi falti. Les recuperacions i els millors registres de temporada són
Medium; High requereix una fita històrica o un fet excepcional actual.

Abans de la petició única a Jev, el backend llegeix la destinació de la notícia:
la crònica, el post públic o la transcripció disponible. L’outbox conserva per separat
la URL de la notícia original i la destinació de l’avís, tal com eren en detectar-la.
Si coincideixen, el text es marca `article_body`; si són diferents, `linked_context`.
Els enllaços de context poden ampliar el fet actual, però els seus fets antics o
altres protagonistes no han de substituir la notícia. Aquesta distinció s’aplica
tant a l’interès com a les colles. Les files antigues sense procedència coneguda
utilitzen conservadorament `linked_context`. Admet Revista Castells,
El Món Casteller, Instagram, X, YouTube, 3Cat i el Diari Digital de la URV. Conserva
el text editorial, els peus de publicacions i les transcripcions públiques, amb un
límit de 20.000 caràcters, 2 MB d’HTML i 5 segons de lectura. Només elimina elements
aliens com menús, scripts, publicitat i recomanacions; també llegeix descripcions
públiques d’Instagram i YouTube encara que no hi hagi un cos HTML convencional.

Els enllaços no admesos (incloent-hi PDF), les stories sense text públic, les notes
sense cos i els errors de lectura fan servir el títol i el resum. No es busquen
altres articles per completar una nota breu. La lectura es fa fora de transaccions
d’escriptura; si esgota el pressupost del cron abans de cridar Jev, la notícia queda
pendent per a la següent execució. L’outbox registra el tipus i la URL del text
addicional, la longitud i el SHA-256 del cos de la petició. Els logs inclouen aquest
hash, el tipus d’entrada, la latència, el consum i els errors de lectura. No es
desa el cos complet a la base de dades.

El catàleg d'àlies és a `backend/adapters/ai/group_aliases.py`, amb una entrada explícita
per a cadascuna de les 118 colles del directori, incloses les universitàries i internacionals.
Combina sobrenoms documentats, noms abreujats distintius i variants descriptives completes
per a les colles sense sobrenom conegut. No s'utilitzen topònims sols ni sigles inventades.
Les fonts són al mateix fitxer; les proves exigeixen cobertura del directori i àlies
sense duplicats entre colles. Els canvis al catàleg han d'incrementar `CRITERIA_VERSION`
(actualment `castells-interest-v8`), ja que poden modificar les classificacions futures.

Configura `JEV_API_KEY` només al servidor i `JEV_MODEL=jev-1.13.0`. La clau és independent
de `AI_API_KEY`. El contracte `PUT /v1/push-subscriptions/{installation_id}` accepta
`minimum_interest` (`low`, `medium`, `high`) i `group_selection`
(`{"mode":"custom","keys":["castellers de vilafranca"]}` o `{"mode":"all","keys":[]}`).
Les peticions antigues preserven els valors existents, amb Low i totes com a defaults.
El camp `platform` indica el servei del token: `ios` (APNs, per defecte i hexadecimal) o
`android` (Firebase Cloud Messaging, que conserva majúscules i minúscules). El `DELETE`
rep la mateixa plataforma com a paràmetre `platform`.

A l'app interna d'iOS, Ajustos → «Quines notícies?» obre una pantalla amb tres opcions: **Totes**
(`low`), **Rellevants** (`medium`) i **Destacades** (`high`). Es poden triar abans
d'activar els avisos i els canvis es desen en tocar l'opció. Les noves activacions
comencen amb Destacades; els usuaris que ja tenien avisos conserven Totes.
L'enllaç «Tria les colles a l’Agenda» obre directament el selector de colles d'aquesta
pestanya. Si un canvi no es pot sincronitzar, es reintenta en segon pla en tornar
a primer pla, sense mostrar un avís de sincronització pendent.

L'outbox conserva l'estat de classificació i el resultat, amb model, criteris i probabilitats.
Les preferències de l'audiència es capturen en detectar la novetat i es buiden en acabar.
El cron revalida la preferència actual abans de reclamar les entregues. Les pujades de
llindar poden suprimir avisos pendents; abaixar-lo o seguir colles no recupera avisos antics.
Els errors de Jev són omissions definitives; els errors transitoris d'APNs i FCM es reintenten.
Si s'esgota el pressupost, les classificacions no iniciades queden per al següent cron.
Un intent interromput es marca omès en recuperar el bloqueig. Les crides Jev no mantenen
cap transacció d'escriptura oberta i les dues rutes d'ingesta comparteixen l'advisory lock.

Per validar el model en català sense escriure a la base de dades ni enviar avisos:

```bash
uv run --env-file .env.jev.local python -m scripts.smoke_jev_news --live-count 5
```

La mostra de regressió versionada conté 40 casos en català, amb paràfrasis del text
addicional i les decisions acordades incorporades. No és una estimació d’exactitud
sobre tot el feed. Es pot executar amb repeticions explícites, sense base de dades:

```bash
uv run --env-file .env.jev.local python -m scripts.evaluate_jev_news \
  --output /tmp/jev-evaluation.json --repetitions 3
```

L’avaluador mostra discrepàncies editorials, falsos High, High perduts i variació
entre repeticions; retorna error si hi ha discrepàncies. No s’executa amb credencials
en CI. Les proves automatitzades cobreixen el contracte, la procedència i la ingesta.
Els resultats es desen una sola vegada en producció: el sistema no depèn que Jev
retorni exactament la mateixa resposta en una nova crida. Vegeu
[avaluació i límits coneguts](docs/jev-evaluation-20260924.md) i
[ordre de desplegament i rollback](docs/jev-notifications-rollout.md).

El fitxer local amb la clau ha de quedar fora de Git i Vercel. El smoke mostra nivells,
colles, latència i consum, sense mostrar credencials. Comprova diades històriques, primers
intents i assoliments inèdits per a una colla, i els distingeix d'estrenes de temporada
i prèvies sense context històric. Retorna un codi d'error si no coincideix amb els nivells
esperats. Els logs de classificació i el cron exposen `classified` i
`classification_skipped` per diagnosticar omissions.

Desplegament: configurar el secret, aplicar Alembic fins a `20260924_07`, desplegar el backend
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

`tests/test_app_build_profiles.py` llegeix el projecte Xcode, el paquet Swift i el build de
Gradle, i falla si un mòdul intern, un punt d'entrada, un permís o un entitlement de les
seccions internes pot arribar a l'app pública, o si l'app interna pot substituir-la.
`tests/test_built_app_inspection.py` prova amb APK i apps falses la inspecció que els
workflows d'iOS i Android fan de totes dues apps després de compilar-les (vegeu
[App pública i app interna](#app-pública-i-app-interna)).

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
