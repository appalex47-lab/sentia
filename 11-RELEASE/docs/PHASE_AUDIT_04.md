# PHASE AUDIT 04 — Performance, Offline y Deployment Hardening

## Resultado
**PASS CON LIMITACIONES DOCUMENTADAS**

## Cambios ejecutados
- Service Worker versionado en `sw.js`.
- Cache de shell de aplicación, JSON inicial y manifest.
- Cache runtime para recursos same-origin y Chart.js CDN después de la primera carga exitosa.
- Fallback offline para navegación hacia `index.html`.
- Registro del Service Worker desde `app.js`.
- CSP explícita en `index.html`.
- `connect-src 'self'`: el navegador no tiene acceso directo a Cohere.
- `worker-src 'self'` y `object-src 'none'`.
- Manifest PWA mínimo.
- Referencia de Chart.js fijada a versión `4.5.0`.
- Animación del gráfico desactivada para reducir trabajo en datasets grandes.
- Debounce de 150 ms en búsqueda de texto.
- `prefers-reduced-motion` incorporado.
- `.nojekyll` agregado para despliegue estático predecible en GitHub Pages.

## Benchmark reproducible
Dataset sintético: 10,000 menciones.

- Input: 1,523,996 bytes.
- Output: 13,290,203 bytes.
- Pipeline completo + validación: 4.29 s.
- Validación posterior de schema: 2.70 s.
- Resultado: PASS.

Estos números corresponden al entorno de auditoría y no son un SLA de navegador.

## Validaciones automatizadas
- `pytest`: 7 passed.
- `python -m python.validate`: PASS.
- `compileall`: PASS.
- `node --check js/app.js`: PASS.
- `node --check js/db.js`: PASS.
- `node --check sw.js`: PASS.
- HTML/manifest/data parse: PASS.
- CSP/dependency contract: PASS.
- Service Worker shell contract: PASS.

## No declarado como PASS
- Offline real en navegador: **LOCAL VALIDATION**.
- Lighthouse/axe: **LOCAL VALIDATION**.
- GitHub Pages real: **LOCAL VALIDATION**.
- Integridad SRI del CDN: pendiente de obtener/verificar hash oficial.
- Benchmark de memoria/CPU del navegador: **LOCAL VALIDATION**.

## Criterio
El RC no declara una capacidad browser como PASS si solo existe evidencia estática. El Service Worker queda implementado y preparado, pero su activación/recuperación offline debe verificarse en un navegador real.
