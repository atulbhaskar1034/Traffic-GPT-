"""
GRIDLOCK — FastAPI Application Entry Point.

Configures the FastAPI app with CORS, routes, exception handlers,
and startup/shutdown lifecycle events.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routes import detect, health
from src.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager.

    Handles startup (model preloading) and shutdown (cleanup) events.
    """
    # ─── Startup ──────────────────────────────────────────────
    logger.info("🚦 GRIDLOCK API starting up...")
    logger.info("Models will be lazy-loaded on first request.")
    # TODO: Pre-load models here for production (eliminate cold-start latency)
    yield
    # ─── Shutdown ─────────────────────────────────────────────
    logger.info("🛑 GRIDLOCK API shutting down...")


# ─── Create FastAPI App ───────────────────────────────────────
app = FastAPI(
    title="GRIDLOCK — Illegal Parking Detection API",
    description=(
        "AI-powered system for detecting illegal parking violations from "
        "smartphone images. Deployed for Bangalore Traffic Police.\n\n"
        "**Pipeline Stages:** Image Quality → Vehicle Detection → "
        "Scene Segmentation → Sign Detection → OCR → Rule Engine → "
        "Duplicate Check → Fraud Detection → GPS Validation"
    ),
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS Middleware ──────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Register Routes ─────────────────────────────────────────
app.include_router(health.router, prefix="/api/v1")
app.include_router(detect.router, prefix="/api/v1")


# ─── Global Exception Handler ────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler to prevent stack traces in production."""
    logger.error(f"Unhandled exception on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred during processing.",
        },
    )


# ─── Root Redirect ───────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to API docs."""
    return {
        "service": "GRIDLOCK — Illegal Parking Detection API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
