# Fase 0.3.12 — Motor de aprendizaje y validación automática

## Alcance

Esta fase pertenece exclusivamente a **Sentia Intelligence from Conversations**.
El conocimiento aprendido se limita al dominio conversacional: temas, entidades, organizaciones, intenciones, problemas y patrones lingüísticos.

No se incorporan conceptos de catálogos de productos, farmacéutica, SKU, marcas de producto, sustancias activas o presentaciones.

## Principios

1. La evidencia repetida aumenta la confianza, pero no convierte una inferencia en verdad absoluta.
2. El estado `proposed` es el estado inicial.
3. `validated` requiere evidencia recurrente y confianza suficiente.
4. `learned` requiere evidencia más fuerte.
5. Un elemento rechazado no se reactiva automáticamente.
6. No se inventa historial cuando no existe evidencia.
7. La IA puede proponer; el motor determinístico valida y controla la memoria.

## Estados

- `proposed`: detectado pero aún no suficientemente confirmado.
- `validated`: evidencia recurrente y confianza mínima.
- `learned`: evidencia recurrente fuerte; puede utilizarse como conocimiento local.
- `rejected`: descartado explícitamente o por política de validación.

## Umbrales actuales

- `validated`: frecuencia >= 3 y confianza >= 0.75.
- `learned`: frecuencia >= 5 y confianza >= 0.85.

Estos umbrales son configurables en una futura fase de calibración y no representan una verdad estadística universal.

## Persistencia

La memoria se almacena en `knowledge_entities` dentro de IndexedDB. Los secretos no forman parte de esta memoria.

## Cloud review

Cloud puede revisar estáticamente el dominio, contratos, estados, umbrales, tests y ausencia de vocabulario de catálogo de productos.

## Validación local pendiente

- comportamiento con corpus reales grandes;
- calibración de falsos positivos/negativos;
- validación humana de entidades y alias;
- desempeño con datos reales;
- integración real con Cohere.
