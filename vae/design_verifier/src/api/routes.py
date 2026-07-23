from fastapi import APIRouter

router = APIRouter(prefix="/vae/design-verifier", tags=["vae-design-verifier"])


@router.get("/health")
def health():
    return {"status": "ok", "csc": "vae", "csu": "design_verifier"}
