from fastapi import APIRouter

router = APIRouter(prefix="/csm/model-manager", tags=["csm-model-manager"])


@router.get("/health")
def health():
    return {"status": "ok", "csc": "csm", "csu": "model_manager"}
