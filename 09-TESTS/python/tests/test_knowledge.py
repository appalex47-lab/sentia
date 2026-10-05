from pipeline.knowledge import extract_knowledge, validate_and_learn


def test_knowledge_is_conversation_domain_only():
    mentions = {
        "m1": {"texto_original": "El cliente está muy molesto por el retraso del servicio."},
        "m2": {"texto_original": "El cliente sigue esperando y solicita seguimiento."},
    }
    conversations = [{"conversation_id": "c1", "turns": [{"mention_id": "m1", "turn_index": 0}, {"mention_id": "m2", "turn_index": 1}]}]
    result = extract_knowledge(conversations, mentions)
    types = {x["type"] for x in result}
    assert types <= {"topic", "entity", "intent", "problem", "organization", "pattern"}
    forbidden = {"sustancia", "laboratorio", "producto", "marca", "presentación", "sku"}
    assert not any(any(term in x["canonical_name"].lower() for term in forbidden) for x in result)


def test_learning_promotes_only_with_repeated_evidence():
    proposals = [{"type":"topic","canonical_name":"retraso","aliases":[],"frequency":2,"confidence":0.7,"status":"proposed"}]
    assert validate_and_learn(proposals)[0]["status"] == "proposed"
    proposals[0]["frequency"] = 3
    proposals[0]["confidence"] = 0.8
    assert validate_and_learn(proposals)[0]["status"] == "validated"
    proposals[0]["frequency"] = 5
    proposals[0]["confidence"] = 0.9
    assert validate_and_learn(proposals)[0]["status"] == "learned"


def test_learning_rejects_product_domain_terms():
    proposals = [{"type":"entity","canonical_name":"Producto ABC","aliases":[],"frequency":10,"confidence":0.99,"status":"proposed"}]
    assert validate_and_learn(proposals) == []


def test_learning_merges_existing_memory():
    existing = [{"type":"topic","canonical_name":"retraso","aliases":["demora"],"frequency":3,"confidence":0.8,"status":"validated"}]
    incoming = [{"type":"topic","canonical_name":"retraso","aliases":["tardanza"],"frequency":2,"confidence":0.85,"status":"proposed"}]
    result = validate_and_learn(incoming, existing)
    assert result[0]["frequency"] == 5
    assert set(result[0]["aliases"]) == {"demora", "tardanza"}
    assert result[0]["status"] == "learned"


def test_learning_does_not_invent_history():
    assert extract_knowledge([], {}) == []
    assert validate_and_learn([], []) == []


from pipeline.knowledge import calculate_semantic_similarity, normalize_semantic_text, search_knowledge


def _memory():
    return [{
        "knowledge_id": "problem:demora_en_entrega",
        "type": "problem",
        "canonical_name": "demora_en_entrega",
        "aliases": ["pedido demorado", "pedido retrasado", "no me entregan", "entrega tarde"],
        "frequency": 8, "confidence": 0.91, "status": "learned"
    }, {
        "knowledge_id": "intent:seguimiento",
        "type": "intent", "canonical_name": "seguimiento", "aliases": ["quiero saber el estado"],
        "frequency": 4, "confidence": 0.82, "status": "validated"
    }]


def test_semantic_normalization_is_stable():
    assert normalize_semantic_text("¡Mi PEDIDO se demoró muchísimo!") == ["pedido", "demora", "muchisimo"]


def test_exact_match_scores_one():
    result = calculate_semantic_similarity("seguimiento", _memory()[1])
    assert result["similarity"] == 1.0
    assert "exact_match" in result["match_reason"]


def test_alias_match_is_explainable():
    result = calculate_semantic_similarity("no me entregan", _memory()[0])
    assert result["similarity"] >= 0.9
    assert "alias_match" in result["match_reason"]


def test_paraphrase_recovers_delivery_delay():
    result = search_knowledge("todavía no me entregan", _memory(), min_similarity=0.35)
    assert result["results"]
    assert result["results"][0]["concept"] == "demora_en_entrega"


def test_delivery_delay_variants_are_retrievable():
    queries = ["mi pedido se demoró", "llevo días esperando", "la entrega viene tarde"]
    for query in queries:
        result = search_knowledge(query, _memory(), min_similarity=0.25)
        assert result["results"]
        assert result["results"][0]["concept"] == "demora_en_entrega"


def test_obvious_false_positive_is_not_returned():
    result = search_knowledge("quiero conocer el horario de atención", _memory(), min_similarity=0.35)
    assert not result["results"] or result["results"][0]["concept"] != "demora_en_entrega"


def test_rejected_memory_is_not_searchable():
    rejected = _memory() + [{"type":"problem","canonical_name":"cancelacion","aliases":["quiero cancelar"],"frequency":10,"confidence":0.99,"status":"rejected"}]
    result = search_knowledge("quiero cancelar", rejected, min_similarity=0.2)
    assert all(x["concept"] != "cancelacion" for x in result["results"])


def test_search_empty_memory():
    assert search_knowledge("demora", [], min_similarity=0.2)["results"] == []


def test_search_options_are_bounded_and_sorted():
    result = search_knowledge("pedido demorado", _memory(), limit=1, min_similarity=0)
    assert len(result["results"]) == 1
    assert 0 <= result["results"][0]["similarity"] <= 1


def test_search_invalid_query():
    import pytest
    with pytest.raises(ValueError, match="INVALID_QUERY"):
        search_knowledge("   ", _memory())


def test_no_catalog_domain_is_introduced():
    result = search_knowledge("producto farmacia", _memory(), min_similarity=0.0)
    assert all(x["concept"] not in {"sustancia", "laboratorio", "producto", "marca", "sku", "principio activo"} for x in result["results"])


def test_learning_records_provenance_and_engine_version():
    mentions = {
        "m1": {"texto_original": "El cliente espera una respuesta sobre retraso."},
        "m2": {"texto_original": "Sigue esperando por el retraso."},
    }
    conversations = [{"conversation_id": "c1", "turns": [{"mention_id": "m1"}, {"mention_id": "m2"}]}]
    result = extract_knowledge(conversations, mentions)
    item = next(x for x in result if x["canonical_name"] == "retraso")
    assert item["evidence_mention_count"] == 2
    assert item["evidence_conversation_count"] == 1
    assert item["evidence_mention_ids"] == ["m1", "m2"]
    assert item["evidence_conversation_ids"] == ["c1"]
    assert item["learning_engine"] == "deterministic-learning-v2"


def test_forbidden_catalog_alias_is_rejected():
    proposals = [{"type":"topic","canonical_name":"entrega","aliases":["producto ABC"],"frequency":5,"confidence":0.9}]
    assert validate_and_learn(proposals) == []


def test_search_skips_untrusted_catalog_memory():
    result = search_knowledge("producto ABC", [{
        "type":"topic","canonical_name":"entrega","aliases":["producto ABC"],
        "frequency":10,"confidence":0.99,"status":"learned"
    }], min_similarity=0.0)
    assert result["results"] == []
