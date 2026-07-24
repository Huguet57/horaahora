# Arquitectura del repositori

Aquest document defineix els límits que han de continuar sent estables quan el projecte creixi. La modularització no altera l'API HTTP, l'esquema PostgreSQL, els models SwiftData ni els productes públics de `CastellsKit`.

## Backend

El backend combina casos d'ús explícits amb ports i adaptadors:

```text
api ───────────────┐
                   v
composition ──> application ──> domain
      │                              ^
      └──────────> adapters ─────────┘
```

Les dependències permeses són:

- `backend/domain` conté models, regles i ports. No importa FastAPI, SQLAlchemy, proveïdors externs ni configuració d'infraestructura.
- `backend/application` implementa casos d'ús i només depèn del domini. Les àrees d'Agenda, Hora a Hora, xat, sincronització, notificacions i paginació es mantenen separades.
- `backend/adapters` implementa ports del domini. La persistència separa Agenda, Hora a Hora, subscripcions push i entregues/outbox.
- `backend/api` transforma HTTP en crides d'aplicació. Cada contracte té el seu esquema i el seu router; els routers no construeixen adaptadors.
- `backend/composition` és l'únic lloc que coneix alhora aplicació, adaptadors i configuració. Construeix `ApplicationContainer` i aplica els `ApplicationOverrides` tipats de proves.
- `backend/app.py` només crea FastAPI, configura errors i middleware, construeix el contenidor i registra routers.

Els ports de contingut són estrets: `HourByHourRepository` i `AgendaRepository` evolucionen independentment. De la mateixa manera, `PushSubscriptionRepository` gestiona dispositius i `NotificationRepository` gestiona ingesta, outbox i entregues.

## Swift

Es conserven els targets públics existents i s'organitza el codi intern per funcionalitat:

```text
HoraAHoraApp ──> Feature* ──> CastellsDomain
      │
      └────────> CastellsData ──> CastellsDomain
```

Les dependències permeses són:

- `CastellsDomain` defineix models i protocols d'Agenda, Hora a Hora i xat, més utilitats compartides. No depèn de dades, features ni de l'app.
- `CastellsData` implementa els repositoris del domini i concentra xarxa, SwiftData i notificacions remotes. Pot dependre de `CastellsDomain`.
- Cada `Feature*` conté presentació, vistes i utilitats pròpies. Pot dependre de `CastellsDomain`, però no de `CastellsData` ni del target principal.
- `HoraAHoraApp` és l'arrel de composició. `AppDependencies` crea implementacions concretes i les injecta a les features; configuració, navegació i notificacions queden separades.

Els noms dels targets, productes públics i models SwiftData són part de la compatibilitat del projecte. Moure implementació entre carpetes no ha de canviar aquests contractes.

## Criteris per a fitxers nous

- Agrupar codi que canvia pel mateix motiu i separar responsabilitats independents.
- Usar fitxers d'unes 150–250 línies com a orientació, no com a límit mecànic.
- Evitar barrels de compatibilitat per a imports Python interns eliminats.
- Afegir proves de caracterització abans de modificar un contracte o una conducta existent.

## Validació

```bash
python3 -m pytest -q

cd HoraAHoraApp/Packages/CastellsKit
swift test

cd ../../..
xcodebuild \
  -project HoraAHoraApp/HoraAHoraApp.xcodeproj \
  -scheme HoraAHoraApp \
  -destination 'generic/platform=iOS Simulator' \
  -configuration Debug \
  CODE_SIGNING_ALLOWED=NO build
```

Amb `TEST_DATABASE_URL`, Pytest també valida migracions i comportament específic de PostgreSQL.
