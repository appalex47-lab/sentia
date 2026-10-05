"""Meta/Facebook + Instagram OAuth connector.

Secrets and OAuth tokens remain exclusively on the Python side. Public
configuration can be supplied by Sentia's Integrations UI and is kept in the
local connector runtime, not in browser storage as a secret.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_GRAPH_VERSION = "v26.0"


class MetaConnector:
    REQUIRED_ENV = ("META_APP_SECRET",)

    def __init__(
        self,
        app_id: str,
        redirect_uri: str,
        scopes: str = "",
        graph_version: str | None = None,
    ):
        self.app_id = app_id.strip()
        self.redirect_uri = redirect_uri.strip()
        self.scopes = scopes.strip()
        self.graph_version = (graph_version or os.getenv("META_GRAPH_VERSION", DEFAULT_GRAPH_VERSION)).strip()

    def missing_secrets(self) -> list[str]:
        return [key for key in self.REQUIRED_ENV if not os.getenv(key)]

    def is_ready(self) -> bool:
        return bool(self.app_id and self.redirect_uri and self.graph_version and not self.missing_secrets())

    def authorization_url(self, state: str) -> str:
        if not self.is_ready():
            raise RuntimeError("META_CONFIGURATION_INCOMPLETE")
        params = {
            "client_id": self.app_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
            "response_type": "code",
        }
        if self.scopes:
            params["scope"] = self.scopes
        return f"https://www.facebook.com/{self.graph_version}/dialog/oauth?" + urlencode(params)

    def exchange_code(self, code: str) -> dict:
        if not self.is_ready():
            raise RuntimeError("META_CONFIGURATION_INCOMPLETE")
        if not code:
            raise ValueError("META_AUTHORIZATION_CODE_MISSING")
        params = urlencode({
            "client_id": self.app_id,
            "client_secret": os.environ["META_APP_SECRET"],
            "redirect_uri": self.redirect_uri,
            "code": code,
        }).encode()
        url = f"https://graph.facebook.com/{self.graph_version}/oauth/access_token"
        request = Request(url, data=params, method="POST", headers={"Accept": "application/json"})
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if not payload.get("access_token"):
            raise RuntimeError("META_TOKEN_EXCHANGE_FAILED")
        return payload

    def graph_get(self, path: str, access_token: str, params: dict | None = None) -> dict:
        if not access_token:
            raise ValueError("META_ACCESS_TOKEN_MISSING")
        clean_path = path.lstrip("/")
        query = dict(params or {})
        query["access_token"] = access_token
        url = f"https://graph.facebook.com/{self.graph_version}/{clean_path}?{urlencode(query)}"
        request = Request(url, headers={"Accept": "application/json"})
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))


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
        "app_id": str(config.get("appId", "")).strip(),
        "redirect_uri": str(config.get("redirectUri", "")).strip(),
        "scopes": str(config.get("scopes", "")).strip(),
        "graph_version": str(config.get("graphVersion", DEFAULT_GRAPH_VERSION)).strip() or DEFAULT_GRAPH_VERSION,
        "page_id": str(config.get("pageId", "")).strip(),
        "instagram_account_id": str(config.get("instagramAccountId", "")).strip(),
    }
    path.write_text(json.dumps(safe, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return safe
