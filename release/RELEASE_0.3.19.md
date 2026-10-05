# Sentia Intelligence from Conversations — RC 0.3.19

## Resumen
Programación persistente y configurable de la sincronización automática multi-fuente.

## Cambios
- IndexedDB v7 con `sync_scheduler`.
- Frecuencia configurable 15 min / 30 min / 60 min / 3 h / 6 h.
- Scheduler basado en `next_run_at`, con comprobación por minuto y al recuperar visibilidad.
- Se elimina la dependencia de `localStorage` para esta preferencia.
- Se mantiene la protección de concurrencia y el retry/backoff de 0.3.18.

## QA
Se debe ejecutar la suite completa, compilación Python, sintaxis JS, schema y pruebas específicas de scheduler.

## Pendientes locales
- Prueba real en navegador con IndexedDB.
- Suspensión/reanudación de pestaña.
- Sesión prolongada con APIs reales.

## Estado
RC 0.3.19 condicionada a validación local. La última fase seguirá siendo la auditoría integral y corrección final.
