from fastapi import APIRouter

router = APIRouter(prefix="/adp", tags=["adp"])


@router.get("/health")
def health():
    return {"status": "ok", "csc": "adp"}
