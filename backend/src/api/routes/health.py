"""
Health check route for the GRIDLOCK API.

Provides liveness and readiness probes for container orchestration.
"""

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Liveness probe")
async def health_check():
    """Basic health check — confirms the API server is running."""
    return {"status": "healthy", "service": "gridlock-api"}


@router.get("/ready", summary="Readiness probe")
async def readiness_check():
    """Readiness check — confirms models are loaded and pipeline is ready.

    TODO: Add actual model loading status checks once models are integrated.
    """
    return {
        "status": "ready",
        "models_loaded": {
            "vehicle_detector": False,
            "segmentation": False,
            "sign_detector": False,
            "ocr": False,
            "fraud_classifier": False,
            "embedding_model": False,
        },
    }
