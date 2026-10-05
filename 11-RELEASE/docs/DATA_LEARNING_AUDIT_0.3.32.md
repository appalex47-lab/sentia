# Auditoría de datos, aprendizaje y memoria — 0.3.32

## Criterios auditados
1. Separación estricta del dominio conversacional.
2. Aprendizaje determinista y reproducible.
3. Evidencia trazable para conocimientos aprendidos.
4. Rechazo conservador de entradas inválidas.
5. Búsqueda sin promoción automática de memoria.
6. Compatibilidad del contrato JSON.
7. Persistencia local sin secretos.

## Resultado
- El motor conserva tipos permitidos: `topic`, `entity`, `intent`, `problem`, `organization`, `pattern`.
- Cada propuesta generada por el extractor registra IDs de menciones y conversaciones de evidencia.
- La evidencia se limita a 100 IDs por dimensión para evitar crecimiento ilimitado del registro.
- `learning_engine` identifica el algoritmo responsable.
- `learned_at` solo se asigna al alcanzar un estado validado/aprendido.
- Los registros `rejected` no aparecen en búsquedas.
- Registros con términos de catálogo prohibidos, incluso dentro de aliases, son rechazados.
- La búsqueda valida la memoria recibida antes de usarla.

## Decisión arquitectónica
La memoria no debe usar un modelo generativo como autoridad. Cualquier IA puede aportar señales o explicaciones, pero la promoción a `validated`/`learned` permanece determinada por evidencia, frecuencia y confianza.

## Evidencia de pruebas
`90 passed in 1.59s`.
