import json
import threading
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from python.connection_server import Handler


def test_knowledge_search_endpoint():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        body = json.dumps({
            "query": "todavía no me entregan",
            "limit": 5,
            "min_similarity": 0.25,
            "knowledge": [{
                "knowledge_id": "problem:demora_en_entrega",
                "type": "problem",
                "canonical_name": "demora_en_entrega",
                "aliases": ["no me entregan", "pedido demorado"],
                "frequency": 8,
                "confidence": 0.91,
                "status": "learned"
            }]
        }).encode()
        conn = HTTPConnection("127.0.0.1", server.server_port, timeout=3)
        conn.request("POST", "/api/knowledge/search", body=body, headers={"Content-Type": "application/json"})
        response = conn.getresponse()
        payload = json.loads(response.read().decode())
        conn.close()
        assert response.status == 200
        assert payload["ok"] is True
        assert payload["engine"] == "deterministic-v1"
        assert payload["results"][0]["concept"] == "demora_en_entrega"
    finally:
        server.shutdown()
        server.server_close()
