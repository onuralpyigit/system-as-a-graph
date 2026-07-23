from fastapi import FastAPI
from fastapi.testclient import TestClient

from msd.src.api.routes import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_health():
    response = client.get("/msd/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "csc": "msd"}
