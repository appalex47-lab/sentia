import json
import pytest
from pipeline.ai import CohereService, AIServiceError

class Item:
    def __init__(self, text): self.text=text
class Message:
    def __init__(self, content): self.content=content
class Response:
    def __init__(self, text): self.message=Message([Item(text)])
class FakeClient:
    def __init__(self, response): self.response=response
    def chat(self, **kwargs): return self.response


def test_ai_structured_response():
    payload={"resumen":"Se repiten retrasos.","hallazgos":["Entrega tardía"],"temas":["logística"],"nivel_confianza":"media","limitaciones":[]}
    service=CohereService(client=FakeClient(Response(json.dumps(payload))))
    result=service.summarize_negative([{"sentimiento_pysentimiento":"negativo","texto_original":"Mi paquete llegó tarde"}])
    assert result["tipo"] == "daily_insight"
    assert result["prompt_version"] == "1.0.0"
    assert result["modelo_ia"]


def test_ai_rejects_unstructured_response():
    service=CohereService(client=FakeClient(Response("texto libre")))
    with pytest.raises(AIServiceError) as exc:
        service.summarize_negative([{"sentimiento_pysentimiento":"negativo","texto_original":"Problema"}])
    assert exc.value.code == "AI_INVALID_RESPONSE"


def test_ai_context_limit():
    service=CohereService(client=FakeClient(Response("{}")))
    huge={"sentimiento_pysentimiento":"negativo","texto_original":"x"*600}
    with pytest.raises(AIServiceError) as exc:
        service.summarize_negative([huge]*100)
    assert exc.value.code == "AI_CONTEXT_TOO_LARGE"

class FakeTranslateClient:
    def chat(self, **kwargs):
        return Response('[{"index": 0, "translated": "La entrega fue tardía."}]')


def test_cohere_translate_rows():
    service=CohereService(client=FakeTranslateClient(), api_key="test-key")
    result=service.translate_rows([{"texto_original":"The delivery was late.","idioma_origen":"en"}], target_language="es")
    assert result["translated_count"] == 1
    assert result["rows"][0]["texto_traducido"] == "La entrega fue tardía."
    assert result["rows"][0]["metodo_traduccion"] == "cohere"


class FakeAudioTranscriptions:
    def create(self, **kwargs):
        class AudioResponse:
            text = "Hola, quiero saber cuándo llegará mi pedido."
        assert kwargs["model"] == "cohere-transcribe-03-2026"
        assert kwargs["language"] == "es"
        return AudioResponse()

class FakeAudioClient:
    def __init__(self): self.audio=type("Audio", (), {"transcriptions": FakeAudioTranscriptions()})()

def test_cohere_transcribe_spanish():
    service=CohereService(client=FakeAudioClient(), api_key="test-key")
    result=service.transcribe_audio(b"RIFF" + b"0"*100, "llamada.wav", language="es")
    assert result["language"] == "es"
    assert "pedido" in result["text"]
    assert result["diarization"] is False

def test_cohere_transcribe_size_limit():
    service=CohereService(client=FakeAudioClient(), api_key="test-key")
    with pytest.raises(AIServiceError) as exc:
        service.transcribe_audio(b"x"*(25*1024*1024+1), "llamada.wav", language="es")
    assert exc.value.code == "AI_AUDIO_TOO_LARGE"
