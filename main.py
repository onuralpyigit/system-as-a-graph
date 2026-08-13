import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from adp.src.api.routes import router as adp_router
from csm.data_binder.src.api.routes import router as csm_data_binder_router
from csm.model_manager.src.api.routes import router as csm_model_manager_router
from frd.src.api.routes import router as frd_router
from msd.src.api.routes import router as msd_router
from scg.src.api.routes import router as scg_router
from vae.design_analyzer.src.api.routes import router as vae_design_analyzer_router
from vae.design_evaluator.src.api.routes import router as vae_design_evaluator_router
from vae.design_verifier.src.api.routes import router as vae_design_verifier_router
from vae.operations_panel.src.api.routes import router as vae_operations_panel_router

#: Origins the Operations Panel UI is served from. The API and the web app
#: run as separate origins (different ports in dev, likely different hosts in
#: production), so the browser needs an explicit CORS allowance to call this
#: API at all.
WEB_ORIGINS_ENV_VAR = "WEB_ALLOWED_ORIGINS"
_DEFAULT_WEB_ORIGINS = "http://localhost:3000"

app = FastAPI(title="system-as-a-graph API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv(WEB_ORIGINS_ENV_VAR, _DEFAULT_WEB_ORIGINS).split(",")
        if origin.strip()
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(msd_router)
app.include_router(scg_router)
app.include_router(frd_router)
app.include_router(adp_router)
app.include_router(csm_model_manager_router)
app.include_router(csm_data_binder_router)
app.include_router(vae_operations_panel_router)
app.include_router(vae_design_verifier_router)
app.include_router(vae_design_analyzer_router)
app.include_router(vae_design_evaluator_router)
