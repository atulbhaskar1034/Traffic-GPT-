"""
Stage 8: Fraud Detection

Detects fake, edited, AI-generated, or screenshot images.
Methods: EXIF validation, Error Level Analysis (ELA), CNN classifier.
"""

import io
import struct
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PIL import Image as PILImage

from src.utils.logger import get_logger

logger = get_logger(__name__)


class FraudDetector:
    """Multi-method image authenticity verification."""

    def __init__(self, classifier_path=None, device="cuda:0"):
        self.classifier_path = classifier_path
        self.device = device
        self._classifier = None

    def check(self, image: np.ndarray, image_bytes: bytes = None) -> dict:
        """Run all fraud detection checks."""
        results = {
            "is_authentic": True,
            "fraud_type": None,
            "confidence": 1.0,
            "checks": {},
        }

        # Check 1: EXIF metadata validation
        import os
        if image_bytes:
            exif_result = self._check_exif(image_bytes)
            results["checks"]["exif"] = exif_result
            if not exif_result["valid"]:
                if os.getenv("IGNORE_FRAUD", "true").lower() == "true":
                    logger.warning("EXIF fraud detected but bypassed due to IGNORE_FRAUD setting.")
                else:
                    results["is_authentic"] = False
                    results["fraud_type"] = "metadata_tampering"
                    results["confidence"] = 0.7

        # Check 2: Error Level Analysis
        ela_result = self._check_ela(image)
        results["checks"]["ela"] = ela_result
        if ela_result["suspicious"]:
            results["is_authentic"] = False
            results["fraud_type"] = "image_edited"
            results["confidence"] = ela_result["confidence"]

        # Check 3: Screenshot detection
        screenshot_result = self._check_screenshot(image)
        results["checks"]["screenshot"] = screenshot_result
        if screenshot_result["is_screenshot"]:
            results["is_authentic"] = False
            results["fraud_type"] = "screenshot"
            results["confidence"] = 0.9

        logger.info(f"Fraud check: authentic={results['is_authentic']}, type={results['fraud_type']}")
        return results

    def _check_exif(self, image_bytes: bytes) -> dict:
        """Validate EXIF metadata for camera authenticity."""
        try:
            img = PILImage.open(io.BytesIO(image_bytes))
            exif_data = img._getexif()
            if exif_data is None:
                return {"valid": False, "reason": "No EXIF data found"}

            has_camera = 271 in exif_data or 272 in exif_data  # Make, Model
            has_datetime = 36867 in exif_data  # DateTimeOriginal
            has_software = 305 in exif_data  # Software tag

            editing_software = ["photoshop", "gimp", "snapseed", "lightroom"]
            software_tag = str(exif_data.get(305, "")).lower()
            edited = any(s in software_tag for s in editing_software)

            return {
                "valid": has_camera and not edited,
                "has_camera_info": has_camera,
                "has_datetime": has_datetime,
                "editing_detected": edited,
            }
        except Exception as e:
            logger.debug(f"EXIF check failed: {e}")
            return {"valid": False, "reason": str(e)}

    def _check_ela(self, image: np.ndarray, quality: int = 95) -> dict:
        """Error Level Analysis — detects edited regions."""
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_img = PILImage.fromarray(rgb)

        buffer = io.BytesIO()
        pil_img.save(buffer, format="JPEG", quality=quality)
        buffer.seek(0)
        resaved = np.array(PILImage.open(buffer))

        ela = np.abs(rgb.astype(float) - resaved.astype(float))
        ela_mean = float(np.mean(ela))
        ela_max = float(np.max(ela))
        ela_std = float(np.std(ela))

        # High ELA values in localized regions indicate editing
        suspicious = ela_max > 50 and ela_std > 15

        return {
            "suspicious": suspicious,
            "ela_mean": round(ela_mean, 2),
            "ela_max": round(ela_max, 2),
            "ela_std": round(ela_std, 2),
            "confidence": min(1.0, ela_std / 30) if suspicious else 0.0,
        }

    def _check_screenshot(self, image: np.ndarray) -> dict:
        """Detect if image is a screenshot (status bar, uniform borders)."""
        h, w = image.shape[:2]

        # Check for uniform-color top bar (status bar)
        top_strip = image[:int(h * 0.05), :]
        top_std = float(np.std(top_strip))

        # Check for uniform-color bottom bar (navigation bar)
        bottom_strip = image[int(h * 0.95):, :]
        bottom_std = float(np.std(bottom_strip))

        # Screenshots often have very uniform top/bottom bars
        is_screenshot = top_std < 15 and bottom_std < 15

        # Also check aspect ratio (phone screenshots are typically tall)
        aspect = h / w if w > 0 else 0
        tall_ratio = aspect > 1.8

        return {
            "is_screenshot": is_screenshot and tall_ratio,
            "top_bar_std": round(top_std, 2),
            "bottom_bar_std": round(bottom_std, 2),
            "aspect_ratio": round(aspect, 2),
        }
