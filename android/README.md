# La calculadora de l'Aleta per a Android

App Android nativa en Kotlin i Jetpack Compose, la de Google Play
(`com.ahuguet.castellsenvena`), amb les mateixes seccions que l'app iOS: Calculadora, Comparador,
Puntuacions i Ajustos.

Parla amb el mateix backend i en respecta els contractes HTTP i el comportament fora de línia.

## Requisits

- JDK 17 o posterior.
- Android SDK amb la plataforma 36 (Android Studio la instal·la automàticament).
- Un dispositiu o emulador amb Android 8.0 (API 26) o posterior.

## Mòduls

```text
:app ──> :feature:*:ui ──> :feature:*:presentation ──> :core:domain ──> :core:common
  │            │
  │            └──> :core:designsystem
  └──> :core:data ──> :core:network, :core:database ──> :core:domain
```

| Mòdul | Contingut | Android? |
| --- | --- | --- |
| `core:common` | Números en català, text sense accents, errors per a l'usuari | No |
| `core:domain` | Models i interfícies de repositori | No |
| `core:network` | Client HTTP (OkHttp) del backend i xat | No |
| `core:database` | Esquema SQLDelight de les converses | No |
| `core:data` | Xat local i emmagatzematge clau-valor | No |
| `feature:*:presentation` | Estat i lògica de cada pantalla, amb proves | No |
| `core:designsystem` | Tema, colors i components Compose compartits | Sí |
| `feature:*:ui` | Pantalles Compose | Sí |
| `app` | Composició, navegació i enllaços | Sí |

La lògica que no depèn d'Android (domini, dades i presentació) es compila i es prova en
qualsevol JVM. Les convencions de Gradle són a `build-logic`.

## Compilar i provar

```bash
./gradlew :app:installDebug                # l'app al dispositiu
./gradlew test                             # totes les proves unitàries
./gradlew -Pcastells.jvmOnly=true test     # sense Android ni l'SDK
./gradlew :app:assembleDebug :app:assembleRelease :app:lintDebug
```

Només hi ha les variants `debug` i `release`. També es pot obrir la carpeta `android` amb Android
Studio.

## Configuració

- **Backend:** les builds de publicació fan servir `castells.apiBaseUrl` de
  `gradle.properties`, que és producció. Les de depuració fan servir
  `castells.apiBaseUrl.debug`, el backend local tal com el veu l'emulador
  (`http://10.0.2.2:8000`), perquè les proves no arribin a producció. Per canviar-lo, fes
  servir `-Pcastells.apiBaseUrl.debug=...`, `~/.gradle/gradle.properties` o la variable
  d'entorn `CASTELLS_API_BASE_URL`, que només afecta les builds de depuració. En un
  dispositiu físic, `adb reverse tcp:8000 tcp:8000` permet fer servir
  `http://127.0.0.1:8000`. Les builds de depuració accepten HTTP.
- **Versió:** `versionName` és el `MARKETING_VERSION` de `Version.xcconfig`, a l'arrel del
  repositori, compartit amb iOS; el `versionCode` es passa amb `-Pcastells.versionCode=N`.
- **Signatura de publicació:** `castells.signing.storeFile`, `storePassword`, `keyAlias` i
  `keyPassword` com a propietats de Gradle (o `CASTELLS_SIGNING_STOREFILE`,
  `CASTELLS_SIGNING_STOREPASSWORD`, `CASTELLS_SIGNING_KEYALIAS` i
  `CASTELLS_SIGNING_KEYPASSWORD`). Sense clau, `./gradlew :app:bundleRelease` genera un
  paquet sense signar.

## Comportament

- **Calculadora:** converses desades només al dispositiu. Les respostes en curs continuen encara
  que es tanqui el xat, i en tornar-hi es mostren quan arriben. És la pestanya inicial.
- **Comparador:** escenaris de fins a quatre colles i cinc rondes, puntuats amb les normes del
  Concurs: compten les tres millors construccions, com a màxim dos carregats, i els empats es
  desfan per penalitzacions i pel millor castell. Tocar una ronda obre un full inferior amb els
  castells per punts (els que la colla no pot intentar, desactivats i amb el motiu) i després el
  resultat; la insígnia D/C obre directament el resultat, i mantenir premuda la ronda en mostra el
  menú. Els escenaris es desen només al dispositiu, amb els favorits a dalt; en mantenir-ne premut
  un es pot arrossegar, i eliminar-lo o buidar-ne les rondes es pot desfer des de l'avís de sota.
  La lògica i les proves són a `:feature:scoretable:presentation`, al costat de la taula.
- **Puntuacions:** la taula oficial del 2026 de més a menys punts, per grups. Les barres fan zoom
  a les files visibles i, en tocar un castell, es ressalten els de sota que descarregats en
  guanyen el carregat. La taula és un recurs del mòdul `:feature:scoretable:presentation`,
  generat amb `scripts/export_score_table.py` a partir del CSV del backend.
- **Ajustos:** política de privacitat, suport, identificador tècnic i fonts. Els enllaços s'obren
  dins l'app amb Custom Tabs.
- **Base de dades local:** les bases de dades creades per versions anteriors també tenen les
  taules `HourByHourItemRecord` i `AgendaEventRecord`, la còpia fora de línia d'Hora a Hora i
  l'Agenda. L'esquema actual ja no les crea ni les llegeix, però no s'esborren: la versió de
  l'esquema continua sent 1, de manera que les bases de dades existents s'obren sense cap
  migració i conserven les converses.
- **Accessibilitat:** etiquetes per a TalkBack, mida de text del sistema i, amb «Suprimeix les
  animacions», canvis d'estat sense animacions intermèdies.
