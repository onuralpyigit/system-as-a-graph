from fastapi import APIRouter

router = APIRouter(prefix="/csm/data-binder", tags=["csm-data-binder"])


@router.get("/health")
def health():
    return {"status": "ok", "csc": "csm", "csu": "data_binder"}
