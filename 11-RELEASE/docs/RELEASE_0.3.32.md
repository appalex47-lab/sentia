# Sentia Intelligence from Conversations — Release 0.3.32

## Fase
Auditoría de datos, aprendizaje y memoria conversacional.

## Cambios
- Memoria conversacional con procedencia explícita de evidencia.
- Conteo de menciones y conversaciones que sustentan cada conocimiento.
- IDs de evidencia acotados a 100 por conocimiento para evitar crecimiento sin control.
- Versión explícita del motor: `deterministic-learning-v2`.
- Marca temporal `learned_at` cuando un conocimiento alcanza estado `validated` o `learned`.
- Rechazo de aliases que introduzcan términos del dominio de catálogo/producto ajeno a Sentia.
- La búsqueda determinista descarta registros de memoria inválidos antes de calcular similitud.
- IndexedDB conserva la procedencia de memoria con límites seguros.
- Esquema JSON ampliado de forma compatible: los nuevos campos son opcionales para preservar datasets anteriores.

## Seguridad de dominio
Sentia aprende únicamente conocimiento conversacional: temas, entidades, intenciones, problemas, organizaciones y patrones. No se habilita aprendizaje de sustancias, laboratorios, productos, marcas, presentaciones, SKU o principios activos.

## Validación
- Pytest: 90/90 PASS
- compileall: PASS
- `node --check js/app.js`: PASS
- `node --check js/db.js`: PASS
- JSON Schema sobre `data/datos_procesados.json`: 0 errores

## Limitaciones / validación local
- La persistencia real de IndexedDB debe comprobarse en navegador.
- La calidad semántica sobre datasets reales requiere validación funcional con conversaciones reales anonimizadas.
- Esta fase no convierte Cohere/LLM en fuente de verdad para memoria.
