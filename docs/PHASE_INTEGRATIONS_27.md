# FASE 0.3.20 — Salud y frescura de sincronización

## Objetivo
Hacer visible y auditable la frescura operativa de cada fuente sin convertir una ausencia de datos en una falsa señal de éxito.

## Alcance implementado
- Nuevo contrato determinista `freshness_status` en `python/pipeline/sync.py`.
- Estados de frescura: `fresh`, `warning`, `stale`, `error`, `never` y `unknown` para datos inválidos.
- Política basada en la frecuencia configurada: hasta 1 intervalo = `fresh`; >1 y <=2 = `warning`; >2 = `stale`.
- Un último estado de error prevalece sobre la edad para evitar presentar una fuente fallida como fresca.
- Nuevo endpoint `GET /api/sync/health?interval=N&providers=...`.
- UI de Integraciones muestra salud global, salud por proveedor y antigüedad aproximada.
- La frecuencia usada por la UI coincide con la frecuencia persistida del scheduler.
- No se exponen secretos, tokens ni contenido sensible en el contrato de salud.

## Decisiones
1. La frescura es una señal operativa, no una métrica de calidad del contenido.
2. `never` no se interpreta como error: significa que todavía no existe una sincronización exitosa registrada.
3. `error` conserva prioridad sobre la antigüedad del último éxito para alertar que el último intento conocido falló.
4. El navegador sigue siendo responsable de la programación local; el bridge sólo calcula salud a partir de estado operativo.

## QA
- Pruebas completas de sincronización ampliadas con frescura y salud agregada.
- Python compileall.
- JavaScript syntax.
- Endpoint de salud validable en servidor local.
- Contratos y documentación actualizados.

## Validación local requerida
- Confirmar visualmente estados en navegador.
- Verificar transición real fresh/warning/stale con el paso del tiempo.
- Ejecutar con proveedores reales y observar errores/rate limits.
- Verificar comportamiento tras reinicio del bridge y de la pestaña.

## Criterio de cierre
La fase es auditable por Cloud a nivel de código, contrato y pruebas. Las validaciones reales de navegador/proveedores quedan marcadas como `REQUIERE VALIDACIÓN LOCAL`.

## Relación con la fase final
La fase final sigue reservada exclusivamente para la **REVISIÓN INTEGRAL FINAL**, que revisará todas las fases y correcciones acumuladas, detectará regresiones y corregirá los hallazgos antes del release definitivo.
