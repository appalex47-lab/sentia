# Sentia Intelligence from Conversations — GitHub Ready 0.3.38

Esta carpeta es la estructura corregida y preparada para subir directamente a la raíz de un repositorio GitHub.

- `index.html` está en la raíz.
- `css/`, `js/`, `data/`, `schemas/`, `python/`, `tests/` y `docs/` están en rutas de repositorio normales.
- No contiene API keys, OAuth tokens ni secretos reales.
- GitHub Pages puede servir el frontend estático.
- El bridge Python local (`127.0.0.1:8787`) sigue siendo necesario para Cohere y las integraciones que requieren backend/secretos.
- No publiques `.env` con valores reales.

## Publicación rápida

1. Extrae este ZIP.
2. Entra a la carpeta extraída.
3. Sube **todo su contenido** a la raíz del repositorio GitHub.
4. Para GitHub Pages, configura Pages para publicar desde la rama y carpeta donde está `index.html`.


## Corrección 0.3.38-GITHUB-READY-FIXED

Se restauró el renderizado del dashboard y las funciones auxiliares que requiere `app.js` (`$`, `filtered`, `render` y el gráfico nativo). El paquete anterior podía cargar el HTML pero romper la inicialización al intentar renderizar los datos.
