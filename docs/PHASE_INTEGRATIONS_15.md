# Fase 0.3.7 — Cohere y traducción asistida

## Objetivo
Configurar Cohere desde Sentia pegando únicamente la API key y habilitar traducción asistida para ingesta manual.

## Flujo Cohere
1. Sentia solicita la API key.
2. La clave viaja únicamente al bridge local Python en `127.0.0.1:8787`.
3. Python valida la clave con Cohere.
4. Python la cifra en el almacén local.
5. IndexedDB sólo conserva el modelo y el estado; nunca la clave.
6. El usuario puede desconectar Cohere desde Sentia.

Cohere documenta `ClientV2`, el endpoint Chat v2 y el uso de una API key para autenticación. cite-source-placeholder

## Traducción
La ingesta manual puede activar `Traducir automáticamente con Cohere`. Se conserva `texto_original`; la traducción se guarda en `texto_traducido`, con `idioma_analisis` y `metodo_traduccion=cohere`. El análisis determinístico posterior usa el texto traducido.

## Seguridad
- La API key no se devuelve al navegador.
- El almacenamiento cifrado usa AES-GCM.
- Si no se proporciona `SENTIA_TOKEN_ENCRYPTION_KEY`, el bridge genera una clave local con permisos restringidos para facilitar la configuración local.
- En entornos administrados se recomienda proporcionar la clave mediante variable de entorno/gestor de secretos.

## Validación local requerida
- Probar una API key real de Cohere.
- Importar una conversación real y activar traducción.
- Confirmar cuotas, modelo y latencia.
