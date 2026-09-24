# Desplegament de les notificacions per interès

El canvi és compatible amb els clients iOS anteriors: les peticions que ometen les
preferències conserven les ja desades i les noves subscripcions antigues comencen
amb Low i totes les colles. L’històric no es torna a notificar.

## Ordre

1. Verificar que l’entorn del servidor té `JEV_API_KEY` i `JEV_MODEL=jev-1.13.0`,
   independents de la clau de la calculadora. No posar secrets a l’app ni al repositori.
2. Amb la connexió de desplegament a PostgreSQL, aplicar `uv run alembic upgrade head`
   i comprovar `uv run alembic check`. El cap esperat d’aquesta PR és `20260924_07`.
   La migració `06` incorpora preferències i classificació; la `07` afegeix la URL
   original a l’outbox. Són additives i compatibles amb el backend anterior.
3. Desplegar el backend de la PR validada. Comprovar `/health/ready` i la primera
   execució ordinària del cron. No reinicialitzar `notification_sync_state`, buidar
   l’outbox ni forçar una reingesta de l’històric per fer una prova.
4. Revisar les classificacions noves (`criteria_version=castells-interest-v8`) i les
   entregues. Verificar amb una instal·lació de prova el registre de preferències,
   la renovació de token i l’augment d’un nivell per colla seguida. No abaixar
   preferències de subscripcions reals per provocar avisos de prova.
5. Publicar l’actualització iOS després de validar el backend. La UI ja permet triar
   Totes, Rellevants o Destacades i obrir el selector de colles de l’Agenda.

La PR prepara aquest ordre; aplicar-la no executa Alembic automàticament. L’última
migració s’ha d’aplicar abans de servir codi que llegeixi la nova columna.

## Observació

- `news_classified`: nivell, versió del model i criteris, latència, consum, tipus de
  text (`summary`, `article_body`, `linked_context`) i hash de la petició.
- `news_article_fallback`: error de lectura; es pot classificar amb títol i resum.
- `news_classification_skipped`: error de Jev o intent interromput; omissió definitiva.
- Resposta del cron: `classified`, `classification_skipped`, `attempted`, `delivered`,
  `retried`, `failed` i `invalidated`. Els reintents corresponen a APNs.

Revisar especialment una concentració inesperada de High, pujades d’omissions o
classificacions pendents que no avancin entre execucions. El primer seguiment ha de
mostrejar titulars i metadades de classificació; no cal registrar cossos d’articles,
preferències, tokens APNs ni credencials als logs.

## Rollback

Si hi ha un problema d’entrega, posar `PUSH_DELIVERY_ENABLED=false` i desplegar aquesta
configuració per aturar el cron d’avisos. Tornar a una versió del backend que entengui
les preferències d’interès abans de reactivar-lo. Mantenir les columnes additives;
no executar un downgrade mentre hi hagi instàncies noves actives. No restablir estats
de classificació ni crear entregues per recuperar avisos omesos.

## Límit editorial

La [mostra d’avaluació](jev-evaluation-20260924.md) conserva els errors coneguts i les
repeticions. El model encara pot variar en casos limítrofs; cada notícia es classifica
una vegada i se’n reutilitza el resultat per a tots els usuaris. La deduplicació és
per notícia, no per esdeveniment: cròniques diferents de la mateixa diada poden
originar avisos diferents.
