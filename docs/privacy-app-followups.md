# Estat de privacitat de l'app iOS

Aquest document separa els controls de privacitat ja disponibles del treball futur. La política i les declaracions d'App Store Connect han de continuar descrivint només comportaments efectivament publicats.

## Implementat

- La quarta secció «Ajustos» centralitza les notificacions, la privacitat, el suport, les fonts i la informació de l'app.
- «Política de privacitat» obre `/privacy`, que mostra la versió catalana i permet canviar a castellà o anglès amb enllaços HTML estàtics.
- El contacte `tenimaletaapp@gmail.com` és accessible des d'Ajustos.
- L'identificador tècnic aleatori de la instal·lació es mostra i es pot copiar.
- «Contacta amb suport» prepara un correu editable amb la versió, el número de build i l'identificador tècnic. L'usuari pot revisar-lo, modificar-lo o cancel·lar-lo, i només es transmet quan prem manualment el botó d'enviament.
- No s'exporten ni s'adjunten converses al correu de suport.
- El backend registra i revoca tokens APNs associats només a l'identificador aleatori d'instal·lació, sense Firebase ni OneSignal.
- Els tokens es desen a Supabase exclusivament per lliurar notificacions, es reenvien quan APNs els rota i se substitueixen per una marca de revocació quan l'usuari desactiva els avisos o Apple els invalida.
- El rate limiting, el contingut sincronitzat, l'outbox i les entregues també es conserven a PostgreSQL; les converses continuen només al dispositiu.

## Pendent

### Compartició explícita de converses

- Implementar, si es decideix oferir-la, la compartició explícita de converses seleccionades individualment.
- Mostrar el contingut complet abans d'adjuntar-lo i no incloure altres converses ni la base de dades local.
- Actualitzar la política, `PrivacyInfo.xcprivacy` i App Store Connect abans d'activar aquesta funció.
