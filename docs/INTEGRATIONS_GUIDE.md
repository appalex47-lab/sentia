# Sentia Intelligence from Conversations — Guía de Integraciones

## 1. Principio de arquitectura

Sentia es local-first. La interfaz puede guardar configuración no sensible en IndexedDB, pero **nunca** debe guardar API keys, client secrets, access tokens, refresh tokens ni claves privadas.

Arquitectura recomendada:

`Proveedor → OAuth/API → conector Python → normalización → pipeline → datos_procesados.json → IndexedDB → Sentia`

La interfaz de Integraciones funciona como catálogo, configuración y documentación. La ejecución real de las APIs corresponde a conectores Python.

## 2. Integraciones iniciales

| Proveedor | Objetivo | Estado de producto | Secretos | Documentación oficial |
|---|---|---|---|---|
| Meta / Facebook Pages | páginas, publicaciones, comentarios y métricas permitidas | Catálogo / conector por implementar | OAuth/client credentials | https://developers.facebook.com/docs/ |
| Instagram | cuentas profesionales, contenido y datos permitidos | Catálogo / conector por implementar | OAuth/access token | https://developers.facebook.com/docs/instagram-platform/ |
| X | búsqueda/lectura de posts y otras capacidades según plan | Catálogo / conector por implementar | OAuth/Bearer según endpoint | https://developer.x.com/ |
| TikTok | contenido y capacidades disponibles según producto/permisos | Catálogo / conector por implementar | OAuth/access token | https://developers.tiktok.com/doc/ |
| YouTube | videos, canales, comentarios y recursos permitidos | Catálogo / conector por implementar | API key/OAuth | https://developers.google.com/youtube/v3/docs |
| LinkedIn | posts y capacidades de organización según permisos | Catálogo / conector por implementar | OAuth | https://learn.microsoft.com/en-us/linkedin/marketing/ |
| Google Analytics 4 | métricas de adquisición/comportamiento | Catálogo / conector por implementar | OAuth/service credentials | https://developers.google.com/analytics |
| Cohere | resumen e interpretación generativa | Integración Python preparada | `COHERE_API_KEY` | https://docs.cohere.com/ |
| Conector personalizado | cualquier API REST/JSON compatible | Arquitectura preparada | depende del proveedor | documentación del proveedor |

## 3. Cómo debe conectarse cada proveedor

### Meta / Facebook / Instagram

Meta agrupa gran parte de las integraciones de Facebook e Instagram en su plataforma de desarrolladores. El conector deberá solicitar únicamente los permisos necesarios, almacenar configuración no sensible en Sentia y mantener tokens fuera del navegador.

### X

X ofrece API v2 y herramientas oficiales de consulta. La disponibilidad de búsqueda, streaming, límites y otros endpoints depende del plan y permisos de la aplicación. No se debe asumir acceso ilimitado.

### TikTok

TikTok dispone de productos separados como Display API, Research API y Content Posting API. Para publicar contenido existen flujos Direct Post y Upload, con scopes y procesos de aprobación específicos. Sentia debe separar lectura/escucha de publicación.

### YouTube

YouTube Data API v3 usa API key u OAuth 2.0 según la operación. Las operaciones privadas o de modificación requieren autorización; la API utiliza cuotas.

### LinkedIn

LinkedIn requiere permisos específicos. Su Posts API permite recuperar/crear publicaciones dependiendo de permisos y contexto de organización/miembro.

### Google Analytics 4

GA4 debe tratarse como fuente analítica complementaria, no como red social. Sus métricas deben ingresar al modelo de datos mediante un conector independiente y conservar `fuente`, `fecha`, dimensiones y métricas originales.

## 4. Variables de entorno

Ejemplo conceptual:

```text
COHERE_API_KEY=
COHERE_MODEL=
META_APP_ID=
META_APP_SECRET=
META_ACCESS_TOKEN=
INSTAGRAM_ACCESS_TOKEN=
X_CLIENT_ID=
X_CLIENT_SECRET=
X_BEARER_TOKEN=
TIKTOK_CLIENT_KEY=
TIKTOK_CLIENT_SECRET=
YOUTUBE_API_KEY=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
LINKEDIN_CLIENT_ID=
LINKEDIN_CLIENT_SECRET=
GA4_PROPERTY_ID=
```

**No rellenar estas variables en el frontend ni en IndexedDB.** Los nombres son un contrato de configuración para futuros conectores; cada proveedor debe validarse contra su documentación vigente antes de activarlo.

## 5. Ciclo de vida de un conector

1. Registrar proveedor.
2. Configurar identificadores no secretos.
3. Configurar credenciales en entorno seguro.
4. Ejecutar autenticación/autorización.
5. Probar conexión.
6. Leer datos.
7. Normalizar al contrato de Sentia.
8. Validar y deduplicar.
9. Ejecutar sentimiento/reglas/scoring.
10. Persistir y registrar diagnóstico.

## 6. Estado de cada integración

Sentia debe distinguir:

- `CATALOG`: proveedor documentado, conector aún no implementado.
- `CONFIGURED`: configuración no sensible registrada.
- `AUTHENTICATION_REQUIRED`: falta autorización.
- `CONNECTED`: prueba de conexión satisfactoria.
- `ERROR`: última prueba falló.
- `DISABLED`: integración desactivada.
- `LOCAL_VALIDATION`: requiere ejecución con credenciales reales.

## 7. Regla de seguridad

Una API no debe llamarse directamente desde el frontend estático si eso expone secretos o requiere un flujo que el navegador no puede manejar de forma segura. En esos casos el conector debe ejecutarse en Python/local o mediante una infraestructura segura que actúe como backend.

## 2026-10 — Asistente de conexión

Sentia usa un asistente de conexión por proveedor. El usuario completa únicamente campos públicos/no sensibles (por ejemplo App ID, Client ID, Property ID, Channel ID, Redirect URI y scopes). Los secretos se muestran como requisitos del conector, pero no se guardan en IndexedDB, localStorage ni JSON.

### Principio de configuración

1. **Campos públicos:** se guardan en IndexedDB para evitar repetirlos.
2. **Secretos:** `client_secret`, API keys, access tokens, refresh tokens y credenciales privadas permanecen en el entorno seguro de Python.
3. **Documentación:** cada tarjeta enlaza a la documentación oficial del proveedor.
4. **Prueba de conexión:** se habilitará por integración cuando exista su conector Python real.

### Campos iniciales por integración

| Integración | Campos públicos | Secretos fuera del navegador |
|---|---|---|
| Meta / Facebook Pages | App ID, Page ID, Redirect URI, Scopes | META_APP_SECRET, META_ACCESS_TOKEN |
| Instagram | App ID, Instagram Account ID, Redirect URI, Scopes | INSTAGRAM_ACCESS_TOKEN, META_APP_SECRET |
| X | Client ID, Redirect URI, Scopes | X_CLIENT_SECRET, X_BEARER_TOKEN |
| TikTok | Client Key, Redirect URI, Scopes | TIKTOK_CLIENT_SECRET |
| YouTube | Project ID, Channel ID, Redirect URI, Scopes | YOUTUBE_API_KEY, GOOGLE_CLIENT_SECRET |
| LinkedIn | Client ID, Organization ID, Redirect URI, Scopes | LINKEDIN_CLIENT_SECRET |
| GA4 | Project ID, Property ID, Redirect URI, Scopes | GOOGLE_CLIENT_SECRET, GOOGLE_SERVICE_ACCOUNT_JSON |
| Cohere | Modelo | COHERE_API_KEY |
| Personalizado | Base URL, nombre, tipo de autenticación, scopes | CUSTOM_SECRET |

> Los campos exactos pueden variar según el producto/API y los permisos aprobados por el proveedor. La interfaz debe ser extensible y no asumir que una API key es suficiente para todos los casos.

## Fase 10 — conexión asistida

El Centro de Integraciones ya diferencia entre **datos públicos de configuración** y **secretos**. La interfaz permite guardar App ID, IDs de recursos, Redirect URI y scopes en IndexedDB. Los secretos se mantienen en Python.

Para Meta/Facebook + Instagram existe ahora un puente local de conexión en `python/connection_server.py`. El puente valida la presencia de `META_APP_SECRET` y prepara el inicio OAuth. La implementación de esta fase es deliberadamente una fundación: el intercambio final del authorization code por tokens y la primera sincronización se validarán e implementarán con la versión vigente de la Graph API y los permisos aprobados.

### ¿Dónde se configura cada cosa?

| Dato | Sentia UI | Python seguro |
|---|---:|---:|
| App ID | Sí | Puede leerse desde entorno si se desea |
| Page ID | Sí | No necesario |
| Instagram Account ID | Sí | No necesario |
| Redirect URI | Sí | Sí, debe coincidir |
| Scopes | Sí | Sí, para el conector |
| Client Secret / App Secret | **No** | **Sí** |
| Access Token | **No** | **Sí** |
| Refresh Token | **No** | **Sí** |

## Fase 0.3.3 — Meta OAuth real

El asistente de Meta ya puede iniciar OAuth desde Sentia y completar el intercambio del authorization code en Python. La UI transmite únicamente configuración pública; `META_APP_SECRET` y el access token permanecen en Python.

El conector usa Graph API versionada y actualmente propone `v26.0`; debe verificarse contra la versión disponible para la Meta App antes de producción. Meta recomienda llamadas versionadas. citeturn1search0turn1search1

La conexión real todavía requiere una Meta App, Redirect URI registrada, permisos adecuados y validación local. No se considera producción hasta completar esa prueba.

## Fase 0.3.3 — Meta OAuth real

El asistente de Meta ya puede iniciar OAuth desde Sentia y completar el intercambio del authorization code en Python. La UI transmite únicamente configuración pública; `META_APP_SECRET` y el access token permanecen en Python.

El conector usa Graph API versionada y actualmente propone `v26.0`; debe verificarse contra la versión disponible para la Meta App antes de producción. Meta recomienda llamadas versionadas. citeturn1search0turn1search1

La conexión real todavía requiere una Meta App, Redirect URI registrada, permisos adecuados y validación local. No se considera producción hasta completar esa prueba.

## Fase 0.3.4 — Selección e ingestión Meta

Después de autorizar Meta, Sentia puede listar las páginas disponibles y detectar una cuenta profesional de Instagram vinculada. La selección se realiza en **Integraciones**. Los identificadores seleccionados pueden guardarse como configuración no sensible; los tokens permanecen en Python.

La sincronización ejecuta la ingesta desde Python y pasa los textos por el pipeline canónico de Sentia antes de devolverlos a la aplicación. Si Meta no concede un permiso, el conector debe informar el error y no inventar datos.

## Fase 0.3.5 — Persistencia segura
Los tokens OAuth no se almacenan en IndexedDB ni localStorage. El bridge Python puede persistirlos cifrados mediante AES-GCM en `python/runtime/tokens.enc`; la clave se proporciona exclusivamente por `SENTIA_TOKEN_ENCRYPTION_KEY`. La UI puede mostrar estado de conexión, expiración y última sincronización sin recibir el token. `Desconectar` elimina el almacenamiento persistido.


## Ingesta de llamadas en español
Sentia usa español (`es`) como idioma predeterminado para WhatsApp y transcripciones de llamadas. Los audios compatibles pueden enviarse al bridge Python para Cohere Transcribe. Cohere documenta soporte de español y formatos FLAC/MP3/MPEG/MPGA/OGG/WAV, con límite de 25 MB; el modelo no ofrece diarización ni timestamps de hablante. citeturn0search3
