# Política de privacitat — Castells en vena

**Darrera actualització:** 22 de juliol de 2026

Aquesta política explica com tracta les dades personals la versió actual de **Castells en vena**, una app gratuïta i sense compte d'usuari.

## 1. Responsable

- **Responsable:** Andreu Huguet, establert a Catalunya, Espanya.
- **Contacte de privacitat:** [tenimaletaapp@gmail.com](mailto:tenimaletaapp@gmail.com).

No s'ha designat un delegat de protecció de dades perquè, atesa la naturalesa i l'escala actuals del tractament, no és obligatori.

## 2. Dades que es tracten

### Dades desades només al dispositiu

- Converses de la calculadora, inclosos els títols i missatges.
- Còpies locals de l'agenda i de l'Hora a Hora per millorar la disponibilitat i la lectura sense connexió.
- Preferències de l'app i un identificador d'instal·lació aleatori. No és un identificador publicitari i no s'utilitza per seguir l'usuari entre apps o webs.

Les converses es poden eliminar individualment. Les dades locals restants desapareixen quan es desinstal·la l'app o se n'eliminen les dades des del sistema.

### Consultes de la calculadora

Quan s'envia una consulta, l'app transmet al backend com a màxim els 12 darrers missatges necessaris per entendre el context, juntament amb l'identificador aleatori d'instal·lació. El backend processa la consulta i la deriva al proveïdor d'intel·ligència artificial configurat. Castells en vena no desa aquestes converses al backend.

> **No hi introdueixis dades personals.** La calculadora només necessita informació castellera per respondre.

### Dades tècniques

En connectar-se al servei es poden processar l'adreça IP, la data i l'hora, la ruta sol·licitada, l'estat de la resposta i informació tècnica imprescindible per prestar el servei, limitar abusos i diagnosticar incidències.

### Notificacions

Si s'activen voluntàriament les notificacions, iOS gestiona el permís i Apple assigna un token d'Apple Push Notification service (APNs) a aquesta instal·lació. L'app envia al backend aquest token, l'identificador aleatori d'instal·lació, la versió de l'app i l'idioma per poder lliurar els avisos sol·licitats. No s'utilitzen per analítica, publicitat ni seguiment. En desactivar les notificacions o quan Apple invalida el token, el backend el substitueix immediatament per una marca de revocació.

### Comunicacions de suport

Quan se selecciona «Contacta amb suport», l'app prepara un correu editable amb la versió, el número de build i l'identificador tècnic. Aquesta informació només es transmet si l'usuari revisa el correu i prem manualment el botó d'enviament; també pot cancel·lar-lo.

Si l'usuari l'envia, es tractaran l'adreça de correu, el contingut del missatge i els fitxers que decideixi adjuntar. L'app no exporta converses ni les adjunta automàticament a suport.

## 3. Finalitats i bases jurídiques

- **Prestar el servei sol·licitat:** mostrar contingut i respondre consultes de la calculadora. La base és l'execució del servei demanat per l'usuari.
- **Seguretat i estabilitat:** limitar peticions abusives, prevenir frau i diagnosticar errors. La base és l'interès legítim a protegir i mantenir el servei, ponderat amb els drets dels usuaris.
- **Funcions opcionals i suport:** gestionar les notificacions activades i la informació enviada voluntàriament a suport. La base és el consentiment o l'acció voluntària, que es pot retirar en qualsevol moment.

Les dades necessàries per respondre una consulta i protegir el servei són imprescindibles per oferir aquestes funcions. Les notificacions i el contacte amb suport són opcionals.

## 4. Proveïdors i destinataris

- **Vercel:** allotjament i execució del backend. La funció principal es configura a París (`cdg1`), tot i que Vercel i els seus subencarregats poden tractar dades en altres països.
- **Neon:** base de dades PostgreSQL gestionada on es conserven el contingut sincronitzat, els comptadors tècnics de seguretat i les subscripcions de notificacions actives.
- **OpenAI:** interpretació lingüística de les consultes de la calculadora mitjançant l'API. Les peticions s'envien amb l'opció de no emmagatzematge de resposta activada (`store: false`).
- **Apple:** distribució de l'app, permisos del sistema i APNs quan s'activen notificacions.
- **Google/Gmail:** recepció i gestió dels correus enviats voluntàriament al contacte de suport o privacitat.

Revista Castells i la Coordinadora de Colles Castelleres de Catalunya (CCCC) no reben consultes, identificadors ni perfils d'usuari. L'app només mostra contingut atribuït i enllaços a les seves fonts oficials.

## 5. Transferències internacionals

Alguns proveïdors o subencarregats poden tractar dades fora de l'Espai Econòmic Europeu. Quan correspon, aquestes transferències es basen en decisions d'adequació, clàusules contractuals tipus de la Comissió Europea o altres garanties reconegudes pel RGPD. Es pot demanar més informació al correu de privacitat.

## 6. Conservació

- **Dades locals:** fins que s'elimina cada conversa o es desinstal·la l'app.
- **Limitador de peticions:** les claus tècniques es mantenen durant una finestra de 10 minuts.
- **Subscripció de notificacions:** el token es conserva mentre els avisos estan actius i es revoca immediatament en desactivar-los o quan APNs el rebutja. Les instal·lacions que no es renoven durant 180 dies s'invaliden; els registres d'entrega es conserven com a màxim 30 dies.
- **Logs de Vercel:** aproximadament 1 dia amb el pla actual.
- **OpenAI:** l'API no s'utilitza per entrenar models per defecte; OpenAI pot retenir logs de prevenció d'abús fins a 30 dies, llevat que una obligació legal exigeixi una altra conservació.
- **Correus de suport o privacitat:** fins a 12 mesos després de resoldre la consulta, tret que sigui necessari conservar-los més temps per complir una obligació legal o defensar reclamacions.

## 7. Publicitat, analítica i decisions automatitzades

No hi ha publicitat, tracking entre apps o webs, perfilat comercial ni SDK addicional d'analítica o crash reporting. La calculadora automatitza la interpretació i el càlcul de puntuacions, però no pren decisions amb efectes jurídics ni similars sobre les persones.

## 8. Enllaços externs

Quan s'obre un enllaç de Revista Castells, CCCC, Google Maps o qualsevol servei extern, el servei de destinació tracta la connexió segons la seva pròpia política de privacitat. Castells en vena no controla aquests tractaments.

## 9. Drets

Es pot demanar l'accés, rectificació, supressió, limitació, oposició o portabilitat de les dades, i retirar el consentiment sense afectar el tractament anterior, escrivint a [tenimaletaapp@gmail.com](mailto:tenimaletaapp@gmail.com). Es respondrà, amb caràcter general, en el termini d'un mes.

Com que no hi ha comptes, molta informació només existeix al dispositiu i el responsable no hi pot accedir. Pot ser necessari demanar informació tècnica addicional per localitzar una petició sense identificar una altra persona per error.

També es pot presentar una reclamació davant l'[Agència Espanyola de Protecció de Dades (AEPD)](https://www.aepd.es/).

## 10. Menors

L'app no està dirigida específicament a menors de 14 anys. Si una persona menor d'aquesta edat facilita dades personals quan el consentiment sigui la base aplicable, cal l'autorització del seu representant legal.

## 11. Seguretat i canvis

S'apliquen mesures proporcionades, com comunicacions HTTPS, accés restringit a la infraestructura i absència de persistència pròpia dels xats al backend. Cap sistema és completament infal·lible.

Els canvis materials es publicaran a les mateixes URLs i se n'actualitzarà la data. Si un canvi requereix consentiment, es demanarà abans d'aplicar-lo.

Les versions públiques es troben a `/privacy/ca`, `/privacy/es` i `/privacy/en` del backend oficial.
