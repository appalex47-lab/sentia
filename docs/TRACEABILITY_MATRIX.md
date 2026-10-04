# TRACEABILITY_MATRIX

| Requirement | Phase | Code | Evidence | Status |
|---|---|---|---|---|
| REQ-DATA-001 | 1 | schemas/datos_procesados.schema.json | `python -m python.validate` | PASS |
| REQ-DB-001 | 2 | js/db.js | static + browser checklist | LOCAL VALIDATION browser |
| REQ-DQ-001 | 3 | python/pipeline/orchestrator.py | 7 pytest | PASS |
| REQ-SENT-001 | 4 | python/pipeline/sentiment.py | contract test | PASS WITH LIMITATION: real model local |
| REQ-RULE-001 | 5 | python/pipeline/orchestrator.py | pipeline tests | PASS |
| REQ-AI-001 | 6 | python/pipeline/ai.py | contract/error tests | IMPLEMENTED / LOCAL VALIDATION real API |
| REQ-PIPE-001 | 7 | python/main.py | fixture export + schema validation | PASS |
| REQ-UI-001 | 8 | index.html/css | static/syntax | LOCAL VALIDATION browser |
| REQ-JS-001 | 9 | js/app.js | node syntax + checklist | LOCAL VALIDATION browser |
| REQ-EXPLAIN-001 | 10 | help + factores_score | static review | PASS |
| REQ-SEC-001 | 11 | CSP + .gitignore + ai.py | static review | PASS STATIC |
| REQ-A11Y-001 | 11 | HTML/CSS | static + browser checklist | LOCAL VALIDATION browser |
| REQ-PERF-001 | 11 | Python pipeline + IndexedDB/UI | 10k benchmark | PASS WITH BROWSER LIMITATION |
| REQ-OFFLINE-001 | 11 | sw.js + app.js | shell/cache contract | LOCAL VALIDATION browser |
| REQ-DEPLOY-001 | 11 | relative paths + .nojekyll | static | LOCAL VALIDATION GitHub Pages |
| REQ-QA-001 | 12 | docs/tests | phase audits 01–05 | BLOCKED: runtime gates |

## Audit status
- RC 0.1.5: Final QA executed. Automated/static gates pass; runtime release gates remain blocked/local-validation.
- Browser, IndexedDB, Service Worker, Lighthouse/axe, GitHub Pages, real pysentimiento and real Cohere remain unverified in this environment.

## Final Certification Gate — 2026-10-04

| Gate | Status | Evidence |
|---|---|---|
| Automated regression | PASS | 7/7 tests |
| Schema contract | PASS | local validator |
| Python/JS syntax | PASS | compileall + node --check |
| Offline runtime dependency contract | PASS | no external CDN/API frontend refs |
| Product identity | PASS | Sentia manifest/title/docs |
| Browser IndexedDB | LOCAL VALIDATION | target browser required |
| Service Worker offline | LOCAL VALIDATION | target browser required |
| Accessibility tooling | LOCAL VALIDATION | target browser required |
| GitHub Pages | LOCAL VALIDATION | deployed target required |
| Real pysentimiento | LOCAL VALIDATION | package/model environment required |
| Real Cohere | LOCAL VALIDATION | credentialed API environment required |
| Production release | CONDITIONAL | blocked only by external evidence |
