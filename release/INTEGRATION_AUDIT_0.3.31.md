# Auditoría de Integraciones — 0.3.31

## Resultado
**APROBADA PARA REVISIÓN DE CLOUD**, con validaciones reales de proveedores pendientes.

## Cobertura
| Área | Resultado | Evidencia |
|---|---|---|
| Meta / Facebook / Instagram | PASS estructural | OAuth state, secretos Python, configuración pública separada |
| Google Analytics 4 | PASS estructural | OAuth state, refresh token, configuración pública |
| X | PASS estructural | OAuth 2.0 + PKCE, estado efímero |
| TikTok | PASS estructural | OAuth, scopes configurables, secretos fuera del navegador |
| YouTube | PASS estructural | OAuth/API key, scopes de solo lectura |
| LinkedIn | PASS estructural | OAuth, versión API configurable |
| Cohere | PASS estructural | API key solo en Python, IndexedDB sin secreto |
| Desconexión | PASS estructural | elimina token del almacén en memoria y persiste estado |
| OAuth state | PASS | expiración 10 min + consumo único |
| CORS / origen | CORREGIDO | `SENTIA_ALLOWED_ORIGINS`, sin `*` |
| Configuración pública | PASS | filtros de secretos en conectores y DB |
| Reconciliación/sync | PASS regresión | suite completa 87 pruebas |

## Hallazgo corregido
El bridge utilizaba `Access-Control-Allow-Origin: *`. Se reemplazó por una política de origen explícita:
- `http://localhost` (puertos de desarrollo permitidos)
- `http://127.0.0.1` (puertos de desarrollo permitidos)
- `https://*.github.io`
- valores adicionales mediante `SENTIA_ALLOWED_ORIGINS`.

Las solicitudes con `Origin` no permitido reciben `403 ORIGIN_NOT_ALLOWED`. Las solicitudes sin `Origin` siguen disponibles para herramientas locales no basadas en navegador.

## Limitaciones
La auditoría de código no demuestra que cada proveedor acepte las credenciales reales, scopes, permisos de cuenta, límites, cuotas o versiones vigentes. Esos puntos requieren validación local con cuentas de prueba y credenciales reales.

## Evidencia automática
- `87 passed`
- `python -m compileall -q python`: PASS
- `node --check js/app.js`: PASS
- `node --check js/db.js`: PASS
- JSON Schema: PASS
- Paquete sin `python/runtime/*` ni caches de ejecución.

## Criterio de Cloud
Cloud puede revisar estáticamente el contrato, flujo OAuth, separación de secretos, política de origen, pruebas y documentación. No debe marcar como verificados los proveedores reales ni GitHub Pages sin ejecutar las validaciones locales correspondientes.
