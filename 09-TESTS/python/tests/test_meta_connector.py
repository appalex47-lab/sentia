import json
from pathlib import Path

from python.connectors.meta import MetaConnector, save_public_config, load_public_config


def test_meta_connector_reports_missing_secret(monkeypatch):
    monkeypatch.delenv("META_APP_SECRET", raising=False)
    connector = MetaConnector("123", "http://127.0.0.1:8787/api/integrations/meta/callback")
    assert connector.missing_secrets() == ["META_APP_SECRET"]
    assert connector.is_ready() is False


def test_meta_connector_builds_versioned_authorization_url(monkeypatch):
    monkeypatch.setenv("META_APP_SECRET", "test-only")
    connector = MetaConnector("123", "http://127.0.0.1:8787/api/integrations/meta/callback", "pages_show_list", "v26.0")
    url = connector.authorization_url("state-test")
    assert "facebook.com/v26.0/dialog/oauth" in url
    assert "client_id=123" in url
    assert "state=state-test" in url
    assert "scope=pages_show_list" in url
    assert "response_type=code" in url


def test_public_config_never_accepts_secret(tmp_path):
    target = tmp_path / "integrations.json"
    saved = save_public_config(target, {
        "appId": "123",
        "redirectUri": "http://127.0.0.1:8787/api/integrations/meta/callback",
        "scopes": "pages_show_list",
        "graphVersion": "v26.0",
        "clientSecret": "DO_NOT_STORE",
    })
    loaded = load_public_config(target)
    assert saved["app_id"] == "123"
    assert "clientSecret" not in json.dumps(loaded)
    assert loaded["graph_version"] == "v26.0"


def test_public_config_preserves_only_selection_metadata(tmp_path):
    target = tmp_path / "integrations.json"
    saved = save_public_config(target, {
        "appId": "123",
        "redirectUri": "http://127.0.0.1:8787/api/integrations/meta/callback",
        "pageId": "page-1",
        "instagramAccountId": "ig-1",
        "accessToken": "SECRET",
    })
    assert saved["page_id"] == "page-1"
    assert saved["instagram_account_id"] == "ig-1"
    assert "SECRET" not in target.read_text(encoding="utf-8")
