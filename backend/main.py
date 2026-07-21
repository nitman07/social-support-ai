from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.v1 import applications, auth, decisions
from backend.core.config import settings
from backend.core.logging import get_logger, setup_logging
from backend.core.metrics import get_metrics
from backend.ml.model import ml_service

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(log_level=settings.app_log_level)
    await ml_service.load_model()
    logger.info("Application started")
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(applications.router, prefix="/api/v1")
app.include_router(decisions.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.app_name, "version": "0.1.0"}


@app.get("/metrics")
async def metrics():
    return get_metrics()
