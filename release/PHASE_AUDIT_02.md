# Auditoría de Fase 02 — Integración Real y Validación de Motores

## Resultado
**PASS CON LIMITACIONES DOCUMENTADAS**

## Objetivo
Cerrar las brechas entre capacidad declarada e integración verificable en el motor de sentimiento, la capa Cohere y el contrato de salida.

## Cambios implementados
1. Validación Draft 2020-12 centralizada en `python/pipeline/validation.py`.
2. El pipeline valida su propio payload antes de devolverlo.
3. `python/main.py` vuelve a validar antes de escribir el archivo final.
4. Cohere dispone de contrato estructurado, prompt versionado y clasificación de errores.
5. Se añadió límite explícito de contexto y rechazo de respuestas no JSON.
6. Se agregaron pruebas de integración simulada para Cohere.
7. Se añadió prueba de bloqueo de payload inválido.

## Evidencia ejecutada
- `python -m pytest -q` → **7 passed**.
- `python -m python.validate` → **Schema validation: PASS**.
- `python -m python.main --input python/tests/fixtures/mentions.json --output /tmp/processed-phase.json` → **Exportado: 3 menciones**.
- Validación del resultado exportado → **Schema validation: PASS**.
- `python -m compileall -q python` → **PASS**.
- Frontend `node --check` → **PASS** si Node está disponible en el entorno.

## Qué no se puede aprobar desde este entorno
- Modelo real de `pysentimiento`: el paquete no está instalado.
- Llamada real a Cohere: el SDK no está instalado y no existe credencial disponible.
- Browser real, IndexedDB, offline mode y GitHub Pages.
- Benchmark de grandes volúmenes.

Estas condiciones quedan como **VALIDACIÓN LOCAL**, no como PASS.

## Seguridad
- La clave Cohere se lee únicamente de `COHERE_API_KEY`.
- No se guarda en IndexedDB, localStorage, JSON ni frontend.
- El prompt contiene instrucciones para no inventar datos, pero la salida generativa sigue siendo secundaria frente a las métricas deterministas.

## Criterio de aceptación
La fase se considera aprobada para continuar porque los contratos y fallos verificables están cubiertos y las integraciones externas no se han falsamente marcado como validadas.
