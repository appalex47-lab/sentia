# FASE 0.3.39 — GitHub Pages + Backend HTTPS + Cohere UX

## Objetivo
Eliminar la dependencia del navegador respecto a `127.0.0.1:8787` para el despliegue habitual desde GitHub Pages y consolidar Cohere en un único punto de configuración.

## Cambios
- Frontend usa una URL de backend HTTPS configurable y almacenada como dato no sensible en IndexedDB.
- Se eliminó la tarjeta duplicada de Cohere de Configuración.
- Cohere vive en Centro de Integraciones.
- Selector de modelos con descripción contextual.
- Catálogo dinámico mediante `/api/cohere/models`, con fallback seguro.
- API key se transmite al backend y se limpia del campo; solo el backend la persiste.
- Modelo predeterminado actualizado a `command-a-plus-05-2026`.
- Backend expone `/api/health`.
- Backend preparado para despliegue HTTPS mediante `render.yaml`.
- CORS continúa restringido por `SENTIA_ALLOWED_ORIGINS`.

## Validación
- JavaScript syntax: PASS.
- Python compile: PASS.
- Tests: PASS.
- Backend `/api/health`: PASS.
- Backend `/api/cohere/models`: PASS.
- Cohere autenticado: REQUIERE VALIDACIÓN DE DESPLIEGUE Y CREDENCIAL REAL.
- OAuth de proveedores: REQUIERE VALIDACIÓN DE DESPLIEGUE Y CREDENCIALES REALES.
