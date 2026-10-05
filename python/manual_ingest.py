"""Manual conversation ingestion adapters.

Supports WhatsApp exports (.txt), CSV and JSON. Audio is intentionally not
transcribed here: a call must arrive as a text transcript, optionally with a
translated_text field. The original text is preserved for traceability.
"""
from __future__ import annotations
import csv, io, json, re, hashlib
from datetime import datetime, timezone

WHATSAPP_PATTERNS = [
    re.compile(r"^\[?(?P<date>\d{1,2}/\d{1,2}/\d{2,4}),?\s+(?P<time>\d{1,2}:\d{2}(?::\d{2})?)\]?\s+-\s+(?P<speaker>[^:]+):\s*(?P<text>.*)$"),
    re.compile(r"^(?P<date>\d{1,2}/\d{1,2}/\d{2,4}),\s+(?P<time>\d{1,2}:\d{2})\s+-\s+(?P<speaker>[^:]+):\s*(?P<text>.*)$"),
]


def _iso(date: str, time: str) -> str:
    for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M"):
        try:
            return datetime.strptime(f"{date} {time}", fmt).replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            pass
    return datetime.now(timezone.utc).isoformat()


def parse_whatsapp(text: str, source="whatsapp") -> list[dict]:
    rows=[]; current=None
    for raw in text.splitlines():
        line=raw.strip("\ufeff")
        match=next((p.match(line) for p in WHATSAPP_PATTERNS if p.match(line)), None)
        if match:
            if current: rows.append(current)
            g=match.groupdict()
            current={"fecha":_iso(g["date"],g["time"]),"fuente":source,"texto_original":g["text"].strip(),"speaker":g["speaker"].strip()}
        elif current and line:
            current["texto_original"] += " " + line
    if current: rows.append(current)
    return rows


def parse_csv(text: str, source="manual_csv") -> list[dict]:
    reader=csv.DictReader(io.StringIO(text))
    rows=[]
    for row in reader:
        r={str(k).strip():v for k,v in row.items() if k is not None}
        text_value=r.get("texto_original") or r.get("texto") or r.get("mensaje") or ""
        if not text_value.strip(): continue
        rows.append({"id_mencion":r.get("id_mencion") or r.get("id") or "", "fecha":r.get("fecha") or datetime.now(timezone.utc).isoformat(), "fuente":r.get("fuente") or source, "texto_original":text_value, "texto_traducido":r.get("texto_traducido") or r.get("translated_text") or "", "idioma_origen":r.get("idioma_origen") or r.get("source_language") or "", "speaker":r.get("speaker") or r.get("emisor") or ""})
    return rows


def parse_json(text: str, source="manual_json") -> list[dict]:
    data=json.loads(text)
    if isinstance(data, dict): data=data.get("mentions") or data.get("mensajes") or data.get("rows") or [data]
    if not isinstance(data, list): raise ValueError("MANUAL_JSON_INVALID")
    rows=[]
    for i,r in enumerate(data):
        if not isinstance(r,dict): continue
        original=str(r.get("texto_original") or r.get("texto") or r.get("mensaje") or "").strip()
        if not original: continue
        rows.append({"id_mencion":str(r.get("id_mencion") or r.get("id") or f"manual-{i+1}"),"fecha":str(r.get("fecha") or datetime.now(timezone.utc).isoformat()),"fuente":str(r.get("fuente") or source),"texto_original":original,"texto_traducido":str(r.get("texto_traducido") or r.get("translated_text") or ""),"idioma_origen":str(r.get("idioma_origen") or r.get("source_language") or ""),"speaker":str(r.get("speaker") or r.get("emisor") or "")})
    return rows


def _conversation_id(source: str, filename: str) -> str:
    seed = f"{source}|{filename}".encode("utf-8")
    return "conv-" + hashlib.sha256(seed).hexdigest()[:16]


def _infer_role(speaker: str) -> str:
    low = str(speaker or "").strip().lower()
    if low in {"cliente", "customer", "usuario", "user", "paciente", "buyer", "comprador"}:
        return "cliente"
    if low in {"agente", "agent", "asesor", "asesora", "soporte", "support", "operador", "operator", "vendedor", "vendedora"}:
        return "agente"
    return "desconocido" if low else "no_atribuido"


def parse_manual(filename: str, content: str, source_type: str, source: str | None = None, conversation_id: str | None = None) -> list[dict]:
    st=source_type.lower()
    source = (source or source_type).strip() or source_type
    conversation_id = conversation_id or _conversation_id(source, filename)
    if st=="whatsapp" or filename.lower().endswith(".txt") and "whatsapp" in filename.lower():
        rows=parse_whatsapp(content)
    elif st in {"csv","spreadsheet"} or filename.lower().endswith(".csv"):
        rows=parse_csv(content)
    elif st=="json" or filename.lower().endswith(".json"):
        rows=parse_json(content)
    elif st in {"call_transcript","transcript","txt"} or filename.lower().endswith(".txt"):
        rows=parse_whatsapp(content) or [{"fecha":datetime.now(timezone.utc).isoformat(),"fuente":"call_transcript","texto_original":content.strip()}]
    else:
        raise ValueError("MANUAL_SOURCE_TYPE_UNSUPPORTED")
    if not rows: raise ValueError("MANUAL_NO_MESSAGES_FOUND")
    for idx, row in enumerate(rows, start=1):
        row["conversation_id"] = conversation_id
        row["turn_index"] = idx
        row["speaker_role"] = _infer_role(row.get("speaker", ""))
        row["idioma_origen"] = row.get("idioma_origen") or "es"
        row["idioma_analisis"] = row.get("idioma_analisis") or "es"
    return rows
