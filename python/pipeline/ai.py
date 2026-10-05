import json
import os
import io
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
    def __init__(self, model=None, client=None, prompt_version=PROMPT_VERSION, api_key=None):
        self.model = model or os.getenv("COHERE_MODEL") or DEFAULT_MODEL
        self.prompt_version = prompt_version
        self.client = client
        self.api_key = api_key or os.getenv("COHERE_API_KEY")
        if self.client is None:
            key = self.api_key
            if key:
                try:
                    import cohere
                    self.client = cohere.ClientV2(api_key=key)
                except Exception:
                    self.client = None

    @property
    def available(self):
        return self.client is not None


    def check_connection(self):
        if not self.available:
            raise AIServiceError("AI_AUTH_ERROR", "COHERE_API_KEY_MISSING_OR_SDK_UNAVAILABLE")
        try:
            # Avoid generating content for a credential check. The SDK exposes
            # check_api_key on the v1 client; when unavailable, fall back to a
            # minimal Chat call only as a compatibility path.
            import cohere
            key = self.api_key
            if key:
                checker = cohere.Client(api_key=key)
                checker.check_api_key()
                return True
            self.client.chat(model=self.model, messages=[{"role":"user","content":"Reply only: OK"}])
            return True
        except Exception as exc:
            message = str(exc).lower()
            if "429" in message or "rate" in message or "quota" in message:
                raise AIServiceError("AI_RATE_LIMIT", f"Error Cohere: {exc}") from exc
            if "401" in message or "403" in message or "498" in message or "auth" in message or "token" in message:
                raise AIServiceError("AI_AUTH_ERROR", f"Error Cohere: {exc}") from exc
            raise AIServiceError("AI_NETWORK_ERROR", f"Error Cohere: {exc}") from exc

    def translate_rows(self, rows, target_language="es"):
        if not rows:
            return {"rows": [], "translated_count": 0}
        if not self.available:
            raise AIServiceError("AI_AUTH_ERROR", "Cohere no está configurado.")
        # Keep a bounded batch to avoid silently sending oversized conversations.
        work = rows[:50]
        payload = [{"index": i, "text": str(r.get("texto_original", ""))[:2000], "source_language": r.get("idioma_origen", "")} for i, r in enumerate(work)]
        prompt = (
            "Traduce al idioma destino cada texto. Devuelve SOLO un JSON array con objetos "
            "{\"index\": number, \"translated\": string}. No resumas, no expliques y conserva nombres, "
            "fechas y sentido. Idioma destino: " + str(target_language) + "\nTEXTOS:\n" + json.dumps(payload, ensure_ascii=False)
        )
        try:
            response = self.client.chat(model=self.model, messages=[{"role":"system","content":"Eres un traductor fiel para análisis de conversaciones."},{"role":"user","content":prompt}])
        except Exception as exc:
            raise AIServiceError("AI_NETWORK_ERROR", f"Error Cohere: {exc}") from exc
        raw=self._extract_text(response)
        try:
            data=json.loads(raw)
        except json.JSONDecodeError as exc:
            raise AIServiceError("AI_INVALID_RESPONSE", "Cohere no devolvió un JSON de traducción válido.") from exc
        if not isinstance(data,list):
            raise AIServiceError("AI_INVALID_RESPONSE", "La traducción no devolvió una lista.")
        by_index={int(x.get("index")):str(x.get("translated","")) for x in data if isinstance(x,dict) and str(x.get("translated","")).strip()}
        out=[]
        for i,row in enumerate(work):
            item=dict(row)
            if i in by_index:
                item["texto_traducido"]=by_index[i]
                item["idioma_analisis"]=target_language
                item["metodo_traduccion"]="cohere"
            out.append(item)
        out.extend(rows[50:])
        return {"rows": out, "translated_count": sum(1 for i in range(len(work)) if i in by_index), "target_language": target_language}


    def transcribe_audio(self, audio_bytes, filename, language="es", temperature=0.0):
        """Transcribe supported audio through Cohere Transcribe.

        Spanish is the default for Sentia manual call ingestion. Cohere Transcribe
        requires an explicit ISO-639-1 language and does not provide diarization.
        """
        if not audio_bytes:
            raise AIServiceError("AI_INVALID_AUDIO", "El archivo de audio está vacío.")
        if len(audio_bytes) > 25 * 1024 * 1024:
            raise AIServiceError("AI_AUDIO_TOO_LARGE", "Cohere Transcribe admite archivos de hasta 25 MB.")
        if not self.available:
            raise AIServiceError("AI_AUTH_ERROR", "Cohere no está configurado.")
        lang = (language or "es").strip().lower()
        if len(lang) != 2:
            raise AIServiceError("AI_AUDIO_LANGUAGE_REQUIRED", "El idioma del audio debe ser ISO-639-1, por ejemplo es.")
        try:
            response = self.client.audio.transcriptions.create(
                model="cohere-transcribe-03-2026",
                language=lang,
                file=io.BytesIO(audio_bytes),
                temperature=temperature,
            )
        except Exception as exc:
            message=str(exc).lower()
            if "429" in message or "rate" in message or "quota" in message:
                raise AIServiceError("AI_RATE_LIMIT", f"Error Cohere: {exc}") from exc
            if "401" in message or "403" in message or "498" in message or "auth" in message:
                raise AIServiceError("AI_AUTH_ERROR", f"Error Cohere: {exc}") from exc
            raise AIServiceError("AI_NETWORK_ERROR", f"Error Cohere Transcribe: {exc}") from exc
        text = getattr(response, "text", None)
        if text is None and isinstance(response, dict):
            text = response.get("text")
        text = str(text or "").strip()
        if not text:
            raise AIServiceError("AI_EMPTY_TRANSCRIPTION", "Cohere no devolvió texto de transcripción.")
        return {"text": text, "language": lang, "model": "cohere-transcribe-03-2026", "diarization": False}

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
