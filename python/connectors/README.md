# Sentia Connectors

Cada conector externo debe implementar el mismo contrato conceptual:

1. `validate_config()` — comprueba configuración no sensible y variables secretas del entorno.
2. `authenticate()` — ejecuta OAuth/API authentication según proveedor.
3. `health_check()` — comprueba acceso sin ingerir grandes volúmenes.
4. `fetch()` — recupera datos paginados y respeta rate limits.
5. `normalize()` — convierte la respuesta al contrato canónico de Sentia.
6. `checkpoint()` — registra cursor/fecha/último elemento para sincronización incremental.
7. `diagnostics()` — devuelve estado, errores, cuotas y timestamps sin exponer secretos.

Los conectores no deben escribir directamente al dashboard. Deben producir datos canónicos para el pipeline existente.
