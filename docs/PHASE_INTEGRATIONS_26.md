# Phase 0.3.19 — Programación y políticas de frescura

## Objetivo
Reemplazar el temporizador fijo de sincronización por una programación persistente y configurable en IndexedDB.

## Cambios
- IndexedDB v7 añade `sync_scheduler`.
- Activación/desactivación explícita de sincronización automática.
- Frecuencias disponibles: 15 min, 30 min, 60 min, 3 h y 6 h.
- Persistencia de `enabled`, `interval_minutes`, `last_run_at` y `next_run_at`.
- El scheduler comprueba cada minuto y también al volver a una pestaña visible.
- La sincronización automática sólo opera mientras Sentia esté abierta; no se presenta como un servicio de background persistente.
- Si no existen proveedores configurados, no intenta sincronizar.
- La programación no contiene secretos ni tokens.

## Seguridad
La configuración es preferencia operativa no sensible. Credenciales y tokens continúan en Python/token store.

## Validación Cloud
A: código, persistencia, ausencia de localStorage para el scheduler y documentación.
B: comportamiento del scheduler en navegador si el entorno lo permite.
C: pruebas de ejecución prolongada, suspensión del navegador y proveedor real requieren validación local.
