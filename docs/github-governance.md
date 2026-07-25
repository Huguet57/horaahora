# Governança de GitHub

La branca per defecte es protegeix amb el ruleset versionat a
`.github/rulesets/main.json`. La política exigeix que tots els canvis arribin per pull
request, bloqueja eliminacions i force-push, obliga a resoldre els fils de revisió i
requereix els checks `Backend required` i `iOS required` sobre l'últim `main`.

El check `iOS required` existeix a totes les pull requests. El build macOS només
s'executa quan canvia `HoraAHoraApp`, el mateix workflow o el detector de paths; per a
la resta de canvis, el check estable valida que el build s'ha omès de manera esperada.

## Activació

El ruleset s'ha d'importar després que els checks estables hagin arribat a `main`:

1. Ves a **Settings → Rules → Rulesets** del repositori.
2. Selecciona **New ruleset → Import a ruleset**.
3. Importa `.github/rulesets/main.json` des del commit fusionat.
4. Revisa que l'objectiu sigui la branca per defecte i crea el ruleset actiu.

No es concedeix cap bypass permanent. En ser un repositori personal, no s'exigeix una
aprovació aliena, però sí una pull request, tots els checks i la resolució de fils. Un
administrador encara pot desactivar temporalment el ruleset des de Settings per a una
recuperació d'emergència, que queda registrada a l'historial del ruleset.
