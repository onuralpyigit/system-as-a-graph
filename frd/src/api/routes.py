from fastapi import APIRouter

router = APIRouter(prefix="/frd", tags=["frd"])


@router.get("/health")
def health():
    return {"status": "ok", "csc": "frd"}
