import importlib
import sys

from fastapi.testclient import TestClient


class DummyRagSystem:
    def query(self, question: str) -> str:
        return f"echo:{question}"

    def get_collection_stats(self):
        return {"total_documents": 0, "collection_name": "documents"}


def load_main(monkeypatch, api_key: str):
    monkeypatch.setenv("API_KEY", api_key)
    monkeypatch.setenv("ENABLE_DOCS", "false")
    for module_name in ["config", "main"]:
        sys.modules.pop(module_name, None)
    import main

    return importlib.reload(main)


def test_query_requires_api_key(monkeypatch):
    main = load_main(monkeypatch, "supersecret")
    monkeypatch.setattr(main, "get_rag_system", lambda: DummyRagSystem())
    client = TestClient(main.app)

    response = client.post("/query", json={"question": "hello"})

    assert response.status_code == 401


def test_query_accepts_valid_api_key(monkeypatch):
    main = load_main(monkeypatch, "supersecret")
    monkeypatch.setattr(main, "get_rag_system", lambda: DummyRagSystem())
    client = TestClient(main.app)

    response = client.post(
        "/query",
        json={"question": "hello"},
        headers={"X-API-Key": "supersecret"},
    )

    assert response.status_code == 200
    assert response.json()["answer"] == "echo:hello"
