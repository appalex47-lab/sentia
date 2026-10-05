"""Conversation-domain knowledge extraction and conservative learning for Sentia."""
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone

KNOWLEDGE_ENGINE_VERSION = "deterministic-learning-v2"

STOPWORDS = {"para","porque","como","este","esta","esto","tengo","tiene","quiero","puede","puedo","cuando","donde","desde","sobre","entre","pero","muy","que","del","las","los","una","uno","con","por","sin","más","menos","hay","han","sus","son","fue","ser","era","nos","nosotros","usted","ustedes","cliente","agente"}
INTENT_PATTERNS = {
    "consulta": ("qué", "cual", "cuál", "cómo", "como", "información"),
    "queja": ("queja", "molesto", "molesta", "reclamo", "inconforme"),
    "solicitud": ("necesito", "quiero", "solicito", "quisiera", "podrían", "pueden"),
    "cancelacion": ("cancelar", "cancelación", "dar de baja"),
    "devolucion": ("devolver", "devolución", "reembolso"),
    "seguimiento": ("seguimiento", "estado", "esperando", "pendiente"),
}
PROBLEM_PATTERNS = {
    "entrega_retrasada": ("retraso", "tardó", "tardo", "no llega", "no ha llegado", "esperando"),
    "cobro": ("cobro", "cargo", "cargos", "cobrado", "factura"),
    "fallo_servicio": ("no funciona", "error", "falla", "fallando", "caído", "caida"),
    "atencion": ("nadie responde", "no me contestan", "mala atención", "mal servicio"),
}
FORBIDDEN_CATALOG_TERMS = {"sustancia", "laboratorio", "producto", "marca", "presentación", "sku", "principio activo"}
ALLOWED_TYPES = {"topic", "entity", "intent", "problem", "organization", "pattern"}


def _norm(text):
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def _learned_entity(text):
    raw = str(text or "")
    candidates = re.findall(r"\b[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ-]{2,}(?:\s+[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ-]{2,}){0,2}", raw)
    return [c.strip() for c in candidates if c.strip()]


def extract_knowledge(conversations, mentions_by_id):
    counters, entities, intents, problems = Counter(), Counter(), Counter(), Counter()
    evidence = defaultdict(lambda: {"mentions": set(), "conversations": set()})
    for conv in conversations:
        for turn in conv.get("turns", []):
            m = mentions_by_id.get(turn.get("mention_id"), {})
            text = str(m.get("texto_original") or m.get("texto_limpio") or "")
            low = _norm(text)
            for token in re.findall(r"[a-záéíóúñü]{5,}", low):
                if token not in STOPWORDS:
                    counters[token] += 1
                    evidence[("topic", token)]["mentions"].add(str(turn.get("mention_id") or ""))
                    evidence[("topic", token)]["conversations"].add(str(conv.get("conversation_id") or ""))
            for entity in _learned_entity(text):
                entities[entity] += 1
                evidence[("entity", entity)]["mentions"].add(str(turn.get("mention_id") or ""))
                evidence[("entity", entity)]["conversations"].add(str(conv.get("conversation_id") or ""))
            for name, patterns in INTENT_PATTERNS.items():
                if any(p in low for p in patterns):
                    intents[name] += 1
                    evidence[("intent", name)]["mentions"].add(str(turn.get("mention_id") or ""))
                    evidence[("intent", name)]["conversations"].add(str(conv.get("conversation_id") or ""))
            for name, patterns in PROBLEM_PATTERNS.items():
                if any(p in low for p in patterns):
                    problems[name] += 1
                    evidence[("problem", name)]["mentions"].add(str(turn.get("mention_id") or ""))
                    evidence[("problem", name)]["conversations"].add(str(conv.get("conversation_id") or ""))
    learned = []
    for name, freq in counters.most_common(50):
        if freq >= 2: learned.append(_proposal("topic", name, freq, min(0.99, 0.55 + freq * 0.05), evidence=evidence[("topic", name)]))
    for name, freq in entities.most_common(50):
        learned.append(_proposal("entity", name, freq, min(0.95, 0.6 + freq * 0.05), evidence=evidence[("entity", name)]))
    for name, freq in intents.items(): learned.append(_proposal("intent", name, freq, 0.9, evidence=evidence[("intent", name)]))
    for name, freq in problems.items(): learned.append(_proposal("problem", name, freq, 0.9, evidence=evidence[("problem", name)]))
    return learned


def _proposal(kind, name, frequency, confidence, aliases=None, status="proposed", evidence=None, learned_at=None, rejection_reason=None):
    ev = evidence or {}
    mentions = sorted({str(x) for x in ev.get("mentions", []) if str(x)})
    conversations = sorted({str(x) for x in ev.get("conversations", []) if str(x)})
    row = {"type": kind, "canonical_name": name, "aliases": aliases or [], "frequency": int(frequency), "confidence": round(float(confidence), 4), "status": status,
           "evidence_mention_count": len(mentions), "evidence_conversation_count": len(conversations),
           "evidence_mention_ids": mentions[:100], "evidence_conversation_ids": conversations[:100],
           "learning_engine": KNOWLEDGE_ENGINE_VERSION}
    if learned_at: row["learned_at"] = str(learned_at)
    if rejection_reason: row["rejection_reason"] = str(rejection_reason)
    return row


def validate_and_learn(proposals, existing=None):
    """Merge proposals into memory conservatively. No LLM inference is treated as truth."""
    existing = existing or []
    merged = {}
    for item in existing:
        clean = _validate_item(item, preserve_status=True)
        if clean:
            merged[(clean["type"], _norm(clean["canonical_name"]))] = clean
    for item in proposals or []:
        clean = _validate_item(item, preserve_status=False)
        if not clean:
            continue
        key = (clean["type"], _norm(clean["canonical_name"]))
        old = merged.get(key)
        if old:
            old["frequency"] += clean["frequency"]
            old["confidence"] = max(old["confidence"], clean["confidence"])
            old["aliases"] = sorted(set(old["aliases"] + clean["aliases"]))
            old["evidence_mention_ids"] = sorted(set(old.get("evidence_mention_ids", []) + clean.get("evidence_mention_ids", [])))[:100]
            old["evidence_conversation_ids"] = sorted(set(old.get("evidence_conversation_ids", []) + clean.get("evidence_conversation_ids", [])))[:100]
            old["evidence_mention_count"] = len(old["evidence_mention_ids"])
            old["evidence_conversation_count"] = len(old["evidence_conversation_ids"])
            old["learning_engine"] = KNOWLEDGE_ENGINE_VERSION
            old["status"] = _status_for(old["frequency"], old["confidence"], old["status"])
            if old["status"] in {"validated", "learned"} and not old.get("learned_at"):
                old["learned_at"] = datetime.now(timezone.utc).isoformat()
        else:
            clean["status"] = _status_for(clean["frequency"], clean["confidence"], "proposed")
            if clean["status"] in {"validated", "learned"}:
                clean["learned_at"] = datetime.now(timezone.utc).isoformat()
            merged[key] = clean
    return sorted(merged.values(), key=lambda x: (-x["frequency"], x["type"], x["canonical_name"]))


def _validate_item(item, preserve_status=False):
    if not isinstance(item, dict): return None
    kind = str(item.get("type", "")).strip().lower()
    name = str(item.get("canonical_name", "")).strip()
    if kind not in ALLOWED_TYPES or not name: return None
    low = _norm(name)
    if any(term in low for term in FORBIDDEN_CATALOG_TERMS): return None
    aliases = [str(a).strip() for a in item.get("aliases", []) if str(a).strip()]
    if any(any(term in _norm(alias) for term in FORBIDDEN_CATALOG_TERMS) for alias in aliases): return None
    evidence_mentions = sorted({str(a).strip() for a in item.get("evidence_mention_ids", []) if str(a).strip()})[:100]
    evidence_conversations = sorted({str(a).strip() for a in item.get("evidence_conversation_ids", []) if str(a).strip()})[:100]
    frequency = max(1, int(item.get("frequency", 1)))
    confidence = min(1.0, max(0.0, float(item.get("confidence", 0))))
    status = str(item.get("status", "proposed")) if preserve_status else "proposed"
    if status not in {"proposed", "validated", "rejected", "learned"}: status = "proposed"
    rejection_reason = str(item.get("rejection_reason", "")).strip() or None
    learned_at = str(item.get("learned_at", "")).strip() or None
    return _proposal(kind, name, frequency, confidence, aliases, status,
                     evidence={"mentions": evidence_mentions, "conversations": evidence_conversations},
                     learned_at=learned_at, rejection_reason=rejection_reason)


def _status_for(frequency, confidence, previous):
    if previous == "rejected": return "rejected"
    if frequency >= 5 and confidence >= 0.85: return "learned"
    if frequency >= 3 and confidence >= 0.75: return "validated"
    return "proposed"


SEMANTIC_STOPWORDS = STOPWORDS | {"a", "al", "el", "la", "lo", "y", "o", "de", "en", "un", "una", "me", "te", "se", "mi", "tu", "ya", "todavia", "todavía", "dias", "días", "hoy", "ahora", "solo", "sigue", "siguen", "estar", "estoy", "está", "esta"}
SEMANTIC_EQUIVALENTS = {
    "demoro": "demora", "demorado": "demora", "demorada": "demora", "demorar": "demora",
    "retraso": "demora", "retrasado": "demora", "retrasada": "demora", "tarde": "demora",
    "esperando": "demora", "esperan": "demora", "esperar": "demora", "esperado": "demora", "espera": "demora",
    "entregan": "entrega", "entregado": "entrega", "entregar": "entrega", "llega": "entrega",
    "llegado": "entrega", "llegar": "entrega",
}


def normalize_semantic_text(text):
    """Return a stable token representation for deterministic retrieval."""
    import unicodedata
    raw = unicodedata.normalize("NFKD", str(text or "").lower())
    raw = "".join(ch for ch in raw if not unicodedata.combining(ch))
    raw = re.sub(r"[^a-z0-9ñü\s-]", " ", raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    tokens = []
    for t in re.findall(r"[a-z0-9ñü-]{2,}", raw.replace("_", " ")):
        if t in SEMANTIC_STOPWORDS:
            continue
        tokens.append(SEMANTIC_EQUIVALENTS.get(t, t))
    return tokens


def _token_set(text):
    return set(normalize_semantic_text(text))


def _jaccard(left, right):
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _contains_phrase(query, candidate):
    q = _norm(query)
    c = _norm(candidate)
    return bool(q and c and (q == c or q in c or c in q))


def calculate_semantic_similarity(query, knowledge):
    """Deterministic, explainable similarity score in [0, 1]."""
    if not isinstance(knowledge, dict) or not str(query or "").strip():
        return {"similarity": 0.0, "match_reason": []}
    concept = str(knowledge.get("canonical_name", ""))
    aliases = [str(a) for a in knowledge.get("aliases", []) if str(a).strip()]
    candidates = [concept, str(knowledge.get("label", ""))] + aliases
    candidates = [c for c in candidates if c.strip()]
    q_tokens = _token_set(query)
    best = 0.0
    reasons = []
    for candidate in candidates:
        c_tokens = _token_set(candidate)
        score = _jaccard(q_tokens, c_tokens)
        if _norm(query) == _norm(candidate):
            score = 1.0
            reason = "alias_match" if candidate in aliases else "exact_match"
        elif candidate in aliases and _contains_phrase(query, candidate):
            score = max(score, 0.96)
            reason = "alias_match"
        elif candidate in aliases and score >= 0.5:
            reason = "alias_match"
        elif _contains_phrase(query, candidate) or _contains_phrase(candidate, query):
            score = max(score, 0.82)
            reason = "normalized_phrase_match"
        elif score >= 0.34:
            reason = "token_similarity"
        else:
            reason = ""
        if score > best:
            best = score
            reasons = [reason] if reason else []
        elif score == best and reason and reason not in reasons:
            reasons.append(reason)
    if best > 0 and q_tokens:
        concept_tokens = _token_set(concept)
        if concept_tokens and q_tokens & concept_tokens and "token_similarity" not in reasons and best < 1.0:
            reasons.append("partial_token_match")
    return {"similarity": round(min(1.0, best), 4), "match_reason": reasons}


def search_knowledge(query, knowledge, limit=10, min_similarity=0.35):
    """Retrieve related knowledge without changing or promoting memory."""
    query = str(query or "").strip()
    if not query:
        raise ValueError("INVALID_QUERY")
    try:
        limit = max(1, min(50, int(limit)))
        min_similarity = max(0.0, min(1.0, float(min_similarity)))
    except (TypeError, ValueError):
        raise ValueError("INVALID_SEARCH_OPTIONS")
    results = []
    for item in knowledge or []:
        if not isinstance(item, dict):
            continue
        if item.get("status") == "rejected":
            continue
        if not _validate_item(item, preserve_status=True):
            continue
        score = calculate_semantic_similarity(query, item)
        if score["similarity"] < min_similarity:
            continue
        results.append({
            "knowledge_id": item.get("knowledge_id") or f"{item.get('type', '')}:{item.get('canonical_name', '')}",
            "concept": item.get("canonical_name", ""),
            "type": item.get("type", ""),
            "similarity": score["similarity"],
            "confidence": float(item.get("confidence", 0) or 0),
            "status": item.get("status", "proposed"),
            "frequency": int(item.get("frequency", 0) or 0),
            "aliases": list(item.get("aliases", []) or []),
            "match_reason": score["match_reason"],
        })
    status_rank = {"learned": 3, "validated": 2, "proposed": 1, "rejected": 0}
    results.sort(key=lambda x: (-x["similarity"], -x["confidence"], -status_rank.get(x["status"], 0), -x["frequency"]))
    return {"query": query, "results": results[:limit]}
