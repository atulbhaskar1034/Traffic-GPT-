"""
Detection route — main endpoint for illegal parking analysis.

Receives an image + metadata, runs the full AI pipeline,
and returns the structured detection response.
"""

import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from src.api.schemas.response import DetectionResponse
from src.pipeline.inference_pipeline import InferencePipeline
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Detection"])

# Pipeline singleton — initialized on first request
_pipeline: Optional[InferencePipeline] = None


def _get_pipeline() -> InferencePipeline:
    """Get or create the inference pipeline singleton."""
    global _pipeline
    if _pipeline is None:
        _pipeline = InferencePipeline()
        logger.info("Inference pipeline initialized")
    return _pipeline


@router.post(
    "/detect",
    response_model=DetectionResponse,
    summary="Detect illegal parking from image",
    description=(
        "Upload a smartphone image along with GPS coordinates, timestamp, "
        "device ID, and user ID. The AI pipeline will analyze the image "
        "and return a structured verdict on whether illegal parking is detected."
    ),
)
async def detect_illegal_parking(
    image: UploadFile = File(..., description="Captured smartphone image (JPEG/PNG)"),
    latitude: Optional[float] = Form(None, ge=-90, le=90),
    longitude: Optional[float] = Form(None, ge=-180, le=180),
    timestamp: Optional[str] = Form(None, description="ISO 8601 timestamp"),
    device_id: Optional[str] = Form(None, max_length=128),
    user_id: str = Form(..., max_length=128),
):
    """Run the full illegal parking detection pipeline on an uploaded image.

    The pipeline processes through 10 stages:
    1. Image quality check
    2. Vehicle detection
    3. Scene segmentation
    4. No-parking sign detection
    5. Number plate OCR
    6. Rule engine evaluation
    7. Duplicate detection
    8. Fraud detection
    9. GPS validation
    10. Multi-image verification

    Returns a comprehensive structured response with the verdict.
    """
    start_time = time.time()

    # ─── Validate image format ────────────────────────────────
    logger.info(f"Received image: filename={image.filename}, content_type={image.content_type}")
    if image.content_type not in ("image/jpeg", "image/png", "image/webp"):
        logger.error(f"Rejecting 400: Unsupported image format: {image.content_type}")
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image format: {image.content_type}. Use JPEG, PNG, or WebP.",
        )

    # ─── Read image bytes ─────────────────────────────────────
    image_bytes = await image.read()
    logger.info(f"Read image bytes: {len(image_bytes)} bytes")
    if len(image_bytes) < 1024:
        logger.error("Rejecting 400: Image file is too small.")
        raise HTTPException(status_code=400, detail="Image file is too small.")
    if len(image_bytes) > 20 * 1024 * 1024:
        logger.error("Rejecting 400: Image file exceeds 20MB limit.")
        raise HTTPException(status_code=400, detail="Image file exceeds 20MB limit.")

    # ─── Parse timestamp ──────────────────────────────────────
    parsed_ts = None
    if timestamp:
        try:
            parsed_ts = datetime.fromisoformat(timestamp)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid timestamp format. Use ISO 8601.")

    # ─── Run pipeline ─────────────────────────────────────────
    logger.info(f"Processing detection request from user={user_id}, device={device_id}")

    pipeline = _get_pipeline()
    result = pipeline.run(
        image_bytes=image_bytes,
        latitude=latitude,
        longitude=longitude,
        timestamp=parsed_ts,
        device_id=device_id,
        user_id=user_id,
    )

    # ─── Add processing time ─────────────────────────────────
    elapsed_ms = (time.time() - start_time) * 1000
    result["processing_time_ms"] = round(elapsed_ms, 1)

    logger.info(
        f"Detection complete: illegal={result['is_illegal_parking']}, "
        f"confidence={result['confidence']:.2f}, time={elapsed_ms:.0f}ms"
    )

    return DetectionResponse(**result)
