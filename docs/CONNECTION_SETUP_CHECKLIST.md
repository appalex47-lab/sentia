# Sentia — Checklist de conexión

## Antes de conectar
- [ ] Crear/registrar la aplicación en el portal oficial del proveedor.
- [ ] Copiar los identificadores públicos solicitados por Sentia.
- [ ] Registrar exactamente el Redirect URI indicado por el conector.
- [ ] Solicitar únicamente scopes necesarios.
- [ ] Configurar secretos exclusivamente en el entorno seguro de Python.

## En Sentia
- [ ] Abrir **Integraciones**.
- [ ] Seleccionar el proveedor.
- [ ] Pulsar **Configurar**.
- [ ] Completar campos públicos.
- [ ] Guardar configuración.
- [ ] Configurar secretos en Python.
- [ ] Ejecutar **Probar conexión** cuando el conector esté implementado.

## Regla de seguridad
Nunca pegar una API key, client secret, access token o refresh token en un campo que vaya a persistirse en IndexedDB/localStorage.
