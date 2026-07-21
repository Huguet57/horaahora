PRIVACY_PAGE_HTML = """<!doctype html>
<html lang="ca">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <title>Privacitat · Castells en vena</title>
  <style>
    :root { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    body { margin: 0; background: Canvas; color: CanvasText; }
    main { max-width: 760px; margin: 0 auto; padding: 32px 22px 64px; }
    header { display: flex; align-items: flex-start; justify-content: space-between; gap: 24px; }
    h1 { font-size: clamp(2rem, 7vw, 3.25rem); letter-spacing: -0.04em; margin: 0 0 8px; }
    h2 { font-size: 1.2rem; margin: 30px 0 8px; }
    p, li { font-size: 1rem; line-height: 1.58; }
    .muted { color: GrayText; margin-top: 0; }
    .languages { display: flex; gap: 6px; padding: 4px; border: 1px solid color-mix(in srgb, CanvasText 15%, transparent); border-radius: 12px; }
    .languages button { border: 0; border-radius: 8px; padding: 8px 10px; color: inherit; background: transparent; font: inherit; font-weight: 650; cursor: pointer; }
    .languages button[aria-pressed="true"] { color: HighlightText; background: Highlight; }
    [data-content-language][hidden] { display: none; }
    a { color: LinkText; }
    footer { border-top: 1px solid color-mix(in srgb, CanvasText 15%, transparent); margin-top: 36px; padding-top: 20px; color: GrayText; }
    @media (max-width: 520px) { header { display: block; } .languages { width: fit-content; margin: 18px 0 24px; } }
  </style>
</head>
<body>
<main>
  <header>
    <div>
      <h1>Castells en vena</h1>
      <p class="muted">Política de privacitat · 22 de juliol de 2026</p>
    </div>
    <nav class="languages" aria-label="Idioma / Idioma / Language">
      <button type="button" data-language="ca" aria-pressed="true">CA</button>
      <button type="button" data-language="es" aria-pressed="false">ES</button>
      <button type="button" data-language="en" aria-pressed="false">EN</button>
    </nav>
  </header>

  <article data-content-language="ca">
    <h2>Quines dades tracta l’app</h2>
    <p>Castells en vena desa al dispositiu les converses de la Calculadora i còpies temporals de l’Hora a Hora i l’Agenda perquè les puguis tornar a consultar. Quan fas una consulta a la Calculadora, s’envien al servei els darrers missatges necessaris per respondre i un identificador tècnic aleatori de la instal·lació. El servei no desa les converses.</p>
    <h2>Notificacions</h2>
    <p>Les notificacions només s’activen si dones permís a iOS i les actives a l’app. Actualment no enviem el token de notificacions a cap backend propi.</p>
    <h2>Correu de suport</h2>
    <p>Quan selecciones «Contacta amb suport», l’app prepara un correu amb la versió, el número de build i l’identificador tècnic. Aquesta informació queda sempre visible i editable: el correu només s’envia quan prems manualment el botó d’enviament després de revisar-lo. També pots cancel·lar-lo.</p>
    <h2>Fonts i enllaços externs</h2>
    <p>L’app mostra contingut atribuït a Revista Castells, la CCCC i la taula oficial del Concurs de Castells 2026. Quan obres un web extern, s’aplica la política de privacitat d’aquell web.</p>
    <h2>Control de les dades</h2>
    <p>Pots eliminar converses des de la Calculadora, revocar les notificacions des dels ajustos d’iOS i desinstal·lar l’app per eliminar-ne les dades locals. Per a qualsevol consulta, escriu a <a href="mailto:tenimaletaapp@gmail.com">tenimaletaapp@gmail.com</a>.</p>
  </article>

  <article data-content-language="es" lang="es" hidden>
    <h2>Qué datos trata la app</h2>
    <p>Castells en vena guarda en el dispositivo las conversaciones de la Calculadora y copias temporales de Hora a Hora y la Agenda para que puedas volver a consultarlas. Cuando consultas la Calculadora, se envían al servicio los últimos mensajes necesarios para responder y un identificador técnico aleatorio de la instalación. El servicio no guarda las conversaciones.</p>
    <h2>Notificaciones</h2>
    <p>Las notificaciones solo se activan si das permiso a iOS y las activas en la app. Actualmente no enviamos el token de notificaciones a ningún backend propio.</p>
    <h2>Correo de soporte</h2>
    <p>Al seleccionar «Contacta con soporte», la app prepara un correo con la versión, el número de build y el identificador técnico. Esta información siempre queda visible y editable: el correo solo se envía cuando pulsas manualmente el botón de envío después de revisarlo. También puedes cancelarlo.</p>
    <h2>Fuentes y enlaces externos</h2>
    <p>La app muestra contenido atribuido a Revista Castells, la CCCC y la tabla oficial del Concurs de Castells 2026. Cuando abres una web externa, se aplica la política de privacidad de esa web.</p>
    <h2>Control de los datos</h2>
    <p>Puedes eliminar conversaciones desde la Calculadora, revocar las notificaciones desde los ajustes de iOS y desinstalar la app para eliminar sus datos locales. Para cualquier consulta, escribe a <a href="mailto:tenimaletaapp@gmail.com">tenimaletaapp@gmail.com</a>.</p>
  </article>

  <article data-content-language="en" lang="en" hidden>
    <h2>Data handled by the app</h2>
    <p>Castells en vena stores Calculator conversations and temporary Hour by Hour and Agenda copies on your device so you can access them again. When you use the Calculator, the latest messages needed to answer and a random technical installation identifier are sent to the service. The service does not store conversations.</p>
    <h2>Notifications</h2>
    <p>Notifications are only enabled if you grant iOS permission and enable them in the app. We currently do not send the notification token to our own backend.</p>
    <h2>Support email</h2>
    <p>When you select “Contact support”, the app prepares an email containing the version, build number and technical identifier. This information is always visible and editable: the email is only sent when you manually tap the send button after reviewing it. You can also cancel it.</p>
    <h2>Sources and external links</h2>
    <p>The app displays content attributed to Revista Castells, the CCCC and the official 2026 Concurs de Castells scoring table. When you open an external website, that website’s privacy policy applies.</p>
    <h2>Your controls</h2>
    <p>You can delete conversations in the Calculator, revoke notification access in iOS Settings and uninstall the app to remove its local data. For questions, email <a href="mailto:tenimaletaapp@gmail.com">tenimaletaapp@gmail.com</a>.</p>
  </article>

  <footer>Castells en vena · <a href="mailto:tenimaletaapp@gmail.com">tenimaletaapp@gmail.com</a></footer>
</main>
<script>
  const buttons = [...document.querySelectorAll('[data-language]')];
  const contents = [...document.querySelectorAll('[data-content-language]')];
  const selectLanguage = (language) => {
    document.documentElement.lang = language;
    buttons.forEach((button) => button.setAttribute('aria-pressed', String(button.dataset.language === language)));
    contents.forEach((content) => { content.hidden = content.dataset.contentLanguage !== language; });
  };
  buttons.forEach((button) => button.addEventListener('click', () => selectLanguage(button.dataset.language)));
  const preferredLanguage = (navigator.language || 'ca').slice(0, 2);
  if (['ca', 'es', 'en'].includes(preferredLanguage)) selectLanguage(preferredLanguage);
</script>
</body>
</html>
"""
