# Fase 0.3.6 — Ingesta multifuente manual, traducción y deduplicación

## Objetivo
Permitir incorporar conversaciones sin conector oficial: exportaciones de WhatsApp, transcripciones de llamadas y archivos TXT/CSV/JSON.

## Arquitectura
`Archivo manual → bridge Python → parser de fuente → contrato de filas → pipeline Sentia → validación → IndexedDB`

El navegador nunca envía el archivo a un tercero. El bridge local Python recibe el contenido y lo transforma antes de persistir resultados.

## WhatsApp
Se acepta la exportación TXT estándar y se extraen fecha, hora, emisor y mensaje. Los mensajes multilínea se agrupan. El nombre de la fuente se conserva como `fuente`.

## Llamadas
Esta fase **no transcribe audio**. Una llamada debe llegar como transcripción de texto producida por una herramienta autorizada. Se aceptan TXT/CSV/JSON. Si existe `texto_traducido`, el pipeline analiza esa versión y conserva `texto_original`.

Esto permite, por ejemplo:
- audio → herramienta de transcripción elegida por el usuario → TXT/CSV → Sentia;
- transcript en inglés → `texto_original` en inglés + `texto_traducido` en español → análisis en español.

No se inventa una traducción cuando no existe.

## Campos adicionales
- `texto_traducido`: versión usada para análisis cuando está disponible.
- `idioma_origen`: idioma original conocido.
- `idioma_analisis`: idioma objetivo del análisis.
- `metodo_traduccion`: `archivo_proporcionado`, `manual`, `no_aplicado` u otro valor documentado.
- `speaker`: emisor/agente cuando la fuente lo permite.

## Seguridad
No se almacenan secretos de proveedores. El archivo se procesa localmente en el bridge Python. La persistencia final continúa en IndexedDB con datos procesados.

## Limitaciones / validación local
- Los formatos exactos de exportación de terceros pueden variar y requieren validación local.
- Audio directo y diarización automática quedan fuera de esta fase.
- La traducción automática de archivos queda como siguiente capacidad; la fase actual admite texto traducido proporcionado por el usuario.

## Criterios de aceptación
- [x] WhatsApp TXT se transforma a filas canónicas.
- [x] TXT/CSV/JSON manuales se aceptan.
- [x] Original y traducción pueden coexistir.
- [x] El pipeline analiza la traducción cuando existe.
- [x] El original permanece para trazabilidad.
- [x] Los resultados pasan por schema validation.
- [x] No se envían archivos a proveedores externos desde esta ingesta.
