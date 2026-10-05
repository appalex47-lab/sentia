# Fase 0.3.9 — Conversaciones, participantes y turnos

## Objetivo
Agrupar menciones provenientes de WhatsApp y transcripciones en conversaciones trazables, con turnos y participantes sin inventar identidades.

## Contrato
Cada mención puede incluir `conversation_id`, `turn_index`, `speaker` y `speaker_role`. Los roles reconocidos de forma determinística incluyen `cliente` y `agente`; nombres desconocidos se conservan como `desconocido` y ausencia de hablante como `no_atribuido`.

## Conversación
El payload incorpora `conversations[]` con turnos, participantes, conteos de sentimiento y turnos no atribuidos.

## Idioma
Para WhatsApp y llamadas el idioma operativo por defecto es `es`. El texto original se conserva.

## No diarización inventada
Si una transcripción de audio no contiene identificación de hablantes, Sentia no asigna roles por inferencia semántica.

## Persistencia
IndexedDB v4 incorpora el store `conversations`.

## Validación
La fase debe pasar pruebas Python, schema validation y revisión de sintaxis JS. La diarización real de audio continúa como integración futura específica de proveedor.
