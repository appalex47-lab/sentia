# Fase 0.3.11 — Aprendizaje de temas y entidades de conversación

## Corrección de alcance
Esta fase pertenece exclusivamente a **Sentia Intelligence from Conversations**. No incorpora catálogo de productos, sustancias activas, laboratorios, marcas farmacéuticas, presentaciones ni SKU.

## Dominio aprendido
Sentia puede proponer conocimiento conversacional: `topic`, `entity`, `intent`, `problem`, `organization` y `pattern`.

## Regla de aprendizaje
La evidencia se extrae únicamente de conversaciones procesadas. La propuesta se guarda como `proposed`; una fase posterior podrá promoverla a `validated` o `learned`. No se inventa historial.

## Persistencia
IndexedDB incorpora `knowledge_entities`. Los datos no sensibles de conocimiento permanecen localmente.

## IA
Cohere puede enriquecer posteriormente la extracción mediante JSON estructurado, pero no es fuente de verdad. La extracción determinística y la validación de Sentia preceden cualquier promoción a conocimiento aprendido.

## Exclusiones explícitas
No implementar ni almacenar conceptos propios del proyecto de fichas de producto.
