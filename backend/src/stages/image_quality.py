"""
Stage 1: Image Quality Verification

Rejects blurry, dark, overexposed, and low-resolution images
using pure OpenCV analysis (no ML model required).

Returns a quality score and pass/fail decision.
"""

from dataclasses import dataclass
from typing import Tuple

import cv2
import numpy as np

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class QualityThresholds:
    """Configurable thresholds for image quality checks."""

    min_blur_score: float = 100.0      # Laplacian variance — below = blurry
    min_brightness: float = 40.0       # Mean pixel intensity — below = too dark
    max_brightness: float = 220.0      # Mean pixel intensity — above = overexposed
    min_contrast: float = 20.0         # Std deviation — below = low contrast
    min_width: int = 640               # Minimum image width in pixels
    min_height: int = 480              # Minimum image height in pixels
    max_overexposed_ratio: float = 0.3 # Max fraction of near-white pixels
    max_underexposed_ratio: float = 0.3  # Max fraction of near-black pixels


class ImageQualityChecker:
    """Performs multi-factor image quality assessment.

    Checks:
    - Blur (Laplacian variance)
    - Brightness (mean intensity)
    - Contrast (standard deviation)
    - Resolution (pixel dimensions)
    - Exposure (over/under-exposed pixel ratios)
    """

    def __init__(self, thresholds: QualityThresholds = None):
        self.thresholds = thresholds or QualityThresholds()

    def check(self, image: np.ndarray) -> dict:
        """Run all quality checks on an image.

        Args:
            image: BGR numpy array (OpenCV format).

        Returns:
            Dictionary with:
                - passed (bool): Overall pass/fail
                - quality_score (float): Normalized 0-1 score
                - checks (dict): Individual check results
                - reasons (list): Failure reasons if any
        """
        h, w = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        t = self.thresholds

        # ─── Individual Checks ────────────────────────────────
        blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        brightness = float(np.mean(gray))
        contrast = float(np.std(gray))
        overexposed = float(np.sum(gray > 240) / gray.size)
        underexposed = float(np.sum(gray < 15) / gray.size)

        checks = {
            "resolution": {"width": w, "height": h, "passed": w >= t.min_width and h >= t.min_height},
            "blur": {"score": blur_score, "passed": blur_score >= t.min_blur_score},
            "brightness": {"value": brightness, "passed": t.min_brightness <= brightness <= t.max_brightness},
            "contrast": {"value": contrast, "passed": contrast >= t.min_contrast},
            "overexposure": {"ratio": overexposed, "passed": overexposed <= t.max_overexposed_ratio},
            "underexposure": {"ratio": underexposed, "passed": underexposed <= t.max_underexposed_ratio},
        }

        # ─── Collect failure reasons ──────────────────────────
        reasons = []
        if not checks["resolution"]["passed"]:
            reasons.append(f"Image resolution too low ({w}x{h}). Minimum: {t.min_width}x{t.min_height}")
        if not checks["blur"]["passed"]:
            reasons.append(f"Image is too blurry (score: {blur_score:.1f}, min: {t.min_blur_score})")
        if brightness < t.min_brightness:
            reasons.append(f"Image is too dark (brightness: {brightness:.1f})")
        if brightness > t.max_brightness:
            reasons.append(f"Image is overexposed (brightness: {brightness:.1f})")
        if not checks["contrast"]["passed"]:
            reasons.append(f"Image has low contrast (std: {contrast:.1f})")
        if not checks["overexposure"]["passed"]:
            reasons.append(f"Too many overexposed pixels ({overexposed:.1%})")
        if not checks["underexposure"]["passed"]:
            reasons.append(f"Too many underexposed pixels ({underexposed:.1%})")

        passed = len(reasons) == 0

        # ─── Compute normalized quality score (0-1) ──────────
        quality_score = self._compute_quality_score(blur_score, brightness, contrast, overexposed, underexposed)

        result = {
            "passed": passed,
            "quality_score": quality_score,
            "checks": checks,
            "reasons": reasons,
        }

        logger.info(f"Image quality: passed={passed}, score={quality_score:.2f}, reasons={reasons}")
        return result

    def _compute_quality_score(
        self,
        blur: float,
        brightness: float,
        contrast: float,
        overexposed: float,
        underexposed: float,
    ) -> float:
        """Compute a weighted quality score normalized to 0-1.

        Each factor is scored individually and combined with weights.
        """
        t = self.thresholds

        # Blur score: 0 at threshold, 1 at 5x threshold
        blur_s = min(1.0, max(0.0, (blur - t.min_blur_score * 0.5) / (t.min_blur_score * 4)))

        # Brightness score: 1 at optimal (128), 0 at extremes
        brightness_s = 1.0 - abs(brightness - 128) / 128

        # Contrast score: 0 at threshold, 1 at 3x threshold
        contrast_s = min(1.0, max(0.0, contrast / (t.min_contrast * 3)))

        # Exposure penalty
        exposure_penalty = max(0.0, 1.0 - (overexposed + underexposed) * 2)

        # Weighted combination
        score = (
            0.35 * blur_s
            + 0.25 * brightness_s
            + 0.20 * contrast_s
            + 0.20 * exposure_penalty
        )
        return round(max(0.0, min(1.0, score)), 3)
