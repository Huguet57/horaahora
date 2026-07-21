# Textos de beta per a TestFlight

## Descripció de la beta

Castells és una prova de concepte d'una super-app castellera col·laborativa. Reuneix l'Hora a Hora de Revista Castells, l'agenda d'actuacions de la Coordinadora de Colles Castelleres de Catalunya i una calculadora conversacional basada en la taula de puntuacions del Concurs de Castells 2026.

## Què cal provar

- **Hora a Hora:** ordre cronològic, enllaços, detall intern dels apunts sense enllaç i lectura després d'una pèrdua temporal de connexió.
- **Agenda:** punts als dies amb actuacions, gestos i fletxes de setmana/mes, plegat manual, canvi de dia, fitxes i obertura de la ubicació a Google Maps.
- **Calculadora:** comparacions amb notació curta o llenguatge natural, sinònims castellers, seguiments dins una conversa, historial local i aclariments quan una expressió és ambigua.
- **General:** llegibilitat, rendiment, errors de dades i comportament en iPhone i iPad.

Envia una captura, el model de dispositiu, la versió d'iOS i els passos exactes per reproduir qualsevol problema.

## Notes per a Beta App Review

- L'app no necessita registre ni credencials.
- L'API de la beta és `https://castells-superapp-poc.vercel.app`.
- Les converses es desen localment. Per interpretar una consulta, s'envien al backend com a màxim els darrers 12 missatges i un identificador aleatori d'instal·lació; no s'utilitzen per publicitat ni tracking.
- La puntuació final es calcula amb un motor determinista i la taula 2026 versionada; la IA només interpreta el llenguatge.
- Les fonts editorials es mostren amb atribució i enllaç de retorn.

## Camps que s'han de completar manualment

| Camp | Valor pendent |
| --- | --- |
| Feedback email | Correu monitoritzat durant la beta |
| Contact name | Persona responsable davant Apple |
| Contact phone | Telèfon accessible per a Beta App Review |
| Privacy policy URL | URL HTTPS publicada i accessible des de l'app |
| Marketing URL | Opcional per TestFlight; recomanada abans de publicar |
