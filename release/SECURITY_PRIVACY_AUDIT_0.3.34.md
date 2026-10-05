# Auditoría de seguridad y privacidad 0.3.34

Se revisaron secretos/tokens, almacenamiento, CORS, CSP, OAuth state/callbacks, diagnósticos, errores y retención.

### Hallazgo corregido
Los mensajes de error recibidos durante callbacks OAuth podían llegar a HTML sin escape. Ahora se aplica `html.escape` antes de renderizar título y mensaje.

### Controles
- Tokens cifrados con AES-GCM en Python.
- No se almacenan API keys/client secrets en IndexedDB/localStorage.
- Orígenes CORS explícitos.
- `Cache-Control: no-store`.
- CSP restrictiva en callbacks HTML.
- `X-Content-Type-Options: nosniff`.
- `Referrer-Policy: no-referrer`.

Resultado automático: 96/96 pruebas PASS.
