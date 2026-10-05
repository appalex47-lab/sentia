"""Google Analytics 4 OAuth + Data/Admin API connector for Sentia.

Secrets and OAuth tokens remain exclusively in the Python bridge. Public
configuration (client id, redirect URI, property id and scopes) is stored in
the local runtime configuration file.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

DEFAULT_SCOPES = "https://www.googleapis.com/auth/analytics.readonly"
DEFAULT_REDIRECT_URI = "http://127.0.0.1:8787/api/integrations/ga4/callback"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
ADMIN_URL = "https://analyticsadmin.googleapis.com/v1beta"
DATA_URL = "https://analyticsdata.googleapis.com/v1beta"


class GoogleAnalyticsError(RuntimeError):
    def __init__(self, code: str, message: str = ""):
        super().__init__(message or code)
        self.code = code


class GoogleAnalyticsConnector:
    REQUIRED_SECRET_ENV = ("GOOGLE_CLIENT_SECRET",)

    def __init__(self, client_id: str, redirect_uri: str = "", scopes: str = ""):
        self.client_id = client_id.strip()
        self.redirect_uri = (redirect_uri.strip() or os.getenv("GA4_REDIRECT_URI", DEFAULT_REDIRECT_URI)).strip()
        self.scopes = (scopes.strip() or DEFAULT_SCOPES).strip()

    def missing_secrets(self) -> list[str]:
        return [key for key in self.REQUIRED_SECRET_ENV if not os.getenv(key)]

    def is_ready(self) -> bool:
        return bool(self.client_id and self.redirect_uri and self.scopes and not self.missing_secrets())

    def authorization_url(self, state: str) -> str:
        if not self.is_ready():
            raise GoogleAnalyticsError("GA4_CONFIGURATION_INCOMPLETE")
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": self.scopes,
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        return AUTH_URL + "?" + urlencode(params)

    def exchange_code(self, code: str) -> dict:
        if not self.is_ready():
            raise GoogleAnalyticsError("GA4_CONFIGURATION_INCOMPLETE")
        if not code:
            raise GoogleAnalyticsError("GA4_AUTHORIZATION_CODE_MISSING")
        body = urlencode({
            "code": code,
            "client_id": self.client_id,
            "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }).encode()
        request = Request(TOKEN_URL, data=body, method="POST", headers={"Accept": "application/json"})
        try:
            with urlopen(request, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise GoogleAnalyticsError("GA4_TOKEN_EXCHANGE_FAILED") from exc
        if not payload.get("access_token"):
            raise GoogleAnalyticsError("GA4_TOKEN_EXCHANGE_FAILED")
        return payload

    def refresh_access_token(self, refresh_token: str) -> dict:
        if not self.is_ready():
            raise GoogleAnalyticsError("GA4_CONFIGURATION_INCOMPLETE")
        if not refresh_token:
            raise GoogleAnalyticsError("GA4_REFRESH_TOKEN_MISSING")
        body = urlencode({
            "client_id": self.client_id,
            "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }).encode()
        request = Request(TOKEN_URL, data=body, method="POST", headers={"Accept": "application/json"})
        try:
            with urlopen(request, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise GoogleAnalyticsError("GA4_TOKEN_REFRESH_FAILED") from exc
        if not payload.get("access_token"):
            raise GoogleAnalyticsError("GA4_TOKEN_REFRESH_FAILED")
        return payload

    def _request(self, method: str, url: str, access_token: str, body: dict | None = None) -> dict:
        if not access_token:
            raise GoogleAnalyticsError("GA4_ACCESS_TOKEN_MISSING")
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {"Accept": "application/json", "Authorization": f"Bearer {access_token}"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        request = Request(url, data=data, method=method, headers=headers)
        try:
            with urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            try:
                detail = json.loads(exc.read().decode("utf-8"))
            except Exception:
                detail = {}
            code = "GA4_API_ERROR"
            if exc.code == 401:
                code = "GA4_TOKEN_EXPIRED"
            elif exc.code == 403:
                code = "GA4_PERMISSION_DENIED"
            elif exc.code == 429:
                code = "GA4_QUOTA_EXCEEDED"
            raise GoogleAnalyticsError(code, json.dumps(detail, ensure_ascii=False)) from exc
        except URLError as exc:
            raise GoogleAnalyticsError("GA4_NETWORK_ERROR") from exc

    def list_account_summaries(self, access_token: str) -> list[dict]:
        payload = self._request("GET", f"{ADMIN_URL}/accountSummaries", access_token)
        return payload.get("accountSummaries", []) if isinstance(payload, dict) else []

    def list_properties(self, access_token: str) -> list[dict]:
        properties: list[dict] = []
        for account in self.list_account_summaries(access_token):
            account_name = account.get("displayName", "")
            account_id = account.get("account", "")
            for prop in account.get("propertySummaries", []) or []:
                properties.append({
                    "property": prop.get("property", ""),
                    "property_id": str(prop.get("property", "")).split("/")[-1],
                    "display_name": prop.get("displayName", ""),
                    "account": account_id,
                    "account_name": account_name,
                })
        return properties

    def run_report(self, access_token: str, property_id: str, start_date: str, end_date: str,
                   dimensions: list[str] | None = None, metrics: list[str] | None = None,
                   limit: int = 1000) -> dict:
        property_id = property_id.strip().removeprefix("properties/")
        if not property_id.isdigit():
            raise GoogleAnalyticsError("GA4_PROPERTY_ID_INVALID")
        if not start_date or not end_date:
            raise GoogleAnalyticsError("GA4_DATE_RANGE_REQUIRED")
        dims = dimensions or ["date"]
        mets = metrics or ["activeUsers", "sessions", "eventCount"]
        if len(dims) > 9:
            raise GoogleAnalyticsError("GA4_TOO_MANY_DIMENSIONS")
        body = {
            "dateRanges": [{"startDate": start_date, "endDate": end_date}],
            "dimensions": [{"name": x} for x in dims],
            "metrics": [{"name": x} for x in mets],
            "limit": min(max(int(limit), 1), 10000),
        }
        payload = self._request("POST", f"{DATA_URL}/properties/{property_id}:runReport", access_token, body)
        return self._normalize_report(payload, property_id, start_date, end_date)

    @staticmethod
    def _normalize_report(payload: dict, property_id: str, start_date: str, end_date: str) -> dict:
        dim_headers = [x.get("name", "") for x in payload.get("dimensionHeaders", [])]
        metric_headers = [x.get("name", "") for x in payload.get("metricHeaders", [])]
        rows = []
        for row in payload.get("rows", []) or []:
            dimensions = [x.get("value", "") for x in row.get("dimensionValues", [])]
            metrics = [x.get("value", "") for x in row.get("metricValues", [])]
            rows.append({
                "dimensions": dict(zip(dim_headers, dimensions)),
                "metrics": dict(zip(metric_headers, metrics)),
            })
        return {
            "provider": "ga4",
            "property_id": property_id,
            "start_date": start_date,
            "end_date": end_date,
            "dimension_headers": dim_headers,
            "metric_headers": metric_headers,
            "rows": rows,
            "row_count": payload.get("rowCount", len(rows)),
            "metadata": payload.get("metadata", {}),
        }


def load_public_config(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_public_config(path: Path, config: dict) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    safe = {
        "client_id": str(config.get("clientId", "")).strip(),
        "project_id": str(config.get("projectId", "")).strip(),
        "property_id": str(config.get("propertyId", "")).strip(),
        "redirect_uri": str(config.get("redirectUri", "")).strip() or DEFAULT_REDIRECT_URI,
        "scopes": str(config.get("scopes", "")).strip() or DEFAULT_SCOPES,
    }
    path.write_text(json.dumps(safe, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return safe
