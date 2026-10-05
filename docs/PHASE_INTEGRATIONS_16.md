# Fase 0.3.8 — Ingesta de llamadas en español

## Objetivo
Permitir que Sentia reciba audio de llamadas en español, lo transcriba con Cohere Transcribe y envíe el texto al pipeline canónico.

## Contrato
- Idioma por defecto: `es`.
- Formatos de audio: FLAC, MP3, MPEG, MPGA, OGG y WAV.
- Límite: 25 MB por archivo para Cohere Transcribe.
- Original de audio: no se persiste en IndexedDB por este endpoint.
- Texto transcrito: se conserva como `texto_original` de la mención de llamada.
- Diarización: no disponible en Cohere Transcribe; Sentia no inventa hablantes.
- `speaker` queda vacío salvo que una fuente posterior proporcione etiquetas.

## Flujo
Audio → Python → Cohere Transcribe (`cohere-transcribe-03-2026`, `language=es`) → texto → limpieza/sentimiento/reglas/score → IndexedDB.

## Fuera de alcance
- Identificación automática de hablantes.
- Timestamps de palabras.
- Archivos mayores de 25 MB sin un adaptador/segmentación específico.

## Validación local requerida
Una llamada real, calidad de audio, acentos, ruido y resultados de transcripción deben validarse con archivos reales.
