"""
Stage 6: Illegal Parking Rule Engine

Determines if a detected vehicle is illegally parked using
geometric reasoning on bounding boxes and segmentation masks.

This is pure logic — no ML model involved.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RuleThresholds:
    """Configurable thresholds for parking violation rules."""

    footpath_overlap_min: float = 0.30       # R1: Vehicle on footpath
    sign_proximity_pixels: float = 500.0     # R2: Distance to no-parking sign
    zebra_overlap_min: float = 0.20          # R3: Blocking zebra crossing
    lane_occupancy_max: float = 0.40         # R4: Blocking traffic lane
    bus_stop_overlap_min: float = 0.20       # R6: Blocking bus stop
    double_park_distance: float = 80.0       # R5: Pixel distance for double park


@dataclass
class RuleResult:
    """Result from a single rule evaluation."""

    rule_id: str
    rule_name: str
    violated: bool
    confidence: float
    description: str


class ParkingRuleEngine:
    """Rule-based engine for illegal parking determination.

    Evaluates 7 geometric rules by analyzing the spatial relationship
    between vehicle bounding boxes and segmentation masks/sign detections.
    """

    def __init__(self, thresholds: RuleThresholds = None):
        self.thresholds = thresholds or RuleThresholds()

    def evaluate(
        self,
        vehicle_bbox: List[float],
        segmentation_mask: Optional[np.ndarray],
        signs: List[dict],
        all_vehicles: List[dict],
        image_shape: Tuple[int, int],
    ) -> dict:
        """Evaluate all parking rules for a given vehicle.

        Args:
            vehicle_bbox: [x1, y1, x2, y2] of the primary vehicle.
            segmentation_mask: H×W mask with class indices (from Stage 3).
            signs: List of detected signs from Stage 4.
            all_vehicles: List of all detected vehicles from Stage 2.
            image_shape: (height, width) of the original image.

        Returns:
            Dictionary with:
                - is_illegal (bool): Any rule violated
                - violated_rules (list): Descriptions of violated rules
                - rule_results (list): Detailed results per rule
                - confidence (float): Aggregate confidence
        """
        results: List[RuleResult] = []
        t = self.thresholds

        # ─── R1: Vehicle on footpath ─────────────────────────
        if segmentation_mask is not None:
            overlap = self._compute_mask_overlap(vehicle_bbox, segmentation_mask, class_id=2)
            results.append(RuleResult(
                rule_id="R1",
                rule_name="Footpath parking",
                violated=overlap >= t.footpath_overlap_min,
                confidence=min(1.0, overlap / t.footpath_overlap_min) if overlap > 0 else 0.0,
                description=f"Vehicle overlaps footpath by {overlap:.1%}" if overlap >= t.footpath_overlap_min
                else f"Footpath overlap {overlap:.1%} below threshold",
            ))

        # ─── R2: Near no-parking sign ────────────────────────
        no_park_signs = [s for s in signs if s["sign_type"] == "no_parking_sign"]
        if no_park_signs:
            min_dist = min(
                self._bbox_distance(vehicle_bbox, s["bbox"]) for s in no_park_signs
            )
            violated = min_dist <= t.sign_proximity_pixels
            results.append(RuleResult(
                rule_id="R2",
                rule_name="No-parking zone",
                violated=violated,
                confidence=min(1.0, 1.0 - (min_dist / t.sign_proximity_pixels)) if violated else 0.0,
                description=f"Vehicle is {min_dist:.0f}px from no-parking sign" if violated
                else f"No-parking sign detected but {min_dist:.0f}px away",
            ))

        # ─── R3: Blocking zebra crossing ─────────────────────
        if segmentation_mask is not None:
            overlap = self._compute_mask_overlap(vehicle_bbox, segmentation_mask, class_id=3)
            results.append(RuleResult(
                rule_id="R3",
                rule_name="Zebra crossing blocked",
                violated=overlap >= t.zebra_overlap_min,
                confidence=min(1.0, overlap / t.zebra_overlap_min) if overlap > 0 else 0.0,
                description=f"Vehicle blocks zebra crossing by {overlap:.1%}" if overlap >= t.zebra_overlap_min
                else f"Zebra crossing overlap {overlap:.1%} below threshold",
            ))

        # ─── R4: Lane blocking ───────────────────────────────
        if segmentation_mask is not None:
            lane_occupancy = self._compute_lane_occupancy(vehicle_bbox, segmentation_mask, image_shape)
            results.append(RuleResult(
                rule_id="R4",
                rule_name="Traffic lane blocked",
                violated=lane_occupancy > t.lane_occupancy_max,
                confidence=min(1.0, lane_occupancy / t.lane_occupancy_max) if lane_occupancy > 0 else 0.0,
                description=f"Vehicle occupies {lane_occupancy:.0%} of traffic lane" if lane_occupancy > t.lane_occupancy_max
                else f"Lane occupancy {lane_occupancy:.0%} within limits",
            ))

        # ─── R5: Double parking ──────────────────────────────
        if len(all_vehicles) >= 2:
            is_double, neighbor = self._check_double_parking(vehicle_bbox, all_vehicles)
            results.append(RuleResult(
                rule_id="R5",
                rule_name="Double parking",
                violated=is_double,
                confidence=0.85 if is_double else 0.0,
                description="Double parking detected — vehicles parked side by side on road edge"
                if is_double else "No double parking detected",
            ))

        # ─── R6: Bus stop blocking ───────────────────────────
        if segmentation_mask is not None:
            overlap = self._compute_mask_overlap(vehicle_bbox, segmentation_mask, class_id=4)
            results.append(RuleResult(
                rule_id="R6",
                rule_name="Bus stop blocked",
                violated=overlap >= t.bus_stop_overlap_min,
                confidence=min(1.0, overlap / t.bus_stop_overlap_min) if overlap > 0 else 0.0,
                description=f"Vehicle blocks bus stop zone by {overlap:.1%}" if overlap >= t.bus_stop_overlap_min
                else f"Bus stop overlap {overlap:.1%} below threshold",
            ))

        # ─── R7: Restricted zone (any restriction sign) ─────
        restricted_signs = [s for s in signs if s["sign_type"] in ("restricted_zone_board", "tow_away_sign")]
        if restricted_signs:
            results.append(RuleResult(
                rule_id="R7",
                rule_name="Restricted zone violation",
                violated=True,
                confidence=max(s["confidence"] for s in restricted_signs),
                description=f"Vehicle in restricted zone ({restricted_signs[0]['sign_type']})",
            ))

        # ─── Aggregate ───────────────────────────────────────
        violated = [r for r in results if r.violated]
        is_illegal = len(violated) > 0
        confidence = max((r.confidence for r in violated), default=0.0) if is_illegal else 0.0

        output = {
            "is_illegal": is_illegal,
            "violated_rules": [f"{r.rule_name}: {r.description}" for r in violated],
            "rule_results": [
                {
                    "rule_id": r.rule_id,
                    "rule_name": r.rule_name,
                    "violated": r.violated,
                    "confidence": round(r.confidence, 3),
                    "description": r.description,
                }
                for r in results
            ],
            "confidence": round(confidence, 3),
        }

        logger.info(f"Rule engine: illegal={is_illegal}, violated={[r.rule_id for r in violated]}")
        return output

    # ─── Geometric Helper Methods ─────────────────────────────

    @staticmethod
    def _compute_mask_overlap(
        bbox: List[float], mask: np.ndarray, class_id: int
    ) -> float:
        """Compute overlap ratio between a bounding box and a segmentation class.

        Returns the fraction of bbox area that overlaps with the class mask.
        """
        x1, y1, x2, y2 = [int(v) for v in bbox]
        h, w = mask.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        if x2 <= x1 or y2 <= y1:
            return 0.0

        bbox_region = mask[y1:y2, x1:x2]
        class_pixels = np.sum(bbox_region == class_id)
        bbox_area = (x2 - x1) * (y2 - y1)

        return float(class_pixels / bbox_area) if bbox_area > 0 else 0.0

    @staticmethod
    def _bbox_distance(bbox1: List[float], bbox2: List[float]) -> float:
        """Compute center-to-center distance between two bounding boxes."""
        cx1 = (bbox1[0] + bbox1[2]) / 2
        cy1 = (bbox1[1] + bbox1[3]) / 2
        cx2 = (bbox2[0] + bbox2[2]) / 2
        cy2 = (bbox2[1] + bbox2[3]) / 2
        return ((cx1 - cx2) ** 2 + (cy1 - cy2) ** 2) ** 0.5

    @staticmethod
    def _compute_lane_occupancy(
        bbox: List[float], mask: np.ndarray, image_shape: Tuple[int, int]
    ) -> float:
        """Estimate how much of the road lane width the vehicle occupies."""
        x1, y1, x2, y2 = [int(v) for v in bbox]
        vehicle_width = x2 - x1

        # Estimate road width at the vehicle's vertical position
        mid_y = (y1 + y2) // 2
        h, w = mask.shape[:2]
        if mid_y >= h:
            return 0.0

        road_row = mask[mid_y, :]
        road_pixels = np.where(road_row == 1)[0]  # class_id=1 for road

        if len(road_pixels) < 10:
            # Fallback heuristic: If no road is segmented (because custom weights are missing),
            # estimate the road as 50% of the image width to allow testing the rule engine.
            road_width = w * 0.50
            return float(vehicle_width / road_width) if road_width > 0 else 0.0

        road_width = road_pixels[-1] - road_pixels[0]
        return float(vehicle_width / road_width) if road_width > 0 else 0.0

    @staticmethod
    def _check_double_parking(
        vehicle_bbox: List[float], all_vehicles: List[dict]
    ) -> Tuple[bool, Optional[dict]]:
        """Check if there's another vehicle parked directly alongside."""
        vx1, vy1, vx2, vy2 = vehicle_bbox
        v_cy = (vy1 + vy2) / 2
        v_width = vx2 - vx1

        for other in all_vehicles:
            ob = other["bbox"]
            if ob == vehicle_bbox:
                continue

            ox1, oy1, ox2, oy2 = ob
            o_cy = (oy1 + oy2) / 2

            # Check: similar vertical position (same "row") and adjacent horizontally
            vertical_overlap = abs(v_cy - o_cy) < (vy2 - vy1) * 0.5
            horizontal_gap = min(abs(vx1 - ox2), abs(ox1 - vx2))
            close_horizontally = horizontal_gap < v_width * 0.5

            if vertical_overlap and close_horizontally:
                return True, other

        return False, None
