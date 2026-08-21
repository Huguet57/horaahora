CONTEST_ROUTER_PROMPT = """<encaminament_concurs>
Classifica les preguntes factuals sobre la normativa, els resultats històrics o el rànquing de puntuacions del Concurs de Castells amb l'intent `informació_concurs`. Aquesta primera fase no les respon: descriu exactament quin coneixement local cal recuperar a `consulta_concurs`.

- `font` és `normativa` per regles, protocol, penalitzacions, rondes i canvis normatius; és `resultats` per edicions, guanyadors, posicions, actuacions, punts històrics i recalculacions d'una actuació passada; `font` és `puntuacions` per l'ordre de la taula 2026, la posició d'un castell, els castells que té per sobre o per sota i fragments com els primers o els últims del rànquing.
- `anys` conté només els anys explícits o inequívocament referits. Deixa'l buit si la consulta abraça totes les edicions.
- `colles` conserva els noms o sobrenoms de colla que dona l'usuari. Deixa'l buit si no en restringeix cap.
- Per `resultats`, `abast_resultats` és `edicions` si pregunta quines edicions es van celebrar o cancel·lar, `guanyadors` per palmarès o guanyadors, i `classificació` per posicions, punts, castells per ronda o recalculacions.
- Per `normativa`, `abast_resultats` és null.
- Per `puntuacions`, `abast_puntuacions` és `rànquing`. `anys` i `colles` són buits i `abast_resultats` és null.
- `resultat_puntuacions` és `carregat`, `descarregat` o `tots_dos`. Si l'usuari no concreta el resultat, usa `tots_dos`.
- Per `puntuacions`, `selecció_rànquing` indica la forma exacta de la resposta: `primers`, `últims`, `posició`, `veïns` o `complet`.
- Amb `primers` i `últims`, `límit_rànquing` és el nombre demanat (1 si l'usuari usa el singular) i `castell_rànquing` és null.
- Amb `posició` i `veïns`, conserva el castell demanat a `castell_rànquing` i deixa `límit_rànquing` a null.
- Amb `complet`, `límit_rànquing` i `castell_rànquing` són null.
- Per `normativa` i `resultats`, tots els camps de rànquing són null.
- Una recalculació històrica també s'encamina primer com `informació_concurs`: cal recuperar l'actuació documentada abans de convertir-la en un intent de càlcul.
- Amb `informació_concurs`, deixa `actuacions` buit i `aclariment` a null.
- Per qualsevol altre intent, `consulta_concurs` és null.

Inclou sempre `intent`, `actuacions`, `aclariment` i `consulta_concurs`, encara que siguin [], null i null. Respon exclusivament amb l'estructura sol·licitada.
</encaminament_concurs>"""
