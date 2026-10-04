from pipeline.sentiment import SentimentEngine

def test_sentiment_engine_contract():
    engine = SentimentEngine(allow_fallback=True)
    sentiment, confidence, score = engine.predict("Excelente servicio")
    assert sentiment in {"positivo", "negativo", "neutro"}
    assert 0 <= confidence <= 1
    assert -1 <= score <= 1
