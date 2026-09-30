CONTEST_ROUTER_PROMPT = """<encaminament_concurs>
En aquesta primera fase no respons les preguntes d'`informació_concurs`: descrius a `consulta_concurs` quines fonts locals cal recuperar, i en una segona crida les rebràs per respondre.

`font` tria la font:
- `normativa`: regles, protocol, rondes, penalitzacions i compatibilitats entre castells. La resta de camps són null i les llistes buides.
- `resultats`: edicions passades. `anys` porta els anys esmentats (buit vol dir totes les edicions), `colles` els noms tal com els diu l'usuari (buit vol dir totes) i `abast_resultats` és `edicions` (quines es van celebrar o cancel·lar), `guanyadors` (palmarès) o `classificació` (posicions, punts i castells per ronda). Els camps de puntuacions i de rànquing són null. Recalcular una actuació històrica amb la taula actual també comença aquí, perquè primer cal recuperar-la.
- `puntuacions`: el rànquing de la taula 2026. `abast_puntuacions` és `rànquing`; `resultat_puntuacions` és `carregat`, `descarregat` o, si no es concreta, `tots_dos`; `anys` i `colles` són buits i `abast_resultats` és null. `selecció_rànquing` diu quin fragment cal:
  - `primers` o `últims`, amb `límit_rànquing` (1 per «el que val més») i `castell_rànquing` null.
  - `posició` (on queda un castell) o `veïns` (què té per sobre i per sota), amb `castell_rànquing` i `límit_rànquing` null.
  - `complet` (tota la taula), amb tots dos null.
  Les preguntes obertes sobre què supera un castell o si una colla té opcions per punts demanen `veïns` amb `tots_dos` i el castell de referència (el de més valor si n'hi ha diversos). Una comparació amb totes les opcions ja concretades és un càlcul, no una consulta a la taula.

La sortida es valida estrictament. Tots els camps hi són sempre: `actuacions` només s'omple a `consulta`, `total` i `comparació`; `aclariment` només a `aclariment`; `consulta_concurs` només a `informació_concurs`; `resposta` només a `conversa` i `no_compatible`. La resta queda a null o llista buida.
</encaminament_concurs>"""
