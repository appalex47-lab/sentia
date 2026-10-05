# Requisito de empaquetado de fase final

La fase final de certificación deberá producir, además del ZIP operativo normal, un paquete maestro organizado por tipo:

- `01_codigo/js/`
- `01_codigo/python/`
- `02_estilos/css/`
- `03_html/`
- `04_datos/`
- `05_schemas/`
- `06_documentacion/`
- `07_pruebas/`
- `08_configuracion/`
- `09_release/`

Reglas:
1. No copiar secretos, tokens, `python/runtime`, `.env` reales, caches ni artefactos temporales.
2. Conservar rutas relativas documentadas y un mapa de correspondencia con el proyecto ejecutable.
3. Incluir `MANIFEST_FINAL.md` con cada archivo, categoría, propósito y origen.
4. Incluir checksum SHA-256 del paquete maestro y del paquete ejecutable.
5. La reorganización por tipo es un artefacto de entrega; no debe romper las rutas del paquete ejecutable.
6. La estructura final debe ser revisada por Cloud y acompañada de criterios de aceptación.
