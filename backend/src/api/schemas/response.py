"""
Response schemas for the GRIDLOCK detection API.

Defines the structured output returned after AI pipeline processing.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class VehicleInfo(BaseModel):
    """Detected vehicle information."""

    vehicle_type: str = Field(..., description="Type of vehicle detected.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence.")
    bbox: List[float] = Field(
        ...,
        description="Bounding box [x1, y1, x2, y2] in pixels.",
    )


class SceneInfo(BaseModel):
    """Scene understanding results."""

    road_detected: bool = False
    footpath_detected: bool = False
    zebra_crossing_detected: bool = False
    bus_stop_detected: bool = False
    lane_marking_detected: bool = False


class DetectionResponse(BaseModel):
    """Full response from the GRIDLOCK illegal parking detection pipeline.

    Contains results from all 10 pipeline stages aggregated into
    a single structured response.
    """

    # ─── Core Verdict ─────────────────────────────────────────
    is_illegal_parking: bool = Field(
        ..., description="Final verdict: is this illegal parking?"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Overall confidence score."
    )

    # ─── Vehicle Detection (Stage 2) ─────────────────────────
    vehicle_detected: bool = Field(False, description="Was any vehicle detected?")
    vehicle_type: Optional[str] = Field(None, description="Primary vehicle type.")
    vehicles: List[VehicleInfo] = Field(
        default_factory=list, description="All detected vehicles."
    )

    # ─── Number Plate (Stage 5) ──────────────────────────────
    number_plate: Optional[str] = Field(None, description="Extracted license plate text.")
    plate_confidence: Optional[float] = Field(None, description="OCR confidence score.")

    # ─── Scene Understanding (Stage 3) ───────────────────────
    scene: SceneInfo = Field(default_factory=SceneInfo)

    # ─── Sign Detection (Stage 4) ────────────────────────────
    no_parking_sign_detected: bool = Field(
        False, description="No-parking sign found in frame?"
    )

    # ─── Integrity Checks ────────────────────────────────────
    duplicate_report: bool = Field(False, description="Is this a duplicate report?")
    image_authentic: bool = Field(True, description="Is the image genuine?")
    location_valid: bool = Field(True, description="Is the GPS location valid?")

    # ─── Violated Rules ──────────────────────────────────────
    violated_rules: List[str] = Field(
        default_factory=list,
        description="List of specific parking rules violated.",
    )

    # ─── Rejection Reasons (if not illegal) ──────────────────
    reasons: List[str] = Field(
        default_factory=list,
        description="Reasons why the report was rejected (if applicable).",
    )

    # ─── Quality & Metadata ──────────────────────────────────
    image_quality_score: Optional[float] = Field(
        None, description="Image quality score (0-1)."
    )
    processing_time_ms: Optional[float] = Field(
        None, description="Total pipeline processing time in milliseconds."
    )

    # ─── Astram Data Enrichment (from Bangalore traffic data) ─
    is_known_hotspot: bool = Field(
        False, description="Location is a known traffic violation hotspot (from Astram data)."
    )
    nearest_police_station: Optional[str] = Field(
        None, description="Nearest police station jurisdiction."
    )
    nearest_junction: Optional[str] = Field(
        None, description="Nearest major junction (from Astram data)."
    )
    nearby_event_count: int = Field(
        0, description="Number of historical traffic events within 500m (from Astram data)."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "is_illegal_parking": True,
                "confidence": 0.93,
                "vehicle_detected": True,
                "vehicle_type": "car",
                "vehicles": [
                    {
                        "vehicle_type": "car",
                        "confidence": 0.95,
                        "bbox": [120.0, 200.0, 450.0, 500.0],
                    }
                ],
                "number_plate": "KA01AB1234",
                "plate_confidence": 0.88,
                "scene": {
                    "road_detected": True,
                    "footpath_detected": False,
                    "zebra_crossing_detected": False,
                    "bus_stop_detected": False,
                    "lane_marking_detected": True,
                },
                "no_parking_sign_detected": True,
                "duplicate_report": False,
                "image_authentic": True,
                "location_valid": True,
                "violated_rules": [
                    "Vehicle parked under no-parking sign",
                    "Vehicle blocking traffic lane (52% occupancy)",
                ],
                "reasons": [],
                "image_quality_score": 0.87,
                "processing_time_ms": 1340.5,
            }
        }
