# Preparació de TestFlight

Estat auditat el 22 de juliol de 2026. Aquesta llista separa el que queda preparat al repositori del que necessita accés al compte d'Apple o una decisió de producte.

## Estat tècnic

| Àrea | Requisit | Estat | Acció pendent |
| --- | --- | --- | --- |
| Codi | `main` estable, tests Python i Swift i build Release | Preparat | Fer merge d'aquesta PR quan el CI sigui verd. |
| Identitat | Bundle ID explícit `com.andreu.HoraAHoraApp` | Configurat | Confirmar que és l'identificador definitiu abans de crear el registre d'App Store Connect. |
| Versió | `CFBundleShortVersionString` 1.0 i build 1 | Configurat | Incrementar sempre el build abans de cada pujada posterior. |
| Nom | Nom visible `Castells en vena` | Configurat | Utilitzar exactament aquest nom al registre d'App Store Connect i confirmar-ne la disponibilitat. |
| Icona | App Icon opaca de 1024 × 1024 a l'asset catalog | Preparat | Validar la marca amb els socis abans de la beta externa. |
| Privacitat | Política completa en CA, ES i EN, enllaç des d'Ajustos i `PrivacyInfo.xcprivacy` integrat | Preparat al repositori | Desplegar aquesta branca i completar l'etiqueta App Privacy d'App Store Connect d'acord amb el manifest. |
| Xifrat | `ITSAppUsesNonExemptEncryption = NO` per HTTPS estàndard | Preparat | Confirmar si s'afegeix criptografia pròpia en el futur. |
| Release | APNs `development` en Debug i `production` en Release | Preparat al projecte | Habilitar Push Notifications a l'App ID i obtenir un perfil de distribució. |
| Backend | URL Release `https://castells-superapp-poc.vercel.app`, amb `cdg1` com a regió principal | Actiu | Desplegar els canvis i verificar la regió, les URLs, la retenció i l'SLA. Vercel i els seus subencarregats poden tractar dades fora de la UE. |
| Automatització | CI de tests Swift i build iOS Release sense signar | Preparat | Vigilar el primer run de GitHub Actions. |
| Archive | Archive genèric sense signar | Validat localment | Fer un archive signat des de Xcode quan hi hagi certificat i perfil. |

## Accions obligatòries al compte d'Apple

| Ordre | Requisit | Qui/On | Bloqueja |
| --- | --- | --- | --- |
| 1 | Membresia Apple Developer activa i acords vigents acceptats | Account Holder | Qualsevol pujada |
| 2 | App ID explícit amb el bundle ID definitiu i Push Notifications | Certificates, Identifiers & Profiles | Signatura Release i notificacions |
| 3 | Certificat Apple Distribution i perfil App Store Connect, o signatura automàtica autoritzada | Xcode / Developer portal | Archive signat |
| 4 | Registre nou de l'app amb el nom `Castells en vena`, idioma principal, Bundle ID i SKU | App Store Connect | Pujada del build |
| 5 | Política de privacitat publicada amb URL HTTPS i accessible des de l'app | Repositori preparat; desplegament pendent | Beta externa / revisió |
| 6 | Formulari App Privacy: identificador de dispositiu i contingut d'usuari per funcionalitat, sense tracking | App Store Connect | Beta externa / distribució |
| 7 | Declarar drets d'ús i atribució de Revista Castells i CCCC | Producte/legal | Beta externa |
| 8 | Edat, content rights i dades de contacte de revisió | App Store Connect | Beta externa |
| 9 | Crear grup intern, afegir testers i assignar el build processat | TestFlight | Prova interna |
| 10 | Per testers externs: beta description, feedback email, “What to Test”, contacte i Beta App Review | TestFlight | Prova externa |

## Pujada recomanada

1. Obre `HoraAHoraApp/HoraAHoraApp.xcodeproj` amb el compte Apple correcte.
2. A **Signing & Capabilities**, comprova l'equip `B94LUNLMW9`, el Bundle ID i que no hi hagi errors de provisioning.
3. Selecciona **Any iOS Device (arm64)** i executa **Product → Archive** amb Release.
4. A Organizer, executa **Validate App** i resol qualsevol avís.
5. Executa **Distribute App → App Store Connect → Upload**.
6. Espera que el build es processi, completa export compliance si Apple ho demana i assigna'l primer a un grup intern.

El fitxer `HoraAHoraApp/ExportOptions-TestFlight.plist` deixa preparada l'exportació automàtica un cop existeixin les credencials de distribució. No s'han d'afegir certificats, claus APNs ni contrasenyes al repositori.

## Criteris mínims abans de convidar testers

- Hora a Hora carrega dades reals, conserva el format editorial i obre links/modals.
- Agenda carrega dades reals, mostra la cache sense missatges tècnics i obre Google Maps.
- Calculadora interpreta variants habituals, demana aclariments naturals i no inventa punts.
- El backend no exposa claus ni proveïdor i limita les peticions.
- La política de privacitat explica que els últims missatges necessaris viatgen al backend i al proveïdor d'IA, mentre l'historial complet queda al dispositiu.
- El correu de suport mostra versió, build i identificador tècnic abans d'enviar-se, i no exporta converses.
- S'ha provat almenys en un iPhone físic, un iPad o simulador i amb connectivitat intermitent.
- Les notificacions o bé funcionen de punta a punta, o bé no es prometen com a funcionalitat de la beta.
