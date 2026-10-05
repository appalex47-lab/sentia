# QA / Regresión 0.3.35

## Resultado
- Suite automatizada: **96/96 PASS**
- Python compileall: **PASS**
- JavaScript syntax checks (`app.js`, `db.js`, `browser-smoke.js`): **PASS**
- JSON Schema parse: **PASS**
- ZIP integrity: **PASS**
- Exclusión de runtime/bytecode/cache del release: **PASS**
- Secret scan: **PASS**

## Nota sobre secret scan
El escaneo detectó únicamente nombres de variables de credenciales en `.env.example` (valores vacíos por diseño) y referencias documentales en `docs/INTEGRATIONS_GUIDE.md`. No se encontraron valores de secretos, tokens ni API keys embebidos.

## Alcance de regresión
Se verificaron las áreas introducidas o modificadas en 0.3.30–0.3.34 junto con contratos anteriores: sincronización, integraciones, aprendizaje/memoria, IndexedDB, seguridad, privacidad, UX/accesibilidad, pipeline, exportación y esquema.

## Resultado
No se detectaron regresiones automatizadas.

## Validación externa pendiente
Navegadores reales, OAuth/API con credenciales reales, GitHub Pages, dispositivos móviles, lectores de pantalla y pruebas de carga sobre infraestructura real requieren validación local/externa.
