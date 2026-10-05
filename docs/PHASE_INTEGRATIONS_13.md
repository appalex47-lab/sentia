# Fase 0.3.5 — Persistencia segura y ciclo de vida de sincronización

## Objetivo
Establecer el patrón reutilizable para mantener una conexión OAuth después de reiniciar Python sin exponer secretos al navegador.

## Implementación
- Tokens Meta persistidos cifrados en `python/runtime/tokens.enc`.
- Cifrado AES-GCM mediante `cryptography`.
- Clave de cifrado exclusivamente en `SENTIA_TOKEN_ENCRYPTION_KEY`.
- Archivo de tokens con permisos de sistema `0600` cuando el sistema operativo lo permite.
- Restauración automática de tokens al iniciar el bridge Python.
- Estado de expiración del token expuesto únicamente como metadato, nunca el token.
- Endpoint de desconexión que elimina token persistido y estado de sesión.
- Registro de última sincronización: timestamp, cantidad de fuentes, Page e Instagram seleccionados.
- La UI ofrece `Sincronizar ahora` y `Desconectar`.
- La selección de cuentas sigue siendo configuración no sensible.

## Seguridad
Nunca se guarda en IndexedDB/localStorage:
- Client Secret
- Access Token
- Page Access Token
- Refresh Token
- Clave de cifrado

El navegador sólo recibe estado, IDs y datos procesados.

## Limitación explícita
Esta fase persiste de forma segura el token recibido por OAuth. No implementa renovación automática porque el comportamiento depende del proveedor y del tipo de token. Cuando Meta devuelva un token que requiera reautorización, Sentia debe mostrar `Reautorización necesaria` en lugar de intentar una renovación no soportada.

La sincronización actual obtiene una ventana reciente y utiliza el pipeline canónico. La deduplicación/ventana incremental específica por proveedor se mantiene separada para una fase posterior y no se inventan parámetros de Graph API no garantizados.

## Validación Cloud
- Cifrado de token y ausencia del secreto en texto plano: verificable con tests.
- Separación navegador/Python: verificable estáticamente.
- Ciclo conectar/desconectar: verificable por contrato.
- OAuth real y expiración efectiva: `REQUIERE VALIDACIÓN LOCAL`.
- Permisos reales de Meta: `REQUIERE VALIDACIÓN LOCAL`.

## Criterios de aceptación
- [x] Token persistido cifrado en Python.
- [x] Clave de cifrado fuera del repositorio y del navegador.
- [x] Restauración tras reinicio del bridge.
- [x] Desconexión elimina el almacenamiento del token.
- [x] Estado de expiración visible sin exponer token.
- [x] Historial de última sincronización guardado como metadato.
- [x] Sincronización continúa entrando por el pipeline canónico.
- [ ] Renovación automática específica de Meta.
- [ ] Validación contra una Meta App real.
