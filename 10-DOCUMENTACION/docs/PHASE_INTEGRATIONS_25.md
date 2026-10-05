# FASE 0.3.18 — Resiliencia, backoff y exclusión de concurrencia

## Objetivo
Reducir fallos transitorios y condiciones de carrera en la sincronización multi-fuente sin ocultar errores permanentes ni alterar la separación de secretos.

## Alcance implementado
- Reintentos deterministas para errores transitorios: `NETWORK_ERROR`, `HTTP_408`, `HTTP_429` y respuestas `HTTP_5xx`.
- Máximo de 3 intentos por operación principal de proveedor.
- Backoff exponencial configurable desde el helper: 0.25 s, 0.5 s por defecto.
- Errores permanentes como `HTTP_401` no se reintentan.
- Contador `retry_count` en cada resultado de proveedor y en cada ejecución.
- Bloqueo de proceso para impedir dos `/api/sync/all` concurrentes; una segunda solicitud recibe `409 SYNC_ALREADY_RUNNING`.
- Historial de sincronización conserva el número de reintentos.
- UI de historial muestra los reintentos por ejecución.

## Seguridad y consistencia
- No se agregan secretos al historial.
- El lock sólo protege la ejecución del orquestador en el proceso Python; no pretende ser un scheduler distribuido.
- Los reintentos no modifican el mecanismo de deduplicación: los IDs externos continúan siendo la clave de idempotencia.
- No se publican cambios en proveedores externos.

## Contratos
`run.retry_count` y `providers[].retry_count` son enteros >= 0.
`POST /api/sync/all` puede responder `409` con `error=SYNC_ALREADY_RUNNING` si ya existe una sincronización en curso.

## QA
- 57/57 pruebas PASS.
- Python compileall PASS.
- JavaScript syntax PASS (`app.js`, `db.js`).
- JSON Schema PASS.
- Pruebas unitarias de reintento: error transitorio reintenta; error permanente no reintenta.

## Validación local requerida
- Simular/observar 429 y 5xx reales de cada proveedor.
- Confirmar que dos acciones simultáneas del usuario reciben el comportamiento esperado.
- Verificar duración percibida y límites de cuota en cuentas reales.
- Confirmar la UI del historial en navegador.

## Criterios de aceptación
- [x] Los errores transitorios se reintentan con backoff.
- [x] Los errores permanentes no se reintentan.
- [x] Se registra el número de reintentos.
- [x] Se impide la concurrencia del orquestador.
- [x] No se exponen secretos.
- [x] Cloud puede auditar código, contrato, pruebas y documentación.
- [ ] Proveedores reales/rate limits: REQUIERE VALIDACIÓN LOCAL.

## Relación con la fase final
La última fase continúa reservada exclusivamente para la **REVISIÓN INTEGRAL FINAL**, incluyendo todas las fases, correcciones y regresiones acumuladas.
