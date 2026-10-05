# FASE 0.3.17 — Observabilidad y trazabilidad de sincronización

## Objetivo
Convertir la sincronización multi-fuente de 0.3.16 en un proceso auditable: cada ejecución debe poder identificarse, medirse y distinguir éxito total, éxito parcial y error.

## Alcance
- Historial persistente de ejecuciones de sincronización en Python.
- Endpoint `GET /api/sync/runs?limit=N`.
- `GET /api/sync/status` incorpora la última ejecución.
- Registro por ejecución: ID, inicio, fin, duración, proveedores solicitados, resultado por proveedor, fallos, registros y duplicados.
- Retención de las últimas 50 ejecuciones en el bridge.
- IndexedDB `sync_runs` conserva las ejecuciones recibidas por el navegador.
- UI de Integraciones muestra estado por proveedor e historial de las últimas 10 ejecuciones.

## Seguridad
- No se almacenan API keys, client secrets, access tokens ni refresh tokens en `sync_runs`.
- El historial contiene únicamente metadatos operativos.
- La persistencia del bridge usa el mismo directorio runtime protegido de la fase anterior.

## Contratos
`run_id`, `started_at`, `finished_at`, `duration_ms`, `status`, `requested_providers`, `providers`, `failure_count`, `source_count`, `duplicate_count`.

## QA
- 55/55 pruebas PASS.
- Python compileall PASS.
- JavaScript syntax PASS.
- La construcción del registro de ejecución tiene pruebas unitarias para success/partial/error.

## Validación local requerida
- Confirmar visualmente el historial en navegador.
- Ejecutar una sincronización real con proveedores conectados.
- Verificar persistencia tras reiniciar el bridge.
- Verificar comportamiento durante errores/rate limits reales.

## Criterio de cierre
La fase queda como RC 0.3.17 condicionada a las validaciones locales anteriores.

## Relación con la fase final
La fase final seguirá siendo exclusivamente la **REVISIÓN INTEGRAL FINAL**, que auditará todas las fases y correcciones acumuladas y corregirá los hallazgos antes del release definitivo.
