# Preparació de TestFlight

Estat auditat el 22 de juliol de 2026. Aquesta llista separa el que queda preparat al repositori del que necessita accés al compte d'Apple o una decisió de producte.

## Estat tècnic

| Àrea | Requisit | Estat | Acció pendent |
| --- | --- | --- | --- |
| Codi | 91 tests Python (inclosa integració PostgreSQL 17), 40 tests Swift i builds Debug/Release | Preparat | Fer merge quan el CI de l'últim commit sigui verd. |
| Identitat | Bundle ID explícit `com.ahuguet.castellsenvena` (target i esquema `HoraAHoraApp`, l'app pública) i App ID amb Push Notifications | Configurat al projecte i al portal | Utilitzar el mateix Bundle ID al registre d'App Store Connect. L'app interna (`HoraAHoraAppInternal`, `com.ahuguet.castellsenvena.internal`) no es puja mai. |
| Versió | `CFBundleShortVersionString` 1.4; el build 5 del projecte només serveix per a compilacions locals i de CI | Configurat | Pujar sempre amb `make deploy-testflight`, que fa servir els segons Unix UTC com a build. |
| Nom | Nom visible `La calculadora de l'Aleta` (abans `Castells en vena`) | Configurat al projecte | Canviar el nom a App Store Connect (App Information) amb la versió que el publiqui i treure'n les captures de l'Hora a Hora i l'Agenda. |
| Icona | App Icon opaca de 1024 × 1024 a l'asset catalog | Preparat | Validar la marca amb els socis abans de la beta externa. |
| Privacitat | Política completa en CA, ES i EN, enllaç des d'Ajustos i `PrivacyInfo.xcprivacy` integrat | Preparat al repositori | Desplegar aquesta branca i completar l'etiqueta App Privacy d'App Store Connect d'acord amb el manifest. |
| Xifrat | `ITSAppUsesNonExemptEncryption = NO` per HTTPS estàndard | Preparat | Confirmar si s'afegeix criptografia pròpia en el futur. |
| Release | L'app pública no té l'entitlement `aps-environment` ni avisos; l'app interna fa servir APNs `development` en Debug i `production` en Release | Preparat | La signatura automàtica generarà el perfil Store sense Push per a l'app pública; l'App ID pot conservar la capacitat. |
| Backend | URL Release `https://castells-superapp-poc.vercel.app`, Vercel `cdg1`, Supabase PostgreSQL a París i cron idempotent | Preparat al repositori | Aplicar Alembic a Supabase, configurar secrets i verificar `/health/ready`. |
| Automatització | CI de tests Swift i builds iOS Release sense signar de les dues apps, inspeccionades amb `make ios-verify` | Preparat | Vigilar el run de l'últim commit. |
| Archive | Archive signat i IPA App Store exportat amb certificat cloud-managed Apple Distribution | Última pujada: 1.4 (build 1790470034), amb `make deploy-testflight` | Pujar els builds següents amb el mateix script i revisar qualsevol avís de processament. |

## Accions obligatòries al compte d'Apple

| Ordre | Requisit | Estat | Acció pendent |
| --- | --- | --- | --- |
| 1 | Membresia Apple Developer activa i acords vigents acceptats | Compte i equip actius | Confirmar que no hi hagi acords pendents a App Store Connect. |
| 2 | App ID explícit `com.ahuguet.castellsenvena` amb Push Notifications | Fet | Cap. |
| 3 | Certificat Apple Distribution i perfil App Store Connect | Fet amb signatura cloud-managed | Renovació automàtica; el perfil Store actual caduca el 29 d'abril de 2027. |
| 4 | Registre nou de l'app amb el nom `Castells en vena`, idioma principal, Bundle ID i SKU | Fet | Registre creat amb el Bundle ID `com.ahuguet.castellsenvena`. |
| 5 | Política de privacitat publicada amb URL HTTPS i accessible des de l'app | Repositori preparat | Desplegar el backend rebasat i verificar les quatre URLs. |
| 6 | Formulari App Privacy: identificador de dispositiu per funcionalitat i contingut d'usuari per funcionalitat i analítica (millora de la calculadora), no vinculat i sense tracking | Publicat el 27 de setembre de 2026 | Mantenir-lo d'acord amb `PrivacyInfo.xcprivacy` quan canviïn les dades que es recullen. |
| 7 | Declarar drets d'ús i atribució de Revista Castells i CCCC | Pendent | Confirmar-ho amb producte/legal abans de la beta externa. |
| 8 | Edat, content rights i dades de contacte de revisió | Pendent | Completar-ho a App Store Connect. |
| 9 | Crear grup intern, afegir testers i assignar el build processat | Build 4 present a TestFlight | Assignar el build més recent al grup intern quan estigui processat. |
| 10 | Per testers externs: beta description, feedback email, “What to Test”, contacte i Beta App Review | Pendent | Utilitzar els textos de `testflight-metadata-ca.md`. |

## Pujada recomanada

1. Amb els canvis ja a `main`, i `Version.xcconfig` amb la versió que vols publicar, executa `make deploy-testflight` en un Mac amb el compte Apple de l'equip `B94LUNLMW9` configurat a Xcode. El script arxiva en Release l'app pública del commit exacte d'`origin/main`, fa servir els segons Unix UTC com a build i atura la pujada si l'arxiu no apunta al backend de producció, si `CASTELLS_BUILD_PROFILE` no és `public` o si l'arxiu no és `com.ahuguet.castellsenvena`.
2. Espera que el build es processi, completa export compliance si Apple ho demana i assigna'l primer a un grup intern.

No pugis un **Product → Archive** fet des d'Xcode: agafaria el build 5 del projecte, més baix que el 1790470034 que la 1.4 ja té a App Store Connect, i la pujada es rebutjaria. Si cal fixar el build, passa `--build-number` al script.

El fitxer `HoraAHoraApp/ExportOptions-TestFlight.plist` ja s'ha validat exportant un IPA App Store signat amb `aps-environment=production` i `beta-reports-active=true`. Des de la separació entre l'app pública i l'app interna, l'IPA públic ja no porta `aps-environment`: cal revisar-ho en la primera pujada. No s'han d'afegir certificats, claus APNs ni contrasenyes al repositori.

La versió 1.0 (build 1) es va pujar correctament a App Store Connect el 22 de juliol de 2026. Apple va acceptar el paquet i en va iniciar el processament.

Després de rebasar sobre l'`origin/main` que inclou la PR #8, la versió 1.0 (build 2) es va pujar correctament a App Store Connect el 22 de juliol de 2026. Apple va acceptar el paquet i en va iniciar el processament.

## Criteris mínims abans de convidar testers

- L'app pública mostra només Calculadora, Puntuacions i Ajustos, i set tocs a la versió no fan res.
- Calculadora interpreta variants habituals, demana aclariments naturals i no inventa punts.
- El backend no exposa claus ni proveïdor i limita les peticions.
- La política de privacitat explica que els últims missatges necessaris viatgen al backend i al proveïdor d'IA, mentre l'historial complet queda al dispositiu. Amb «Millora la calculadora», les converses noves es desen 90 dies al backend sense identificadors del dispositiu.
- El correu de suport mostra versió, build i identificador tècnic abans d'enviar-se, i no exporta converses.
- S'ha provat almenys en un iPhone físic, un iPad o simulador i amb connectivitat intermitent.
- Una instal·lació TestFlight que tenia els avisos de notícies activats deixa de rebre'n després d'actualitzar-se i d'obrir l'app, i la subscripció queda invalidada a Supabase.
- Les proves d'Hora a Hora, Agenda i els avisos es fan amb l'app interna, que no passa per TestFlight: carreguen dades reals, obren enllaços i mapes, i un avís arriba amb l'app tancada (el backend el lliura amb el Bundle ID intern com a tema d'APNs).
