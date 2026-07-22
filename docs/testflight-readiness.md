# Preparació de TestFlight

Estat auditat el 22 de juliol de 2026. Aquesta llista separa el que queda preparat al repositori del que necessita accés al compte d'Apple o una decisió de producte.

## Estat tècnic

| Àrea | Requisit | Estat | Acció pendent |
| --- | --- | --- | --- |
| Codi | PR #4 rebasada; 67 tests Python, 35 tests Swift i build Release | Preparat | Fer merge quan el CI de l'últim commit sigui verd. |
| Identitat | Bundle ID explícit `com.ahuguet.castellsenvena` i App ID amb Push Notifications | Configurat al projecte i al portal | Utilitzar el mateix Bundle ID al registre d'App Store Connect. |
| Versió | `CFBundleShortVersionString` 1.0 i build 1 | Configurat | Incrementar sempre el build abans de cada pujada posterior. |
| Nom | Nom visible `Castells en vena` | Configurat | Utilitzar exactament aquest nom al registre d'App Store Connect i confirmar-ne la disponibilitat. |
| Icona | App Icon opaca de 1024 × 1024 a l'asset catalog | Preparat | Validar la marca amb els socis abans de la beta externa. |
| Privacitat | Política completa en CA, ES i EN, enllaç des d'Ajustos i `PrivacyInfo.xcprivacy` integrat | Preparat al repositori | Desplegar aquesta branca i completar l'etiqueta App Privacy d'App Store Connect d'acord amb el manifest. |
| Xifrat | `ITSAppUsesNonExemptEncryption = NO` per HTTPS estàndard | Preparat | Confirmar si s'afegeix criptografia pròpia en el futur. |
| Release | APNs `development` en Debug i `production` en Release; perfils Development i Store generats | Preparat | La signatura automàtica gestionarà les renovacions. |
| Backend | URL Release `https://castells-superapp-poc.vercel.app`, amb `cdg1` com a regió principal | Actiu | Desplegar els canvis i verificar la regió, les URLs, la retenció i l'SLA. Vercel i els seus subencarregats poden tractar dades fora de la UE. |
| Automatització | CI de tests Swift i build iOS Release sense signar | Preparat | Vigilar el run de l'últim commit. |
| Archive | Archive signat i IPA App Store exportat amb certificat cloud-managed Apple Distribution | Build 1 acceptat per App Store Connect | Esperar que Apple acabi de processar-lo i revisar qualsevol avís. |

## Accions obligatòries al compte d'Apple

| Ordre | Requisit | Estat | Acció pendent |
| --- | --- | --- | --- |
| 1 | Membresia Apple Developer activa i acords vigents acceptats | Compte i equip actius | Confirmar que no hi hagi acords pendents a App Store Connect. |
| 2 | App ID explícit `com.ahuguet.castellsenvena` amb Push Notifications | Fet | Cap. |
| 3 | Certificat Apple Distribution i perfil App Store Connect | Fet amb signatura cloud-managed | Renovació automàtica; el perfil Store actual caduca el 29 d'abril de 2027. |
| 4 | Registre nou de l'app amb el nom `Castells en vena`, idioma principal, Bundle ID i SKU | Fet | Registre creat amb el Bundle ID `com.ahuguet.castellsenvena`. |
| 5 | Política de privacitat publicada amb URL HTTPS i accessible des de l'app | Repositori preparat | Desplegar el backend rebasat i verificar les quatre URLs. |
| 6 | Formulari App Privacy: identificador de dispositiu i contingut d'usuari per funcionalitat, sense tracking | Pendent | Completar-lo a App Store Connect d'acord amb `PrivacyInfo.xcprivacy`. |
| 7 | Declarar drets d'ús i atribució de Revista Castells i CCCC | Pendent | Confirmar-ho amb producte/legal abans de la beta externa. |
| 8 | Edat, content rights i dades de contacte de revisió | Pendent | Completar-ho a App Store Connect. |
| 9 | Crear grup intern, afegir testers i assignar el build processat | Pujada feta; processament pendent | Fer-ho quan App Store Connect mostri el build 1 com a disponible. |
| 10 | Per testers externs: beta description, feedback email, “What to Test”, contacte i Beta App Review | Pendent | Utilitzar els textos de `testflight-metadata-ca.md`. |

## Pujada recomanada

1. Crea el registre de `Castells en vena` a App Store Connect amb el Bundle ID `com.ahuguet.castellsenvena`.
2. Obre `HoraAHoraApp/HoraAHoraApp.xcodeproj` amb el compte Apple de l'equip `B94LUNLMW9`.
3. A **Signing & Capabilities**, comprova el Bundle ID, Push Notifications i la signatura automàtica.
4. Selecciona **Any iOS Device (arm64)** i executa **Product → Archive** amb Release.
5. A Organizer, executa **Validate App** i resol qualsevol avís.
6. Executa **Distribute App → App Store Connect → Upload**.
7. Espera que el build es processi, completa export compliance si Apple ho demana i assigna'l primer a un grup intern.

El fitxer `HoraAHoraApp/ExportOptions-TestFlight.plist` ja s'ha validat exportant un IPA App Store signat amb `aps-environment=production` i `beta-reports-active=true`. No s'han d'afegir certificats, claus APNs ni contrasenyes al repositori.

La versió 1.0 (build 1) es va pujar correctament a App Store Connect el 22 de juliol de 2026. Apple va acceptar el paquet i en va iniciar el processament.

## Criteris mínims abans de convidar testers

- Hora a Hora carrega dades reals, conserva el format editorial i obre links/modals.
- Agenda carrega dades reals, mostra la cache sense missatges tècnics i obre Google Maps.
- Calculadora interpreta variants habituals, demana aclariments naturals i no inventa punts.
- El backend no exposa claus ni proveïdor i limita les peticions.
- La política de privacitat explica que els últims missatges necessaris viatgen al backend i al proveïdor d'IA, mentre l'historial complet queda al dispositiu.
- El correu de suport mostra versió, build i identificador tècnic abans d'enviar-se, i no exporta converses.
- S'ha provat almenys en un iPhone físic, un iPad o simulador i amb connectivitat intermitent.
- Les notificacions o bé funcionen de punta a punta, o bé no es prometen com a funcionalitat de la beta.
