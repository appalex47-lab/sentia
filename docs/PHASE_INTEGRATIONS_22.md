# PHASE INTEGRATIONS 22 — RC 0.3.15

## Objetivo
Integrar X, TikTok, YouTube y LinkedIn mediante conectores Python, OAuth gestionado fuera del navegador y normalización al contrato de menciones de Sentia.

## Fuentes y alcance
- **X:** OAuth 2.0 con PKCE y lectura de búsqueda reciente. El acceso y coste dependen del plan de X API; la plataforma publica actualmente un modelo pay-per-use para recursos de lectura. La consulta puede devolver posts recientes con texto, fecha, autor y métricas disponibles.
- **TikTok:** Login/Display API para perfil y videos recientes. La ruta implementada no inventa comentarios: Display API expone perfil y videos, no un feed general de comentarios.
- **YouTube:** YouTube Data API para identificar el canal, sus videos recientes y comentarios públicos disponibles. Puede operar con API key para datos públicos o OAuth para datos autorizados.
- **LinkedIn:** OAuth 2.0 y Marketing/Community Management APIs para posts y comentarios de organizaciones, sujeto a permisos aprobados.

## Seguridad
- Client secrets, access tokens y refresh tokens permanecen en Python.
- IndexedDB solo guarda configuración pública y estado no sensible.
- Tokens se conservan en el almacén cifrado existente.
- OAuth utiliza `state` efímero; X utiliza PKCE.
- No se imprimen secretos en respuestas HTTP.

## Arquitectura
`UI -> localhost Python bridge -> proveedor -> normalización -> Pipeline -> IndexedDB`

Los conectores están en `python/connectors/social.py` y comparten manejo de errores de proveedor.

## Contratos
Endpoints comunes:
- `GET /api/integrations/{provider}/status`
- `GET /api/integrations/{provider}/authorize`
- `GET /api/integrations/{provider}/callback`
- `POST /api/integrations/{provider}/config`
- `POST /api/integrations/{provider}/ingest`
- `GET /api/integrations/{provider}/disconnect`

Proveedores: `x`, `tiktok`, `youtube`, `linkedin`.

La salida de ingestión es `payload` compatible con el pipeline y con `mentions` del contrato existente.

## Normalización
- X -> posts recientes.
- TikTok -> título/descrición de videos.
- YouTube -> comentarios de videos del canal seleccionado.
- LinkedIn -> posts y comentarios de la organización cuando el permiso lo permite.

Los registros se procesan mediante el pipeline existente, preservando sentimiento, score, calidad y demás campos calculados.

## Versionado externo
LinkedIn usa por defecto `LinkedIn-Version: 202609`, configurable mediante `LINKEDIN_VERSION`. La documentación de LinkedIn indica que Marketing APIs utilizan versiones mensuales y que 202609 está activa; el valor queda configurable para futuras migraciones.

## Tests
- OAuth/PKCE URL construction.
- Configuración pública sin secretos.
- Scopes.
- Normalización X/TikTok/YouTube/LinkedIn.
- Integración con pipeline existente.

Resultado actual: **46/46 tests PASS**.

## Validación Cloud
### Nivel A
- código Python/JS
- contratos
- seguridad estática
- separación de secretos
- documentación
- tests

### Nivel B
- tests automatizados y compilación

### Nivel C — REQUIERE VALIDACIÓN LOCAL
- OAuth real de cada proveedor
- credenciales reales
- permisos aprobados
- cuotas/costes
- lectura real de posts/comentarios
- navegador + IndexedDB
- GitHub Pages + bridge local

## Limitaciones
- X puede requerir un plan con acceso al endpoint de búsqueda y genera costes según uso.
- TikTok no se presenta como fuente de comentarios en esta release.
- LinkedIn requiere permisos/programas aprobados para lectura de determinadas publicaciones, comentarios y analítica.
- YouTube puede requerir API key u OAuth según el recurso solicitado y sus restricciones.
- No se implementa publicación/escritura hacia redes en esta fase.
- No se afirma que una fuente tenga datos cuando el proveedor no los concede.

## Decisiones
1. Lectura antes que escritura.
2. Python como único lugar para secretos y tokens.
3. Contrato de menciones unificado.
4. Conectores independientes para evitar acoplamiento entre proveedores.
5. Capacidades específicas del proveedor se reflejan explícitamente en UI y documentación.

## Evidencia
- Pytest: 46/46 PASS.
- Python compileall: PASS.
- JavaScript syntax: PASS.
- JSON Schema: PASS.
- HTTP bridge real en este entorno: **REQUIERE VALIDACIÓN LOCAL**.
