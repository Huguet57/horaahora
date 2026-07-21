# Canvis de privacitat pendents a l'app iOS

Aquest document recull treball futur. **No forma part de la implementació actual** i cap d'aquests comportaments s'ha de descriure com a disponible fins que estigui implementat, provat i reflectit en la política de privacitat i a App Store Connect.

## Abans d'una beta externa o revisió d'Apple

- Afegir una pantalla «Sobre i privacitat» accessible dins l'app.
- Enllaçar-hi les versions catalana, castellana i anglesa de la política publicada.
- Mostrar el contacte `tenimaletaapp@gmail.com` i un identificador tècnic de suport que l'usuari pugui copiar.
- Revisar `PrivacyInfo.xcprivacy` i les respostes d'App Privacy d'App Store Connect perquè coincideixin amb el comportament real.

L'accés fàcil a la política dins l'app continua sent un requisit pendent i bloqueja la preparació completa per a una beta externa o una revisió pública d'Apple.

## Suport voluntari

- Preparar un correu de suport amb l'identificador tècnic inclòs al cos.
- Mostrar el correu complet abans d'obrir el client de correu; no enviar res en segon pla.
- Permetre seleccionar una conversa concreta per compartir-la voluntàriament.
- Mostrar-ne el contingut abans d'adjuntar-lo i no incloure altres converses ni la base de dades local.
- Actualitzar la política abans d'activar aquest flux, explicant exactament què es comparteix i durant quant temps es conserva.

## Notificacions remotes

- Implementar el registre directe del token amb APNs sense afegir Firebase ni OneSignal.
- Afegir al backend un registre associat a l'identificador aleatori d'instal·lació, no a una identitat real.
- Revocar el token quan es desactivin les notificacions.
- Eliminar-lo quan Apple el marqui com a invàlid o després de 12 mesos sense activitat.
- No reutilitzar el token per analítica, perfilat ni altres finalitats.
- Abans d'activar-ho, actualitzar la política, el manifest de privacitat, App Store Connect i els tests de baixa i caducitat.

## Criteris d'acceptació futurs

- Cap identificador ni conversa surt del dispositiu sense una acció explícita i revisable de l'usuari.
- Desactivar les notificacions revoca el registre del backend.
- L'app pot obrir la política encara que no hi hagi una sessió o compte.
- Els textos i les etiquetes de privacitat descriuen només comportaments ja disponibles.
