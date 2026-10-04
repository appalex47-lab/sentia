import json
import sys
from pathlib import Path
from .pipeline.validation import validate_payload

def main():
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "data/datos_procesados.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    errors = validate_payload(payload)
    if errors:
        for error in errors[:20]: print(f"{list(error.path)}: {error.message}")
        raise SystemExit(1)
    print("Schema validation: PASS")

if __name__ == "__main__": main()
