# Browser / IndexedDB Smoke Test

## Environment
- Serve repository over HTTP/HTTPS; do not open `index.html` via `file://`.
- Chromium/Chrome/Firefox/Safari supported browser.

## Acceptance
1. Open dashboard with empty IndexedDB.
2. Confirm `datos_procesados.json` is imported automatically.
3. Reload page; confirm data remains in IndexedDB and JSON is not imported a second time.
4. Navigate Dashboard → Menciones → Insights → IA/Configuración → Ayuda.
5. Change date filters and search; confirm KPI/table/chart update.
6. Navigate Menciones; confirm pagination and counts.
7. Import the bundled `data/datos_procesados.json`; confirm replacement succeeds.
8. Import malformed JSON; confirm rejection and no destructive database change.
9. Import JSON with missing required mention fields; confirm contract rejection.
10. Use “Borrar datos locales”; confirm stores are emptied and empty state appears.
11. Disconnect network after initial load; confirm stored data and core dashboard remain usable. Chart must degrade gracefully if Chart.js is unavailable.
12. Verify API key is never requested by the frontend and never appears in IndexedDB/localStorage.
13. Keyboard-only navigation: skip link, navigation, filters, pagination, import, delete.
14. Screen reader: page title, live import status, chart fallback, table headers and controls have meaningful labels.

## Evidence to capture locally
- Browser console: no uncaught errors.
- Application → IndexedDB → `SocialListeningDB` → `mentions`, `insights`, `metadata`.
- Network panel: expected static assets only; no secret-bearing request.
- Lighthouse/axe results for accessibility and performance.
