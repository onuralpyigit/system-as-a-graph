from fastapi import APIRouter

router = APIRouter(prefix="/scg", tags=["scg"])


@router.get("/health")
def health():
    return {"status": "ok", "csc": "scg"}
