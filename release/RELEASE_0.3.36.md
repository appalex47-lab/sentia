# Release 0.3.36 — Release Candidate final

## Estado
RELEASE CANDIDATE CONGELADO — listo para certificación 0.3.37.

## Objetivo
Congelar la base validada de 0.3.35 sin introducir funcionalidad nueva, dejando trazabilidad y evidencia para la certificación final.

## Validación automatizada
- pytest: 96/96 PASS
- Python compileall: PASS
- JavaScript syntax check: PASS
- JSON manifest/schema parse: PASS
- ausencia de python/runtime: PASS
- ausencia de __pycache__, .pyc y .pyo: PASS
- ausencia de archivos .env reales: PASS

## Regla de congelamiento
No se aceptan cambios funcionales nuevos en el RC salvo corrección de bloqueo crítico descubierta durante la certificación 0.3.37. Todo cambio posterior al congelamiento requiere nueva ejecución de QA y nuevo checksum.

## Validación externa pendiente
- OAuth y APIs reales de cada proveedor.
- Cohere con credencial real.
- GitHub Pages desplegado.
- Navegadores/dispositivos reales y lector de pantalla.
- pruebas con datasets reales y cargas operativas representativas.

## Criterio de certificación
La fase 0.3.37 debe comprobar este artefacto, su checksum y la matriz de evidencias. Ninguna validación no reproducible en el entorno de Cloud debe marcarse como aprobada.
