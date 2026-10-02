# Arquitectura del repositori

Aquest document defineix els límits que han de continuar sent estables quan el projecte creixi. La modularització no altera l'API HTTP, l'esquema PostgreSQL, els models SwiftData ni els productes públics de `CastellsKit`, i l'app Android segueix els mateixos contractes.

## Backend

El backend combina casos d'ús explícits amb ports i adaptadors:

```text
api ───────────────┐
                   v
composition ──> application ──> domain
      │                              ^
      └──────────> adapters ─────────┘
```

Les dependències permeses són:

- `backend/domain` conté models, regles i ports. No importa FastAPI, SQLAlchemy, proveïdors externs ni configuració d'infraestructura.
- `backend/application` implementa casos d'ús i només depèn del domini: el xat i la compartició de converses.
- `backend/adapters` implementa ports del domini: proveïdors d'IA, coneixement del Concurs, rate limiting i persistència de converses compartides.
- `backend/api` transforma HTTP en crides d'aplicació. Cada contracte té el seu esquema i el seu router; els routers no construeixen adaptadors.
- `backend/composition` és l'únic lloc que coneix alhora aplicació, adaptadors i configuració. Construeix `ApplicationContainer` i aplica els `ApplicationOverrides` tipats de proves.
- `backend/app.py` només crea FastAPI, configura errors i middleware, construeix el contenidor i registra routers.

## Swift

Es conserven els targets públics existents i s'organitza el codi intern per funcionalitat. El
projecte Xcode té un target d'app, `HoraAHoraApp`, amb el seu esquema:

```text
HoraAHoraApp ──> FeatureCalculator, FeatureScoreTable, FeatureSettings ──> CastellsDomain
      │
      └────────> CastellsData ──> CastellsDomain
```

Les dependències permeses són:

- `CastellsDomain` defineix models i protocols del xat, més utilitats compartides. No depèn de dades, features ni de l'app.
- `CastellsData` té el client de l'API, el xat i l'esquema SwiftData. L'esquema conserva, només per compatibilitat, les entitats de la caché d'Hora a Hora i l'Agenda de versions anteriors: així una actualització obre la base existent sense migració i no perd les converses. Pot dependre de `CastellsDomain`.
- Cada `Feature*` conté presentació, vistes i utilitats pròpies. Pot dependre de `CastellsDomain`, però no de `CastellsData` ni del target principal.
- El target d'app (`HoraAHoraApp/HoraAHoraApp`) té l'entrada (`App/`), la composició (`AppDependencies`, que crea l'emmagatzematge, el client de l'API i la calculadora), la configuració, l'arrencada i la navegació.
- `FeatureScoreTable` mostra la taula de puntuacions a partir d'una còpia en JSON que porta com a recurs. `scripts/export_score_table.py` la genera del CSV del backend, que continua sent l'única font dels punts, i una prova de Pytest comprova que no quedi desfasada.
- `FeatureSettings` conté els ajustos de la calculadora i no té punts d'extensió.

Els noms dels targets, productes públics i models SwiftData són part de la compatibilitat del projecte. Moure implementació entre carpetes no ha de canviar aquests contractes.

## Android

L'app Android (`android/`) reprodueix les mateixes funcionalitats i contractes que l'app iOS amb mòduls Gradle. El mòdul `:app` té les variants `debug` i `release`:

```text
:app ──> :feature:*:ui ──> :feature:*:presentation ──> :core:domain ──> :core:common
  │            │
  │            └──> :core:designsystem
  └──> :core:data ──> :core:network, :core:database ──> :core:domain
```

Les dependències permeses són:

- `:core:common` conté utilitats sense estat (números en català, text sense accents, errors per a l'usuari). No depèn de cap altre mòdul.
- `:core:domain` defineix models i interfícies de repositori del xat. És Kotlin pur.
- `:core:network` té el client HTTP del backend (OkHttp i kotlinx.serialization) i el servei del xat. `:core:database` té l'esquema SQLDelight local. Cap dels dos coneix Android. L'esquema es manté a la versió 1: les bases de versions anteriors conserven les taules d'Hora a Hora i l'Agenda, sense ús, i no s'han de reutilitzar aquests noms.
- `:core:data` implementa el xat amb la base local i l'emmagatzematge clau-valor.
- Cada `:feature:*:presentation` conté l'estat i la lògica de la pantalla (`StateFlow` i funcions `suspend`) en Kotlin pur, amb proves unitàries. Pot dependre del domini, però no de dades, d'Android ni d'altres features.
- Cada `:feature:*:ui` conté només Compose. Depèn de la seva presentació i de `:core:designsystem`, no de dades.
- `:app` és l'arrel de composició: `AppContainer`, configuració, enllaços, arrencada, l'activitat i la navegació.
- `:feature:scoretable:presentation` porta la taula de puntuacions com a recurs JSON, la mateixa còpia que l'app iOS, i n'ordena les files i calcula l'escala de les barres.

Els mòduls que no depenen d'Android es compilen i es proven en qualsevol JVM amb `-Pcastells.jvmOnly=true`. Les convencions de compilació viuen a `android/build-logic`.

## Criteris per a fitxers nous

- Agrupar codi que canvia pel mateix motiu i separar responsabilitats independents.
- Usar fitxers d'unes 150–250 línies com a orientació, no com a límit mecànic.
- Evitar barrels de compatibilitat per a imports Python interns eliminats.
- Afegir proves de caracterització abans de modificar un contracte o una conducta existent.

## Validació

```bash
python3 -m pytest -q

cd HoraAHoraApp/Packages/CastellsKit
swift test

cd ../../..
make ios-build
```

Amb `TEST_DATABASE_URL`, Pytest també valida migracions i comportament específic de PostgreSQL.

```bash
cd android
./gradlew -Pcastells.jvmOnly=true test   # domini, dades i presentació, sense l'SDK d'Android
./gradlew test                           # totes les proves, amb l'SDK d'Android
cd ..
make android-build android-lint
```
