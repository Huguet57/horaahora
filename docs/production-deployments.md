# Desplegaments i migracions de producció

La producció es desplega manualment des del workflow **Deploy production** de GitHub
Actions. `vercel.json` desactiva els auto-deploys només per a `main`; les previews de les
PR continuen funcionant. Això evita que Vercel publiqui codi que depèn d'un esquema que
encara no s'ha migrat.

## Configuració inicial

1. Crea l'environment de GitHub `production` i limita'l a la branca protegida `main`.
2. Afegeix-hi un revisor obligatori, si el pla del repositori ho permet.
3. Desa-hi els secrets `VERCEL_TOKEN`, `VERCEL_ORG_ID` i `VERCEL_PROJECT_ID`.
4. Mantén `DATABASE_URL` i la resta de secrets de runtime a l'environment Production de
   Vercel; el workflow els llegeix amb `vercel env run` i no els copia a GitHub.

Per desplegar, obre **Actions → Deploy production**, selecciona `main` i executa el
workflow. Cada execució queda serialitzada amb el grup de concurrència `production` i
desplega exactament el SHA seleccionat.

## Ordre i recuperació

El workflow segueix aquest ordre:

1. aplica `alembic upgrade head` i comprova la revisió activa;
2. crea un deployment de producció amb `--skip-domain`, sense trànsit d'usuaris;
3. exigeix que `/health/ready` respongui `{"status":"ready"}`;
4. promociona aquell deployment al domini de producció;
5. repeteix el smoke test contra el domini promocionat.

Si la migració falla, no es desplega codi. Si el build o el primer smoke test fallen, el
deployment actual continua servint trànsit. Si una migració ja aplicada té un defecte,
cal publicar una migració **forward** correctiva: el workflow no executa mai
`alembic downgrade`, perquè una reversió destructiva automàtica pot perdre dades.

## Política expand/contract

Cada canvi d'esquema s'ha de poder executar mentre la versió anterior del backend encara
serveix trànsit:

- **Expand:** afegeix taules o columnes compatibles, inicialment opcionals o amb un valor
  segur. Evita renombrar o eliminar camps en aquesta fase.
- **Migrate:** desplega codi compatible amb els dos esquemes i fes els backfills com a
  jobs separats, idempotents i observables.
- **Contract:** en una PR i desplegament posteriors, elimina el codi antic i només llavors
  les columnes, índexs o restriccions obsoletes.

No afegeixis una columna `NOT NULL` sense un valor segur a una taula poblada, ni facis un
rename, drop o backfill llarg a la mateixa release que comença a dependre del resultat.
Els canvis irreversibles han d'indicar explícitament el pla de recuperació a la PR.

## Docker Compose

`docker compose up --build` espera que PostgreSQL estigui sa, executa el servei d'una sola
execució `migrate` i només arrenca `api` i `agenda-sync` si Alembic acaba correctament.
Per executar només la base de dades durant desenvolupament continua sent vàlid
`docker compose up -d db`.
