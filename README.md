# Super-app castellera

Primera fase d'una app iOS modular amb tres seccions natives: Hora a Hora, Agenda i una calculadora conversacional. El backend és una aplicació ASGI portable i no exposa cap proveïdor d'IA ni infraestructura concreta al domini o al contracte HTTP.

## Estructura

- `HoraAHoraApp/HoraAHoraApp`: composició, navegació, notificacions i configuració iOS.
- `HoraAHoraApp/Packages/CastellsKit`: paquet Swift local amb domini, dades i features independents.
- `backend/domain`: models, ports i motor de puntuació determinista.
- `backend/application`: casos d'ús.
- `backend/adapters`: IA, Revista Castells, persistència i rate limiting.
- `backend/api`: esquemes HTTP neutrals.
- `tests`: proves del domini, ingesta, contractes d'IA i API.
- `openapi/partner-api.yaml`: contracte reduït per a clients i reunions amb socis.
- `docs/integracio-socis.md`: proposta de col·laboració amb Revista Castells i la CCCC.

## Backend local

Amb Python 3.11 o posterior:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
AGENDA_SOURCE=fixture uvicorn backend.app:app --reload
```

O amb infraestructura local completa:

```bash
cp .env.example .env
docker compose up --build
```

L'API queda disponible a `http://127.0.0.1:8000` i la documentació interactiva a `/docs`. Compose aporta PostgreSQL i Redis. L'adaptador HTML es pot desactivar amb `HOUR_BY_HOUR_SOURCE_ENABLED=false`.

### Agenda de la CCCC

`AGENDA_SOURCE` selecciona un adaptador intercanviable:

- `fixture`: dades simulades locals per al simulador i les proves;
- `disabled`: integració desactivada, valor segur per defecte fora de Compose;
- `cccc_html`: consulta mensual de l'HTML de la CCCC, només després d'obtenir autorització escrita.

El mode real exigeix també `CCCC_AGENDA_AUTHORIZED=true`; si no, el backend falla a l'arrencada per evitar una activació accidental. La font real conserva atribució i enllaç de retorn, refresca com a màxim cada 30 minuts i manté l'última còpia si falla una actualització. L'app desa també una cache SwiftData per consultar els dies carregats sense connexió.

### Interpretació de consultes

`AI_PROVIDER=local` usa l'intèrpret determinista inclòs, sense claus externes. També hi ha adaptadors desacoblats per `openai` i `anthropic`; el model, la clau i un endpoint compatible es configuren amb `AI_MODEL`, `AI_API_KEY` i `AI_BASE_URL`. Tots validen la mateixa sortida estructurada abans d'invocar el motor de puntuació.

## App iOS

Obre `HoraAHoraApp/HoraAHoraApp.xcodeproj`. El projecte referencia el paquet local `Packages/CastellsKit` i admet iPhone i iPad amb iOS 17 o posterior.

La URL del backend es resol en aquest ordre:

1. variable de procés `CASTELLS_API_BASE_URL`;
2. clau `CastellsAPIBaseURL` de l'Info.plist generat;
3. `http://127.0.0.1:8000`.

En un iPhone físic cal indicar una URL accessible des del dispositiu. Les converses i les còpies de l'Hora a Hora i l'Agenda es desen només amb SwiftData al dispositiu; el backend rep com a màxim els darrers 12 missatges i no persisteix cap conversa.

## Proves

```bash
python3 -m pytest -q
cd HoraAHoraApp/Packages/CastellsKit
swift test
```

La taula oficial versionada és `backend/data/taula_puntuacions_concurs_castells_2026.csv`. El motor aplica tres millors castells, màxim dos carregats, intents, estructures repetides i àlies explícits com `4d9net -> 4de9sf`.
