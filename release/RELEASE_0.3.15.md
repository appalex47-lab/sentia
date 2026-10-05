# Sentia Intelligence from Conversations — RC 0.3.15

## Cambios
- Conectores Python para X, TikTok, YouTube y LinkedIn.
- OAuth server-side/local bridge.
- X PKCE.
- Ingestión normalizada al pipeline de menciones.
- UI de configuración y sincronización.
- YouTube API key/OAuth path.
- LinkedIn version configurable.
- Corrección de `DB.put` requerida por `saveAnalyticsReport`.

## QA
46/46 tests PASS; compileall PASS; JS syntax PASS; schema PASS.

## Gate
Provider OAuth and real-data validation: REQUIERE VALIDACIÓN LOCAL.
