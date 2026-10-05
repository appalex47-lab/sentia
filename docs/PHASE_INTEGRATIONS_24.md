# FASE 0.3.16 — Sincronización automática y orquestación multi-fuente

## Objetivo
Coordinar la sincronización de fuentes sociales conectadas sin depender de importaciones manuales repetitivas, manteniendo un flujo local-first, seguro e idempotente.

## Alcance implementado
- Orquestador local `POST /api/sync/all`.
- Estado persistente de sincronización en `python/runtime/sync_state.json`.
- Estado local en IndexedDB (`sync_state`, `sync_runs`) mediante DB v6.
- Sincronización individual desde las tarjetas de X, TikTok, YouTube y LinkedIn.
- Botón **Sincronizar todo**.
- Sincronización automática opt-in cada 30 minutos mientras la aplicación permanezca abierta.
- Conteo de registros obtenidos y duplicados evitados.
- Estados `success` / `error`, último intento y último éxito.
- Fallo parcial tolerado: una fuente con error no invalida las demás.
- IDs deterministas para objetos externos; se elimina la generación aleatoria de IDs de LinkedIn.
- Deduplicación previa al pipeline mediante `id_mencion` estable.
- Cursors básicos conservados cuando el proveedor los devuelve (TikTok/YouTube).
- Secretos y tokens permanecen en Python; el navegador sólo envía configuración pública y solicitudes de sincronización.

## Decisiones
1. La sincronización automática no se activa por defecto.
2. En esta fase no se publica ni modifica contenido en proveedores externos.
3. Meta mantiene su flujo de selección/ingesta existente; el orquestador social de esta fase coordina X/TikTok/YouTube/LinkedIn.
4. GA4 mantiene su flujo de reportes independiente porque sus datos no son menciones conversacionales.
5. La deduplicación usa IDs externos estables cuando existen y hash determinista como respaldo.

## Contratos
### `POST /api/sync/all`
Entrada opcional:
- `providers`: lista de `x`, `tiktok`, `youtube`, `linkedin`.
- `x_query`.
- `youtube_channel_id`.
- `linkedin_organization_id`.

Salida:
- `payload.mentions`: menciones normalizadas listas para importar.
- `providers[]`: resultado individual por proveedor.
- `failures[]`: errores parciales.
- `synced_at`.

### `GET /api/sync/status`
Devuelve el registro de estado por proveedor sin exponer secretos.

## Persistencia
- Browser: `sync_state`, `sync_runs`.
- Python: `runtime/sync_state.json`.
- Tokens: continúan exclusivamente en el almacén cifrado existente.

## Pruebas
- 51/51 tests PASS.
- JSON Schema PASS.
- Python compileall PASS.
- JavaScript syntax PASS.
- Endpoint `/api/sync/status`: PASS en servidor efímero.
- Endpoint `/api/sync/all` con lista vacía: PASS en servidor efímero.

## Validación local pendiente
- OAuth real de cada proveedor.
- Cuotas/rate limits y respuestas reales.
- Cursor/incrementalidad real por proveedor con cuentas conectadas.
- IndexedDB real en navegador objetivo.
- Funcionamiento de sincronización automática durante sesiones largas.
- Prueba con volúmenes grandes y redes intermitentes.

## Riesgos conocidos
- La automatización del navegador deja de ejecutarse si la pestaña/app está cerrada.
- La coordinación Meta sigue separada para respetar su flujo de selección de página/cuenta.
- No se deben interpretar los IDs internos como evidencia de que un proveedor entregó un objeto nuevo; la fuente de verdad sigue siendo el ID externo.

## Criterios de aceptación
- [x] Existe un orquestador multi-fuente.
- [x] Los duplicados no generan nuevas menciones cuando el ID externo es estable.
- [x] Un fallo de una fuente no borra los datos de otras.
- [x] El estado de sincronización queda registrado.
- [x] La automatización es opt-in.
- [x] No se exponen secretos al navegador.
- [x] Cloud puede auditar endpoints, código, contrato, tests y persistencia.
- [ ] OAuth/proveedores reales: REQUIERE VALIDACIÓN LOCAL.
- [ ] Navegador/IndexedDB/automatización prolongada: REQUIERE VALIDACIÓN LOCAL.
