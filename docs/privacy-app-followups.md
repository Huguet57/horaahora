# Estat de privacitat de l'app iOS

Aquest document separa els controls de privacitat ja disponibles del treball futur. La política i les declaracions d'App Store Connect han de continuar descrivint només comportaments efectivament publicats.

## Implementat

- La quarta secció «Ajustos» centralitza les notificacions, la privacitat, el suport, les fonts i la informació de l'app.
- «Política de privacitat» obre `/privacy`, que mostra la versió catalana i permet canviar a castellà o anglès amb enllaços HTML estàtics.
- El contacte `tenimaletaapp@gmail.com` és accessible des d'Ajustos.
- L'identificador tècnic aleatori de la instal·lació es mostra i es pot copiar.
- «Contacta amb suport» prepara un correu editable amb la versió, el número de build i l'identificador tècnic. L'usuari pot revisar-lo, modificar-lo o cancel·lar-lo, i només es transmet quan prem manualment el botó d'enviament.
- No s'exporten ni s'adjunten converses al correu de suport.
- El backend no rep ni conserva tokens APNs en la versió actual.

## Pendent

### Compartició explícita de converses

- Implementar, si es decideix oferir-la, la compartició explícita de converses seleccionades individualment.
- Mostrar el contingut complet abans d'adjuntar-lo i no incloure altres converses ni la base de dades local.
- Actualitzar la política, `PrivacyInfo.xcprivacy` i App Store Connect abans d'activar aquesta funció.

### Registre de notificacions remotes

- Implementar en el futur el registre i revocació de tokens APNs al backend, sense Firebase ni OneSignal.
- Associar cada token només a l'identificador aleatori d'instal·lació; revocar-lo quan es desactivin les notificacions i eliminar-lo quan Apple el marqui com a invàlid o després del termini que es defineixi.
- No reutilitzar els tokens per analítica, perfilat ni cap altra finalitat, i actualitzar la política i les proves abans d'activar el registre.
