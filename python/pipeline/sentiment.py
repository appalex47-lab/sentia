class SentimentEngine:
    """pysentimiento adapter with explicit deterministic fallback for offline tests."""
    def __init__(self, allow_fallback=True):
        self.allow_fallback = allow_fallback
        self._analyzer = None
        self.backend = "unavailable"
        try:
            from pysentimiento import create_analyzer
            self._analyzer = create_analyzer(task="sentiment", lang="es")
            self.backend = "pysentimiento"
        except Exception:
            if not allow_fallback:
                raise
            self.backend = "heuristic_fallback"

    def predict(self, text):
        if self._analyzer is not None:
            result = self._analyzer.predict(text)
            probs = getattr(result, "probas", {}) or {}
            label = str(getattr(result, "output", "NEU")).lower()
            mapped = {"pos":"positivo", "neg":"negativo", "neu":"neutro"}
            sentiment = mapped.get(label, label if label in mapped.values() else "neutro")
            confidence = float(max(probs.values())) if probs else 0.0
            signed = 1.0 if sentiment == "positivo" else -1.0 if sentiment == "negativo" else 0.0
            return sentiment, confidence, signed * confidence
        low = text.lower()
        positive=["excelente","genial","gracias","me encanta","bueno","feliz"]
        negative=["malo","horrible","retraso","error","falla","no funciona","queja"]
        p=sum(t in low for t in positive); n=sum(t in low for t in negative)
        if p>n: return "positivo", min(1,p/3), min(1,p/3)
        if n>p: return "negativo", min(1,n/3), -min(1,n/3)
        return "neutro", 0.34, 0.0
