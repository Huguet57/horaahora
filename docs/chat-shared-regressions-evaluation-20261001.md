# Edicions d'escenari mal interpretades a les converses compartides

Origen: revisió de les converses compartides del 30/09 a l'01/10 de 2026, en què hi havia
26 converses i 83 torns. Diversos usuaris havien de corregir el bot quan retocaven un
escenari:

- «afegir el 3 net» substituïa el 4 net de la mateixa colla en lloc d'afegir-lo;
- «no carrega el 2d9sm i fa el 2d8 net» deixava el 2d9sm descarregat i hi afegia el 2d8;
- «carrega el 4d10fm, el 3d9sf i el 2d9sm» només marcava carregat el primer;
- a «Vilafranca carrega el pd9fmp i la Joves el pd7 net», el pd7 quedava descarregat;
- «els dos de 10» es llegia com el 2d10fmp en lloc del 3d10fm i el 4d10fm.

La fixture `tests/fixtures/chat_shared_regression_cases.json` en reprodueix els patrons.
Els missatges són paràfrasis, no el text dels usuaris. L'historial previ conté les
respostes reals del motor i l'escenari desat que rep l'app. Els totals els calcula el motor.

## Canvi

El prompt de la calculadora distingeix ara entre actualitzar, afegir i substituir un
castell. També fixa que un verb de resultat val per a tota l'enumeració que el segueix
i per a la segona colla quan s'omet. A més, afegeix «els dos de 10» a la taula de noms
convencionals.

L'avaluador accepta un `scenario` inicial per fixture, que és el que l'app envia com a
últim càlcul. També compara les etiquetes sense l'article: «la Joves» i «Joves» són la
mateixa colla, però «Jove» i «Joves» continuen sent diferents.

## Resultats reals

Sonnet 5.5 via OpenRouter, `reasoning.effort=low`, el mateix model que hi ha a producció.

| Fixture | Prompt | Passades | Torns superats | Escenaris complets | Cost USD |
|---|---|---:|---:|---:|---:|
| Converses compartides | Abans | 3 | 3/15 | 3/12 | 0,309 |
| Converses compartides | Final | 3 | 15/15 | 12/12 | 0,304 |
| Converses | Final | 1 | 21/23 | 18/20 | 0,479 |
| Preguntes obertes | Final | 1 | 20/21 | 15/16 | 0,582 |
| Autoria | Final | 1 | 9/9 | 9/9 | 0,182 |
| Ampliada | Final | 1 | 118/121 | 97/100 | 2,855 |

Abans del canvi, a la fixture de converses compartides només passava el cas d'afegir
el 3 net. Els altres tres fallaven les tres vegades, amb el mateix error que es veu a
producció.

Les fallades de la resta de fixtures no venen d'aquest canvi:

- **Converses, 2 fallades.** `corrections_keep_unaffected_groups` i
  `multi_group_update_keeps_omitted_group` retornen bé l'escenari, però etiqueten la
  intenció `total` en lloc de `comparació`. El motor calcula el guanyador igualment.
  Repetits tres vegades, passen 12/12 tant en aquesta branca com a `main`: és soroll del
  model.
- **Respostes redactades, 2 fallades.** `loaded_reference` (preguntes obertes) i
  `verds_alias` (ampliada) fallen per paraules de la resposta d'`informació_concurs`, que
  aquest canvi no toca.
- **Motor de puntuació, 2 fallades.** `duplicate_base` i `compatible_towers` (ampliada)
  tenen la interpretació correcta, però el motor no hi aplica la mateixa regla
  d'estructures repetides que la fixture. El motor no canvia en aquesta PR.

## Redacció i mida del prompt

La primera redacció de les regles superava el límit de 15.000 caràcters del prompt
d'interpretació. Una versió massa compactada va fer que «no carrega el 2d9sm i fa el 2d8
net» deixés el 2d9sm com a intent: 9/15 torns. La redacció final diu explícitament que
X surt de l'actuació i no queda com a intent ni descarregat. El prompt queda en 14.963
caràcters.
