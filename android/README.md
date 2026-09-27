# La calculadora de l'Aleta per a Android

App Android nativa en Kotlin i Jetpack Compose, amb les mateixes seccions que l'app iOS:
**Calculadora**, **Puntuacions** i **Ajustos**, més **Hora a Hora** i **Agenda** com a seccions
ocultes. Parla amb el mateix backend i en respecta els contractes HTTP, les preferències d'avisos
i el comportament fora de línia.

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
| `core:common` | Dates i números en català, text sense accents, errors per a l'usuari | No |
| `core:domain` | Models i interfícies de repositori | No |
| `core:network` | Client HTTP (OkHttp) i DTO del contracte del backend | No |
| `core:database` | Esquema SQLDelight: Hora a Hora, Agenda i converses | No |
| `core:data` | Repositoris amb memòria cau, xat local i subscripció push | No |
| `feature:*:presentation` | Estat i lògica de cada pantalla, amb proves | No |
| `core:designsystem` | Tema, colors i components Compose compartits | Sí |
| `feature:*:ui` | Pantalles Compose | Sí |
| `app` | Composició, navegació, Firebase, permisos i enllaços | Sí |

La lògica que no depèn d'Android (domini, dades i presentació) es compila i es prova en
qualsevol JVM. Les convencions de Gradle són a `build-logic`.

## Compilar i provar

```bash
./gradlew :app:installDebug                   # instal·la l'app al dispositiu connectat
./gradlew testDebugUnitTest test              # totes les proves unitàries
./gradlew -Pcastells.jvmOnly=true test        # només els mòduls sense Android, sense l'SDK
```

També es pot obrir la carpeta `android` amb Android Studio.

## Configuració

- **Backend:** les builds de publicació fan servir `castells.apiBaseUrl` de
  `gradle.properties`, que és producció. Les de depuració fan servir
  `castells.apiBaseUrl.debug`, el backend local tal com el veu l'emulador
  (`http://10.0.2.2:8000`), perquè les proves no arribin a producció. Per canviar-lo, fes
  servir `-Pcastells.apiBaseUrl.debug=...`, `~/.gradle/gradle.properties` o la variable
  d'entorn `CASTELLS_API_BASE_URL`, que només afecta les builds de depuració. En un
  dispositiu físic, `adb reverse tcp:8000 tcp:8000` permet fer servir
  `http://127.0.0.1:8000`. Les builds de depuració accepten HTTP.
- **Avisos (Firebase Cloud Messaging):** el `google-services.json` del projecte Firebase
  `castells-en-vena` no es versiona perquè el repositori és públic. Per compilar en local,
  copia'l a `android/app/`. El workflow d'Android el crea a partir del secret de GitHub
  `GOOGLE_SERVICES_JSON`, que conté el fitxer sencer. Sense aquest fitxer l'app compila i
  funciona, i Ajustos indica que els avisos no estan disponibles en aquesta versió.
  El backend necessita `FCM_SERVICE_ACCOUNT_JSON` per enviar-los (vegeu el README principal).
- **Entorn dels avisos:** les builds de depuració es registren com a `development` i les de
  publicació com a `production`, igual que a iOS.
- **Versió:** `versionName` és a `app/build.gradle.kts`; el `versionCode` es passa amb
  `-Pcastells.versionCode=N`.
- **Signatura de publicació:** `castells.signing.storeFile`, `storePassword`, `keyAlias` i
  `keyPassword` com a propietats de Gradle (o `CASTELLS_SIGNING_STOREFILE`,
  `CASTELLS_SIGNING_STOREPASSWORD`, `CASTELLS_SIGNING_KEYALIAS` i
  `CASTELLS_SIGNING_KEYPASSWORD`). Sense clau, `./gradlew :app:bundleRelease` genera un
  paquet sense signar.

## Comportament

- **Hora a Hora:** llista agrupada per dies, estirar per actualitzar, paginació, actualització
  automàtica cada minut mentre la pestanya és visible i còpia local si no hi ha connexió. Els
  enllaços s'obren dins l'app amb Custom Tabs.
- **Agenda:** calendari mensual que es plega fins a la setmana activa en desplaçar les
  actuacions, sis mesos precarregats al voltant del mes visible, filtre i colles destacades.
- **Calculadora:** converses desades només al dispositiu. Les respostes en curs continuen encara
  que es tanqui el xat, i en tornar-hi es mostren quan arriben. És la pestanya inicial.
- **Puntuacions:** la taula oficial del 2026 de més a menys punts, per grups. Les barres fan zoom
  a les files visibles i, en tocar un castell, es ressalten els de sota que descarregats en
  guanyen el carregat. La taula és un recurs del mòdul `:feature:scoretable:presentation`,
  generat amb `scripts/export_score_table.py` a partir del CSV del backend.
- **Ajustos:** política de privacitat, suport, identificador tècnic i fonts. Set tocs seguits a la
  versió mostren o amaguen Hora a Hora, Agenda i els avisos de notícies (amb el llindar
  d'interès); qui ja tenia els avisos activats les conserva. A Android 13 o posterior, el permís
  de notificacions només es demana quan l'usuari activa els avisos.
- **Accessibilitat:** etiquetes per a TalkBack, mida de text del sistema i, amb «Suprimeix les
  animacions», el calendari canvia d'estat sense animacions intermèdies.
