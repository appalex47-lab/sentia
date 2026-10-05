import json
from pathlib import Path

from python.connectors.google_analytics import GoogleAnalyticsConnector, save_public_config


def test_ga4_public_config_excludes_secret(tmp_path):
    path = tmp_path / "ga4.json"
    cfg = save_public_config(path, {"clientId": "client-123", "projectId": "proj", "propertyId": "123456", "redirectUri": "http://127.0.0.1:8787/api/integrations/ga4/callback"})
    raw = path.read_text()
    assert cfg["client_id"] == "client-123"
    assert "client_secret" not in raw.lower()
    assert "GOOGLE_CLIENT_SECRET" not in raw


def test_ga4_authorization_url_requires_secret(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLIENT_SECRET", raising=False)
    connector = GoogleAnalyticsConnector("client-123", "http://127.0.0.1:8787/api/integrations/ga4/callback")
    assert connector.is_ready() is False
    assert "GOOGLE_CLIENT_SECRET" in connector.missing_secrets()


def test_ga4_normalizes_report():
    payload = {
        "dimensionHeaders": [{"name": "date"}],
        "metricHeaders": [{"name": "activeUsers", "type": "TYPE_INTEGER"}],
        "rows": [{"dimensionValues": [{"value": "20261001"}], "metricValues": [{"value": "42"}]}],
        "rowCount": 1,
        "metadata": {"currencyCode": "MXN"},
    }
    result = GoogleAnalyticsConnector._normalize_report(payload, "123", "2026-10-01", "2026-10-01")
    assert result["rows"][0]["dimensions"]["date"] == "20261001"
    assert result["rows"][0]["metrics"]["activeUsers"] == "42"
    assert result["row_count"] == 1
