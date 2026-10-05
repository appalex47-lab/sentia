# RELEASE_CANDIDATE

## Version
RC-0.2.0

## Included
- Data contract/schema.
- Local IndexedDB stores and migrations.
- Python batch pipeline with automatic schema validation.
- Cleaning, hash deduplication, quality, deterministic rules/scoring.
- pysentimiento adapter with explicit fallback state.
- Cohere adapter with versioned prompt and structured errors.
- Dashboard, filters, table, chart, insights and educational help.
- IndexedDB import/replace/append/clear/pagination primitives.
- Service Worker and manifest for offline-first shell caching.
- CSP and static deployment hardening.
- Performance benchmark evidence.
- Audit and traceability documents.

## Explicitly pending local validation
- Real pysentimiento model execution.
- Real Cohere request with valid credentials.
- Browser execution of IndexedDB and Service Worker.
- Lighthouse/axe audit.
- GitHub Pages deployment/cache verification.
- Browser memory benchmark at large scale.
- Official SRI hash verification for CDN Chart.js.

## Release decision
**BLOCKED — NO PRODUCTION RELEASE.** Runtime validation gates must be executed before promotion.

## RC 0.3.13

Fase 0.3.13 implementada: memoria semántica determinista y búsqueda local-first.

Validaciones ejecutadas: 35/35 tests, schema PASS, compileall PASS, JavaScript syntax PASS. La validación de navegador/IndexedDB/offline/GitHub Pages requiere ejecución local.

### RC 0.3.14 — GA4
Estado: **READY FOR LOCAL VALIDATION**.

Automated evidence:
- pytest: 38/38 PASS
- schema: PASS
- Python compile: PASS
- JavaScript syntax: PASS
- GA4 status endpoint without credentials: PASS (safe failure)
- GA4 authorize endpoint without credentials: PASS (400 configuration error, no secret disclosure)

Local validation required:
- Google Cloud project + Analytics Data API/Admin API enabled.
- OAuth client configured with exact redirect URI.
- `GOOGLE_CLIENT_SECRET` supplied only to Python.
- User grants Analytics read access.
- Property discovery and real `runReport` execution.
- Browser IndexedDB v5 migration and report persistence.
- GitHub Pages/browser deployment constraints.
