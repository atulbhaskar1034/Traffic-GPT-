"""Tests for Stage 1: Image Quality Checker."""

import numpy as np
import pytest

from src.stages.image_quality import ImageQualityChecker, QualityThresholds


@pytest.fixture
def checker():
    return ImageQualityChecker()


def _make_image(h=480, w=640, brightness=128, noise=True):
    """Create a synthetic test image."""
    img = np.full((h, w, 3), brightness, dtype=np.uint8)
    if noise:
        noise_arr = np.random.randint(0, 150, (h, w, 3), dtype=np.uint8)
        img = np.clip(img.astype(int) + noise_arr - 75, 0, 255).astype(np.uint8)
    return img


class TestImageQuality:
    def test_good_image_passes(self, checker):
        img = _make_image(brightness=128, noise=True)
        result = checker.check(img)
        assert result["passed"] is True
        assert result["quality_score"] > 0.3

    def test_dark_image_fails(self, checker):
        img = _make_image(brightness=20, noise=False)
        result = checker.check(img)
        assert result["passed"] is False
        assert any("dark" in r.lower() for r in result["reasons"])

    def test_overexposed_image_fails(self, checker):
        img = _make_image(brightness=240, noise=False)
        result = checker.check(img)
        assert result["passed"] is False

    def test_low_resolution_fails(self, checker):
        img = _make_image(h=100, w=100)
        result = checker.check(img)
        assert result["passed"] is False
        assert any("resolution" in r.lower() for r in result["reasons"])

    def test_quality_score_range(self, checker):
        img = _make_image()
        result = checker.check(img)
        assert 0.0 <= result["quality_score"] <= 1.0
