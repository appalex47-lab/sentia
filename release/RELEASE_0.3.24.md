# Release 0.3.24 — Integridad de checkpoints y reconciliación

Estado: RELEASE CANDIDATE.

Base verificada: 0.3.22. La referencia 0.3.23 no estaba disponible como artefacto materializado; por ello esta release incorpora la protección de checkpoint y deja explícita la reconstrucción/validación de ese comportamiento en la trazabilidad.

## Objetivo
Evitar que una sincronización parcial o interrumpida avance un cursor como si hubiera sido procesado correctamente y proporcionar una revisión determinista de consistencia.

## Cambios
- Checkpoint versionado por proveedor.
- Flujo de dos fases: `pending` → `committed`.
- El cursor confirmado anterior se conserva mientras existe un checkpoint pendiente.
- Un fallo/interrupción elimina únicamente la posición pendiente y conserva el último cursor confirmado.
- Validación de coincidencia entre `run_id` y checkpoint para evitar commits cruzados.
- Reconciliación sin llamadas externas mediante `/api/sync/reconcile`.
- Detección de checkpoints pendientes, commits sin run, secuencias inválidas y estados legacy con cursor sin checkpoint.
- Botón UI **Revisar consistencia** en Integraciones.
- Compatibilidad con estados anteriores: no se inventa ningún cursor histórico.

## Contratos
`checkpoint.version=1` y campos `status`, `committed_cursor`, `pending_cursor`, `sequence`, `run_id`, `page`, `updated_at`.

## Evidencia
- Pytest: se ejecuta sobre la suite completa.
- `py_compile`: `python/pipeline/sync.py` y `python/connection_server.py`.
- Pruebas nuevas: commit de dos fases, conservación de cursor ante fallo, protección contra run cruzado y reconciliación.

## Validación local requerida
- Interrumpir realmente el proceso Python durante una sincronización y comprobar que al reiniciar se conserva el último cursor comprometido.
- Probar cada proveedor real y verificar que su cursor/token/paginación siga siendo válido según la API vigente.
- Ejecutar en navegador real y comprobar el botón **Revisar consistencia**.

## Criterio de aceptación
Ningún cursor nuevo se considera confirmado antes de completar con éxito el procesamiento asociado; cualquier inconsistencia queda visible y accionable sin exponer secretos.
