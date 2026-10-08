"""Main FastAPI application entrypoint."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CERTIFICATES_DIR
from app.database import init_db
from app.routes.jobs import router as jobs_router
from app.routes.certificates import router as certificates_router

# Configure clean logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("bulk_certificate_app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for startup and shutdown hooks."""
    logger.info("Initializing Bulk Certificate Generator application...")
    CERTIFICATES_DIR.mkdir(parents=True, exist_ok=True)
    init_db()
    logger.info("Database initialized and storage directory verified at %s", CERTIFICATES_DIR)
    yield
    logger.info("Application shutting down.")


app = FastAPI(
    title="Bulk Certificate Generator API",
    description=(
        "Production-ready, beginner-friendly asynchronous backend for bulk personalized PDF "
        "certificate generation built with FastAPI, SQLite, SQLAlchemy, and ReportLab."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Enable CORS for frontend or local testing flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(jobs_router)
app.include_router(certificates_router)


@app.get("/", tags=["Health"])
def root():
    """Health check and overview endpoint."""
    return {
        "status": "online",
        "service": "Bulk Certificate Generator API",
        "version": "1.0.0",
        "documentation": "/docs",
        "endpoints": {
            "create_job": "POST /api/jobs/",
            "get_job_status": "GET /api/jobs/{job_id}",
            "list_certificates": "GET /api/jobs/{job_id}/certificates",
            "download_certificate": "GET /api/certificates/{certificate_id}",
        },
    }
