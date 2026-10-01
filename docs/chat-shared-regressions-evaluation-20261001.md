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

> **Pendent.** Aquests resultats són de la primera redacció de les regles, que era uns
> 400 caràcters més llarga. Superava el límit de 15.000 caràcters del prompt
> d'interpretació, i per això se n'ha compactat el text sense canviar-ne el contingut.
> Aquesta redacció final encara no s'ha executat, perquè la clau d'avaluació s'ha quedat
> sense crèdit (límit de 20 USD). Cal repetir la fixture de converses compartides amb
> tres passades abans de fer el merge.

Sonnet 5.5 via OpenRouter, `reasoning.effort=low`, el mateix model que hi ha a producció.

| Fixture | Prompt | Passades | Torns superats | Escenaris complets | Cost USD |
|---|---|---:|---:|---:|---:|
| Converses compartides | Abans | 3 | 3/15 | 3/12 | 0,309 |
| Converses compartides | Després | 3 | 15/15 | 12/12 | 0,312 |
| Converses | Després | 1 | 23/23 | 20/20 | 0,481 |
| Preguntes obertes | Després | 1 | 21/21 | 16/16 | 0,592 |
| Autoria | Després | 1 | 8/9 | 8/9 | 0,189 |
| Ampliada | Després | 1 | 81 de 83 executats | 63 de 65 executats | — |

Notes:

- **Converses compartides, abans del canvi:** només passava el cas d'afegir el 3 net.
  Els altres tres fallaven les tres vegades, amb el mateix error que es veu a producció.
- **Autoria:** l'única fallada és `reported_open_question`, perquè a la resposta redactada
  li falta una de les paraules exigides. És una resposta d'`informació_concurs`, que
  aquest canvi no toca, i el mateix cas passa a la fixture de preguntes obertes.
- **Ampliada:** OpenRouter va retornar 402 (sense crèdit) a 35 dels 100 escenaris, i
  aquests no s'han executat. Les dues fallades de la part executada, `duplicate_base` i
  `compatible_towers`, són de les regles del motor de puntuació. La interpretació és la
  correcta, però el motor no hi aplica la mateixa regla d'estructures repetides que la
  fixture. El motor no canvia en aquesta PR.
