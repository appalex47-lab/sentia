# Sentia 0.3.39 — GitHub Pages + Backend HTTPS

## Por qué existe el backend
GitHub Pages ejecuta únicamente HTML/CSS/JavaScript. Cohere, OAuth y las demás integraciones requieren un servicio HTTPS que mantenga las credenciales fuera del navegador.

## Flujo
GitHub Pages → Backend HTTPS → Cohere / Meta / Instagram / X / TikTok / YouTube / LinkedIn / GA4

## Configuración en Sentia
1. Configuración → Backend seguro.
2. Pega la URL HTTPS pública del backend.
3. Pulsa Guardar URL.
4. Pulsa Probar conexión.
5. Integraciones → Cohere.

## Cohere
El selector intenta consultar `/api/cohere/models`. Si el backend todavía no está conectado, muestra un catálogo de respaldo de modelos activos conocidos. Al guardar una API Key, el navegador la envía al backend y limpia el campo; IndexedDB solo conserva el modelo seleccionado.

## Render
El repositorio incluye `render.yaml`. En el servicio configura:
- `SENTIA_ALLOWED_ORIGINS`: origen exacto de GitHub Pages, por ejemplo `https://usuario.github.io`.
- `SENTIA_TOKEN_ENCRYPTION_KEY`: clave segura persistente.
- `COHERE_API_KEY`: opcional si prefieres provisionarla en el servidor.
- `COHERE_MODEL`: opcional; por defecto `command-a-plus-05-2026`.

El endpoint `/api/health` permite comprobar el servicio.
