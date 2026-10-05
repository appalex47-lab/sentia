"""Local secure bridge for Sentia integrations.

The browser can configure public Meta values. Client secrets and OAuth tokens
never cross into the browser and are held by this Python process. The OAuth
state is server-bound and short-lived. Tokens are persisted only in the encrypted
Python-side token store; secrets never cross into browser storage.
"""
from __future__ import annotations

import json
import os
import html
import secrets
import time
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
from email.parser import BytesParser
from email.policy import default

from .pipeline.orchestrator import Pipeline, PipelineConfig
from .token_store import delete as delete_token_store, load as load_token_store, save as save_token_store
from .manual_ingest import parse_manual
from .pipeline.ai import CohereService, AIServiceError
from .pipeline.knowledge import search_knowledge
from .pipeline.sync import canonical_external_id, deduplicate_rows, load_state, merge_sync_state, save_state, build_sync_run, retry_sync_call, build_sync_health, build_sync_alerts, build_sync_diagnostic_report, begin_checkpoint, commit_checkpoint, abandon_checkpoint, reconcile_sync_states, reconcile_local_manifests, build_sync_repair_plan, retention_policy, prune_sync_runs, prune_operational_records, DEFAULT_RETENTION_POLICY
from .connectors.google_analytics import (
    DEFAULT_REDIRECT_URI as GA4_DEFAULT_REDIRECT_URI,
    DEFAULT_SCOPES as GA4_DEFAULT_SCOPES,
    GoogleAnalyticsConnector,
    GoogleAnalyticsError,
    load_public_config as load_ga4_public_config,
    save_public_config as save_ga4_public_config,
)
from .connectors.social import XConnector, TikTokConnector, YouTubeConnector, LinkedInConnector, SocialConnectorError, public_config as save_social_public_config
from .connectors.meta import (
    DEFAULT_GRAPH_VERSION,
    MetaConnector,
    load_public_config,
    save_public_config,
)

HOST = os.getenv("SENTIA_CONNECTOR_HOST", "127.0.0.1")
PORT = int(os.getenv("SENTIA_CONNECTOR_PORT", "8787"))
ALLOWED_ORIGINS = tuple(x.strip() for x in os.getenv(
    "SENTIA_ALLOWED_ORIGINS",
    "http://localhost,http://127.0.0.1,https://*.github.io"
).split(",") if x.strip())
CONFIG_PATH = os.getenv("SENTIA_CONNECTOR_CONFIG", str(os.path.join(os.path.dirname(__file__), "runtime", "integrations.json")))
TOKEN_PATH = Path(os.getenv("SENTIA_TOKEN_STORE", str(Path(__file__).resolve().parent / "runtime" / "tokens.enc")))

PENDING_STATES: dict[str, float] = {}
TOKENS: dict[str, dict] = {}
LAST_SYNC: dict[str, dict] = {}
GA4_STATES: dict[str, float] = {}

SOCIAL_STATES: dict[str, dict] = {}
SOCIAL_LAST_SYNC: dict[str, dict] = {}
SYNC_STATE_PATH = Path(os.getenv("SENTIA_SYNC_STATE", str(Path(__file__).resolve().parent / "runtime" / "sync_state.json")))
SYNC_STATE: dict[str, dict] = load_state(SYNC_STATE_PATH)
SYNC_RUNS_PATH = Path(os.getenv("SENTIA_SYNC_RUNS", str(Path(__file__).resolve().parent / "runtime" / "sync_runs.json")))
_sync_runs_saved = load_state(SYNC_RUNS_PATH)
SYNC_RUNS: list[dict] = _sync_runs_saved.get("runs", []) if isinstance(_sync_runs_saved, dict) else []

RETENTION_POLICY = retention_policy({
    "sync_runs_days": os.getenv("SENTIA_SYNC_RUNS_RETENTION_DAYS", DEFAULT_RETENTION_POLICY["sync_runs_days"]),
    "sync_runs_max": os.getenv("SENTIA_SYNC_RUNS_RETENTION_MAX", DEFAULT_RETENTION_POLICY["sync_runs_max"]),
})

def apply_runtime_retention(*, dry_run: bool = False, policy: dict | None = None) -> dict:
    """Prune only operational server history; never mentions, tokens, configs or business data."""
    global SYNC_RUNS
    effective = retention_policy({**RETENTION_POLICY, **(policy or {})})
    before = list(SYNC_RUNS)
    kept, runs_report = prune_sync_runs(before, now=time.time(), policy=effective)
    report = {"version": 1, "safe_scope": ["sync_runs"], "dry_run": bool(dry_run), "policy": effective, "sync_runs": runs_report}
    if not dry_run:
        SYNC_RUNS = kept
        persist_sync_run_list()
    return report

def persist_sync_run_list():
    save_state(SYNC_RUNS_PATH, {"runs": SYNC_RUNS[-500:]})

SYNC_LOCK = threading.Lock()

def social_config(provider: str) -> dict:
    path = Path(CONFIG_PATH).with_name(f"{provider}.json")
    try: return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, json.JSONDecodeError): return {}

def social_connector(provider: str):
    c=social_config(provider)
    if provider=="x": return XConnector(c.get("clientId","") or os.getenv("X_CLIENT_ID",""), c.get("redirectUri","") or os.getenv("X_REDIRECT_URI",f"http://127.0.0.1:{PORT}/api/integrations/x/callback"), c.get("scopes","") or os.getenv("X_SCOPES","tweet.read users.read offline.access"))
    if provider=="tiktok": return TikTokConnector(c.get("clientKey","") or os.getenv("TIKTOK_CLIENT_KEY",""), c.get("redirectUri","") or os.getenv("TIKTOK_REDIRECT_URI",f"http://127.0.0.1:{PORT}/api/integrations/tiktok/callback"), c.get("scopes","") or os.getenv("TIKTOK_SCOPES","user.info.basic,video.list"))
    if provider=="youtube": return YouTubeConnector(c.get("clientId","") or os.getenv("GOOGLE_CLIENT_ID",""), c.get("redirectUri","") or os.getenv("YOUTUBE_REDIRECT_URI",f"http://127.0.0.1:{PORT}/api/integrations/youtube/callback"), c.get("scopes","") or os.getenv("YOUTUBE_SCOPES","https://www.googleapis.com/auth/youtube.readonly"))
    if provider=="linkedin": return LinkedInConnector(c.get("clientId","") or os.getenv("LINKEDIN_CLIENT_ID",""), c.get("redirectUri","") or os.getenv("LINKEDIN_REDIRECT_URI",f"http://127.0.0.1:{PORT}/api/integrations/linkedin/callback"), c.get("scopes","") or os.getenv("LINKEDIN_SCOPES","openid profile email r_organization_social"), os.getenv("LINKEDIN_VERSION","202609"))
    raise ValueError("SOCIAL_PROVIDER_UNSUPPORTED")

def social_secret(provider):
    return {"x":os.getenv("X_CLIENT_SECRET",""),"tiktok":os.getenv("TIKTOK_CLIENT_SECRET",""),"youtube":os.getenv("GOOGLE_CLIENT_SECRET",""),"linkedin":os.getenv("LINKEDIN_CLIENT_SECRET","")}.get(provider,"")

def social_ready(provider):
    c=social_connector(provider); missing=[]
    if not getattr(c,"client_id",getattr(c,"client_key", "")): missing.append("CLIENT_ID_OR_KEY")
    if not getattr(c,"redirect_uri",""): missing.append("REDIRECT_URI")
    if provider=="tiktok" and not social_secret(provider): missing.append("TIKTOK_CLIENT_SECRET")
    if provider=="youtube" and not (social_secret(provider) or os.getenv("YOUTUBE_API_KEY")): missing.append("GOOGLE_CLIENT_SECRET_OR_YOUTUBE_API_KEY")
    if provider=="linkedin" and not social_secret(provider): missing.append("LINKEDIN_CLIENT_SECRET")
    return missing

def social_access_token(provider):
    token=TOKENS.get(provider) or {}; access=token.get("access_token","")
    if access and float(token.get("expires_at",0) or 0)>time.time()+60:return access
    refresh=token.get("refresh_token","")
    if not refresh:return access
    c=social_connector(provider); sec=social_secret(provider)
    payload=c.refresh(refresh,sec)
    token.update({"access_token":payload.get("access_token",access),"expires_at":time.time()+int(payload.get("expires_in",3600))})
    TOKENS[provider]=token; persist_tokens(); return token.get("access_token","")

def social_to_mentions(provider, payload):
    rows=[]
    if provider=="x":
        users={u.get("id"):u for u in payload.get("includes",{}).get("users",[])}
        for x in payload.get("data",[]):
            rows.append({"id_mencion":canonical_external_id("x", x.get("id"), x.get("text", "")),"fecha":x.get("created_at") or time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"fuente":"x","texto_original":x.get("text","")})
    elif provider=="tiktok":
        for v in payload.get("data",{}).get("videos",[]):
            text=(v.get("title") or "").strip() + (" " + (v.get("video_description") or "").strip() if v.get("video_description") else "")
            if text.strip(): rows.append({"id_mencion":canonical_external_id("tiktok", v.get("id"), text.strip()),"fecha":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime(int(v.get('create_time',0) or 0))) if v.get('create_time') else time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"fuente":"tiktok","texto_original":text.strip()})
    elif provider=="youtube":
        for item in payload.get("comments",[]):
            sn=item.get("snippet",{}).get("topLevelComment",{}).get("snippet",{})
            if sn.get("textDisplay"): rows.append({"id_mencion":canonical_external_id("youtube", item.get("id"), sn.get("textDisplay", "")),"fecha":sn.get("publishedAt") or time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"fuente":"youtube","texto_original":sn.get("textDisplay","")})
    elif provider=="linkedin":
        for item in payload.get("comments",[]):
            text=item.get("message",{}).get("text") or item.get("commentary") or ""
            external_id=item.get("id") or item.get("urn") or item.get("commentUrn")
            if text: rows.append({"id_mencion":canonical_external_id("linkedin-comment", external_id, text),"fecha":item.get("created", "") or time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"fuente":"linkedin","texto_original":text})
        for item in payload.get("posts",{}).get("elements",[]):
            text=item.get("commentary") or ""
            external_id=item.get("id") or item.get("urn")
            if text: rows.append({"id_mencion":canonical_external_id("linkedin-post", external_id, text),"fecha":item.get("created", "") or time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"fuente":"linkedin","texto_original":text})
    return rows

def persist_sync(provider: str, state: dict) -> None:
    SYNC_STATE[provider] = state
    save_state(SYNC_STATE_PATH, SYNC_STATE)


def fetch_comments_parallel(fetcher, identifiers: list[str], *, item_key: str = "items") -> list[dict]:
    """Fetch independent comment pages concurrently with a small bounded pool.

    Ordering follows the source identifier order, and individual comment failures
    remain non-fatal just as in the sequential implementation. This improves
    latency without changing provider semantics or retry policy.
    """
    ids = [str(x) for x in identifiers if str(x)]
    if not ids:
        return []
    try:
        workers = max(1, min(4, int(os.getenv("SENTIA_SYNC_COMMENT_WORKERS", "3"))))
    except (TypeError, ValueError):
        workers = 3
    results = {}
    with ThreadPoolExecutor(max_workers=min(workers, len(ids))) as executor:
        futures = {executor.submit(fetcher, identifier): (index, identifier) for index, identifier in enumerate(ids)}
        for future in as_completed(futures):
            index, _identifier = futures[future]
            try:
                payload = future.result()
                values = payload.get(item_key, []) if isinstance(payload, dict) else []
                results[index] = values if isinstance(values, list) else []
            except Exception:
                results[index] = []
    merged = []
    for index in range(len(ids)):
        merged.extend(results.get(index, []))
    return merged


def sync_payload_result(provider: str, rows: list[dict], *, cursor: str = "", run_id: str = "", page: int = 0) -> tuple[dict, int, int]:
    unique, duplicates = deduplicate_rows(rows)
    result = Pipeline(PipelineConfig()).run(unique) if unique else Pipeline(PipelineConfig()).run([])
    previous = SYNC_STATE.get(provider)
    if run_id:
        # Two-phase persistence: keep the new cursor pending until the browser
        # explicitly confirms that the payload was written to IndexedDB.
        cp = begin_checkpoint(previous, run_id=run_id, cursor=cursor, page=page)
        state = merge_sync_state(previous, status="awaiting_persistence", source_count=len(unique), duplicate_count=duplicates, cursor=str((previous or {}).get("cursor") or ""))
        state["checkpoint"] = cp
    else:
        state = merge_sync_state(previous, status="success", source_count=len(unique), duplicate_count=duplicates, cursor=cursor)
    persist_sync(provider, state)
    return result, len(unique), duplicates


def confirm_sync_persistence(provider: str, run_id: str, persisted_count: int, content_keys: list[str]) -> dict:
    provider = str(provider or "").strip().lower()
    run_id = str(run_id or "").strip()
    state = SYNC_STATE.get(provider) or {}
    cp = state.get("checkpoint") if isinstance(state.get("checkpoint"), dict) else {}
    if not run_id or cp.get("run_id") != run_id or cp.get("status") != "pending":
        raise ValueError("SYNC_PERSISTENCE_CONFIRMATION_INVALID")
    run = next((r for r in reversed(SYNC_RUNS) if str(r.get("run_id") or "") == run_id), None)
    if not run:
        raise ValueError("SYNC_RUN_NOT_FOUND")
    expected = next((x for x in run.get("providers", []) if str(x.get("provider") or "").lower() == provider and x.get("ok")), None)
    if not expected:
        raise ValueError("SYNC_PROVIDER_RESULT_NOT_FOUND")
    expected_keys = {str(x) for x in (expected.get("content_keys") or []) if str(x)}
    actual_keys = {str(x) for x in (content_keys or []) if str(x)}
    if expected_keys != actual_keys:
        raise ValueError("SYNC_CONTENT_CONFIRMATION_MISMATCH")
    if int(persisted_count or 0) < int(expected.get("source_count") or 0):
        raise ValueError("SYNC_PERSISTED_COUNT_SHORTFALL")
    cursor = str(expected.get("cursor") or cp.get("pending_cursor") or "")
    page = int(expected.get("page") or cp.get("page") or 0)
    committed = commit_checkpoint(state, run_id=run_id, cursor=cursor, page=page)
    next_state = merge_sync_state(state, status="success", source_count=int(expected.get("source_count") or 0), duplicate_count=int(expected.get("duplicate_count") or 0), cursor=cursor)
    next_state["checkpoint"] = committed
    next_state["persistence_confirmed_at"] = time.time()
    persist_sync(provider, next_state)
    return {"provider": provider, "run_id": run_id, "status": "committed", "cursor": cursor, "sequence": committed.get("sequence", 0)}


def sync_status_payload() -> dict:
    providers = {k: dict(v) for k, v in SYNC_STATE.items()}
    return {"version": 1, "providers": providers, "last_run": SYNC_RUNS[-1] if SYNC_RUNS else None}

def persist_sync_run(run: dict) -> None:
    global SYNC_RUNS
    SYNC_RUNS = (SYNC_RUNS + [run])[-50:]
    save_state(SYNC_RUNS_PATH, {"version": 1, "runs": SYNC_RUNS})

def sync_runs_payload(limit: int = 20) -> dict:
    safe_limit = max(1, min(int(limit or 20), 50))
    return {"version": 1, "runs": list(reversed(SYNC_RUNS[-safe_limit:]))}


def restore_tokens() -> None:
    saved = load_token_store(TOKEN_PATH)
    if saved and isinstance(saved.get("meta"), dict):
        TOKENS["meta"] = saved["meta"]
    if saved and isinstance(saved.get("cohere"), dict):
        TOKENS["cohere"] = saved["cohere"]
    if saved and isinstance(saved.get("ga4"), dict): TOKENS["ga4"] = saved["ga4"]
    for provider in ("x","tiktok","youtube","linkedin"):
        if saved and isinstance(saved.get(provider), dict): TOKENS[provider] = saved[provider]

def persist_tokens() -> None:
    save_token_store(TOKEN_PATH, {
        "meta": TOKENS.get("meta", {}),
        "cohere": TOKENS.get("cohere", {}),
        "ga4": TOKENS.get("ga4", {}),
        **{p: TOKENS.get(p, {}) for p in ("x","tiktok","youtube","linkedin")},
    })


def cohere_service() -> CohereService:
    record = TOKENS.get("cohere") or {}
    key = record.get("api_key") or os.getenv("COHERE_API_KEY", "")
    model = record.get("model") or os.getenv("COHERE_MODEL") or None
    if not key:
        raise AIServiceError("AI_AUTH_ERROR", "COHERE_API_KEY_MISSING")
    return CohereService(api_key=key, model=model)


def current_meta_config() -> dict:
    saved = load_public_config(__import__("pathlib").Path(CONFIG_PATH))
    return {
        "app_id": saved.get("app_id") or os.getenv("META_APP_ID", ""),
        "redirect_uri": saved.get("redirect_uri") or os.getenv("META_REDIRECT_URI", f"http://127.0.0.1:{PORT}/api/integrations/meta/callback"),
        "scopes": saved.get("scopes") or os.getenv("META_SCOPES", "pages_show_list,pages_read_engagement,instagram_basic"),
        "graph_version": saved.get("graph_version") or os.getenv("META_GRAPH_VERSION", DEFAULT_GRAPH_VERSION),
    }


def meta_from_config() -> MetaConnector:
    cfg = current_meta_config()
    return MetaConnector(cfg["app_id"], cfg["redirect_uri"], cfg["scopes"], cfg["graph_version"])



def current_ga4_config() -> dict:
    saved = load_ga4_public_config(Path(CONFIG_PATH).with_name("ga4.json"))
    return {
        "client_id": saved.get("client_id") or os.getenv("GOOGLE_CLIENT_ID", ""),
        "project_id": saved.get("project_id") or os.getenv("GOOGLE_CLOUD_PROJECT_ID", ""),
        "property_id": saved.get("property_id") or os.getenv("GA4_PROPERTY_ID", ""),
        "redirect_uri": saved.get("redirect_uri") or os.getenv("GA4_REDIRECT_URI", GA4_DEFAULT_REDIRECT_URI),
        "scopes": saved.get("scopes") or os.getenv("GA4_SCOPES", GA4_DEFAULT_SCOPES),
    }

def ga4_from_config() -> GoogleAnalyticsConnector:
    cfg = current_ga4_config()
    return GoogleAnalyticsConnector(cfg["client_id"], cfg["redirect_uri"], cfg["scopes"])

def ga4_access_token() -> str:
    token = TOKENS.get("ga4") or {}
    access_token = token.get("access_token", "")
    expires_at = float(token.get("expires_at", 0) or 0)
    if access_token and expires_at > time.time() + 60:
        return access_token
    refresh_token = token.get("refresh_token", "")
    if not refresh_token:
        return access_token
    payload = ga4_from_config().refresh_access_token(refresh_token)
    token["access_token"] = payload["access_token"]
    token["expires_at"] = time.time() + int(payload.get("expires_in", 3600))
    TOKENS["ga4"] = token
    persist_tokens()
    return token["access_token"]


def token_record() -> dict | None:
    token = TOKENS.get("meta")
    return token if token and token.get("access_token") else None


def selected_config() -> dict:
    return load_public_config(__import__("pathlib").Path(CONFIG_PATH))


def cleanup_states() -> None:
    now = time.time()
    for state, created in list(PENDING_STATES.items()):
        if now - created > 600:
            PENDING_STATES.pop(state, None)
    for state, created in list(GA4_STATES.items()):
        if now - created > 600: GA4_STATES.pop(state, None)
    for state, rec in list(SOCIAL_STATES.items()):
        if now - rec.get("created", now) > 600: SOCIAL_STATES.pop(state, None)


def _read_multipart_audio(handler, max_bytes=25 * 1024 * 1024):
    content_type = handler.headers.get("Content-Type", "")
    if not content_type.lower().startswith("multipart/form-data"):
        raise ValueError("AUDIO_MULTIPART_REQUIRED")
    length = int(handler.headers.get("Content-Length", "0"))
    if length > max_bytes + 2 * 1024 * 1024:
        raise ValueError("AUDIO_REQUEST_TOO_LARGE")
    body = handler.rfile.read(length)
    header = ("Content-Type: " + content_type + "\r\nMIME-Version: 1.0\r\n\r\n").encode()
    message = BytesParser(policy=default).parsebytes(header + body)
    if not message.is_multipart():
        raise ValueError("AUDIO_MULTIPART_INVALID")
    for part in message.iter_parts():
        if part.get_param("name", header="content-disposition") == "file":
            data = part.get_payload(decode=True) or b""
            if len(data) > max_bytes:
                raise ValueError("AI_AUDIO_TOO_LARGE")
            return data, part.get_filename() or "audio.wav", part.get_content_type()
    raise ValueError("AUDIO_FILE_MISSING")


def _origin_allowed(origin: str) -> bool:
    if not origin:
        return True
    origin = origin.rstrip("/")
    parsed_origin = urlparse(origin)
    if not parsed_origin.scheme or not parsed_origin.hostname:
        return False
    for allowed in ALLOWED_ORIGINS:
        allowed = allowed.rstrip("/")
        parsed_allowed = urlparse(allowed)
        if parsed_allowed.scheme != parsed_origin.scheme:
            continue
        if "*" in allowed:
            allowed_prefix, allowed_suffix = allowed.split("*", 1)
            if origin.startswith(allowed_prefix) and origin.endswith(allowed_suffix):
                wildcard_host = urlparse(origin).hostname or ""
                suffix_host = allowed_suffix.lstrip(".")
                if suffix_host and wildcard_host.endswith("." + suffix_host):
                    return True
            continue
        if parsed_allowed.hostname != parsed_origin.hostname:
            continue
        # A base local origin intentionally permits its development ports.
        if parsed_allowed.port is None:
            return True
        if parsed_allowed.port == parsed_origin.port:
            return True
    return False


class Handler(BaseHTTPRequestHandler):
    def _request_origin(self) -> str:
        return self.headers.get("Origin", "").strip()

    def _origin_guard(self) -> bool:
        origin = self._request_origin()
        if _origin_allowed(origin):
            return True
        self._json(403, {"error": "ORIGIN_NOT_ALLOWED"})
        return False

    def _json(self, status: int, payload: dict):
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        origin = self._request_origin()
        if origin and _origin_allowed(origin):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Accept, Content-Type")
        self._security_headers()
        self.end_headers()
        self.wfile.write(raw)

    def _security_headers(self):
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; frame-ancestors 'none'")

    def _html(self, status: int, title: str, message: str):
        safe_title = html.escape(str(title), quote=True)
        safe_message = html.escape(str(message), quote=True)
        body = f"<!doctype html><meta charset='utf-8'><title>{safe_title}</title><main style='font:16px system-ui;max-width:700px;margin:12vh auto;padding:24px'><h1>{safe_title}</h1><p>{safe_message}</p><p>Puedes cerrar esta ventana y volver a Sentia.</p></main>"
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self._security_headers()
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def do_OPTIONS(self):
        origin = self._request_origin()
        if not _origin_allowed(origin):
            self._json(403, {"error": "ORIGIN_NOT_ALLOWED"})
            return
        self.send_response(204)
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Accept, Content-Type")
        self.end_headers()

    def _read_json(self, max_bytes=12 * 1024 * 1024):
        length = int(self.headers.get("Content-Length", "0"))
        if length > max_bytes:
            raise ValueError("REQUEST_TOO_LARGE")
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_POST(self):
        if not self._origin_guard():
            return
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/ingest/audio":
                audio_bytes, filename, mime = _read_multipart_audio(self)
                language = "es"
                query = parse_qs(urlparse(self.path).query)
                language = str(query.get("language", ["es"])[0]).strip().lower() or "es"
                result = cohere_service().transcribe_audio(audio_bytes, filename, language=language)
                row = {
                    "id_mencion": "audio-" + secrets.token_hex(8),
                    "fecha": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "fuente": "llamada_audio",
                    "texto_original": result["text"],
                    "texto_traducido": "",
                    "idioma_origen": language,
                    "idioma_analisis": "es",
                    "metodo_traduccion": "no_aplicado",
                    "speaker": "",
                }
                pipeline = Pipeline(PipelineConfig()).run([row])
                self._json(200, {"payload": pipeline, "transcription": result, "source_count": 1})
                return

            if parsed.path == "/api/ingest/manual":
                payload = self._read_json()
                filename = str(payload.get("filename", "manual.txt"))
                content = str(payload.get("content", ""))
                source_type = str(payload.get("source_type", "txt"))
                source = str(payload.get("source", source_type)).strip() or source_type
                rows = parse_manual(filename, content, source_type, source=source, conversation_id=str(payload.get("conversation_id", "")).strip() or None)
                language = str(payload.get("analysis_language", "es")).strip() or "es"
                auto_translate = bool(payload.get("auto_translate", False))
                for row in rows:
                    row["fuente"] = source
                    row["idioma_analisis"] = language
                    if row.get("texto_traducido"):
                        row["metodo_traduccion"] = "archivo_proporcionado"
                if auto_translate:
                    service = cohere_service()
                    translated = service.translate_rows(rows, target_language=language)
                    rows = translated["rows"]
                result = Pipeline(PipelineConfig()).run(rows)
                self._json(200, {"payload": result, "source_type": source_type, "source_count": len(rows), "translation": {"automatic": auto_translate, "analysis_language": language}})
                return

            if parsed.path == "/api/integrations/ga4/config":
                payload = self._read_json(64 * 1024)
                cfg = save_ga4_public_config(Path(CONFIG_PATH).with_name("ga4.json"), payload)
                self._json(200, {"provider": "ga4", "configured": bool(cfg["client_id"]), "property_id": cfg["property_id"], "redirect_uri": cfg["redirect_uri"], "scopes": cfg["scopes"]})
                return

            if parsed.path == "/api/integrations/ga4/report":
                payload = self._read_json(64 * 1024)
                token = TOKENS.get("ga4") or {}
                access_token = ga4_access_token()
                if not access_token:
                    self._json(401, {"error": "GA4_NOT_CONNECTED"}); return
                cfg = current_ga4_config()
                result = ga4_from_config().run_report(
                    access_token, str(payload.get("property_id") or cfg.get("property_id", "")),
                    str(payload.get("start_date", "")), str(payload.get("end_date", "")),
                    payload.get("dimensions"), payload.get("metrics"), payload.get("limit", 1000)
                )
                LAST_SYNC["ga4"] = {"at": time.time(), "property_id": result["property_id"], "row_count": result["row_count"]}
                self._json(200, {"ok": True, "report": result, "synced_at": LAST_SYNC["ga4"]["at"]})
                return

            if parsed.path.startswith("/api/integrations/") and parsed.path.endswith("/config"):
                provider=parsed.path.split("/")[3]
                if provider in {"x","tiktok","youtube","linkedin"}:
                    payload=self._read_json(64*1024); cfg=save_social_public_config(Path(CONFIG_PATH).with_name(f"{provider}.json"),payload); self._json(200,{"provider":provider,"saved":True,"missing":social_ready(provider)}); return
            if parsed.path.startswith("/api/integrations/") and parsed.path.endswith("/ingest"):
                provider=parsed.path.split("/")[3]
                if provider in {"x","tiktok","youtube","linkedin"}:
                    token=social_access_token(provider)
                    if not token and provider!="youtube": self._json(401,{"error":f"{provider.upper()}_NOT_CONNECTED"}); return
                    c=social_connector(provider); payload={};
                    if provider=="x": payload=c.recent(token,str(self._read_json(128*1024).get("query","")).strip(),100)
                    elif provider=="tiktok": payload=c.videos(token,20)
                    elif provider=="youtube":
                        body=self._read_json(64*1024); channel=body.get("channel_id") or social_config(provider).get("channelId")
                        if not channel: self._json(400,{"error":"YOUTUBE_CHANNEL_ID_REQUIRED"}); return
                        vids=c.videos(token,channel,20,os.getenv("YOUTUBE_API_KEY","")); comments=[]
                        for v in vids.get("items",[]):
                            vid=v.get("snippet",{}).get("resourceId",{}).get("videoId");
                            if vid:
                                try: comments.extend(c.comments(token,vid,100,os.getenv("YOUTUBE_API_KEY","" )).get("items",[]))
                                except SocialConnectorError: pass
                        payload={"videos":vids,"comments":comments}
                    else:
                        body=self._read_json(64*1024); org=body.get("organization_id") or social_config(provider).get("organizationId")
                        if not org: self._json(400,{"error":"LINKEDIN_ORGANIZATION_ID_REQUIRED"}); return
                        posts=c.posts(token,org,100); comments=[]
                        for post in posts.get("elements",[]):
                            urn=post.get("id")
                            if urn:
                                try: comments.extend(c.comments(token,urn,100).get("elements",[]))
                                except SocialConnectorError: pass
                        payload={"posts":posts,"comments":comments}
                    rows=social_to_mentions(provider,payload); result,count,duplicates=sync_payload_result(provider,rows)
                    SOCIAL_LAST_SYNC[provider]={"at":time.time(),"source_count":count,"duplicate_count":duplicates}; self._json(200,{"ok":True,"payload":result,"source_count":count,"duplicate_count":duplicates,"synced_at":SOCIAL_LAST_SYNC[provider]["at"]}); return
            if parsed.path == "/api/sync/reconcile":
                body = self._read_json(256 * 1024)
                providers = [str(x).strip().lower() for x in (body.get("providers") or ["x", "tiktok", "youtube", "linkedin"]) if str(x).strip()]
                base = reconcile_sync_states(SYNC_STATE, providers=providers)
                manifests = body.get("local_manifests") if isinstance(body.get("local_manifests"), list) else []
                local = reconcile_local_manifests(SYNC_RUNS, manifests, providers=providers)
                all_issues = list(base.get("issues", [])) + list(local.get("issues", []))
                base["ok"] = not all_issues
                base["issue_count"] = len(all_issues)
                base["issues"] = all_issues
                base["local_reconciliation"] = local
                base["repair_plan"] = build_sync_repair_plan(base, allow_resync=True)
                self._json(200, base); return

            if parsed.path == "/api/sync/confirm-persistence":
                body = self._read_json(256 * 1024)
                try:
                    result = confirm_sync_persistence(str(body.get("provider") or ""), str(body.get("run_id") or ""), int(body.get("persisted_count") or 0), body.get("content_keys") if isinstance(body.get("content_keys"), list) else [])
                except ValueError as exc:
                    self._json(409, {"ok": False, "error": str(exc)}); return
                self._json(200, {"ok": True, **result}); return

            if parsed.path == "/api/sync/repair-plan":
                body = self._read_json(256 * 1024)
                reconciliation = body.get("reconciliation") if isinstance(body.get("reconciliation"), dict) else {}
                self._json(200, build_sync_repair_plan(reconciliation, allow_resync=True)); return

            if parsed.path == "/api/maintenance/cleanup":
                body = self._read_json(64 * 1024)
                dry_run = bool(body.get("dry_run", False))
                requested = body.get("policy") if isinstance(body.get("policy"), dict) else {}
                result = apply_runtime_retention(dry_run=dry_run, policy=requested)
                self._json(200, {"ok": True, **result})
                return

            if parsed.path == "/api/sync/all":
                if not SYNC_LOCK.acquire(blocking=False):
                    self._json(409, {"ok": False, "error": "SYNC_ALREADY_RUNNING"})
                    return
                try:
                    body = self._read_json(256 * 1024)
                    requested = body["providers"] if isinstance(body.get("providers"), list) else ["meta", "x", "tiktok", "youtube", "linkedin"]
                    run_id = "sync-" + secrets.token_urlsafe(12)
                    started_at = time.time()
                    results = []; combined = []; failures = []
                    for provider in requested:
                        provider = str(provider).strip().lower()
                        try:
                            if provider not in {"x","tiktok","youtube","linkedin"}:
                                failures.append({"provider":provider,"error":"META_ORCHESTRATOR_USE_EXISTING_SELECTION_FLOW"})
                                results.append({"provider":provider,"ok":False,"error":"META_ORCHESTRATOR_USE_EXISTING_SELECTION_FLOW"})
                                continue
                            token=social_access_token(provider)
                            if not token and provider!="youtube": raise SocialConnectorError(f"{provider.upper()}_NOT_CONNECTED")
                            previous_state = SYNC_STATE.get(provider)
                            persist_sync(provider, {**(previous_state or {}), "status": "running", "checkpoint": begin_checkpoint(previous_state, run_id=run_id, cursor=str((previous_state or {}).get("cursor") or ""), page=int((previous_state or {}).get("checkpoint", {}).get("page", 0) or 0) + 1)})
                            c=social_connector(provider); payload={}; cursor=""
                            if provider=="x":
                                q=str(body.get("x_query") or social_config(provider).get("query") or "").strip()
                                if not q: raise SocialConnectorError("X_QUERY_REQUIRED")
                                payload, retry_attempts = retry_sync_call(lambda: c.recent(token,q,100))
                            elif provider=="tiktok":
                                payload, retry_attempts = retry_sync_call(lambda: c.videos(token,20)); cursor=str(payload.get("cursor") or "")
                            elif provider=="youtube":
                                channel=body.get("youtube_channel_id") or social_config(provider).get("channelId")
                                if not channel: raise SocialConnectorError("YOUTUBE_CHANNEL_ID_REQUIRED")
                                vids, retry_attempts = retry_sync_call(lambda: c.videos(token,channel,20,os.getenv("YOUTUBE_API_KEY",""))); comments=[]
                                video_ids=[str(v.get("snippet",{}).get("resourceId",{}).get("videoId") or "") for v in vids.get("items",[])]
                                video_ids=[v for v in video_ids if v]
                                comments = fetch_comments_parallel(lambda vid: c.comments(token,vid,100,os.getenv("YOUTUBE_API_KEY","")), video_ids)
                                payload={"videos":vids,"comments":comments}; cursor=str(vids.get("nextPageToken") or "")
                            else:
                                org=body.get("linkedin_organization_id") or social_config(provider).get("organizationId")
                                if not org: raise SocialConnectorError("LINKEDIN_ORGANIZATION_ID_REQUIRED")
                                posts, retry_attempts = retry_sync_call(lambda: c.posts(token,org,100)); comments=[]
                                urns=[str(post.get("id") or "") for post in posts.get("elements",[])]
                                urns=[u for u in urns if u]
                                comments = fetch_comments_parallel(lambda urn: c.comments(token,urn,100), urns, item_key="elements")
                                payload={"posts":posts,"comments":comments}
                            retry_count=max(0,int(retry_attempts or 1)-1)
                            rows=social_to_mentions(provider,payload); result,count,duplicates=sync_payload_result(provider,rows,cursor=cursor,run_id=run_id,page=int((SYNC_STATE.get(provider) or {}).get("checkpoint", {}).get("page", 0) or 0))
                            combined.extend(result.get("mentions",[])); results.append({"provider":provider,"ok":True,"source_count":count,"duplicate_count":duplicates,"retry_count":retry_count,"cursor":cursor,"page":int((SYNC_STATE.get(provider) or {}).get("checkpoint", {}).get("page", 0) or 0),"content_keys":[str(m.get("id_mencion") or m.get("hash_mencion") or "") for m in result.get("mentions",[]) if str(m.get("id_mencion") or m.get("hash_mencion") or "")]})
                        except Exception as exc:
                            failures.append({"provider":provider,"error":str(exc) or type(exc).__name__})
                            previous_state = SYNC_STATE.get(provider)
                            state = merge_sync_state(previous_state,status="error",error=str(exc) or type(exc).__name__)
                            try:
                                state["checkpoint"] = abandon_checkpoint(previous_state, run_id=run_id, reason=str(exc) or type(exc).__name__)
                            except ValueError:
                                pass
                            persist_sync(provider, state)
                            results.append({"provider":provider,"ok":False,"error":str(exc) or type(exc).__name__})
                    finished_at = time.time()
                    run = build_sync_run(run_id, started_at, finished_at, requested, results, failures)
                    persist_sync_run(run)
                    self._json(200,{"ok":not failures,"run":run,"payload":{"mentions":combined,"insights":[],"conversations":[],"knowledge":[],"metadata":{"version":"1.0.0","source":"sync_orchestrator"}},"providers":results,"failures":failures,"synced_at":finished_at}); return
                finally:
                    SYNC_LOCK.release()
            if parsed.path == "/api/sync/status":
                self._json(200, sync_status_payload()); return
            if parsed.path == "/api/sync/health":
                query = parse_qs(parsed.query)
                interval = query.get("interval", [30])[0]
                providers = [x.strip() for x in query.get("providers", [""])[0].split(",") if x.strip()] or ["x", "tiktok", "youtube", "linkedin"]
                try:
                    health = build_sync_health(SYNC_STATE, interval_minutes=int(interval), providers=providers)
                except (TypeError, ValueError):
                    self._json(400, {"ok": False, "error": "INVALID_SYNC_INTERVAL"}); return
                self._json(200, health); return
            if parsed.path == "/api/sync/runs":
                query = parse_qs(parsed.query)
                self._json(200, sync_runs_payload(query.get("limit", [20])[0])); return
            if parsed.path == "/api/sync/diagnostic":
                query = parse_qs(parsed.query)
                try:
                    interval = max(5, int(query.get("interval", [30])[0] or 30))
                except (TypeError, ValueError):
                    self._json(400, {"ok": False, "error": "INVALID_SYNC_INTERVAL"}); return
                providers = [x.strip() for x in query.get("providers", ["x,tiktok,youtube,linkedin"])[0].split(",") if x.strip()]
                report = build_sync_diagnostic_report(SYNC_STATE, SYNC_RUNS, interval_minutes=interval, providers=providers)
                self._json(200, {"ok": True, "report": report}); return
            if parsed.path == "/api/sync/alerts":
                query = parse_qs(parsed.query)
                interval = max(5, int(query.get("interval", [30])[0] or 30))
                providers = [x.strip() for x in query.get("providers", ["x,tiktok,youtube,linkedin"])[0].split(",") if x.strip()]
                health = build_sync_health(SYNC_STATE, interval_minutes=interval, providers=providers)
                self._json(200, {"version": 1, "alerts": build_sync_alerts(health), "health": health}); return

            if parsed.path == "/api/knowledge/search":
                payload = self._read_json(512 * 1024)
                query = str(payload.get("query", "")).strip()
                knowledge = payload.get("knowledge", [])
                if not query:
                    self._json(400, {"ok": False, "error": {"code": "INVALID_QUERY", "message": "La consulta no puede estar vacía."}})
                    return
                if not isinstance(knowledge, list):
                    self._json(400, {"ok": False, "error": {"code": "INVALID_KNOWLEDGE", "message": "knowledge debe ser un arreglo."}})
                    return
                try:
                    result = search_knowledge(query, knowledge, payload.get("limit", 10), payload.get("min_similarity", 0.35))
                except ValueError as exc:
                    code = str(exc)
                    self._json(400, {"ok": False, "error": {"code": code, "message": code}})
                    return
                self._json(200, {"ok": True, **result, "engine": "deterministic-v1"})
                return

            if parsed.path == "/api/integrations/meta/config":
                payload = self._read_json(256 * 1024)
                saved = save_public_config(Path(CONFIG_PATH), payload)
                self._json(200, {"provider": "meta", "saved": True, "config": saved})
                return

            if parsed.path == "/api/cohere/config":
                payload = self._read_json(64 * 1024)
                api_key = str(payload.get("apiKey", "")).strip()
                model = str(payload.get("model", "")).strip()
                if not api_key:
                    self._json(400, {"error": "COHERE_API_KEY_MISSING"}); return
                # Validate before persisting. The key is sent only to localhost Python.
                service = CohereService(api_key=api_key, model=model or None)
                service.check_connection()
                TOKENS["cohere"] = {"api_key": api_key, "model": service.model, "configured_at": time.time()}
                persist_tokens()
                self._json(200, {"provider": "cohere", "configured": True, "model": service.model, "secret_stored_in_python": True})
                return

            if parsed.path == "/api/cohere/test":
                service = cohere_service()
                service.check_connection()
                self._json(200, {"provider": "cohere", "connected": True, "model": service.model})
                return

            if parsed.path == "/api/cohere/translate":
                payload = self._read_json(512 * 1024)
                rows = payload.get("rows") if isinstance(payload.get("rows"), list) else [{"texto_original": str(payload.get("text", ""))}]
                target = str(payload.get("target_language", "es")).strip() or "es"
                result = cohere_service().translate_rows(rows, target_language=target)
                self._json(200, result)
                return

            self._json(404, {"error": "NOT_FOUND"})
        except AIServiceError as exc:
            status = 401 if exc.code == "AI_AUTH_ERROR" else 429 if exc.code == "AI_RATE_LIMIT" else 502
            self._json(status, {"error": exc.code, "message": str(exc)})
        except (ValueError, json.JSONDecodeError, OSError) as exc:
            self._json(400, {"error": str(exc) or "REQUEST_INVALID"})
        except Exception as exc:
            self._json(500, {"error": "BRIDGE_REQUEST_FAILED", "detail": type(exc).__name__})

    def do_GET(self):
        if not self._origin_guard():
            return
        cleanup_states()
        parsed = urlparse(self.path)
        if parsed.path == "/api/sync/status":
            self._json(200, sync_status_payload()); return
        if parsed.path == "/api/sync/health":
            query = parse_qs(parsed.query)
            interval = query.get("interval", [30])[0]
            providers = [x.strip() for x in query.get("providers", [""])[0].split(",") if x.strip()] or ["x", "tiktok", "youtube", "linkedin"]
            try:
                health = build_sync_health(SYNC_STATE, interval_minutes=int(interval), providers=providers)
            except (TypeError, ValueError):
                self._json(400, {"ok": False, "error": "INVALID_SYNC_INTERVAL"}); return
            self._json(200, health); return
        if parsed.path == "/api/sync/runs":
            query = parse_qs(parsed.query)
            self._json(200, sync_runs_payload(query.get("limit", [20])[0])); return
        if parsed.path == "/api/sync/alerts":
            query = parse_qs(parsed.query)
            interval = max(5, int(query.get("interval", [30])[0] or 30))
            providers = [x.strip() for x in query.get("providers", ["x,tiktok,youtube,linkedin"])[0].split(",") if x.strip()]
            health = build_sync_health(SYNC_STATE, interval_minutes=interval, providers=providers)
            self._json(200, {"version": 1, "alerts": build_sync_alerts(health), "health": health}); return
        if parsed.path == "/api/sync/reconcile":
            query = parse_qs(parsed.query)
            providers = [x.strip() for x in query.get("providers", ["x,tiktok,youtube,linkedin"])[0].split(",") if x.strip()]
            self._json(200, reconcile_sync_states(SYNC_STATE, providers=providers)); return
        if parsed.path == "/api/maintenance/policy":
            self._json(200, {"version": 1, "policy": RETENTION_POLICY, "scope": ["sync_runs"], "business_data_untouched": True})
            return
        if parsed.path.startswith("/api/integrations/"):
            parts=parsed.path.split("/"); provider=parts[3] if len(parts)>3 else ""; action=parts[4] if len(parts)>4 else ""
            if provider in {"x","tiktok","youtube","linkedin"}:
                c=social_connector(provider)
                if action=="status": self._json(200,{"provider":provider,"configured":not social_ready(provider),"ready":not social_ready(provider),"connected":bool((TOKENS.get(provider) or {}).get("access_token")),"missing":social_ready(provider),"last_sync":SOCIAL_LAST_SYNC.get(provider)}); return
                if action=="authorize":
                    missing=social_ready(provider)
                    if missing: self._json(400,{"error":"SOCIAL_CONFIGURATION_INCOMPLETE","missing":missing}); return
                    state=secrets.token_urlsafe(32); SOCIAL_STATES[state]={"provider":provider,"created":time.time()}
                    if provider=="x":
                        verifier=secrets.token_urlsafe(64); SOCIAL_STATES[state]["verifier"]=verifier
                        url=c.authorization(state,verifier)
                    else: url=c.authorization(state)
                    self.send_response(302); self.send_header("Location",url); self.send_header("Cache-Control","no-store"); self.end_headers(); return
                if action=="callback":
                    params=parse_qs(parsed.query); state=params.get("state",[""])[0]; code=params.get("code",[""])[0]; rec=SOCIAL_STATES.pop(state,None)
                    if not rec: self._html(400,"Estado OAuth inválido","El estado de seguridad no coincide o expiró. Inicia la conexión nuevamente desde Sentia."); return
                    try:
                        sec=social_secret(provider)
                        if provider=="x": payload=c.exchange(code,rec["verifier"],sec)
                        else: payload=c.exchange(code,sec)
                        TOKENS[provider]={"access_token":payload.get("access_token",""),"refresh_token":payload.get("refresh_token","") or "","expires_at":time.time()+int(payload.get("expires_in",3600))}
                        persist_tokens(); self._html(200,f"{provider.upper()} conectado","La autorización fue completada en Python. Puedes volver a Sentia.")
                    except SocialConnectorError as exc: self._html(502,"No se pudo conectar",exc.code)
                    return
                if action=="disconnect": TOKENS.pop(provider,None); SOCIAL_LAST_SYNC.pop(provider,None); persist_tokens(); self._json(200,{"provider":provider,"disconnected":True}); return

        if parsed.path == "/api/integrations/ga4/status":
            cfg = current_ga4_config()
            token = TOKENS.get("ga4") or {}
            self._json(200, {
                "provider": "ga4", "configured": bool(cfg["client_id"]),
                "ready": ga4_from_config().is_ready(), "connected": bool(token.get("access_token")),
                "property_id": cfg.get("property_id", ""), "missing": ga4_from_config().missing_secrets(),
                "last_sync": LAST_SYNC.get("ga4"),
            })
            return
        if parsed.path == "/api/integrations/ga4/authorize":
            connector = ga4_from_config()
            if not connector.is_ready():
                self._json(400, {"error": "GA4_CONFIGURATION_INCOMPLETE", "missing": connector.missing_secrets()})
                return
            state = secrets.token_urlsafe(32); GA4_STATES[state] = time.time()
            self.send_response(302); self.send_header("Location", connector.authorization_url(state)); self.send_header("Cache-Control", "no-store"); self.end_headers(); return
        if parsed.path == "/api/integrations/ga4/callback":
            params = parse_qs(parsed.query)
            if "error" in params:
                self._html(400, "Conexión GA4 cancelada", params.get("error_description", params["error"])[0]); return
            state = params.get("state", [""])[0]; code = params.get("code", [""])[0]
            if not state or state not in GA4_STATES:
                self._html(400, "Estado OAuth inválido", "El estado de seguridad no coincide o expiró. Inicia la conexión nuevamente desde Sentia."); return
            GA4_STATES.pop(state, None)
            try:
                payload = ga4_from_config().exchange_code(code)
                TOKENS["ga4"] = {"access_token": payload["access_token"], "refresh_token": payload.get("refresh_token", ""), "expires_at": time.time() + int(payload.get("expires_in", 3600))}
                persist_tokens()
                self._html(200, "Google Analytics conectada", "La autorización fue completada en Python. Puedes volver a Sentia y consultar las propiedades GA4.")
            except GoogleAnalyticsError as exc:
                self._html(502, "No se pudo conectar GA4", exc.code)
            return
        if parsed.path == "/api/integrations/ga4/properties":
            token = TOKENS.get("ga4") or {}
            if not token.get("access_token"):
                self._json(401, {"error": "GA4_NOT_CONNECTED"}); return
            try:
                props = ga4_from_config().list_properties(ga4_access_token())
                self._json(200, {"properties": props})
            except GoogleAnalyticsError as exc:
                status = 401 if exc.code == "GA4_TOKEN_EXPIRED" else 403 if exc.code == "GA4_PERMISSION_DENIED" else 502
                self._json(status, {"error": exc.code})
            return
        if parsed.path == "/api/integrations/ga4/disconnect":
            TOKENS.pop("ga4", None); LAST_SYNC.pop("ga4", None); persist_tokens(); self._json(200, {"provider": "ga4", "disconnected": True}); return

        if parsed.path == "/api/integrations/meta/status":
            connector = meta_from_config()
            token = TOKENS.get("meta")
            connected = bool(token and token.get("access_token"))
            self._json(200, {
                "provider": "meta",
                "ready": connector.is_ready(),
                "configured": bool(connector.app_id and connector.redirect_uri),
                "connected": connected,
                "missing": connector.missing_secrets(),
                "graph_version": connector.graph_version,
                "account": token.get("account") if token else None,
                "token_expires_at": token.get("expires_at") if token else None,
                "last_sync": LAST_SYNC.get("meta"),
            })
            return
        if parsed.path == "/api/integrations/meta/authorize":
            connector = meta_from_config()
            if not connector.is_ready():
                self._json(400, {"error": "META_CONFIGURATION_INCOMPLETE", "missing": connector.missing_secrets()})
                return
            state = secrets.token_urlsafe(32)
            PENDING_STATES[state] = time.time()
            self.send_response(302)
            self.send_header("Location", connector.authorization_url(state))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            return
        if parsed.path == "/api/integrations/meta/callback":
            params = parse_qs(parsed.query)
            if "error" in params:
                self._html(400, "Conexión cancelada", params["error_description"][0] if params.get("error_description") else params["error"][0])
                return
            state = params.get("state", [""])[0]
            code = params.get("code", [""])[0]
            if not state or state not in PENDING_STATES:
                self._html(400, "Estado OAuth inválido", "El estado de seguridad no coincide o expiró. Inicia la conexión nuevamente desde Sentia.")
                return
            PENDING_STATES.pop(state, None)
            try:
                connector = meta_from_config()
                token_payload = connector.exchange_code(code)
                access_token = token_payload["access_token"]
                account = connector.graph_get("me", access_token, {"fields": "id,name"})
                pages = connector.graph_get("me/accounts", access_token, {"fields": "id,name,access_token,instagram_business_account"})
                expires_at = time.time() + int(token_payload.get("expires_in", 0) or 0) if token_payload.get("expires_in") else None
                TOKENS["meta"] = {"access_token": access_token, "account": account, "pages": pages.get("data", []), "expires_at": expires_at}
                persist_tokens()
                self._html(200, "Meta conectada", "La autorización fue completada en Python. Sentia ya puede consultar las páginas disponibles. Los tokens no fueron enviados al navegador.")
            except Exception as exc:
                self._html(502, "No se pudo completar la conexión", f"El intercambio OAuth o la consulta inicial falló: {type(exc).__name__}. Revisa la configuración, permisos y versión de Graph API en Sentia.")
            return
        if parsed.path == "/api/integrations/meta/disconnect":
            TOKENS.pop("meta", None)
            LAST_SYNC.pop("meta", None)
            delete_token_store(TOKEN_PATH)
            self._json(200, {"provider": "meta", "disconnected": True})
            return
        if parsed.path == "/api/integrations/meta/pages":
            token = token_record()
            if not token:
                self._json(401, {"error": "META_NOT_CONNECTED"})
                return
            pages = []
            for page in token.get("pages", []):
                pages.append({
                    "id": page.get("id"),
                    "name": page.get("name"),
                    "instagram_business_account": page.get("instagram_business_account"),
                })
            self._json(200, {"pages": pages})
            return
        if parsed.path == "/api/integrations/meta/selection":
            cfg = selected_config()
            self._json(200, {"page_id": cfg.get("page_id", ""), "instagram_account_id": cfg.get("instagram_account_id", "")})
            return
        if parsed.path == "/api/integrations/meta/ingest":
            token = token_record()
            if not token:
                self._json(401, {"error": "META_NOT_CONNECTED"})
                return
            cfg = selected_config()
            page_id = cfg.get("page_id", "")
            if not page_id:
                self._json(400, {"error": "META_PAGE_NOT_SELECTED"})
                return
            page = next((p for p in token.get("pages", []) if p.get("id") == page_id), None)
            if not page:
                self._json(400, {"error": "META_PAGE_NOT_AVAILABLE"})
                return
            connector = meta_from_config()
            page_token = page.get("access_token")
            if not page_token:
                self._json(502, {"error": "META_PAGE_TOKEN_MISSING"})
                return
            try:
                page_posts = connector.graph_get(page_id + "/posts", page_token, {
                    "fields": "id,message,created_time,permalink_url", "limit": "50"
                }).get("data", [])
                rows = [{
                    "id_mencion": "meta:" + str(x.get("id")),
                    "fuente": "facebook",
                    "fecha": x.get("created_time", ""),
                    "texto_original": x.get("message", ""),
                } for x in page_posts if x.get("message")]

                ig = page.get("instagram_business_account") or {}
                ig_id = cfg.get("instagram_account_id") or ig.get("id")
                if ig_id:
                    media = connector.graph_get(str(ig_id) + "/media", page_token, {
                        "fields": "id,caption,timestamp,permalink", "limit": "50"
                    }).get("data", [])
                    rows.extend([{
                        "id_mencion": "instagram:" + str(x.get("id")),
                        "fuente": "instagram",
                        "fecha": x.get("timestamp", ""),
                        "texto_original": x.get("caption", ""),
                    } for x in media if x.get("caption")])

                result = Pipeline(PipelineConfig()).run(rows)
                LAST_SYNC["meta"] = {"at": time.time(), "source_count": len(rows), "page_id": page_id, "instagram_account_id": ig_id or None}
                self._json(200, {"provider": "meta", "page": {"id": page.get("id"), "name": page.get("name")}, "instagram_account_id": ig_id or None, "payload": result, "source_count": len(rows), "synced_at": LAST_SYNC["meta"]["at"]})
            except Exception as exc:
                self._json(502, {"error": "META_INGEST_FAILED", "detail": type(exc).__name__})
            return
        if parsed.path == "/api/cohere/status":
            record = TOKENS.get("cohere") or {}
            configured = bool(record.get("api_key") or os.getenv("COHERE_API_KEY"))
            self._json(200, {"provider": "cohere", "configured": configured, "model": record.get("model") or os.getenv("COHERE_MODEL") or CohereService().model})
            return
        if parsed.path == "/api/cohere/disconnect":
            TOKENS.pop("cohere", None)
            persist_tokens()
            self._json(200, {"provider": "cohere", "disconnected": True})
            return
        self._json(404, {"error": "NOT_FOUND"})

    def log_message(self, fmt, *args):
        print("[sentia-connector] " + (fmt % args))


def main():
    restore_tokens()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Sentia connector bridge: http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
