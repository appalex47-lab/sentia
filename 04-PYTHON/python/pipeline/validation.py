import json
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schemas" / "datos_procesados.schema.json"


def validate_payload(payload):
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
    return errors


def assert_valid_payload(payload):
    errors = validate_payload(payload)
    if errors:
        details = "; ".join(f"{list(e.path)}: {e.message}" for e in errors[:10])
        raise ValueError(f"SCHEMA_VALIDATION_FAILED: {details}")
