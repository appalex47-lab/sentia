# Sentia Intelligence from Conversations — Release 0.3.28

## Objetivo
Convertir la persistencia de sincronizaciones en un protocolo de dos fases: Python entrega el lote y mantiene el checkpoint pendiente hasta que el navegador confirma que el contenido esperado fue persistido en IndexedDB.

## Cambios
- Nuevo estado transitorio `awaiting_persistence`.
- El cursor nuevo ya no reemplaza al cursor confirmado antes de la persistencia local.
- `POST /api/sync/confirm-persistence` valida `provider`, `run_id`, `content_keys` y `persisted_count` contra el resultado de la ejecución.
- El checkpoint pasa de `pending` a `committed` sólo después de la confirmación.
- Un desajuste de contenido produce `SYNC_CONTENT_CONFIRMATION_MISMATCH` y no modifica el checkpoint.
- Se conserva el cursor confirmado anterior si la persistencia del navegador falla o se interrumpe.
- IndexedDB sube a versión 11 y garantiza la existencia del store `sync_repairs` usado por las reparaciones.
- Las reparaciones también usan el protocolo de confirmación antes de marcarse como completadas.
- Los resultados de proveedor incluyen `cursor` y `page` para que el commit sea reproducible.

## Seguridad y datos
- No se agregan secretos a manifests, runs o repair history.
- No se inventan cursores ni posiciones.
- La confirmación exige coincidencia exacta de claves de contenido.
- El flujo sigue siendo local-first: IndexedDB conserva los datos del navegador.

## QA
- Suite Python: 79 pruebas PASS.
- JavaScript: `node --check` PASS para `app.js` y `db.js`.
- Python: `compileall` PASS.
- JSON Schema: parseo PASS.
- Validación real de navegador/IndexedDB, interrupción física del navegador y APIs reales: REQUIERE VALIDACIÓN LOCAL.

## Cloud
- Nivel A: PASS — código, contratos y documentación.
- Nivel B: PASS — pruebas automatizadas.
- Nivel C: pendiente — navegador real, IndexedDB real y fallos reales durante persistencia.

## Criterio de aceptación principal
Si el navegador no confirma el contenido exacto de una ejecución, el servidor no debe avanzar el cursor comprometido de esa ejecución.
