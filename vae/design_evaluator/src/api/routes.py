from fastapi import APIRouter

router = APIRouter(prefix="/vae/design-evaluator", tags=["vae-design-evaluator"])


@router.get("/health")
def health():
    return {"status": "ok", "csc": "vae", "csu": "design_evaluator"}
