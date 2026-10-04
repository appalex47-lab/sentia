import json
import os
from pathlib import Path

PROMPT_VERSION = "1.0.0"
DEFAULT_MODEL = "command-r7b-12-2024"
MAX_CONTEXT_CHARS = 30000

class AIServiceError(RuntimeError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code

class CohereService:
    """Cohere adapter. Secrets are read only from process environment."""
    def __init__(self, model=None, client=None, prompt_version=PROMPT_VERSION):
        self.model = model or os.getenv("COHERE_MODEL") or DEFAULT_MODEL
        self.prompt_version = prompt_version
        self.client = client
        if self.client is None:
            key = os.getenv("COHERE_API_KEY")
            if key:
                try:
                    import cohere
                    self.client = cohere.ClientV2(api_key=key)
                except Exception:
                    self.client = None

    @property
    def available(self):
        return self.client is not None

    def _prompt(self, context, period):
        template = Path(__file__).resolve().parents[1] / "prompts" / "negative_insight_v1.txt"
        if template.exists():
            base = template.read_text(encoding="utf-8")
        else:
            base = "Analiza menciones negativas sin inventar datos."
        return f"{base}\nPeriodo: {period}\nMenciones:\n{context}"

    @staticmethod
    def _extract_text(response):
        message = getattr(response, "message", None)
        content = getattr(message, "content", None) if message else None
        if isinstance(content, str):
            return content.strip()
        parts = []
        for item in content or []:
            text = getattr(item, "text", None)
            if text:
                parts.append(str(text))
            elif isinstance(item, dict) and item.get("text"):
                parts.append(str(item["text"]))
        return "".join(parts).strip()

    @staticmethod
    def _validate_insight(data):
        if not isinstance(data, dict):
            raise AIServiceError("AI_INVALID_RESPONSE", "La respuesta de Cohere no es un objeto JSON.")
        summary = str(data.get("resumen", "")).strip()
        if not summary:
            raise AIServiceError("AI_INVALID_RESPONSE", "La respuesta de Cohere no contiene resumen.")
        return {
            "tipo": "daily_insight",
            "resumen": summary,
            "hallazgos": [str(x) for x in data.get("hallazgos", []) if str(x).strip()],
            "temas": [str(x) for x in data.get("temas", []) if str(x).strip()],
            "nivel_confianza": str(data.get("nivel_confianza", "baja")),
            "limitaciones": [str(x) for x in data.get("limitaciones", []) if str(x).strip()],
            "modelo_ia": str(data.get("modelo_ia", "")),
            "prompt_version": PROMPT_VERSION,
        }

    def summarize_negative(self, mentions, period="daily"):
        texts = [m.get("texto_original", "") for m in mentions if m.get("sentimiento_pysentimiento") == "negativo"]
        if not texts:
            return {"tipo":"daily_insight","resumen":"No hay menciones negativas suficientes para generar un insight.","hallazgos":[],"temas":[],"nivel_confianza":"baja","limitaciones":["Sin menciones negativas"],"prompt_version":PROMPT_VERSION}
        context = "\n".join(f"- {t[:500]}" for t in texts[:100])
        if len(context) > MAX_CONTEXT_CHARS:
            raise AIServiceError("AI_CONTEXT_TOO_LARGE", "El contexto excede el límite permitido para Cohere.")
        if not self.available:
            return None
        prompt = self._prompt(context, period)
        try:
            response = self.client.chat(
                model=self.model,
                messages=[{"role":"user","content":prompt}],
            )
        except Exception as exc:
            message = str(exc).lower()
            if "429" in message or "rate" in message or "quota" in message:
                code = "AI_RATE_LIMIT"
            elif "timeout" in message:
                code = "AI_TIMEOUT"
            elif "401" in message or "403" in message or "auth" in message:
                code = "AI_AUTH_ERROR"
            else:
                code = "AI_NETWORK_ERROR"
            raise AIServiceError(code, f"Error Cohere: {exc}") from exc
        raw = self._extract_text(response)
        if not raw:
            raise AIServiceError("AI_INVALID_RESPONSE", "Cohere devolvió una respuesta vacía.")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            # Preserve useful model text, but never pretend it is structured data.
            raise AIServiceError("AI_INVALID_RESPONSE", "Cohere no devolvió JSON estructurado válido.")
        result = self._validate_insight(parsed)
        result["modelo_ia"] = self.model
        return result
