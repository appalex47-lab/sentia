# Release 0.3.34 — Auditoría final de seguridad y privacidad

## Correcciones
- Escape HTML contextual en callbacks OAuth.
- Headers defensivos: CSP, X-Content-Type-Options y Referrer-Policy.
- CORS/orígenes explícitos conservados.
- Secretos y tokens fuera de IndexedDB/localStorage.

## Validación
- pytest: 96/96 PASS
- compileall: PASS
- Node syntax: PASS
- JSON Schema: PASS
- secret scan: PASS
- ZIP integrity: PASS

## Validación local pendiente
OAuth real, proveedores reales, navegador y despliegue publicado.
