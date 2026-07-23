from fastapi import APIRouter

router = APIRouter(prefix="/vae/design-analyzer", tags=["vae-design-analyzer"])


@router.get("/health")
def health():
    return {"status": "ok", "csc": "vae", "csu": "design_analyzer"}
