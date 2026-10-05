# Fase 0.3.38 — Centro de Conexiones e Integraciones

## Objetivo
Hacer visible y usable desde la interfaz el centro de configuración de conexiones externas.

## Proveedores visibles
- Meta / Facebook Pages
- Instagram
- X
- TikTok
- YouTube
- LinkedIn
- Google Analytics 4
- Cohere
- Conector personalizado

## UX
- Acceso destacado desde Configuración.
- Centro de conexiones con filtros por categoría.
- Estado de conexiones configuradas.
- Formularios dinámicos para campos públicos.
- Acciones de conexión, sincronización y desconexión según proveedor.

## Seguridad
Los secretos y tokens no se solicitan como campos persistentes del navegador. Se mantienen en el bridge Python y en el almacenamiento seguro correspondiente.

## Compatibilidad del paquete final
Se corrigió la resolución del JSON Schema para funcionar con el paquete organizado por tipo de archivo (`06-SCHEMAS`) sin romper el layout original.
