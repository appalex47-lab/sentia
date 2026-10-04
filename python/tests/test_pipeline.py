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
