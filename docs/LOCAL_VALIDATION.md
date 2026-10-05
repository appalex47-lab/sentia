# Validación local requerida — RC 0.1.2

## 1. Motores Python
```bash
python -m pip install -r requirements.txt
python -m pytest -q
python -m python.main --input python/tests/fixtures/mentions.json --output data/datos_procesados.json
python -m python.validate data/datos_procesados.json
```

### pysentimiento
Debe observarse que el backend reportado sea `pysentimiento`, no `heuristic_fallback`. Validar al menos ejemplos positivo/negativo/neutro en español y registrar versión instalada.

### Cohere
Definir `COHERE_API_KEY` como variable de entorno. Nunca pegarla en código, JSON, IndexedDB, frontend o commits.
```bash
export COHERE_API_KEY="..."
export COHERE_MODEL="..."
python -m python.main --input python/tests/fixtures/mentions.json --output data/datos_procesados.json
```
Validar respuesta estructurada, errores de autenticación/rate limit y que el dashboard siga funcionando si Cohere falla.

## 2. Browser
Servir el proyecto:
```bash
python -m http.server 8000
```
Abrir `http://localhost:8000/` y verificar IndexedDB, carga inicial, filtros, gráfica, XSS-safe rendering y funcionamiento sin Cohere.

## 3. Release
Verificar GitHub Pages, modo offline, tamaño de dataset y rendimiento en el navegador objetivo antes de declarar RELEASE FINAL.
