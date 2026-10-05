# FASE 0.3.21 — Alertas accionables y recuperación de sincronización

## Objetivo
Convertir los estados de salud/frescura de 0.3.20 en alertas deterministas y accionables, sin introducir almacenamiento de credenciales ni ejecución en segundo plano fuera del ciclo ya aprobado.

## Alcance
- `GET /api/sync/alerts`.
- Alertas para `error`, `stale`, `warning` y `never`.
- Acción sugerida `retry` para errores y `sync` para estados de frescura.
- Panel de alertas en Integraciones.
- Botón de recuperación que reutiliza la orquestación existente y su protección de concurrencia.
- Sin nuevos proveedores.

## Seguridad
Las alertas sólo exponen proveedor, estado, severidad, mensaje y acción. No incluyen tokens, refresh tokens, API keys, client secrets ni valores de OAuth.

## Contratos
Cada alerta contiene: `id`, `provider`, `severity`, `status`, `message`, `action`.

## Pruebas
- Suite: 65/65 PASS.
- Python compileall: PASS.
- JavaScript syntax (`app.js`, `db.js`): PASS.
- Smoke determinista de alertas: PASS.

## Validación local requerida
- Visualización real en navegador.
- Click de recuperación con cuentas OAuth reales.
- Comportamiento ante rate limits y errores reales.
- Accesibilidad visual/interacción con lectores de pantalla.

## Criterio Cloud
Cloud puede revisar código, contratos, ausencia de secretos en las alertas, pruebas y trazabilidad. No debe marcar como verificados los flujos que requieren proveedores o navegador real.
