from fastapi import FastAPI

from adp.src.api.routes import router as adp_router
from csm.data_binder.src.api.routes import router as csm_data_binder_router
from csm.model_manager.src.api.routes import router as csm_model_manager_router
from frd.src.api.routes import router as frd_router
from msd.src.api.routes import router as msd_router
from scg.src.api.routes import router as scg_router
from vae.design_analyzer.src.api.routes import router as vae_design_analyzer_router
from vae.design_evaluator.src.api.routes import router as vae_design_evaluator_router
from vae.design_verifier.src.api.routes import router as vae_design_verifier_router

app = FastAPI(title="system-as-a-graph API")


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(msd_router)
app.include_router(scg_router)
app.include_router(frd_router)
app.include_router(adp_router)
app.include_router(csm_model_manager_router)
app.include_router(csm_data_binder_router)
app.include_router(vae_design_verifier_router)
app.include_router(vae_design_analyzer_router)
app.include_router(vae_design_evaluator_router)
