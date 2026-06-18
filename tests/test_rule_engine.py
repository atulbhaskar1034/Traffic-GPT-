"""Tests for Stage 6: Parking Rule Engine."""

import numpy as np
import pytest

from src.stages.rule_engine import ParkingRuleEngine, RuleThresholds


@pytest.fixture
def engine():
    return ParkingRuleEngine()


def _make_mask(h=480, w=640, road_region=True, footpath_region=False):
    """Create a synthetic segmentation mask."""
    mask = np.zeros((h, w), dtype=np.uint8)
    if road_region:
        mask[200:480, :] = 1  # Road (class 1)
    if footpath_region:
        mask[150:200, :] = 2  # Footpath (class 2)
    return mask


class TestRuleEngine:
    def test_vehicle_on_footpath_is_illegal(self, engine):
        mask = _make_mask(footpath_region=True)
        # Vehicle bbox overlapping footpath region
        result = engine.evaluate(
            vehicle_bbox=[100, 150, 300, 250],
            segmentation_mask=mask,
            signs=[], all_vehicles=[], image_shape=(480, 640),
        )
        assert result["is_illegal"] is True
        assert any("footpath" in r.lower() for r in result["violated_rules"])

    def test_vehicle_on_road_only_is_legal(self, engine):
        mask = _make_mask(road_region=True, footpath_region=False)
        # Vehicle fully on road
        result = engine.evaluate(
            vehicle_bbox=[100, 300, 300, 450],
            segmentation_mask=mask,
            signs=[], all_vehicles=[], image_shape=(480, 640),
        )
        assert result["is_illegal"] is False

    def test_no_parking_sign_triggers_violation(self, engine):
        mask = _make_mask()
        signs = [{"sign_type": "no_parking_sign", "confidence": 0.9, "bbox": [200, 100, 250, 150]}]
        result = engine.evaluate(
            vehicle_bbox=[100, 200, 400, 450],
            segmentation_mask=mask,
            signs=signs, all_vehicles=[], image_shape=(480, 640),
        )
        assert result["is_illegal"] is True

    def test_no_mask_no_crash(self, engine):
        result = engine.evaluate(
            vehicle_bbox=[100, 200, 300, 400],
            segmentation_mask=None,
            signs=[], all_vehicles=[], image_shape=(480, 640),
        )
        assert isinstance(result["is_illegal"], bool)
