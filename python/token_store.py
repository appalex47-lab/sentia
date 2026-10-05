"""Encrypted-at-rest token store for the local Sentia connector bridge.

The encryption key is supplied only through SENTIA_TOKEN_ENCRYPTION_KEY.
The browser never receives the key or encrypted token blob.
"""
from __future__ import annotations

import base64
import json
import os
import secrets
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

KEY_ENV = "SENTIA_TOKEN_ENCRYPTION_KEY"
KEY_FILE_ENV = "SENTIA_TOKEN_KEY_FILE"
DEFAULT_KEY_FILE = Path(__file__).resolve().parent / "runtime" / ".sentia-key"


def _key() -> bytes:
    raw = os.getenv(KEY_ENV, "")
    if not raw:
        key_file = Path(os.getenv(KEY_FILE_ENV, str(DEFAULT_KEY_FILE)))
        try:
            if key_file.exists():
                raw = key_file.read_text(encoding="ascii").strip()
            else:
                raw = generate_key()
                key_file.parent.mkdir(parents=True, exist_ok=True)
                key_file.write_text(raw, encoding="ascii")
                try:
                    os.chmod(key_file, 0o600)
                except OSError:
                    pass
        except OSError as exc:
            raise RuntimeError("TOKEN_ENCRYPTION_KEY_MISSING") from exc
    try:
        key = base64.urlsafe_b64decode(raw.encode("ascii"))
    except Exception as exc:
        raise RuntimeError("TOKEN_ENCRYPTION_KEY_INVALID") from exc
    if len(key) not in (16, 24, 32):
        raise RuntimeError("TOKEN_ENCRYPTION_KEY_INVALID")
    return key


def generate_key() -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii")


def save(path: Path, data: dict) -> None:
    key = _key()
    nonce = secrets.token_bytes(12)
    plaintext = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, b"sentia-token-store-v1")
    payload = {"version": 1, "nonce": base64.urlsafe_b64encode(nonce).decode("ascii"), "ciphertext": base64.urlsafe_b64encode(ciphertext).decode("ascii")}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def load(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        nonce = base64.urlsafe_b64decode(payload["nonce"])
        ciphertext = base64.urlsafe_b64decode(payload["ciphertext"])
        plaintext = AESGCM(_key()).decrypt(nonce, ciphertext, b"sentia-token-store-v1")
        data = json.loads(plaintext.decode("utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, ValueError, KeyError, json.JSONDecodeError, RuntimeError):
        return None


def delete(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass
