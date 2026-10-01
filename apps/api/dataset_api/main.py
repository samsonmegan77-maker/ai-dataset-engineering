from __future__ import annotations
import logging, uuid
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dataset_engineering import __version__
from dataset_engineering.config import Settings
from dataset_api.routes.datasets import router as datasets_router
from dataset_api.routes.processing import router as processing_router
from dataset_api.routes.imports import router as imports_router
from dataset_api.routes.provenance import router as provenance_router
from dataset_api.dependencies.repository import get_service
settings = Settings.from_env()
logging.basicConfig(level=getattr(logging, settings.log_level, logging.INFO), format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("dataset_api")
app = FastAPI(title="AI Dataset Engineering API", version=__version__, description="Stateful dataset validation, quality, processing, provenance, and evaluation service.")
app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins), allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["*"])
@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > settings.max_upload_bytes:
        return JSONResponse(status_code=413, content={"error":"request_too_large","message":"Request body exceeds configured limit"}, headers={"X-Request-ID": request_id})
    response = await call_next(request); response.headers["X-Request-ID"] = request_id; return response
@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError): return JSONResponse(status_code=422, content={"error":"validation_error","message":"Request validation failed","details":exc.errors()})
@app.exception_handler(KeyError)
async def key_error(_: Request, exc: KeyError): return JSONResponse(status_code=404, content={"error":"not_found","message":str(exc).strip("'")})
@app.get("/health", tags=["health"])
def health(): return {"status":"ok","version":__version__}
@app.get("/readiness", tags=["health"])
def readiness(): get_service(settings.database_url).repo.list_datasets(); return {"status":"ready","storage":"configured"}
app.include_router(datasets_router); app.include_router(processing_router); app.include_router(imports_router); app.include_router(provenance_router)
@app.get("/api/v1/health", tags=["health"], operation_id="api_v1_health")
def api_v1_health(): return {"status":"ok","version":__version__}
@app.get("/api/v1/readiness", tags=["health"], operation_id="api_v1_readiness")
def api_v1_readiness(): get_service(settings.database_url).repo.list_datasets(); return {"status":"ready","storage":"configured"}
app.include_router(datasets_router, prefix="/api/v1"); app.include_router(processing_router, prefix="/api/v1"); app.include_router(imports_router, prefix="/api/v1"); app.include_router(provenance_router, prefix="/api/v1")
