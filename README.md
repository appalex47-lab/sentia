# Sentia Intelligence from Conversations — Release Candidate 0.2.1

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
