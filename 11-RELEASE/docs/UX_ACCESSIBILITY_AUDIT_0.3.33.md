# Auditoría UX/UI y accesibilidad 0.3.33

## Alcance
Navegación, foco, teclado, responsive, estados ARIA, reducción de movimiento, CSP necesaria para el bridge local y regresiones estáticas.

## Hallazgos corregidos
1. La navegación no expresaba el estado actual mediante `aria-current`.
2. El cambio de sección no devolvía el foco al contenido principal.
3. El modal de integraciones no tenía ciclo de foco ni cierre por Escape.
4. El skip link y algunos estados de foco podían ser poco visibles.
5. La navegación y filtros móviles requerían una adaptación más explícita.
6. La CSP no incluía los endpoints locales utilizados por el bridge, lo que podía bloquear las peticiones desde un navegador real.

## Garantías preservadas
- Sin frameworks pesados.
- IndexedDB local-first.
- Secretos fuera del navegador.
- Sin modificación del contrato de datos.
- Sin cambio de la lógica de aprendizaje o scoring.

## Evidencia
95 pruebas automatizadas PASS.
