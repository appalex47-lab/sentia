# Release 0.3.41 — Demo robusto y visibilidad de Cohere

## Correcciones
- Conectados los botones Importar/Borrar datos de ejemplo a sus handlers.
- Dataset demo ampliado a 96 menciones, 24 conversaciones, 12 conocimientos y 4 insights.
- Incluye WhatsApp y llamadas en español con casos de logística, pagos, devoluciones, cuenta, fraude, cancelación, producto, soporte, escalación, errores técnicos y resoluciones.
- Integraciones → Cohere ahora explica cuándo se invoca Cohere y cuándo no.

## Cohere
- Validación de credencial: llamada mínima Chat V2.
- Audio: Cohere Transcribe.
- Traducción: solo con auto_translate=true.
- Sentimiento/score/reglas/memoria: determinísticos, sin Cohere.
- Insights generativos: adaptador disponible, no ejecución automática en cada importación.

## Validación
- El dataset cumple el contrato de menciones requerido por el frontend.
- Los IDs son únicos.
- Cada conversación referencia únicamente menciones existentes.
