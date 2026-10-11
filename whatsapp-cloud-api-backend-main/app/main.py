import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.core.logging import setup_logging
from app.services.scheduler_service import scheduler_service
from app.api.v1.router import api_v1_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager: starts database schema and background scheduler."""
    setup_logging()
    logger.info("Initializing WhatsApp Weekly PDF Report Automation System...")

    # Auto-create database tables on startup
    Base.metadata.create_all(bind=engine)
    logger.info("SQLAlchemy database schema verified.")

    # Start APScheduler background scheduler
    scheduler_service.start()

    yield

    # Graceful shutdown
    logger.info("Shutting down background scheduler...")
    scheduler_service.shutdown()
    logger.info("Application shutdown complete.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Production-grade backend for automated weekly PDF report generation and distribution "
        "via the official Meta WhatsApp Cloud API (Graph API v21.0)."
    ),
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Cross-Origin Resource Sharing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gzip compression for larger payloads
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include routes at root level (as specified in requirements)
app.include_router(api_v1_router)

# Also expose under /api/v1 prefix
app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/", include_in_schema=False)
def root():
    """Redirect root path to interactive Swagger documentation."""
    return RedirectResponse(url="/docs")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global unhandled exception fallback handler."""
    logger.error(f"Unhandled server error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred.",
            "error_type": exc.__class__.__name__
        }
    )
