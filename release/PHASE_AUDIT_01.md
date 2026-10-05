# FASE DE AUDITORÍA Y CORRECCIÓN — RC-0.1.1

## Resultado
PASS CON LIMITACIONES DOCUMENTADAS.

## Evidencia ejecutada
- `python -m pytest -q` → 3 passed.
- `python -m compileall -q python` → PASS.
- `python -m python.validate` sobre `data/datos_procesados.json` → PASS.
- Pipeline real con fixture → exportación de 3 menciones → PASS.
- JSON exportado por pipeline → validación JSON Schema → PASS.

## Correcciones aplicadas
1. Se corrigió el descubrimiento de `pipeline` durante las pruebas mediante `conftest.py`.
2. Se corrigió el import del entrypoint `python/main.py` para ejecución como módulo.
3. Se creó `SentimentEngine` con adaptador explícito para pysentimiento y fallback heurístico identificable.
4. Se creó `CohereService`; la clave se lee exclusivamente desde `COHERE_API_KEY` del entorno.
5. Se añadió `python/validate.py` con JSON Schema 2020-12 + FormatChecker.
6. Se añadieron pruebas del contrato del motor de sentimiento.

## No aprobado todavía
- Ejecución con el modelo real de pysentimiento: REQUIERE VALIDACIÓN LOCAL.
- Ejecución real de Cohere: REQUIERE CREDENCIAL LOCAL y validación de respuesta.
- Pruebas reales de IndexedDB/navegador: REQUIERE VALIDACIÓN LOCAL.
- Accesibilidad completa y benchmark de grandes volúmenes: PENDIENTE.
- Auditoría final de CSP/CDN y GitHub Pages: PENDIENTE.

## Regla de auditoría
No se considera PASS una capacidad que solamente tenga código preparado si no existe evidencia de ejecución. En esos casos el estado correcto es LOCAL VALIDATION o PENDING.
