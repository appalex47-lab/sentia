# FASE 0.3.13 — Memoria semántica y búsqueda de conocimiento

## Estado
IMPLEMENTADA — validación automatizada completada.

## Objetivo
Permitir recuperar conocimiento conversacional previamente aprendido frente a nuevas expresiones, sin depender de Cohere y sin promover coincidencias automáticamente.

## Implementación
- `python/pipeline/knowledge.py`: normalización semántica, equivalencias lingüísticas conservadoras, similitud Jaccard, búsqueda explicable y exclusión de memoria rechazada.
- `python/connection_server.py`: `POST /api/knowledge/search`.
- `js/db.js`: `searchKnowledge()` local-first sobre IndexedDB.
- `js/app.js`: buscador en la vista Conocimiento y explicación de coincidencias.
- `index.html` / `css/styles.css`: UI del buscador.

## Motor determinista
La representación normaliza mayúsculas, acentos, ruido, stopwords y variantes lingüísticas controladas. Se consideran coincidencia exacta, alias, frase normalizada y similitud de tokens. El resultado está entre 0 y 1.

Las equivalencias no constituyen una ontología universal: son una capa conservadora de recuperación. La validación y promoción de conocimiento siguen perteneciendo a 0.3.12.

## Ejemplo
`mi pedido se demoró`, `llevo días esperando`, `todavía no me entregan` y `la entrega viene tarde` pueden recuperar `demora_en_entrega` cuando existe memoria compatible.

## Cohere
No es obligatorio. La interfaz futura `SemanticProvider` queda conceptualmente preparada, pero 0.3.13 no depende de embeddings externos.

## Seguridad
No se reciben ni almacenan secretos en el endpoint. El endpoint recibe memoria pública/local y consulta; no altera la memoria.

## Pruebas
- 34/34 pytest PASS.
- `compileall` PASS.
- `node --check` para `js/app.js`, `js/db.js`, `js/browser-smoke.js` PASS.

## Validación Cloud
Puede revisar código, contrato, tests, documentación, seguridad y arquitectura. La ejecución real del navegador/IndexedDB requiere validación local.

## Validación local requerida
- Abrir `index.html` en navegador soportado.
- Entrar a Conocimiento.
- Consultar las cuatro variantes de demora en entrega.
- Confirmar resultados y razones de coincidencia.
- Recargar y comprobar persistencia IndexedDB.
- Probar offline.
- Ejecutar el bridge y comprobar `/api/knowledge/search`.

## Limitaciones
- No es un modelo de lenguaje.
- No garantiza equivalencia semántica profunda.
- Las equivalencias lingüísticas son deliberadamente conservadoras.
- Los embeddings de Cohere quedan para una evolución posterior.
