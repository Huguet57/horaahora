# Arquitectura del repositori

Aquest document defineix els límits que han de continuar sent estables quan el projecte creixi. La modularització no altera l'API HTTP, l'esquema PostgreSQL, els models SwiftData ni els productes públics de `CastellsKit`, i l'app Android segueix els mateixos contractes.

## App pública i app interna

Cada plataforma genera dues apps a partir del mateix codi, triades en compilar amb
`CASTELLS_BUILD_PROFILE=public|internal` (`public` per defecte):

- L'**app pública** (`com.ahuguet.castellsenvena`) té la calculadora, la taula de puntuacions i els
  ajustos de la calculadora. És l'única que es publica.
- L'**app interna** (`com.ahuguet.castellsenvena.internal`) hi afegeix Hora a Hora, Agenda, els seus
  ajustos, el gest secret i els avisos de notícies. És una app diferent: s'instal·la al costat de la
  pública i no la pot substituir.

La separació es fa en temps de compilació i per mòduls, no amb un booleà en temps d'execució:
l'app pública no depèn dels mòduls interns ni en conté cap punt d'entrada (pestanyes, deep links,
delegat de notificacions, permisos o entitlements). Les dues apps fan servir el mateix esquema
de base de dades local, sencer, perquè l'app pública es pugui actualitzar des de les versions que
tenien les seccions internes sense perdre les converses. El backend desa les subscripcions d'avisos
amb l'identificador de l'app que les fa (`app_id`), perquè APNs lliura els tokens de l'app interna
amb el seu propi Bundle ID.

`tests/test_app_build_profiles.py` fa complir aquests límits llegint el projecte Xcode, el paquet
Swift i el build de Gradle amb `scripts/app_profiles`, que també inspecciona les apps compilades a
CI (`tests/test_built_app_inspection.py` en prova la inspecció).

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
- `backend/application` implementa casos d'ús i només depèn del domini. Les àrees d'Agenda, Hora a Hora, xat, sincronització, notificacions i paginació es mantenen separades.
- `backend/adapters` implementa ports del domini. La persistència separa Agenda, Hora a Hora, subscripcions push, entregues/outbox i converses compartides.
- `backend/api` transforma HTTP en crides d'aplicació. Cada contracte té el seu esquema i el seu router; els routers no construeixen adaptadors.
- `backend/composition` és l'únic lloc que coneix alhora aplicació, adaptadors i configuració. Construeix `ApplicationContainer` i aplica els `ApplicationOverrides` tipats de proves.
- `backend/app.py` només crea FastAPI, configura errors i middleware, construeix el contenidor i registra routers.

Els ports de contingut són estrets: `HourByHourRepository` i `AgendaRepository` evolucionen independentment. De la mateixa manera, `PushSubscriptionRepository` gestiona dispositius i `NotificationRepository` gestiona ingesta, outbox i entregues.

La ingesta d'El Món Casteller separa la conversió de l'RSS (`el_mon_casteller_rss.py`,
sense accés a xarxa ni rellotge) de la descàrrega i deduplicació de categories
(`el_mon_casteller.py`). `CombinedHourByHourSource` combina mitjans i aïlla les fallades
sense conèixer els seus formats. La composició proporciona la mateixa font al cron i
al job manual; les proves cobreixen per separat el parser, la descàrrega, la combinació,
el job i el contracte HTTP.

## Swift

Es conserven els targets públics existents i s'organitza el codi intern per funcionalitat. El
projecte Xcode té dos targets d'app amb el seu esquema:

```text
HoraAHoraApp (pública) ──> FeatureCalculator, FeatureScoreTable, FeatureSettings ──> CastellsDomain
      │
      └─────────────────> CastellsData ──> CastellsDomain

HoraAHoraAppInternal ──> el mateix, més FeatureHourByHour, FeatureAgenda i
                         FeatureInternalSettings ──> FeatureSettings
```

Les dependències permeses són:

- `CastellsDomain` defineix models i protocols d'Agenda, Hora a Hora i xat, més utilitats compartides. No depèn de dades, features ni de l'app.
- `CastellsData` implementa els repositoris del domini i concentra xarxa, SwiftData i notificacions remotes. Pot dependre de `CastellsDomain`.
- Cada `Feature*` conté presentació, vistes i utilitats pròpies. Pot dependre de `CastellsDomain`, però no de `CastellsData` ni del target principal.
- Els dos targets d'app compilen el codi compartit de `HoraAHoraApp/HoraAHoraApp` (configuració, arrencada, navegació i `CoreDependencies`, que crea l'emmagatzematge, el client de l'API i la calculadora). Cada un afegeix la seva entrada i la seva composició: `Public/` (`PublicAppDependencies`, `PublicContentView`) i `Internal/` (`InternalAppDependencies`, `InternalContentView`, el delegat d'avisos i el gestor de notificacions, i l'entitlement `aps-environment`).
- El target `HoraAHoraApp` és l'app pública: només pot dependre de `CastellsDomain`, `CastellsData`, `FeatureCalculator`, `FeatureScoreTable` i `FeatureSettings`, i no té entitlements. El target `HoraAHoraAppInternal` és l'app interna.
- `FeatureScoreTable` mostra la taula de puntuacions a partir d'una còpia en JSON que porta com a recurs. `scripts/export_score_table.py` la genera del CSV del backend, que continua sent l'única font dels punts, i una prova de Pytest comprova que no quedi desfasada.
- `FeatureSettings` conté els ajustos de la calculadora i ofereix punts d'extensió: seccions al principi, fonts addicionals i un gestor dels tocs a la versió. `FeatureInternalSettings`, només a l'app interna, els omple amb els avisos de notícies, les fonts d'Hora a Hora i Agenda i el gest secret. És l'única dependència entre features i sempre va en aquest sentit.
- A l'app interna, Hora a Hora, Agenda i els seus ajustos són seccions ocultes. `HiddenSectionsPreferences` (domini) i `HiddenSectionsStore` (dades) en desen l'estat; `InternalSettingsModel` compta el gest secret d'Ajustos i la navegació només les mostra quan estan desbloquejades.
- `CastellsData` conserva els models SwiftData i els repositoris d'Hora a Hora i Agenda, perquè l'esquema ha de continuar sent el mateix a les dues apps. L'app pública no els crida; només fa servir `LegacyNewsNotificationsRetirement` per retirar els avisos que hagués activat una versió anterior.

Els noms dels targets, productes públics i models SwiftData són part de la compatibilitat del projecte. Moure implementació entre carpetes no ha de canviar aquests contractes.

## Android

L'app Android (`android/`) reprodueix les mateixes funcionalitats i contractes que l'app iOS amb mòduls Gradle. El mòdul `:app` té dos flavors, `public` i `internal`, i només existeixen les variants del perfil triat:

```text
:app ──> :feature:*:ui ──> :feature:*:presentation ──> :core:domain ──> :core:common
  │            │
  │            └──> :core:designsystem
  └──> :core:data ──> :core:network, :core:database ──> :core:domain
```

Les dependències permeses són:

- `:core:common` conté utilitats sense estat (dates i números en català, text sense accents, errors per a l'usuari). No depèn de cap altre mòdul.
- `:core:domain` defineix models i interfícies de repositori d'Agenda, Hora a Hora, colles, notificacions i xat. És Kotlin pur.
- `:core:network` implementa el contracte HTTP del backend (OkHttp i kotlinx.serialization) i `:core:database` l'esquema SQLDelight local. Cap dels dos coneix Android.
- `:core:data` implementa els repositoris del domini amb xarxa i base local, i la sincronització de la subscripció push.
- Cada `:feature:*:presentation` conté l'estat i la lògica de la pantalla (`StateFlow` i funcions `suspend`) en Kotlin pur, amb proves unitàries. Pot dependre del domini, però no de dades, d'Android ni d'altres features.
- Cada `:feature:*:ui` conté només Compose. Depèn de la seva presentació i de `:core:designsystem`, no de dades.
- `:app` és l'arrel de composició. `src/main` té el codi compartit (`CoreContainer`, configuració, enllaços, arrencada, la barra de navegació i el manifest sense avisos); `src/public` i `src/internal` tenen cadascun el seu `AppContainer`, l'activitat i la navegació. Només `src/internal` té Firebase, el permís de notificacions, el servei de missatges, el canal d'avisos i els enllaços des dels avisos.
- `:feature:hourbyhour:*`, `:feature:agenda:*` i `:feature:internalsettings:*` són dependències `internalImplementation`: l'app pública no les inclou. `:feature:internalsettings` amplia `:feature:settings`, com a iOS.
- `:feature:scoretable:presentation` porta la taula de puntuacions com a recurs JSON, la mateixa còpia que l'app iOS, i n'ordena les files i calcula l'escala de les barres. Com a iOS, `HiddenSectionsPreferences` (`:core:domain`) i `KeyValueHiddenSectionsStore` (`:core:data`) desen si Hora a Hora i Agenda es mostren a l'app interna, i `:core:data` i `:core:database` conserven el codi i l'esquema d'aquestes seccions per a totes dues apps.

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
make ios-build ios-verify                                  # app pública
make ios-build ios-verify CASTELLS_BUILD_PROFILE=internal  # app interna
```

Amb `TEST_DATABASE_URL`, Pytest també valida migracions i comportament específic de PostgreSQL.

```bash
cd android
./gradlew -Pcastells.jvmOnly=true test   # domini, dades i presentació, sense l'SDK d'Android
./gradlew test                           # totes les proves, amb l'SDK d'Android
cd ..
make android-build android-lint android-verify                                  # app pública
make android-build android-lint android-verify CASTELLS_BUILD_PROFILE=internal  # app interna
```
