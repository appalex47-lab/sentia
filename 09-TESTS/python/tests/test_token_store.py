from pathlib import Path
from python.token_store import generate_key, load, save


def test_encrypted_token_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("SENTIA_TOKEN_ENCRYPTION_KEY", generate_key())
    target = tmp_path / "tokens.enc"
    save(target, {"meta": {"access_token": "SECRET", "pages": []}})
    raw = target.read_text(encoding="utf-8")
    assert "SECRET" not in raw
    assert load(target)["meta"]["access_token"] == "SECRET"
