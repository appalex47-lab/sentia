# AUDIT_MASTER

## Estado
Release Candidate RC-0.1.4. La implementación está endurecida para ejecución local/offline y despliegue estático, pero conserva gates de validación que requieren navegador/GitHub Pages/credenciales reales.

## Evidencia
- PRD maestro: fuente de requisitos originales.
- Fases 0–12: arquitectura, contratos y criterios.
- Código: `python/`, `js/`, `css/`, `index.html`, `sw.js`.
- Contrato: `schemas/datos_procesados.schema.json`.
- Pruebas: `python/tests/`.
- Auditorías: `docs/PHASE_AUDIT_01.md` a `docs/PHASE_AUDIT_04.md`.

## Matriz resumida
| ID | Área | Implementación | Evidencia | Estado |
|---|---|---|---|---|
| REQ-DATA-001 | JSON | schema + validator | schema PASS | PASS |
| REQ-DB-001 | IndexedDB | `js/db.js` | estático + checklist | LOCAL VALIDATION browser |
| REQ-PIPE-001 | Pipeline | `python/pipeline/` | 7 tests + benchmark | PASS |
| REQ-SENT-001 | Sentimiento | `sentiment.py` | contract/fallback | PASS WITH LIMITATION |
| REQ-AI-001 | Cohere | `ai.py` | mock/contract tests | LOCAL VALIDATION real API |
| REQ-UI-001 | Dashboard | HTML/CSS/JS | static/syntax | LOCAL VALIDATION browser |
| REQ-OFFLINE-001 | Offline | `sw.js` | static contract | LOCAL VALIDATION browser |
| REQ-SEC-001 | Seguridad | CSP + secret boundaries | static | PASS STATIC |
| REQ-A11Y-001 | Accesibilidad | semantic HTML/focus | static | LOCAL VALIDATION browser |
| REQ-PERF-001 | Rendimiento | benchmark 10k + pagination | measured | PASS WITH BROWSER LIMITATION |
| REQ-DEPLOY-001 | GitHub Pages | relative paths + `.nojekyll` | static | LOCAL VALIDATION |

## Niveles de auditoría
A = revisión estática de código/documentación/arquitectura.
B = funcional cuando el entorno lo permita.
C = REQUIERE VALIDACIÓN LOCAL: dependencias Python, modelo real de pysentimiento, credenciales Cohere, navegador real, IndexedDB, Service Worker, GitHub Pages y datasets grandes.

## Limitaciones conocidas
1. El fallback de sentimiento es heurístico y no sustituye una ejecución real de pysentimiento.
2. Cohere no se conecta desde el navegador; la integración real vive en Python.
3. Los secretos no deben introducirse en la UI.
4. Chart.js está fijado a `4.5.0` pero continúa siendo CDN; el Service Worker permite cachearlo después de una primera carga exitosa. SRI oficial pendiente de verificación.
5. El benchmark 10k mide pipeline Python y schema, no rendimiento del navegador.
6. GitHub Pages no permite configurar cabeceras HTTP arbitrarias mediante este repositorio estático; CSP se entrega como meta tag.
7. El score inicial es una implementación de referencia y sus pesos deben validarse con reglas de negocio reales.

## Gate de release
No aprobar producción si falla cualquiera de: exposición de secretos, corrupción de datos, contrato JSON, transacciones IndexedDB, pipeline principal, offline browser, accesibilidad crítica, o errores críticos no controlados.
