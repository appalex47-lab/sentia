# Sentia Intelligence from Conversations — Release 0.3.27

## Objetivo
Reconciliación de contenido real entre la ejecución de sincronización, el manifiesto local y las menciones persistidas en IndexedDB.

## Cambios
- Los resultados de sincronización registran `content_keys` deterministas por proveedor.
- Los manifiestos IndexedDB registran las claves de contenido recibidas.
- La revisión de consistencia compara esas claves contra las menciones actualmente persistidas.
- Nuevos diagnósticos: `LOCAL_CONTENT_MANIFEST_MISMATCH` y `LOCAL_CONTENT_MISSING`.
- IndexedDB sube a versión 10; la migración es aditiva y conserva stores existentes.
- La reparación existente puede utilizar la reconciliación como condición previa; no se inventan registros ni cursores.

## Seguridad
No se agregan tokens, API keys, client secrets ni payloads de credenciales a los manifiestos o al historial.

## QA
- Suite Python: 77 pruebas esperadas.
- JavaScript: sintaxis validada con Node.
- Python: compileall validado.
- Validación real de IndexedDB y proveedores: requiere validación local.

## Cloud
A: código, arquitectura y documentación verificables.
B: pruebas automatizadas ejecutadas.
C: navegador real, IndexedDB real, interrupciones reales y APIs reales requieren validación local.
