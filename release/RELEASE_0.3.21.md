# Release 0.3.21 — Alertas accionables y recuperación

## Estado
RELEASE CANDIDATE — validaciones automatizadas PASS; validaciones externas/locales pendientes.

## Base
0.3.20 — Salud y frescura de sincronización.

## Cambios
- Alertas deterministas de sincronización.
- Endpoint `/api/sync/alerts`.
- Acciones de sincronización/reintento desde la interfaz.
- Reutilización del lock y backoff existentes.
- Documentación y trazabilidad actualizadas.

## Evidencia
- 65/65 pytest PASS.
- compileall PASS.
- JS syntax PASS.
- smoke de alertas PASS.

## No verificado aquí
OAuth real, APIs reales, navegador/IndexedDB, ejecución prolongada y GitHub Pages.
