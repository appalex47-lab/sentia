"""Deterministic conversation-level analysis for Sentia.

The module intentionally does not infer speaker identity. It aggregates turn-level
signals and exposes explainable metrics that can later be enriched by AI.
"""

FRICTION_TERMS = (
    "retraso", "no llega", "no funciona", "error", "falla", "problema",
    "queja", "molesto", "molesta", "esperando", "cancelar", "devolver",
    "devolución", "cobro", "cargo", "urgente", "nunca", "otra vez"
)
RESOLUTION_TERMS = (
    "resuelto", "resuelta", "solucionado", "solucionada", "listo", "lista",
    "confirmado", "confirmada", "queda resuelto", "quedó resuelto", "gracias"
)


def _ratio(part, total):
    return round(part / total, 4) if total else 0.0


def analyze_conversation(conversation, mentions_by_id):
    turns = sorted(conversation.get("turns", []), key=lambda x: x.get("turn_index", 0))
    mentions = [mentions_by_id[t["mention_id"]] for t in turns if t.get("mention_id") in mentions_by_id]
    total = len(mentions)
    negative = sum(m.get("sentimiento_pysentimiento") == "negativo" for m in mentions)
    positive = sum(m.get("sentimiento_pysentimiento") == "positivo" for m in mentions)
    neutral = total - negative - positive
    scores = [float(m.get("score_matematico", 0)) for m in mentions]
    texts = [str(m.get("texto_limpio", "")).lower() for m in mentions]
    friction_hits = sum(any(term in text for term in FRICTION_TERMS) for text in texts)
    resolution_hits = sum(any(term in text for term in RESOLUTION_TERMS) for text in texts)
    negative_indices = [i for i, m in enumerate(mentions) if m.get("sentimiento_pysentimiento") == "negativo"]
    trajectory = [m.get("sentimiento_pysentimiento") for m in mentions]
    first_score = scores[0] if scores else 0
    last_score = scores[-1] if scores else 0
    trend = "mejora" if last_score < first_score else "empeora" if last_score > first_score else "estable"
    friction = min(100, round(_ratio(negative, total) * 70 + _ratio(friction_hits, total) * 30))
    resolution = min(100, round(_ratio(resolution_hits, max(1, total)) * 70 + (30 if trajectory and trajectory[-1] == "positivo" else 0)))
    global_score = round(sum(scores) / total) if total else 0
    severity = "critica" if global_score >= 85 or negative >= max(3, total // 2 + 1) else "alta" if global_score >= 65 or negative else "media" if global_score >= 45 else "baja"
    return {
        "turn_count": total,
        "sentiment_counts": {"positivo": positive, "negativo": negative, "neutro": neutral},
        "sentiment_trajectory": trajectory,
        "sentiment_trend": trend,
        "first_score": first_score,
        "last_score": last_score,
        "score_global": global_score,
        "severidad_global": severity,
        "friction_score": friction,
        "resolution_score": resolution,
        "friction_hits": friction_hits,
        "resolution_hits": resolution_hits,
        "negative_turns": negative_indices,
        "unattributed_turns": conversation.get("unattributed_turns", 0),
        "analysis_language": "es"
    }
