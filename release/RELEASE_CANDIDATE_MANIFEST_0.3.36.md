# Manifiesto del Release Candidate 0.3.36

## Base
0.3.35 — QA y regresión integral.

## Alcance congelado
Sin cambios funcionales nuevos respecto a 0.3.35. Este RC agrega trazabilidad de release y criterios de certificación.

## Evidencia
- 96 pruebas automatizadas PASS.
- compileall PASS.
- sintaxis JS PASS.
- JSON manifest/schema PASS.
- sin runtime operativo en el paquete.
- sin bytecode Python ni caches.
- sin archivos de secretos reales.

## Clasificación de validación
### Nivel A — verificable por revisión estática/automatizada
Arquitectura, contratos, código, documentación, ausencia de secretos, sintaxis, tests automatizados y empaquetado.

### Nivel B — verificable si el entorno dispone de navegador/servicios equivalentes
Smoke funcional de interfaz y operaciones locales.

### Nivel C — REQUIERE VALIDACIÓN LOCAL
Credenciales reales, OAuth real, APIs de proveedores, GitHub Pages, dispositivos/navegadores físicos, lectores de pantalla y datasets reales.

## Regla
Cloud no debe convertir un elemento Nivel C en PASS sin evidencia de ejecución real.
