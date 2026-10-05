"""Deterministic synchronization state and deduplication helpers."""
from __future__ import annotations
import hashlib, json, time
from collections.abc import Callable
from pathlib import Path





CHECKPOINT_VERSION = 1
CHECKPOINT_CAPABLE_PROVIDERS = {"tiktok", "youtube", "x", "linkedin"}


def normalize_checkpoint(state: dict | None) -> dict:
    """Return a safe checkpoint record without inventing a provider position."""
    state = state if isinstance(state, dict) else {}
    cp = state.get("checkpoint") if isinstance(state.get("checkpoint"), dict) else {}
    return {
        "version": int(cp.get("version") or CHECKPOINT_VERSION),
        "status": str(cp.get("status") or "empty"),
        "committed_cursor": str(cp.get("committed_cursor") or ""),
        "pending_cursor": str(cp.get("pending_cursor") or ""),
        "sequence": int(cp.get("sequence") or 0),
        "run_id": str(cp.get("run_id") or ""),
        "page": int(cp.get("page") or 0),
        "updated_at": cp.get("updated_at"),
    }


def begin_checkpoint(previous: dict | None, *, run_id: str, cursor: str = "", page: int = 0) -> dict:
    """Create a pending checkpoint; the committed cursor remains unchanged until commit."""
    cp = normalize_checkpoint(previous)
    cp.update({
        "version": CHECKPOINT_VERSION,
        "status": "pending",
        "pending_cursor": str(cursor or ""),
        "run_id": str(run_id),
        "page": max(0, int(page or 0)),
        "updated_at": time.time(),
    })
    return cp


def commit_checkpoint(previous: dict | None, *, run_id: str, cursor: str = "", page: int = 0) -> dict:
    """Commit a checkpoint only after the corresponding payload has been persisted successfully."""
    cp = normalize_checkpoint(previous)
    if cp.get("status") == "pending" and cp.get("run_id") not in {"", str(run_id)}:
        raise ValueError("CHECKPOINT_RUN_MISMATCH")
    cp.update({
        "version": CHECKPOINT_VERSION,
        "status": "committed",
        "committed_cursor": str(cursor or cp.get("pending_cursor") or ""),
        "pending_cursor": "",
        "sequence": int(cp.get("sequence") or 0) + 1,
        "run_id": str(run_id),
        "page": max(0, int(page or 0)),
        "updated_at": time.time(),
    })
    return cp


def abandon_checkpoint(previous: dict | None, *, run_id: str, reason: str = "") -> dict:
    """Discard only the pending position; never replace the last committed cursor."""
    cp = normalize_checkpoint(previous)
    if cp.get("run_id") not in {"", str(run_id)}:
        raise ValueError("CHECKPOINT_RUN_MISMATCH")
    cp.update({
        "version": CHECKPOINT_VERSION,
        "status": "interrupted",
        "pending_cursor": "",
        "run_id": str(run_id),
        "reason": str(reason or "")[:200],
        "updated_at": time.time(),
    })
    return cp


def reconcile_local_manifests(server_runs: list[dict], local_manifests: list[dict], *, providers: list[str]) -> dict:
    """Compare server run manifests with browser-confirmed IndexedDB persistence receipts."""
    providers = [str(p).strip().lower() for p in (providers or []) if str(p).strip()]
    latest = {}
    for run in server_runs or []:
        if not isinstance(run, dict):
            continue
        for item in run.get("providers", []):
            if not isinstance(item, dict) or not item.get("ok"):
                continue
            provider = str(item.get("provider") or "").strip().lower()
            if provider in providers:
                latest[provider] = {
                    "run_id": str(run.get("run_id") or ""),
                    "source_count": int(item.get("source_count") or 0),
                    "duplicate_count": int(item.get("duplicate_count") or 0),
                    "content_keys": [str(x) for x in (item.get("content_keys") or []) if str(x)],
                    "finished_at": run.get("finished_at"),
                }
    manifests = {}
    for manifest in local_manifests or []:
        if not isinstance(manifest, dict):
            continue
        provider = str(manifest.get("provider") or "").strip().lower()
        if provider in providers and provider not in manifests:
            manifests[provider] = manifest
    issues = []
    for provider in providers:
        expected = latest.get(provider)
        local = manifests.get(provider)
        if not expected:
            continue
        if not local:
            issues.append({"provider": provider, "code": "LOCAL_MANIFEST_MISSING", "severity": "error", "run_id": expected["run_id"]})
            continue
        if str(local.get("run_id") or "") != expected["run_id"]:
            issues.append({"provider": provider, "code": "LOCAL_RUN_MISMATCH", "severity": "error", "expected_run_id": expected["run_id"], "local_run_id": str(local.get("run_id") or "")})
        received = int(local.get("received_count") or 0)
        persisted = int(local.get("persisted_count") or 0)
        if received != expected["source_count"]:
            issues.append({"provider": provider, "code": "LOCAL_RECEIVED_COUNT_MISMATCH", "severity": "error", "expected": expected["source_count"], "local": received})
        if persisted < received:
            issues.append({"provider": provider, "code": "LOCAL_PERSISTED_COUNT_SHORTFALL", "severity": "error", "received": received, "persisted": persisted})
        expected_keys = set(expected.get("content_keys") or [])
        local_keys = set(str(x) for x in (local.get("content_keys") or []) if str(x))
        if expected_keys:
            missing_from_manifest = sorted(expected_keys - local_keys)
            if missing_from_manifest:
                issues.append({"provider": provider, "code": "LOCAL_CONTENT_MANIFEST_MISMATCH", "severity": "error", "missing_count": len(missing_from_manifest), "missing_keys": missing_from_manifest[:25]})
        local_db_keys = set(str(x) for x in (local.get("db_content_keys") or []) if str(x))
        if expected_keys and local_db_keys:
            missing_from_db = sorted(expected_keys - local_db_keys)
            if missing_from_db:
                issues.append({"provider": provider, "code": "LOCAL_CONTENT_MISSING", "severity": "error", "missing_count": len(missing_from_db), "missing_keys": missing_from_db[:25]})
    return {"ok": not issues, "issue_count": len(issues), "issues": issues, "providers_checked": providers, "server_runs_checked": len(server_runs or []), "manifests_checked": len(local_manifests or [])}




def build_sync_repair_plan(reconciliation: dict, *, allow_resync: bool = True) -> dict:
    """Create a deterministic, safe repair plan from reconciliation issues.

    Only issues that can be repaired without inventing a cursor are scheduled for
    provider re-sync. Checkpoint corruption is inspected first and never mutated
    by this planner.
    """
    issues = reconciliation.get("issues", []) if isinstance(reconciliation, dict) else []
    by_provider = {}
    for issue in issues:
        if not isinstance(issue, dict):
            continue
        provider = str(issue.get("provider") or "").strip().lower()
        code = str(issue.get("code") or "")
        if not provider:
            continue
        item = by_provider.setdefault(provider, {"provider": provider, "codes": [], "actions": []})
        if code not in item["codes"]:
            item["codes"].append(code)
        if code in {"LOCAL_MANIFEST_MISSING", "LOCAL_RUN_MISMATCH", "LOCAL_RECEIVED_COUNT_MISMATCH", "LOCAL_PERSISTED_COUNT_SHORTFALL"} and allow_resync:
            if "resync_provider" not in item["actions"]:
                item["actions"].append("resync_provider")
        elif code in {"PENDING_CHECKPOINT", "LEGACY_CURSOR_WITHOUT_CHECKPOINT", "STATE_SUCCESS_CHECKPOINT_INTERRUPTED", "COMMITTED_WITHOUT_RUN_ID", "NEGATIVE_SEQUENCE"}:
            if "manual_review" not in item["actions"]:
                item["actions"].append("manual_review")
    repairs = list(by_provider.values())
    return {
        "version": 1,
        "safe": not any("manual_review" in x["actions"] for x in repairs),
        "requires_manual_review": [x["provider"] for x in repairs if "manual_review" in x["actions"]],
        "providers": repairs,
    }

def reconcile_sync_states(states: dict[str, dict], *, providers: list[str] | None = None) -> dict:
    """Detect checkpoint/state inconsistencies deterministically without contacting providers."""
    requested = [str(p).strip().lower() for p in (providers or sorted(states.keys())) if str(p).strip()]
    issues = []
    items = {}
    for provider in requested:
        state = states.get(provider) if isinstance(states, dict) else None
        cp = normalize_checkpoint(state)
        provider_issues = []
        if cp["status"] == "pending":
            provider_issues.append("PENDING_CHECKPOINT")
        if cp["status"] == "committed" and not cp["run_id"]:
            provider_issues.append("COMMITTED_WITHOUT_RUN_ID")
        if cp["sequence"] < 0:
            provider_issues.append("NEGATIVE_SEQUENCE")
        if state and state.get("status") == "success" and cp["status"] == "interrupted":
            provider_issues.append("STATE_SUCCESS_CHECKPOINT_INTERRUPTED")
        if provider in CHECKPOINT_CAPABLE_PROVIDERS and state and state.get("status") == "success" and cp["sequence"] == 0 and state.get("cursor"):
            provider_issues.append("LEGACY_CURSOR_WITHOUT_CHECKPOINT")
        items[provider] = {"status": "ok" if not provider_issues else "attention", "issues": provider_issues, "checkpoint": cp}
        for issue in provider_issues:
            issues.append({"provider": provider, "code": issue, "severity": "warning"})
    return {"version": 1, "ok": not issues, "issue_count": len(issues), "providers": items, "issues": issues}



DEFAULT_RETENTION_POLICY = {
    "sync_runs_days": 90,
    "sync_runs_max": 500,
    "sync_manifests_days": 90,
    "sync_manifests_max": 500,
    "sync_repairs_days": 180,
    "sync_repairs_max": 250,
}

def retention_policy(overrides: dict | None = None) -> dict:
    """Return bounded operational-retention settings; never targets business data."""
    result = dict(DEFAULT_RETENTION_POLICY)
    if isinstance(overrides, dict):
        for key in result:
            try:
                value = int(overrides.get(key, result[key]))
            except (TypeError, ValueError):
                continue
            result[key] = max(1, min(3650 if key.endswith("_days") else 10000, value))
    return result

def _retention_sort_key(item: dict) -> float:
    for key in ("started_at", "persisted_at", "created_at", "completed_at"):
        value = item.get(key)
        if value is not None:
            try: return float(value)
            except (TypeError, ValueError): pass
    return 0.0

def prune_operational_records(records: list[dict], *, now: float, days: int, max_records: int) -> tuple[list[dict], dict]:
    """Prune only operational history, preserving newest records and returning an audit summary."""
    cutoff = float(now) - max(1, int(days)) * 86400
    ordered = sorted([r for r in records if isinstance(r, dict)], key=_retention_sort_key, reverse=True)
    kept = []
    removed_by_age = 0
    removed_by_limit = 0
    for item in ordered:
        ts = _retention_sort_key(item)
        if ts and ts < cutoff:
            removed_by_age += 1
            continue
        if len(kept) >= max(1, int(max_records)):
            removed_by_limit += 1
            continue
        kept.append(item)
    return kept, {"before": len(records), "after": len(kept), "removed_by_age": removed_by_age, "removed_by_limit": removed_by_limit}

def prune_sync_runs(records: list[dict], *, now: float, policy: dict | None = None) -> tuple[list[dict], dict]:
    return prune_operational_records(records, now=now, days=retention_policy(policy)["sync_runs_days"], max_records=retention_policy(policy)["sync_runs_max"])

TRANSIENT_SYNC_ERRORS = {"NETWORK_ERROR", "HTTP_408", "HTTP_429", "HTTP_500", "HTTP_502", "HTTP_503", "HTTP_504"}

def is_transient_sync_error(exc: Exception) -> bool:
    code = str(getattr(exc, "code", "") or "")
    return code in TRANSIENT_SYNC_ERRORS or code.startswith("HTTP_5")

def retry_sync_call(call: Callable, *, attempts: int = 3, base_delay: float = 0.25, sleep: Callable = time.sleep):
    attempts = max(1, int(attempts))
    last = None
    for attempt in range(1, attempts + 1):
        try:
            return call(), attempt
        except Exception as exc:
            last = exc
            if attempt >= attempts or not is_transient_sync_error(exc):
                raise
            sleep(base_delay * (2 ** (attempt - 1)))
    raise last

def canonical_external_id(provider: str, external_id: str, fallback_text: str = "") -> str:
    provider = str(provider or "unknown").strip().lower()
    external_id = str(external_id or "").strip()
    if external_id:
        return f"{provider}:{external_id}"
    digest = hashlib.sha256(str(fallback_text or "").strip().encode("utf-8")).hexdigest()[:24]
    return f"{provider}:hash:{digest}"


def deduplicate_rows(rows: list[dict]) -> tuple[list[dict], int]:
    unique = {}
    duplicates = 0
    for row in rows or []:
        key = str(row.get("id_mencion") or "").strip()
        if not key:
            key = hashlib.sha256(json.dumps(row, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
            row = {**row, "id_mencion": f"row:{key[:24]}"}
        if key in unique:
            duplicates += 1
            continue
        unique[key] = row
    return list(unique.values()), duplicates


def merge_sync_state(previous: dict | None, *, status: str, source_count: int = 0, duplicate_count: int = 0, error: str = "", cursor: str = "") -> dict:
    previous = previous or {}
    now = time.time()
    return {
        **previous,
        "status": status,
        "last_sync_at": now if status == "success" else previous.get("last_sync_at"),
        "last_attempt_at": now,
        "source_count": int(source_count),
        "duplicate_count": int(duplicate_count),
        "error": error or "",
        "cursor": cursor or previous.get("cursor", ""),
        "version": 3,
    }


def freshness_status(state: dict | None, *, now: float | None = None, interval_minutes: int = 30) -> dict:
    """Return deterministic freshness metadata without exposing credentials."""
    state = state or {}
    now = time.time() if now is None else float(now)
    interval = max(5, int(interval_minutes or 30)) * 60
    last = state.get("last_sync_at")
    if not last:
        return {"status": "never", "age_seconds": None, "threshold_seconds": interval, "last_sync_at": None}
    try:
        age = max(0.0, now - float(last))
    except (TypeError, ValueError):
        return {"status": "unknown", "age_seconds": None, "threshold_seconds": interval, "last_sync_at": last}
    if state.get("status") == "error":
        status = "error"
    elif age <= interval:
        status = "fresh"
    elif age <= interval * 2:
        status = "warning"
    else:
        status = "stale"
    return {
        "status": status,
        "age_seconds": round(age, 3),
        "threshold_seconds": interval,
        "last_sync_at": float(last),
    }

def build_sync_health(states: dict[str, dict], *, now: float | None = None, interval_minutes: int = 30, providers: list[str] | None = None) -> dict:
    requested = providers or sorted(states.keys())
    items = {}
    for provider in requested:
        items[str(provider)] = freshness_status(states.get(provider), now=now, interval_minutes=interval_minutes)
    statuses = [x["status"] for x in items.values()]
    if any(x == "error" for x in statuses):
        overall = "error"
    elif any(x == "stale" for x in statuses):
        overall = "stale"
    elif any(x == "warning" for x in statuses):
        overall = "warning"
    elif any(x == "fresh" for x in statuses):
        overall = "fresh"
    else:
        overall = "never"
    return {"version": 1, "overall": overall, "interval_minutes": max(5, int(interval_minutes or 30)), "providers": items}




def build_sync_alerts(health: dict) -> list[dict]:
    """Build deterministic, actionable alerts from synchronization health."""
    alerts = []
    for provider, item in (health.get("providers") or {}).items():
        status = item.get("status")
        if status == "error":
            alerts.append({"id": f"sync:{provider}:error", "provider": provider, "severity": "error", "status": status, "message": "La última sincronización terminó con error.", "action": "retry"})
        elif status == "stale":
            alerts.append({"id": f"sync:{provider}:stale", "provider": provider, "severity": "warning", "status": status, "message": "La fuente está atrasada respecto a la política de frescura.", "action": "sync"})
        elif status == "warning":
            alerts.append({"id": f"sync:{provider}:warning", "provider": provider, "severity": "info", "status": status, "message": "La fuente se acerca al límite de frescura.", "action": "sync"})
        elif status == "never":
            alerts.append({"id": f"sync:{provider}:never", "provider": provider, "severity": "info", "status": status, "message": "La fuente todavía no tiene una sincronización exitosa registrada.", "action": "sync"})
    return alerts


def _redact_diagnostic_text(value: object) -> str:
    text = str(value or "")
    import re
    text = re.sub(r"(?i)(access[_ -]?token|refresh[_ -]?token|client[_ -]?secret|api[_ -]?key|secret|authorization)\s*[:=]\s*(?:bearer\s+)?[^,;\s]+", r"\1=[REDACTED]", text)
    text = re.sub(r"(?i)bearer\s+[^,;\s]+", "Bearer [REDACTED]", text)
    return text[:500]


def build_sync_diagnostic_report(states: dict[str, dict], runs: list[dict], *, now: float | None = None, interval_minutes: int = 30, providers: list[str] | None = None) -> dict:
    """Build a shareable operational report with secrets excluded by construction."""
    health = build_sync_health(states, now=now, interval_minutes=interval_minutes, providers=providers)
    alerts = build_sync_alerts(health)
    safe_runs = []
    for run in list(reversed(runs or []))[:10]:
        safe = {
            "run_id": run.get("run_id"), "started_at": run.get("started_at"),
            "finished_at": run.get("finished_at"), "duration_ms": run.get("duration_ms"),
            "status": run.get("status"), "requested_providers": run.get("requested_providers", []),
            "source_count": run.get("source_count", 0), "duplicate_count": run.get("duplicate_count", 0),
            "retry_count": run.get("retry_count", 0),
            "providers": []
        }
        for item in run.get("providers", []) or []:
            safe["providers"].append({
                "provider": item.get("provider"), "ok": bool(item.get("ok")),
                "source_count": item.get("source_count", 0), "duplicate_count": item.get("duplicate_count", 0),
                "retry_count": item.get("retry_count", 0), "content_keys": list(item.get("content_keys") or [])[:2000],
                "error": _redact_diagnostic_text(item.get("error", "")) if item.get("error") else ""
            })
        safe_runs.append(safe)
    return {
        "version": 1, "generated_at": float(time.time() if now is None else now),
        "scope": "sync-operational-diagnostic", "health": health, "alerts": alerts,
        "recent_runs": safe_runs, "providers": list(providers or sorted(states.keys())),
        "security": {"secrets_included": False, "tokens_included": False, "credential_payloads_included": False}
    }

def load_state(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        import os
        os.chmod(path, 0o600)
    except OSError:
        pass


def build_sync_run(run_id: str, started_at: float, finished_at: float, requested_providers: list[str], results: list[dict], failures: list[dict]) -> dict:
    status = "success" if not failures else ("partial" if any(bool(x.get("ok")) for x in results) else "error")
    return {
        "run_id": str(run_id),
        "started_at": float(started_at),
        "finished_at": float(finished_at),
        "duration_ms": round(max(0.0, finished_at - started_at) * 1000),
        "status": status,
        "requested_providers": [str(x) for x in requested_providers],
        "providers": results,
        "failure_count": len(failures),
        "source_count": sum(int(x.get("source_count") or 0) for x in results),
        "duplicate_count": sum(int(x.get("duplicate_count") or 0) for x in results),
        "retry_count": sum(int(x.get("retry_count") or 0) for x in results),
    }
