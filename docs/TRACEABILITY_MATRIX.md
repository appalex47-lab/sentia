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

- REQ-CONV-001: agrupar turnos por conversación y conservar `conversation_id`.
- REQ-CONV-002: conservar participante/rol sin inventar atribuciones.
- REQ-CONV-003: exponer conteos por conversación y participante.

## FASE 0.3.13 — MEMORIA SEMÁNTICA Y BÚSQUEDA DE CONOCIMIENTO

- Estado: IMPLEMENTADA; pruebas automatizadas 34/34.
- Determinismo: búsqueda local-first sin Cohere.
- Backend: `/api/knowledge/search`.
- Seguridad: sin secretos; memoria rechazada excluida.
- Validación local pendiente: navegador/IndexedDB/offline/bridge real.

| REQ-GA4-001 | GA4 OAuth 2.0 server-side | RC 0.3.14 | Python bridge | Local validation required for real OAuth |
| REQ-GA4-002 | Descubrimiento de propiedades GA4 | RC 0.3.14 | Admin API | Local validation required |
| REQ-GA4-003 | runReport con métricas de comportamiento | RC 0.3.14 | Data API | Local validation required |
| REQ-GA4-004 | Tokens fuera del navegador | RC 0.3.14 | token_store.py | Automated + local |
| REQ-GA4-005 | Persistencia local de reportes | RC 0.3.14 | IndexedDB v5 | Browser local validation required |

## RC 0.3.15 — Multi-source social connectors
| ID | Requisito | Implementación | Evidencia | Estado |
|---|---|---|---|---|
| REQ-SOC-015-01 | X OAuth + lectura reciente | `python/connectors/social.py`, bridge X routes | `test_social_connectors.py` | PASS estático/tests |
| REQ-SOC-015-02 | TikTok profile/video ingestion | `TikTokConnector`, bridge ingest | `test_social_connectors.py` | PASS estático/tests |
| REQ-SOC-015-03 | YouTube videos/comments | `YouTubeConnector`, bridge ingest | `test_social_connectors.py` | PASS estático/tests |
| REQ-SOC-015-04 | LinkedIn org posts/comments | `LinkedInConnector`, bridge ingest | `test_social_connectors.py` | PASS estático/tests |
| REQ-SOC-015-05 | Secrets outside browser | encrypted Python token store + public config filter | tests/config review | PASS |
| REQ-SOC-015-06 | Normalization into mentions | `social_to_mentions()` + existing Pipeline | tests | PASS |
| REQ-SOC-015-07 | Real provider authorization | local credentials required | local validation | REQUIERE VALIDACIÓN LOCAL |

## RC 0.3.16 — Sincronización y orquestación
| ID | Requisito | Implementación | Evidencia | Estado |
|---|---|---|---|---|
| REQ-SYNC-016-01 | Orquestador multi-fuente | `connection_server.py` `/api/sync/all` | `test_sync.py` + HTTP efímero | PASS |
| REQ-SYNC-016-02 | Estado persistente | `pipeline/sync.py`, `runtime/sync_state.json`, IndexedDB v6 | tests + static review | PASS |
| REQ-SYNC-016-03 | Deduplicación determinista | `canonical_external_id`, `deduplicate_rows` | tests | PASS |
| REQ-SYNC-016-04 | IDs externos estables LinkedIn | `social_to_mentions()` | tests | PASS |
| REQ-SYNC-016-05 | Fallos parciales | `sync/all` por proveedor | tests/static | PASS |
| REQ-SYNC-016-06 | Automatización opt-in | `setupSync()` cada 30 min mientras app abierta | JS syntax/static | PASS STATIC; browser local |
| REQ-SYNC-016-07 | Secretos fuera del navegador | token store + public config | existing security tests | PASS |
| REQ-SYNC-016-08 | Proveedores reales | OAuth/API/rate limits | local environment | REQUIERE VALIDACIÓN LOCAL |

| REQ-SYNC-OBS-001 | Cada ejecución de sincronización debe ser auditable | RC 0.3.17 | `python/pipeline/sync.py`, `/api/sync/runs`, UI Integraciones | 55/55 tests | Local pendiente |
| REQ-SYNC-OBS-002 | Los fallos parciales deben distinguirse de errores totales | RC 0.3.17 | `build_sync_run` + historial UI | PASS | Local pendiente |
| REQ-SYNC-OBS-003 | El historial no debe contener secretos | RC 0.3.17 | registro de ejecución operativo | PASS | Auditoría local pendiente |

| REQ-SYNC-RES-001 | Reintentar fallos transitorios con backoff | RC 0.3.18 | `pipeline/sync.py`, orquestador | 57/57 tests | Proveedores reales pendientes |
| REQ-SYNC-RES-002 | No reintentar errores permanentes | RC 0.3.18 | `retry_sync_call` | PASS | Local pendiente |
| REQ-SYNC-RES-003 | Evitar sincronizaciones concurrentes | RC 0.3.18 | `SYNC_LOCK`, `/api/sync/all` | PASS estático | HTTP concurrente local pendiente |
| REQ-SYNC-RES-004 | Registrar cantidad de reintentos | RC 0.3.18 | `build_sync_run`, UI historial | PASS | Navegador pendiente |


## REQ-SYNC-019 — Programación persistente de sincronización
- Implementación: `js/db.js`, `js/app.js`, `index.html`.
- Persistencia: IndexedDB `sync_scheduler` v7.
- Validación: suite + sintaxis JS; navegador real pendiente.

| REQ-SYNC-HEALTH-001 | La plataforma debe mostrar la frescura operativa de las fuentes sincronizadas | 0.3.20 | `/api/sync/health`, UI Integraciones, tests de sync | PASS automatizado / local pendiente |

| ID | Requisito | Implementación | Evidencia | Estado |
|---|---|---|---|---|
| REQ-SYNC-021 | Detectar estados accionables | `build_sync_alerts`, `/api/sync/alerts` | 65 tests PASS | PASS |
| REQ-SYNC-022 | Recuperar sincronización desde UI | acción de alerta reutiliza orquestador | JS syntax PASS | PASS |
| REQ-SEC-021 | No exponer secretos en alertas | payload limitado a metadatos operativos | test de alerta | PASS |


## RC 0.3.22 — Diagnóstico operativo
| ID | Requisito | Implementación | Evidencia | Estado |
|---|---|---|---|---|
| REQ-SYNC-DIAG-001 | Exportar evidencia operacional sin secretos | `build_sync_diagnostic_report`, `/api/sync/diagnostic`, UI | tests + HTTP smoke | PASS |
| REQ-SYNC-DIAG-002 | Limitar historial exportado | últimas 10 ejecuciones | test | PASS |
| REQ-SEC-DIAG-001 | Redactar credenciales de mensajes de error | `_redact_diagnostic_text` | test | PASS |

## RC 0.3.25 — Reconciliación extremo a extremo
| ID | Requisito | Implementación | Evidencia | Estado |
|---|---|---|---|---|
| REQ-SYNC-E2E-001 | Asociar evidencia local a cada sincronización exitosa | `sync_manifests`, `run_id` | 72 tests PASS | PASS |
| REQ-SYNC-E2E-002 | Detectar ausencia de persistencia local | `reconcile_local_manifests`, `/api/sync/reconcile` | tests de reconciliación | PASS |
| REQ-SYNC-E2E-003 | Detectar discrepancia de ejecución y conteos | comparación server/local | tests de reconciliación | PASS |
| REQ-SYNC-E2E-004 | Migrar IndexedDB sin eliminar stores existentes | DB v8 | revisión estática | PASS |
| REQ-SEC-E2E-001 | Manifiestos sin secretos | campos limitados a metadatos de persistencia | revisión estática | PASS |
