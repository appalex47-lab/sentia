# Sentia Intelligence from Conversations — Release Candidate 0.3.0

Implementación materializada a partir del PRD maestro y de las fases 0–12 de arquitectura.

## Stack congelado
- Python local/batch para ingestión y procesamiento.
- HTML5 + CSS3 + Vanilla JavaScript.
- IndexedDB como persistencia local-first.
- GitHub Pages para despliegue estático.
- Cohere exclusivamente desde Python.
- pysentimiento para sentimiento.
- SVG nativo para visualización, sin CDN de runtime.

No se usan React, Angular, Vue ni backend web.

## Flujo
Input → validación → normalización/limpieza → deduplicación → calidad → sentimiento → reglas → scoring → Cohere opcional → estadísticas → JSON → IndexedDB → Dashboard.

## Seguridad
Las claves API no se almacenan en IndexedDB, localStorage, sessionStorage, JSON exportado, logs ni Git.
Use `COHERE_API_KEY` como variable de entorno local.

## Ejecución
1. `python -m pytest`
2. `python -m python.main --input python/tests/fixtures/mentions.json --output data/datos_procesados.json`
3. Sirva el directorio raíz con un servidor HTTP local para probar `fetch()` e IndexedDB:
   `python -m http.server 8000`
4. Abra `http://localhost:8000/`
5. El Service Worker cachea el shell para uso offline después de una primera carga exitosa. La visualización usa SVG nativo y no depende de una CDN externa.

La validación real de pysentimiento/Cohere requiere instalar dependencias y disponer de credenciales.

## Offline y deployment
- `sw.js` cachea el shell, datos iniciales y recursos runtime.
- `manifest.json` permite instalación como aplicación.
- `.nojekyll` hace predecible el despliegue estático en GitHub Pages.
- La visualización temporal usa SVG nativo y no depende de CDN. El primer arranque puede funcionar sin red después de que el navegador haya recibido el shell estático.
- No se requiere Chart.js ni ninguna CDN externa en runtime.

## Identidad de producto
Nombre del producto: **Sentia Intelligence from Conversations**. Describe la propuesta central: convertir conversaciones en inteligencia accionable. La disponibilidad legal, de dominio y de marca debe verificarse antes de uso comercial.

## Centro de Integraciones

La vista **Integraciones** centraliza proveedores sociales, analíticos e IA. La vista **Configuración** administra preferencias locales y enlaza la guía descargable. La catalogación no implica que cada API esté conectada: cada proveedor requiere su propio conector, credenciales y validación.

## Conector local de Integraciones

Para probar la fundación Meta/Facebook + Instagram desde la interfaz:

```bash
export META_APP_ID="tu_app_id"
export META_APP_SECRET="tu_app_secret"
export META_REDIRECT_URI="http://127.0.0.1:8787/api/integrations/meta/callback"
export META_SCOPES=""
python -m python.connection_server
```

Después abre Sentia, entra en **Integraciones → Meta / Facebook Pages** o **Instagram**, guarda los campos públicos y usa **Validar entorno Python**. No introduzcas el App Secret en el navegador.


## Integraciones 0.3.4

Meta/Facebook + Instagram ahora incluyen selección de cuentas e ingestión inicial hacia el pipeline canónico. Los tokens permanecen en Python; el navegador solo recibe metadatos y resultados procesados.


## Ingesta manual 0.3.6

Desde **Ingesta manual** puedes cargar exportaciones de WhatsApp, transcripciones de llamadas y TXT/CSV/JSON. Para llamadas, Sentia recibe texto: la grabación debe transcribirse previamente. Si existe `texto_traducido`, Sentia conserva el original y utiliza la traducción para el análisis.

## Fase 0.3.10

El motor analiza conversaciones completas con trayectoria de sentimiento, fricción, resolución y score global. Las credenciales continúan fuera del navegador.

## RC 0.3.13 — memoria semántica

- Búsqueda local-first en IndexedDB.
- Endpoint Python `/api/knowledge/search`.
- Similitud determinista y explicable.
- Aliases y variantes lingüísticas conservadoras.
- Sin dependencia de Cohere.
- Sin mezcla con dominios de catálogo/farmacia.
- 35/35 tests PASS.


## 0.3.22
Diagnóstico operativo exportable de sincronizaciones sin credenciales.


## Release actual
**0.3.24 — Integridad de checkpoints y reconciliación.** Revisa `docs/RELEASE_0.3.24.md`.


## Release 0.3.27 — Reparación segura de inconsistencias

Esta versión añade un plan determinista de reparación. Las inconsistencias de persistencia local pueden disparar una re-sincronización del proveedor usando el flujo existente de deduplicación y checkpoints. Las inconsistencias de checkpoint o estado no se modifican automáticamente y quedan marcadas para revisión manual.

Cada intento de reparación se registra localmente en `sync_repairs` con estado `running`, `completed` o `failed`, proveedor, códigos de causa, `run_id` y duración. No contiene tokens ni credenciales.
