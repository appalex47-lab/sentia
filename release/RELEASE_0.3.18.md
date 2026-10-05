# Sentia Intelligence from Conversations — RC 0.3.18

## Resumen
Release de resiliencia de la sincronización multi-fuente. No incorpora nuevos proveedores. Fortalece el orquestador 0.3.16 y la observabilidad 0.3.17.

## Cambios
- Retry/backoff para errores transitorios.
- Exclusión de sincronizaciones concurrentes.
- `retry_count` en contratos de ejecución y UI.
- Historial de ejecuciones ampliado.

## QA
- 57/57 tests PASS.
- Python compileall PASS.
- JavaScript syntax PASS.
- JSON Schema PASS.

## Pendientes locales
- OAuth y APIs reales.
- Rate limits reales.
- Navegador/IndexedDB.
- Sesiones prolongadas y red intermitente.

## Estado
RC 0.3.18 condicionada a validación local. La fase final seguirá siendo la auditoría integral de todo el proyecto y las correcciones derivadas de ella.
