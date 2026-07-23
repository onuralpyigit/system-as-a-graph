from fastapi import APIRouter

router = APIRouter(prefix="/msd", tags=["msd"])


@router.get("/health")
def health():
    return {"status": "ok", "csc": "msd"}
