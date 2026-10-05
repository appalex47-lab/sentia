# Sentia Intelligence from Conversations — Release 0.3.33

## Fase
Auditoría UX/UI, accesibilidad y experiencia de uso.

## Cambios
- Navegación con `aria-current` y botones explícitos.
- El foco vuelve al contenido principal al cambiar de sección.
- Modal de integraciones con soporte de Escape y trampa de foco por teclado.
- Skip link y estados `:focus-visible` reforzados.
- Soporte `prefers-reduced-motion` conservado.
- Navegación lateral y filtros adaptados a pantallas pequeñas.
- CSP permite únicamente los bridges locales requeridos (`127.0.0.1:8787` y `localhost:8787`) además del propio origen.
- Pruebas automatizadas de accesibilidad estática y contrato UX.

## Validación
- 95/95 pruebas PASS.
- Python compileall PASS.
- Node syntax check `js/app.js` PASS.
- Node syntax check `js/db.js` PASS.
- JSON Schema parse PASS.

## Validación pendiente local
- Prueba visual manual en Chromium/Firefox/Safari.
- Navegación completa con lector de pantalla real.
- Prueba táctil en Android/iOS.
- Verificación real del bridge desde GitHub Pages publicado.

## No verificado por esta fase
No se considera aprobada ninguna prueba que requiera un navegador real, dispositivo físico, lector de pantalla o despliegue externo.
