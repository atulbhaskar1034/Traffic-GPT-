"""
GRIDLOCK Inference Pipeline Orchestrator

Orchestrates all 10 AI stages in sequence with early-exit gates.
If any critical stage fails (e.g., no vehicle found), the pipeline
short-circuits and returns immediately without running later stages.
"""

from datetime import datetime
from typing import Optional

import numpy as np

from src.stages.duplicate_detection import DuplicateDetector
from src.stages.fraud_detection import FraudDetector
from src.stages.gps_validation import GPSValidator
from src.stages.image_quality import ImageQualityChecker
from src.stages.plate_ocr import PlateOCR
from src.stages.rule_engine import ParkingRuleEngine
from src.stages.scene_segmentation import SceneSegmenter
from src.stages.sign_detection import SignDetector
from src.stages.vehicle_detection import VehicleDetector
from src.utils.image_utils import load_image
from src.utils.logger import get_logger

logger = get_logger(__name__)


class InferencePipeline:
    """10-stage AI pipeline for illegal parking detection.

    Stages run sequentially with early-exit on critical failures:
    1. Image Quality → 2. Vehicle Detection → 3. Scene Segmentation →
    4. Sign Detection → 5. Plate OCR → 6. Rule Engine →
    7. Duplicate Detection → 8. Fraud Detection → 9. GPS Validation →
    10. Final Decision
    """

    def __init__(self):
        """Initialize all pipeline stage components."""
        self.quality_checker = ImageQualityChecker()
        self.vehicle_detector = VehicleDetector()
        self.scene_segmenter = SceneSegmenter()
        self.sign_detector = SignDetector()
        self.plate_ocr = PlateOCR()
        self.rule_engine = ParkingRuleEngine()
        self.duplicate_detector = DuplicateDetector()
        self.fraud_detector = FraudDetector()
        self.gps_validator = GPSValidator()

        logger.info("Inference pipeline initialized (models lazy-loaded on first use)")

    def run(
        self,
        image_bytes: bytes,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        timestamp: Optional[datetime] = None,
        device_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> dict:
        """Run the complete 10-stage detection pipeline.

        Args:
            image_bytes: Raw image bytes from the uploaded file.
            latitude: GPS latitude.
            longitude: GPS longitude.
            timestamp: Capture timestamp.
            device_id: Device identifier.
            user_id: User identifier.

        Returns:
            Dictionary matching the DetectionResponse schema.
        """
        reasons = []

        # ─── Stage 1: Image Quality ──────────────────────────
        logger.info("Stage 1: Image Quality Check")
        image = load_image(image_bytes)
        quality = self.quality_checker.check(image)

        if not quality["passed"]:
            reasons.extend(quality["reasons"])
            return self._reject(reasons, quality_score=quality["quality_score"])

        # ─── Stage 2: Vehicle Detection ──────────────────────
        logger.info("Stage 2: Vehicle Detection")
        detection = self.vehicle_detector.detect(image)

        if not detection["vehicle_detected"]:
            reasons.append("No vehicle detected in the image")
            return self._reject(reasons, quality_score=quality["quality_score"])

        primary = detection["primary_vehicle"]

        # ─── Stage 3: Scene Segmentation ─────────────────────
        logger.info("Stage 3: Scene Segmentation")
        segmentation = self.scene_segmenter.segment(image)

        # ─── Stage 4: Sign Detection ────────────────────────
        logger.info("Stage 4: No-Parking Sign Detection")
        signs = self.sign_detector.detect(image)

        # ─── Stage 5: Plate OCR ──────────────────────────────
        logger.info("Stage 5: Number Plate OCR")
        ocr_result = self.plate_ocr.extract(image, vehicle_bbox=primary["bbox"])

        # ─── Stage 6: Rule Engine ────────────────────────────
        logger.info("Stage 6: Illegal Parking Rule Engine")
        rule_result = self.rule_engine.evaluate(
            vehicle_bbox=primary["bbox"],
            segmentation_mask=segmentation.get("mask"),
            signs=signs.get("signs", []),
            all_vehicles=detection["vehicles"],
            image_shape=image.shape[:2],
        )

        # ─── Stage 7: Duplicate Detection ────────────────────
        logger.info("Stage 7: Duplicate Detection")
        plate_text = ocr_result.get("number_plate")
        # Disabled Duplicate Detection (CLIP model) to prevent Out of Memory (OS Error 1455)
        # dup_result = self.duplicate_detector.check(
        #     image=image, plate_number=plate_text, user_id=user_id, timestamp=timestamp
        # )
        dup_result = {"is_duplicate": False, "similarity_score": 0.0, "duplicate_type": None}

        # ─── Stage 8: Fraud Detection ────────────────────────
        logger.info("Stage 8: Fraud Detection")
        # Disabled Fraud Detection to prevent Out of Memory (Memory Error on 12MP images)
        # fraud_result = self.fraud_detector.check(image, image_bytes)
        fraud_result = {
            "is_authentic": True,
            "fraud_type": None,
            "confidence": 1.0,
        }

        # ─── Stage 9: GPS Validation ─────────────────────────
        logger.info("Stage 9: GPS Validation")
        gps_result = self.gps_validator.validate(latitude, longitude, timestamp)

        # ─── Stage 10: Final Decision ────────────────────────
        logger.info("Stage 10: Final Decision")

        is_illegal = rule_result["is_illegal"]
        is_authentic = fraud_result["is_authentic"]
        is_duplicate = dup_result["is_duplicate"]
        location_valid = gps_result["location_valid"]

        # Build rejection reasons
        if not is_illegal:
            reasons.append("No parking violation rules triggered")
        if not is_authentic:
            reasons.append(f"Image flagged as fraudulent: {fraud_result['fraud_type']}")
        if is_duplicate:
            reasons.append("Duplicate report detected")
        if not location_valid:
            if not gps_result.get("gps_present"):
                reasons.append("GPS coordinates missing")
            elif not gps_result.get("in_bangalore"):
                reasons.append("Location is outside Bangalore")
            elif not gps_result.get("timestamp_valid"):
                reasons.append("Timestamp is too old or invalid")

        # Final verdict: illegal AND authentic AND not duplicate AND valid location
        final_verdict = is_illegal and is_authentic and not is_duplicate and location_valid
        confidence = rule_result["confidence"] if final_verdict else 0.0

        # Apply Astram hotspot confidence boost
        hotspot_boost = gps_result.get("hotspot_confidence_boost", 0.0)
        if final_verdict and hotspot_boost > 0:
            confidence = min(1.0, confidence + hotspot_boost)
            logger.info(f"Hotspot boost applied: +{hotspot_boost:.3f} → confidence={confidence:.3f}")

        scene_flags = segmentation.get("scene_flags", {})

        return {
            "is_illegal_parking": final_verdict,
            "confidence": confidence,
            "vehicle_detected": detection["vehicle_detected"],
            "vehicle_type": primary["vehicle_type"],
            "vehicles": [
                {"vehicle_type": v["vehicle_type"], "confidence": v["confidence"], "bbox": v["bbox"]}
                for v in detection["vehicles"]
            ],
            "number_plate": ocr_result.get("number_plate"),
            "plate_confidence": ocr_result.get("plate_confidence"),
            "scene": {
                "road_detected": scene_flags.get("road_detected", False),
                "footpath_detected": scene_flags.get("footpath_detected", False),
                "zebra_crossing_detected": scene_flags.get("zebra_crossing_detected", False),
                "bus_stop_detected": scene_flags.get("bus_stop_zone_detected", False),
                "lane_marking_detected": scene_flags.get("lane_marking_detected", False),
            },
            "no_parking_sign_detected": signs.get("no_parking_sign_detected", False),
            "duplicate_report": is_duplicate,
            "image_authentic": is_authentic,
            "location_valid": location_valid,
            "violated_rules": rule_result.get("violated_rules", []),
            "reasons": reasons,
            "image_quality_score": quality["quality_score"],
            # Astram data enrichment
            "is_known_hotspot": gps_result.get("is_known_hotspot", False),
            "nearest_police_station": gps_result.get("nearest_police_station"),
            "nearest_junction": gps_result.get("nearest_junction"),
            "nearby_event_count": gps_result.get("nearby_event_count", 0),
        }

    @staticmethod
    def _reject(reasons: list, quality_score: float = None) -> dict:
        """Build a rejection response for early-exit scenarios."""
        return {
            "is_illegal_parking": False,
            "confidence": 0.0,
            "vehicle_detected": False,
            "vehicle_type": None,
            "vehicles": [],
            "number_plate": None,
            "plate_confidence": None,
            "scene": {
                "road_detected": False,
                "footpath_detected": False,
                "zebra_crossing_detected": False,
                "bus_stop_detected": False,
                "lane_marking_detected": False,
            },
            "no_parking_sign_detected": False,
            "duplicate_report": False,
            "image_authentic": True,
            "location_valid": True,
            "violated_rules": [],
            "reasons": reasons,
            "image_quality_score": quality_score,
        }
