# Release 0.3.25 — Reconciliación extremo a extremo

Estado: RELEASE CANDIDATE.

## Objetivo

Verificar no sólo que el backend haya completado una sincronización, sino que el resultado recibido haya sido persistido correctamente en la IndexedDB del navegador.

## Cambios

- Nueva versión IndexedDB v8.
- Nuevo store `sync_manifests` con índices por `run_id`, `provider` y `persisted_at`.
- Cada sincronización exitosa genera un recibo local asociado al `run_id`.
- El recibo registra conteo recibido, conteo persistido, duplicados y momento de persistencia.
- `/api/sync/reconcile` acepta los manifiestos locales y compara el último run exitoso del servidor contra la evidencia local.
- Detección de `LOCAL_MANIFEST_MISSING`, `LOCAL_RUN_MISMATCH`, `LOCAL_RECEIVED_COUNT_MISMATCH` y `LOCAL_PERSISTED_COUNT_SHORTFALL`.
- La reconciliación mantiene la validación anterior de checkpoints y estados legacy.
- No se almacenan tokens, API keys ni secretos en los manifiestos.

## Contratos

`sync_manifests`:
- `manifest_id`
- `run_id`
- `provider`
- `source_count`
- `duplicate_count`
- `received_count`
- `persisted_count`
- `persisted_at`
- `mode`

## Evidencia

- Pruebas unitarias de reconciliación de manifiestos.
- Suite completa de Python.
- Compilación Python.
- Sintaxis JavaScript.
- Integridad del ZIP.

## Validación local requerida

- Ejecutar una sincronización real desde cada proveedor.
- Confirmar que IndexedDB v8 migra sin pérdida de datos.
- Interrumpir el navegador durante la persistencia y comprobar que la reconciliación detecta la ausencia del manifiesto.
- Ejecutar el flujo real con el bridge Python y APIs externas.

## Criterio de aceptación

Una sincronización no se considera completamente reconciliada hasta que el servidor y la evidencia local de IndexedDB coincidan en `run_id` y cantidad de registros recibidos/persistidos.
