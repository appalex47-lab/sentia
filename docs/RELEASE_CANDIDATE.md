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
