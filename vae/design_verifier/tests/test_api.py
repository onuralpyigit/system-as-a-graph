from fastapi import FastAPI
from fastapi.testclient import TestClient

from vae.design_verifier.src.api.routes import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_health():
    response = client.get("/vae/design-verifier/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "csc": "vae", "csu": "design_verifier"}
