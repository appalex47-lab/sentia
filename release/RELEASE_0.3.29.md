# Sentia Intelligence from Conversations — Release 0.3.29

## Retención, limpieza y mantenimiento automático

Esta fase depura exclusivamente historial operativo de sincronización. Nunca elimina `mentions`, `conversations`, `knowledge_entities`, `insights`, configuraciones públicas de integraciones ni secretos.

### Política predeterminada
- sync_runs: 90 días / máximo 500
- sync_manifests: 90 días / máximo 500
- sync_repairs: 180 días / máximo 250

Los límites se acotan para impedir valores peligrosos. El mantenimiento local puede ejecutarse al abrir Integraciones una vez por sesión y también manualmente. El mantenimiento del bridge Python afecta únicamente `sync_runs`.

### Auditoría
Cada operación devuelve conteos antes/después, eliminados por antigüedad y eliminados por límite. Los datos de negocio quedan fuera del alcance del mantenimiento.

### Validación local requerida
- comprobar migración IndexedDB v12 en un navegador real;
- verificar que menciones/conversaciones/conocimiento permanecen intactos;
- ejecutar mantenimiento con historial real;
- comprobar que el bridge no elimina tokens, configuración ni datos de negocio.
