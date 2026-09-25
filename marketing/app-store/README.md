# Captures de l'App Store

Tres captures per a iPhone de 6,9" (1320 × 2868 px, PNG sense canal alfa), una per a
cada part de l'app: calculadora, calendari i actualitat. App Store Connect només
necessita aquesta mida; les pantalles més petites s'escalen automàticament.

| Fitxer | Titular | Subtítol |
| --- | --- | --- |
| `output/01-calculadora.png` | Qui guanya? Pregunta-ho. | La calculadora castellera que funciona com un xat. |
| `output/02-calendari.png` | Totes les diades, en un calendari | Qui actua, on i a quina hora. |
| `output/03-actualitat.png` | Tota l’actualitat, hora a hora | Revista Castells i El Món Casteller, en un sol lloc. |

## Com es generen

- `raw/`: captures reals del simulador, que es mostren dins del mòbil.
- `screens.js`: titular, subtítol i captura de cada imatge.
- `template.html`: composició (fons vermell de la icona, esclat, mòbil blanc).
- `render.sh`: renderitza cada imatge amb Chrome sense interfície i la desa a `output/`.

```bash
marketing/app-store/render.sh
```

Cal Google Chrome i [uv](https://docs.astral.sh/uv/). Per canviar un text només cal
editar `screens.js` i tornar a executar el script.

## Com es tornen a capturar

1. Simulador iPhone 17 Pro Max en català, mode clar i barra d'estat neta:

   ```bash
   xcrun simctl spawn booted defaults write "Apple Global Domain" AppleLanguages -array ca-ES
   xcrun simctl ui booted appearance light
   xcrun simctl status_bar booted override --time 9:41 --dataNetwork wifi --wifiBars 3 --cellularMode active --cellularBars 4 --batteryState discharging --batteryLevel 100
   ```

   El canvi d'idioma requereix reiniciar el simulador.

2. Contingut de cada captura:
   - **Calculadora:** «Si la Vella fa 4 net, 4d10fm i 3 net carregat, i Vilafranca 3 i 4 de 10 i pilar de 9 carregat, qui guanya?» i, després, «I si la Vella descarrega el 3 net?». Captura amb la conversa desplaçada fins a dalt.
   - **Calendari:** colles seguides a l'Agenda: Capgrossos de Mataró, Castellers de Vilafranca i la Colla Jove de Castellers de Sitges. Dia seleccionat: dissabte 26 de setembre del 2026 (Santa Tecla a Sitges).
   - **Actualitat:** avisos activats i, amb l'Hora a Hora oberta, una notificació amb el mateix format que envia el backend (`title` = titular, `body` = resum):

     ```bash
     xcrun simctl push booted com.ahuguet.castellsenvena push.json
     ```

3. Desa cada captura a `raw/` amb `xcrun simctl io booted screenshot --type=png raw/<nom>.png`.

El mòbil només mostra els ~2.340 px de dalt de cada captura: el contingut important
ha de quedar per sobre d'aquesta alçada, i la barra de pestanyes queda fora.

## Abans de pujar-les

- Les captures mostren el vermell de marca com a color d'accent de l'app. Han d'anar
  amb una versió que ja porti aquest canvi.
- Els titulars de l'actualitat i els noms de Revista Castells i El Món Casteller són
  seus: cal que hi estiguin d'acord abans de fer-los servir en promoció.
