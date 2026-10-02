# Estat de privacitat de l'app iOS

Aquest document separa els controls de privacitat ja disponibles del treball futur. La política i les declaracions d'App Store Connect han de continuar descrivint només comportaments efectivament publicats.

## Implementat

- La secció «Ajustos» centralitza la privacitat, el suport, les fonts i la informació de l'app.
- L'app no inclou avisos de notícies: no demana el permís, no registra tokens ni inclou Firebase. Les subscripcions d'avisos de les versions anteriors deixen de rebre'n perquè el backend de la calculadora ja no n'envia; Hora a Hora és ara una app separada.
- «Política de privacitat» obre `/privacy`, que mostra la versió catalana i permet canviar a castellà o anglès amb enllaços HTML estàtics.
- El contacte `tenimaletaapp@gmail.com` és accessible des d'Ajustos.
- L'identificador tècnic aleatori de la instal·lació es mostra i es pot copiar.
- «Contacta amb suport» prepara un correu editable amb la versió, el número de build i l'identificador tècnic. L'usuari pot revisar-lo, modificar-lo o cancel·lar-lo, i només es transmet quan prem manualment el botó d'enviament.
- No s'exporten ni s'adjunten converses al correu de suport.
- El rate limiting i les converses compartides es conserven a PostgreSQL; l'historial complet de converses continua només al dispositiu.
- «Millora la calculadora» (Ajustos, activada per defecte) desa al backend les consultes de les converses noves, la resposta o l'error i un identificador aleatori de la conversa durant 90 dies, sense l'identificador d'instal·lació ni la IP. La base és l'interès legítim: la calculadora ho explica en obrir la primera conversa amb l'opció de no compartir-ho, i només es comparteixen converses començades després de l'avís. Les versions anteriors de l'app no envien el camp `share_for_improvement` i el backend no en desa res.

## Pendent

### Compartició explícita de converses

- Implementar, si es decideix oferir-la, la compartició explícita de converses seleccionades individualment.
- Mostrar el contingut complet abans d'adjuntar-lo i no incloure altres converses ni la base de dades local.
- Actualitzar la política, `PrivacyInfo.xcprivacy` i App Store Connect abans d'activar aquesta funció.
