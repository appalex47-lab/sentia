# Fase 0.3.4 — Selección de cuentas e ingestión Meta

## Objetivo
Convertir la conexión Meta OAuth en una fuente real del pipeline Sentia sin exponer tokens al navegador.

## Alcance
- Listar Facebook Pages disponibles después de OAuth.
- Detectar `instagram_business_account` asociado cuando Meta lo devuelve.
- Permitir seleccionar Page e Instagram desde la vista Integraciones.
- Persistir únicamente IDs/selección pública en el navegador y en el runtime de configuración.
- Mantener Page Access Token/User Access Token exclusivamente en Python.
- Leer publicaciones de Facebook Page y media de Instagram profesional cuando los permisos concedidos lo permitan.
- Transformar resultados a filas canónicas y ejecutar el pipeline existente de limpieza, sentimiento, reglas y scoring.
- Importar el payload procesado en IndexedDB mediante el mismo contrato de Sentia.

## Seguridad
El endpoint `/api/integrations/meta/pages` elimina tokens antes de responder. `/api/integrations/meta/ingest` devuelve únicamente datos procesados; nunca devuelve tokens.

## Evidencia externa
La documentación consultada indica que Instagram API con Facebook Login trabaja con cuentas profesionales y que el modelo de permisos depende de los datos solicitados. Meta también documenta que determinados datos de Page requieren permisos/features adicionales. Ver referencias oficiales enlazadas desde `INTEGRATIONS_GUIDE.md`.

## Validación Cloud
- Código Python/JS estático: verificable.
- Contrato de no exposición de tokens: verificable mediante tests y revisión estática.
- Pipeline canónico: verificable.
- OAuth real, permisos de una Meta App real y disponibilidad efectiva de Page/Instagram: `REQUIERE VALIDACIÓN LOCAL`.

## Criterios de aceptación
- [x] Selector de páginas tras conexión.
- [x] Detección de Instagram profesional vinculado cuando la API lo devuelve.
- [x] Selección persistida sin secretos.
- [x] Endpoint de ingestión protegido por token Python.
- [x] Ingestión pasa por `Pipeline` y validación de schema.
- [x] Resultado compatible con importación de Sentia.
- [ ] Validación contra Meta App real y permisos aprobados.
- [ ] Persistencia cifrada de tokens para uso prolongado; se deja para la siguiente fase.
