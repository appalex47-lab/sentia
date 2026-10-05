# Despliegue separado 0.3.39

## Repositorios

- `sentia-intelligence-from-conversations`: frontend GitHub Pages.
- `sentia-intelligence-from-conversations-api`: backend Python HTTPS.

## Flujo

`GitHub Pages → Backend HTTPS → Cohere / conectores externos`

GitHub Pages no ejecuta Python. El backend debe estar desplegado en un servicio HTTPS.
