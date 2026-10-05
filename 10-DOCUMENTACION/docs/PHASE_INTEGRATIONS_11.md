# Fase Integraciones 11 — Meta OAuth real + descubrimiento inicial

## Objetivo
Convertir el asistente de conexión de Meta/Facebook + Instagram en un flujo OAuth real sin exponer secretos ni tokens al navegador.

## Arquitectura
1. La vista `Integraciones` recopila App ID, Redirect URI y scopes.
2. Sentia envía únicamente configuración pública al puente Python local.
3. Python obtiene `META_APP_SECRET` exclusivamente del entorno.
4. Python genera `state` aleatorio y lo conserva temporalmente en memoria.
5. Meta devuelve un authorization code al callback Python.
6. Python intercambia el code por un access token en Graph API.
7. Python consulta `/me` y `/me/accounts` para descubrir la cuenta y páginas disponibles.
8. El token permanece en memoria del proceso Python; no se devuelve al frontend.

Meta recomienda especificar una versión de Graph API; esta fase fija `v26.0` como versión configurable del conector. citeturn1search0turn1search1

## Seguridad
- Nunca solicitar `META_APP_SECRET` en la UI.
- Nunca guardar access tokens en IndexedDB/localStorage.
- `state` expira después de 10 minutos.
- El intercambio OAuth ocurre exclusivamente en Python.
- La persistencia duradera de tokens queda fuera de esta fase para evitar introducir almacenamiento de secretos sin cifrado/gestor de secretos.

## Estado de la fase
**IMPLEMENTADA — requiere validación local real con una Meta App.**

## Validación Cloud
- [x] Tests Python
- [x] Compilación Python
- [x] Sintaxis JavaScript
- [x] No almacenamiento de secretos en configuración pública
- [x] OAuth versionado
- [x] Intercambio de code del lado Python
- [x] Descubrimiento inicial de páginas

## Validación local obligatoria
- Crear/configurar una Meta App real.
- Registrar exactamente el Redirect URI.
- Configurar `META_APP_SECRET` en el entorno Python.
- Confirmar permisos/scopes y App Review cuando corresponda.
- Ejecutar el puente Python.
- Completar login OAuth con una cuenta de prueba.
- Confirmar que Sentia muestra conexión sin revelar el token.

## Próxima fase
Persistencia segura de credenciales/tokens y selector de Página/Instagram, seguida por ingestión de datos permitidos hacia el contrato canónico de Sentia.
