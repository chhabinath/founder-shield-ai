from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.errors import register_error_handlers


def _app() -> FastAPI:
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/boom")
    def boom():
        raise HTTPException(status_code=403, detail="nope")

    @app.get("/crash")
    def crash():
        raise RuntimeError("secret-token=sk-SHOULDNOTLEAK123")

    return app


def test_http_exception_envelope():
    client = TestClient(_app())
    resp = client.get("/boom")
    assert resp.status_code == 403
    body = resp.json()
    assert body["error"]["code"] == "forbidden"
    assert body["error"]["request_id"]


def test_unhandled_exception_hides_internals():
    client = TestClient(_app(), raise_server_exceptions=False)
    resp = client.get("/crash")
    assert resp.status_code == 500
    body = resp.json()
    assert body["error"]["code"] == "internal_error"
    # No leaked secret / internal detail in the client response.
    assert "sk-SHOULDNOTLEAK123" not in resp.text
    assert "RuntimeError" not in resp.text
