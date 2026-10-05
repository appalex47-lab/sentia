# Release 0.3.31 — Auditoría de integraciones

## Alcance
- Auditoría de Meta, GA4, X, TikTok, YouTube, LinkedIn y Cohere.
- Revisión de configuración pública, secretos, tokens, OAuth state, callbacks, desconexión y sincronización.
- Endurecimiento del bridge Python contra solicitudes cross-origin no autorizadas.
- Lista de orígenes configurable mediante `SENTIA_ALLOWED_ORIGINS`.
- CORS ya no utiliza `*`: solo devuelve el origen solicitado cuando está permitido.
- Los secretos y tokens continúan exclusivamente en Python y los tokens persistidos usan el almacén cifrado existente.

## Política de origen
Valor predeterminado:
- `http://localhost`
- `http://127.0.0.1`
- `https://*.github.io`

Se puede sobrescribir con una lista separada por comas en `SENTIA_ALLOWED_ORIGINS`.
Las solicitudes sin cabecera `Origin` siguen permitidas para herramientas locales/CLI. Una solicitud con un origen no permitido recibe `403 ORIGIN_NOT_ALLOWED`.

## Hallazgo corregido
Antes del cambio, las respuestas JSON del bridge declaraban `Access-Control-Allow-Origin: *`. Esto no exponía directamente tokens, pero permitía que cualquier sitio web pudiera invocar los endpoints del bridge si el proceso local estaba activo. La política de origen reduce esa superficie manteniendo el funcionamiento de la aplicación desplegada.

## Seguridad de secretos
- IndexedDB elimina `apiKey`, `clientSecret`, `accessToken`, `refreshToken` y `privateKey` antes de persistir integraciones.
- Los archivos públicos de configuración excluyen secretos.
- Los tokens OAuth y la API key de Cohere permanecen en el almacén Python cifrado.
- Las respuestas de estado no devuelven secretos.
- OAuth state expira y se consume una sola vez.

## Validación
- Pruebas de regresión de conectores.
- Pruebas nuevas de política de origen.
- `compileall`.
- `node --check` de los módulos principales.
- Validación de esquema.
- Integridad del paquete.
- Pruebas reales contra proveedores: `REQUIERE VALIDACIÓN LOCAL`.
- OAuth real, credenciales reales y GitHub Pages real: `REQUIERE VALIDACIÓN LOCAL`.
