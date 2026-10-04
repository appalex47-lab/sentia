# RELEASE DECISION — Sentia Intelligence from Conversations 0.2.1

## Current decision
**CONDITIONAL RELEASE CANDIDATE — NOT YET PRODUCTION CERTIFIED**

## Passed locally

- Automated Python suite: 7/7.
- Schema validation.
- Python compilation.
- JavaScript syntax.
- Offline/runtime dependency contract.
- Product identity and manifest.
- Static security checks.
- Package integrity.

## Remaining mandatory evidence

- Browser IndexedDB execution.
- Service Worker/offline reload.
- Browser accessibility audit.
- Lighthouse/performance in target browser.
- GitHub Pages deployment smoke test.
- Real pysentimiento execution.
- Real Cohere integration with a user-provided environment secret.
- Browser stress test on representative large datasets.

## Why this is not called FAIL

No reproducible local gate failed. The remaining statuses are **LOCAL VALIDATION** because the authoritative target environment is outside the current execution environment.

## Why this is not called RELEASE

Production certification requires evidence from the actual browser/deployment/API environments, not static inspection or inference.

## Product name

**Sentia Intelligence from Conversations**
Short name: **Sentia**.

Commercial use additionally requires independent domain, trademark, and legal availability checks.
