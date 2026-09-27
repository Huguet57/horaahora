# Estat de privacitat de l'app iOS

Aquest document separa els controls de privacitat ja disponibles del treball futur. La política i les declaracions d'App Store Connect han de continuar descrivint només comportaments efectivament publicats.

## Implementat

- La quarta secció «Ajustos» centralitza les notificacions, la privacitat, el suport, les fonts i la informació de l'app.
- «Política de privacitat» obre `/privacy`, que mostra la versió catalana i permet canviar a castellà o anglès amb enllaços HTML estàtics.
- El contacte `tenimaletaapp@gmail.com` és accessible des d'Ajustos.
- L'identificador tècnic aleatori de la instal·lació es mostra i es pot copiar.
- «Contacta amb suport» prepara un correu editable amb la versió, el número de build i l'identificador tècnic. L'usuari pot revisar-lo, modificar-lo o cancel·lar-lo, i només es transmet quan prem manualment el botó d'enviament.
- No s'exporten ni s'adjunten converses al correu de suport.
- El backend registra i revoca tokens APNs associats només a l'identificador aleatori d'instal·lació; l'app iOS no inclou Firebase ni OneSignal.
- L'app Android registra tokens de Firebase Cloud Messaging amb el mateix contracte i la plataforma `android`. Només demana el token quan l'usuari activa els avisos, l'esborra quan els desactiva i no inclou Google Analytics per a Firebase.
- Els tokens es desen a Supabase exclusivament per lliurar notificacions, es reenvien quan APNs els rota i se substitueixen per una marca de revocació quan l'usuari desactiva els avisos o Apple els invalida.
- El rate limiting, el contingut sincronitzat, l'outbox i les entregues també es conserven a PostgreSQL; l'historial complet de converses continua només al dispositiu.
- «Millora la calculadora» (Ajustos, activada per defecte) desa al backend les consultes de les converses noves, la resposta o l'error i un identificador aleatori de la conversa durant 90 dies, sense l'identificador d'instal·lació ni la IP. La base és l'interès legítim: la calculadora ho explica en obrir la primera conversa amb l'opció de no compartir-ho, i només es comparteixen converses començades després de l'avís. Les versions anteriors de l'app no envien el camp `share_for_improvement` i el backend no en desa res.

- Les notificacions sincronitzen el llindar d'interès i les colles seguides amb el backend. Jev rep només el contingut públic de les notícies; la personalització es calcula al backend.

## Pendent

### Compartició explícita de converses

- Implementar, si es decideix oferir-la, la compartició explícita de converses seleccionades individualment.
- Mostrar el contingut complet abans d'adjuntar-lo i no incloure altres converses ni la base de dades local.
- Actualitzar la política, `PrivacyInfo.xcprivacy` i App Store Connect abans d'activar aquesta funció.
