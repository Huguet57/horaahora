# Textos de beta per a TestFlight

## Descripció de la beta

La calculadora de l'Aleta és una calculadora castellera que funciona com un xat: compara castells i actuacions escrits amb notació curta o en llenguatge natural i calcula la puntuació amb la taula oficial del Concurs de Castells 2026. La pestanya Puntuacions mostra aquesta taula de més a menys punts.

## Què cal provar

- **Calculadora:** comparacions amb notació curta o llenguatge natural, sinònims castellers, seguiments dins una conversa, historial local i aclariments quan una expressió és ambigua.
- **Puntuacions:** ordre de més a menys punts, barres que s'ajusten als castells visibles mentre es fa scroll i, en tocar un castell, el ressaltat dels castells de sota que descarregats en guanyen el carregat.
- **General:** llegibilitat, rendiment, errors de dades i comportament en iPhone i iPad.

Envia una captura, el model de dispositiu, la versió d'iOS i els passos exactes per reproduir qualsevol problema.

## Notes per a Beta App Review

- L'app no necessita registre ni credencials.
- L'API de la beta és `https://castells-superapp-poc.vercel.app`.
- Les converses es desen localment. Per interpretar una consulta, s'envien al backend com a màxim els darrers 12 missatges, l'últim escenari de càlcul complet de la conversa i un identificador aleatori d'instal·lació; no s'utilitzen per publicitat ni tracking. Amb «Millora la calculadora» (activada per defecte i desactivable a Ajustos), les converses noves es desen 90 dies sense identificadors del dispositiu per millorar les respostes.
- Ajustos obre la política de privacitat i prepara un correu de suport editable amb la versió, el build i l'identificador tècnic; no s'envia res fins que l'usuari ho confirma manualment i no s'exporten converses.
- La puntuació final es calcula amb un motor determinista i la taula 2026 versionada; la IA només interpreta el llenguatge.
- Les fonts editorials es mostren amb atribució i enllaç de retorn.
- L'app no demana permís de notificacions ni registra tokens APNs. Si una versió anterior tenia els avisos activats, en obrir-se deixa de registrar-se a APNs i en demana la baixa al backend.

### Sense seccions ocultes

Des de la versió que separa l'app pública de l'app interna, el build que es puja no conté Hora a Hora, Agenda ni cap gest secret. La nota sobre seccions ocultes que es copiava a **App Review Information → Notes** (guideline 2.3.1) ja no s'aplica a aquestes versions i s'ha de treure d'App Store Connect en enviar-les. Aquest repositori no modifica App Store Connect.

## Camps que s'han de completar manualment

| Camp | Valor pendent |
| --- | --- |
| Feedback email | Correu monitoritzat durant la beta |
| Contact name | Persona responsable davant Apple |
| Contact phone | Telèfon accessible per a Beta App Review |
| Privacy policy URL | URL HTTPS publicada i accessible des de l'app |
| Marketing URL | Opcional per TestFlight; recomanada abans de publicar |
