import json
from pathlib import Path
from pipeline.orchestrator import Pipeline, PipelineConfig, clean_text

def test_clean_and_pipeline():
    rows=json.loads(open(Path(__file__).parent / "fixtures" / "mentions.json",encoding="utf-8").read())
    result=Pipeline(PipelineConfig()).run(rows)
    assert len(result["mentions"])==3
    assert result["mentions"][0]["sentimiento_pysentimiento"]=="positivo"
    assert result["mentions"][1]["categoria"]=="logistica"
    assert 0 <= result["mentions"][1]["score_matematico"] <= 100

def test_dedup():
    rows=[
      {"id_mencion":"a","fecha":"2026-10-01T10:00:00Z","fuente":"x","texto_original":"mismo texto"},
      {"id_mencion":"b","fecha":"2026-10-01T10:00:00Z","fuente":"x","texto_original":"mismo texto"}
    ]
    ms=Pipeline(PipelineConfig()).run(rows)["mentions"]
    assert ms[1]["es_duplicado"] is True


def test_schema_validator_rejects_invalid_payload():
    from pipeline.validation import assert_valid_payload
    rows=[{"texto_original":"válido","fecha":"2026-10-01T10:00:00Z","fuente":"x"}]
    result=Pipeline(PipelineConfig()).run(rows)
    result["mentions"][0]["score_matematico"] = 101
    try:
        assert_valid_payload(result)
    except ValueError as exc:
        assert "SCHEMA_VALIDATION_FAILED" in str(exc)
    else:
        raise AssertionError("El validador debía bloquear score_matematico > 100")

def test_conversation_level_analysis():
    rows = [
      {"id_mencion":"c1","conversation_id":"conv-1","turn_index":1,"fecha":"2026-10-01T10:00:00Z","fuente":"whatsapp","speaker":"Cliente","speaker_role":"cliente","texto_original":"Llevo tres dias esperando mi pedido."},
      {"id_mencion":"c2","conversation_id":"conv-1","turn_index":2,"fecha":"2026-10-01T10:01:00Z","fuente":"whatsapp","speaker":"Agente","speaker_role":"agente","texto_original":"Voy a revisar el problema."},
      {"id_mencion":"c3","conversation_id":"conv-1","turn_index":3,"fecha":"2026-10-01T10:02:00Z","fuente":"whatsapp","speaker":"Cliente","speaker_role":"cliente","texto_original":"Gracias, quedó resuelto."}
    ]
    conv = Pipeline(PipelineConfig()).run(rows)["conversations"][0]
    assert conv["analysis"]["turn_count"] == 3
    assert conv["analysis"]["analysis_language"] == "es"
    assert 0 <= conv["analysis"]["friction_score"] <= 100
    assert 0 <= conv["analysis"]["resolution_score"] <= 100
    assert conv["analysis"]["sentiment_trend"] in {"mejora","empeora","estable"}
