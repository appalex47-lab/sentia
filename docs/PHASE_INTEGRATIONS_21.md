# RC 0.3.14 — Google Analytics 4 y enriquecimiento de comportamiento

## Objetivo
Integrar GA4 como fuente complementaria de comportamiento mediante OAuth 2.0 y Google Analytics Data API/Admin API, manteniendo secretos y tokens exclusivamente en Python.

## Alcance
- Configuración pública de client ID, proyecto, propiedad, redirect URI y scopes.
- OAuth 2.0 con usuario.
- Descubrimiento de propiedades accesibles mediante `accountSummaries`.
- Reporte GA4 mediante `properties.runReport`.
- Consulta inicial: `date` + `activeUsers`, `sessions`, `eventCount`.
- Persistencia local de reportes en IndexedDB (`analytics_reports`).
- Desconexión y borrado de tokens del bridge.

Google documenta `runReport` como el método recomendado para reportes simples y exige un property ID; la API admite el scope `analytics.readonly`. citeturn0search5turn0search1

## Seguridad
El navegador nunca recibe `GOOGLE_CLIENT_SECRET`, access tokens ni refresh tokens. Los tokens se conservan en el almacén cifrado de Python.

## Decisiones
- OAuth de usuario como camino principal de esta release.
- Service Account queda fuera de 0.3.14 para evitar dos mecanismos de autenticación simultáneos.
- No se escriben métricas de GA4 como si fueran menciones o sentimiento. Se mantienen en un almacén separado.
- No se confunde `activeUsers`, `sessions` o `eventCount` con KPIs de sentimiento.

## Validación Cloud
### Nivel A
Código, contratos, separación de secretos, documentación, tests.
### Nivel B
Tests automatizados y endpoints locales si el entorno lo permite.
### Nivel C — REQUIERE VALIDACIÓN LOCAL
OAuth real de Google, permisos sobre una propiedad real, cuotas, navegador, GitHub Pages y comparación de resultados con la UI de GA4.

## Referencias oficiales
- Google Analytics Data API: https://developers.google.com/analytics/devguides/reporting/data/v1
- `runReport`: https://developers.google.com/analytics/devguides/reporting/data/v1/basics
- Google Analytics Admin API: https://developers.google.com/analytics/devguides/config/admin/v1
