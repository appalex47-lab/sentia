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
