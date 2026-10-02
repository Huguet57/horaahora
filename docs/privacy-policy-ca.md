# Política de privacitat — La calculadora de l'Aleta

**Darrera actualització:** 2 d'octubre de 2026

Aquesta política explica com tracta les dades personals la versió actual de **La calculadora de l'Aleta**, una app gratuïta i sense compte d'usuari.

## 1. Responsable

- **Responsable:** Andreu Huguet, establert a Catalunya, Espanya.
- **Contacte de privacitat:** [tenimaletaapp@gmail.com](mailto:tenimaletaapp@gmail.com).

No s'ha designat un delegat de protecció de dades perquè, atesa la naturalesa i l'escala actuals del tractament, no és obligatori.

## 2. Dades que es tracten

### Dades desades només al dispositiu

- L'historial complet de les converses de la calculadora, inclosos els títols. Les consultes que es comparteixen per millorar la calculadora s'expliquen més avall.
- Preferències locals de visualització.

Les converses es poden eliminar individualment. Les dades locals restants desapareixen quan es desinstal·la l'app o se n'eliminen les dades des del sistema.

### Consultes de la calculadora

Quan s'envia una consulta, l'app transmet al backend com a màxim els 12 darrers missatges necessaris per entendre el context, juntament amb l'identificador aleatori d'instal·lació. El backend processa la consulta i la deriva al proveïdor d'intel·ligència artificial configurat. Si no es comparteixen per millorar la calculadora, La calculadora de l'Aleta no desa aquestes converses al backend.

> **No hi introdueixis dades personals.** La calculadora només necessita informació castellera per respondre.

### Millora de la calculadora

Per defecte, el backend desa les converses noves de la calculadora per detectar errors i millorar les respostes. De cada consulta es desen els missatges enviats (com a màxim els 12 darrers), la resposta o l'error obtingut, la data i un identificador aleatori de la conversa. No es desen amb l'identificador d'instal·lació ni amb l'adreça IP, de manera que no es poden associar al dispositiu.

La primera vegada que s'obre una conversa, l'app ho explica i permet no compartir-les. L'opció «Millora la calculadora» d'Ajustos permet canviar-ho en qualsevol moment i, en desactivar-la, deixa de compartir-se cap consulta. Només es comparteixen les converses començades després de veure aquest avís o de tornar a activar l'opció; les anteriors i les enviades des de versions de l'app sense aquesta opció no es desen mai.

Les converses compartides es conserven 90 dies i després s'eliminen automàticament. Només les consulta el responsable per revisar errors, avaluar canvis i millorar la interpretació i les respostes. No s'utilitzen per a publicitat ni per crear perfils, i no es cedeixen a tercers.

### Dades tècniques

En connectar-se al servei es poden processar l'adreça IP, la data i l'hora, la ruta sol·licitada, l'estat de la resposta i informació tècnica imprescindible per prestar el servei, limitar abusos i diagnosticar incidències.

### Comunicacions de suport

Quan se selecciona «Contacta amb suport», l'app prepara un correu editable amb la versió, el número de build i l'identificador tècnic. Aquesta informació només es transmet si l'usuari revisa el correu i prem manualment el botó d'enviament; també pot cancel·lar-lo.

Si l'usuari l'envia, es tractaran l'adreça de correu, el contingut del missatge i els fitxers que decideixi adjuntar. L'app no exporta converses ni les adjunta automàticament a suport.

## 3. Finalitats i bases jurídiques

- **Prestar el servei sol·licitat:** respondre les consultes de la calculadora. La base és l'execució del servei demanat per l'usuari.
- **Seguretat i estabilitat:** limitar peticions abusives, prevenir frau i diagnosticar errors. La base és l'interès legítim a protegir i mantenir el servei, ponderat amb els drets dels usuaris.
- **Millorar la calculadora:** desar les converses compartides per detectar errors i millorar les respostes. La base és l'interès legítim a millorar un servei gratuït, ponderat amb els drets dels usuaris: s'informa abans de començar, només es desen converses noves, sense identificadors del dispositiu i durant 90 dies. Desactivar «Millora la calculadora» a Ajustos és la manera immediata d'exercir el dret d'oposició.
- **Suport:** gestionar la informació enviada voluntàriament a suport. La base és el consentiment o l'acció voluntària, que es pot retirar en qualsevol moment.

Les dades necessàries per respondre una consulta i protegir el servei són imprescindibles per oferir aquestes funcions. El contacte amb suport i la compartició de converses per millorar la calculadora són opcionals.

## 4. Proveïdors i destinataris

- **Vercel:** allotjament i execució del backend. La funció principal es configura a París (`cdg1`), tot i que Vercel i els seus subencarregats poden tractar dades en altres països.
- **Supabase:** base de dades PostgreSQL gestionada a la regió de París on es conserven els comptadors tècnics de seguretat i les converses compartides per millorar la calculadora.
- **OpenRouter:** encamina les consultes de la calculadora cap al model d'intel·ligència artificial. Les peticions s'envien amb `data_collection: "deny"`, perquè no s'encaminin a proveïdors que les puguin utilitzar per entrenar models. OpenRouter conserva metadades tècniques de cada petició, com el nombre de tokens i la latència, i pot assignar una categoria temàtica anònima a una petita mostra de consultes, però no en desa el contingut.
- **Google (Gemini):** interpretació lingüística de les consultes de la calculadora, rebudes a través d'OpenRouter.
- **Apple:** distribució de l'app a iOS.
- **Google (Google Play):** distribució de l'app a Android.
- **Google/Gmail:** recepció i gestió dels correus enviats voluntàriament al contacte de suport o privacitat.

El Concurs de Castells, d'on surt la taula oficial de puntuacions, i la Coordinadora de Colles Castelleres de Catalunya (CCCC), d'on surt la llista de colles, no reben consultes, identificadors ni perfils d'usuari. L'app només mostra les dades atribuïdes i enllaços a les seves fonts oficials.

## 5. Transferències internacionals

Alguns proveïdors o subencarregats poden tractar dades fora de l'Espai Econòmic Europeu. Quan correspon, aquestes transferències es basen en decisions d'adequació, clàusules contractuals tipus de la Comissió Europea o altres garanties reconegudes pel RGPD. Es pot demanar més informació al correu de privacitat.

## 6. Conservació

- **Dades locals:** fins que s'elimina cada conversa o es desinstal·la l'app.
- **Converses compartides per millorar la calculadora:** 90 dies des de cada consulta; després s'eliminen automàticament.
- **Limitador de peticions:** les claus tècniques es mantenen durant una finestra de 10 minuts.
- **Logs de Vercel:** aproximadament 1 dia amb el pla actual.
- **Google (Gemini):** no utilitza les consultes per entrenar models. Segons el servei de Google que atengui la petició, les pot conservar fins a 55 dies per prevenir abusos, llevat que una obligació legal exigeixi una altra conservació.
- **Correus de suport o privacitat:** fins a 12 mesos després de resoldre la consulta, tret que sigui necessari conservar-los més temps per complir una obligació legal o defensar reclamacions.

## 7. Publicitat, analítica i decisions automatitzades

No hi ha publicitat, tracking entre apps o webs, perfilat comercial ni SDK addicional d'analítica o crash reporting. La calculadora automatitza la interpretació i el càlcul de puntuacions, però no pren decisions amb efectes jurídics ni similars sobre les persones.

## 8. Enllaços externs

Quan s'obre un enllaç al web del Concurs de Castells o a qualsevol servei extern, el servei de destinació tracta la connexió segons la seva pròpia política de privacitat. La calculadora de l'Aleta no controla aquests tractaments.

## 9. Drets

Es pot demanar l'accés, rectificació, supressió, limitació, oposició o portabilitat de les dades, i retirar el consentiment sense afectar el tractament anterior, escrivint a [tenimaletaapp@gmail.com](mailto:tenimaletaapp@gmail.com). Es respondrà, amb caràcter general, en el termini d'un mes.

Com que no hi ha comptes, molta informació només existeix al dispositiu i el responsable no hi pot accedir. Les converses compartides no porten cap identificador del dispositiu: per localitzar-ne una cal indicar-ne el text i la data aproximada. Pot ser necessari demanar informació tècnica addicional per localitzar una petició sense identificar una altra persona per error.

També es pot presentar una reclamació davant l'[Agència Espanyola de Protecció de Dades (AEPD)](https://www.aepd.es/).

## 10. Menors

L'app no està dirigida específicament a menors de 14 anys. Si una persona menor d'aquesta edat facilita dades personals quan el consentiment sigui la base aplicable, cal l'autorització del seu representant legal.

## 11. Seguretat i canvis

S'apliquen mesures proporcionades: comunicacions HTTPS, accés restringit a la infraestructura i, per a les converses compartides, conservació sense identificadors del dispositiu amb eliminació automàtica als 90 dies. Cap sistema és completament infal·lible.

Els canvis materials es publicaran a les mateixes URLs i se n'actualitzarà la data. Si un canvi requereix consentiment, es demanarà abans d'aplicar-lo.

Les versions públiques es troben a `/privacy/ca`, `/privacy/es` i `/privacy/en` del backend oficial.
