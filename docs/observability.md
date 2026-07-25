# Observabilitat del backend

El backend escriu un esdeveniment JSON per petició. Accepta `X-Request-ID` quan conté
només lletres, números, punts, guions o guions baixos (màxim 128 caràcters); en cas
contrari en genera un UUID. El mateix identificador apareix a la resposta i als logs
emesos durant la petició.

Els logs HTTP inclouen `method`, `path`, `status_code` i `duration_ms`. No registren la
query, el cos, capçalera d'autorització, tokens de dispositiu ni claus. `LOG_LEVEL`
controla el nivell mínim i té `INFO` com a valor per defecte.

## Senyals operatius

Cal configurar el proveïdor de logs o alertes perquè avisi sobre els esdeveniments
següents de nivell `ERROR`:

- `readiness_check_failed`: la dependència indicada no està disponible;
- `cron_failed`: el cron indicat ha acabat amb una excepció;
- `cron_completed` amb `failed > 0`: el cron ha acabat però hi ha entregues fallides;
- `apns_delivery_rejected` amb `disposition = failed`: APNs ha rebutjat definitivament
  una entrega;
- `notification_delivery_exception`: l'accés a la passarel·la push ha fallat i
  l'entrega s'ha programat per reintentar-se;
- `http_request_failed`: una petició ha produït una excepció no gestionada.

Els rebuigs recuperables d'APNs i els tokens invàlids s'emeten a nivell `WARNING`; el
cron en conserva els comptadors `retried` i `invalidated`. Una alerta de disponibilitat
externa ha de consultar periòdicament `/health/ready` i avisar després de dues respostes
503 consecutives, per evitar soroll durant canvis breus de base de dades.

Exemple de línia produïda:

```json
{"timestamp":"2026-07-25T10:00:00Z","level":"ERROR","logger":"horaahora.health","event":"readiness_check_failed","request_id":"9f28b274-e360-4faa-9ee0-1216ca3a66b0","dependency":"database"}
```
