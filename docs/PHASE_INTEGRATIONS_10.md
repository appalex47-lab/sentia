# Fase 0.3.10 — Inteligencia de conversación completa

## Objetivo
Pasar del análisis de turnos individuales al análisis explicable de una conversación completa, manteniendo español como idioma operativo para WhatsApp y llamadas.

## Capacidades
- Agregación por `conversation_id`.
- Trayectoria de sentimiento por turno.
- Tendencia global: `mejora`, `empeora`, `estable`.
- Score global de conversación (promedio de scores matemáticos).
- Severidad global.
- `friction_score` y `resolution_score` determinísticos.
- Conteo de señales de fricción/resolución.
- Identificación de turnos negativos por índice.
- Conservación de turnos no atribuidos.
- Idioma de análisis explícito (`es` para estas fuentes).

## Principios
1. No se inventan hablantes ni roles.
2. Los scores de conversación derivan de señales determinísticas de los turnos.
3. Cohere puede explicar o enriquecer posteriormente, pero no sustituye las métricas base.
4. El texto original permanece disponible para auditoría.

## Persistencia
IndexedDB v4 incorpora `conversations`. El contrato de menciones añade `conversation_id`, `turn_index` y `speaker_role`.

## QA
- 18 tests Python: PASS.
- `compileall`: PASS.
- `node --check js/app.js`: PASS.
- Schema validation: integrada en el pipeline.

## Validación local pendiente
- Validación visual del dashboard en navegador real.
- Conversaciones reales de WhatsApp y llamadas.
- Validación con Cohere real.
