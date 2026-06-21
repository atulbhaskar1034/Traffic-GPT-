"""
Request schemas for the GRIDLOCK detection API.

Defines the expected input format for parking violation reports.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DetectionRequest(BaseModel):
    """Schema for an illegal parking detection request.

    The image is uploaded as a multipart file separately.
    This schema carries the associated metadata.
    """

    latitude: Optional[float] = Field(
        None,
        ge=-90,
        le=90,
        description="GPS latitude of the capture location.",
    )
    longitude: Optional[float] = Field(
        None,
        ge=-180,
        le=180,
        description="GPS longitude of the capture location.",
    )
    timestamp: Optional[datetime] = Field(
        None,
        description="ISO 8601 timestamp of when the photo was taken.",
    )
    device_id: Optional[str] = Field(
        None,
        max_length=128,
        description="Unique device identifier.",
    )
    user_id: str = Field(
        ...,
        max_length=128,
        description="Unique user identifier.",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "latitude": 12.9716,
                "longitude": 77.5946,
                "timestamp": "2026-06-17T14:30:00+05:30",
                "device_id": "DEVICE-ABC-123",
                "user_id": "USER-001",
            }
        }
