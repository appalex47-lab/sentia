# Release 0.3.30 — Optimización final de sincronización y performance

## Alcance
- Bounded parallelism para consultas independientes de comentarios de YouTube y LinkedIn.
- Orden determinista de resultados y fallos individuales no fatales.
- Nuevo `SENTIA_SYNC_COMMENT_WORKERS` (1–4, default 3).
- IndexedDB v13 con `getCount()` y lectura por índice acotada.
- Sin cambios al contrato de deduplicación, checkpoints o confirmación en dos fases.

## Seguridad
No se introducen secretos nuevos ni se persisten credenciales en IndexedDB.

## Validación
- 84/84 pruebas Python: PASS.
- `python -m compileall python`: PASS.
- `node --check js/app.js`: PASS.
- `node --check js/db.js`: PASS.
- JSON Schema: parse PASS.
- Integridad ZIP: PASS.
- Comparación 0.3.29 → 0.3.30: cambios limitados a `python/connection_server.py`, `js/db.js`, `python/tests/test_sync.py` y esta documentación.
- Validación real de proveedores (YouTube/LinkedIn) y smoke test de navegador: `REQUIERE VALIDACIÓN LOCAL`.

## Seguridad de distribución
El paquete de release no contiene archivos de estado de ejecución bajo `python/runtime/`; esos archivos son datos operativos locales y no forman parte del código distribuible.
