# Proposta d'integració amb Revista Castells i la CCCC

## Objectiu compartit

La super-app vol reunir actualitat, agenda i eines castelleres sense substituir les fonts editorials ni institucionals. Cada registre conserva la procedència, l'atribució, l'enllaç de retorn, l'identificador extern i la revisió. L'app no enriquirà ni redistribuirà contingut editorial fora del que s'acordi amb cada organització.

## Decisions per a la reunió

### Accés i contracte de dades

- Quines API, feeds RSS/Atom, calendaris, webhooks o exportacions existeixen avui?
- Quin identificador canònic i estable té cada notícia, entrada de l'Hora a Hora i diada?
- Quins camps, idiomes i període històric es poden servir?
- Com s'expressen una correcció, una cancel·lació, una eliminació i una nova revisió?
- Quina latència i freqüència d'actualització són raonables?
- Hi haurà entorn de proves, autenticació, quotes o límits d'ús?
- Quin procés de versionat i quin període de compatibilitat tindrà el contracte?

### Drets, marca i experiència

- Quins textos, extractes i imatges pot conservar o mostrar l'app?
- Quina atribució, marca i enllaç de retorn són obligatoris?
- Qui decideix si una entrada pot originar una notificació i amb quin text?
- Quin és el protocol per retirar contingut o corregir una notificació?
- Quines mètriques agregades pot retornar la super-app: obertures, clics de retorn, seguiment d'una diada o interessos territorials?
- Quina retenció, anonimització i periodicitat tindran aquestes mètriques?

### Operació

- Persona o canal de suport tècnic i editorial de cada part.
- Temps de resposta davant incidències urgents.
- Propietari del contracte, calendari de revisions i registre de canvis.
- Data i criteris per retirar l'adaptador HTML provisional.

## Tres modes d'ingesta intercanviables

1. **Webhook del soci.** És el mode preferent per a novetats i correccions immediates. Cal signatura, idempotència per `sourceID + externalID`, revisió i marca temporal.
2. **Consulta d'API o feed oficial.** Sincronització incremental per cursor o `updatedSince`, amb reintents i reconciliació periòdica.
3. **HTML provisional.** Adaptador activat per feature flag, amb fixtures de contracte i monitoratge de canvis de marcatge. No és una dependència del domini i es pot desactivar sense publicar una app nova.

Els tres modes produeixen els mateixos models neutrals. Canviar de font no modifica les features iOS ni els casos d'ús.

## Contracte mínim proposat

### Hora a Hora

`sourceID`, `externalID`, titular, extracte acordat, data estructurada quan existeixi, ordre de font, URL de l'article, URL d'acció, atribució, data de creació i data d'actualització.

Si una font no publica data estructurada es conserva el seu ordre; no es dedueix la data a partir del titular. La deduplicació principal és `sourceID + externalID`; només es crea una empremta estable quan manca un identificador.

### Agenda

`sourceID`, `externalID`, títol, data local, hora exacta opcional, etiqueta horària original, zona horària, ordre de font, recinte, municipi, colles, notes, atribució, URL oficial, revisió i data d'actualització. Una cancel·lació o correcció ha de conservar l'identificador i incrementar o substituir la revisió.

La CCCC ha autoritzat explícitament l'adaptador HTML per a aquesta prova de concepte. L'accés tècnic automatitzat encara necessita una excepció de Cloudflare, un token o un feed oficial. Fins aleshores, la POC utilitza una instantània oficial amb procedència i data de captura; el mode `fixture` queda reservat exclusivament a tests.

### Notificacions

Proposta de governança:

- la font indica si el contingut és notificable;
- la super-app aplica preferències de l'usuari, freqüència i silenci nocturn;
- el payload conté l'identificador canònic i obre l'entrada corresponent dins l'app;
- les dades de lliurament i obertura es comparteixen només de forma agregada i segons acord.

## Seguretat i privacitat

- Autenticació servidor-servidor i rotació de credencials.
- Webhooks signats, protecció contra repeticions i claus d'idempotència.
- Minimització de dades: cap historial del xat-calculadora no surt del dispositiu excepte els últims missatges necessaris per a cada consulta.
- Registres operatius sense contingut sensible i amb retenció pactada.
- Límits de trànsit, alertes i procediment de revocació.

## Prova pilot proposada

1. Acordar camps, drets i un conjunt petit de fixtures.
2. Validar el contracte d'`openapi/partner-api.yaml` en un entorn de proves.
3. Executar dues setmanes en paral·lel amb la font actual, sense notificacions públiques.
4. Comparar completitud, ordre, correccions i temps d'actualització.
5. Activar gradualment la font oficial i retirar l'HTML quan els criteris siguin estables.
