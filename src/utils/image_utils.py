"""
Image utility functions for the GRIDLOCK pipeline.

Provides helpers for loading, resizing, color conversion,
and preprocessing images for model inference.
"""

from pathlib import Path
from typing import Optional, Tuple, Union

import cv2
import numpy as np
from PIL import Image

from src.utils.logger import get_logger

logger = get_logger(__name__)


def load_image(
    source: Union[str, Path, bytes, np.ndarray],
    target_size: Optional[Tuple[int, int]] = None,
) -> np.ndarray:
    """Load an image from various sources and return as BGR numpy array.

    Args:
        source: File path, raw bytes, or numpy array.
        target_size: Optional (width, height) to resize to.

    Returns:
        BGR numpy array (OpenCV format).

    Raises:
        ValueError: If the image cannot be loaded or decoded.
    """
    if isinstance(source, np.ndarray):
        img = source
    elif isinstance(source, bytes):
        arr = np.frombuffer(source, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Failed to decode image from bytes.")
    elif isinstance(source, (str, Path)):
        path = str(source)
        img = cv2.imread(path, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError(f"Failed to load image from path: {path}")
    else:
        raise TypeError(f"Unsupported image source type: {type(source)}")

    if target_size is not None:
        img = cv2.resize(img, target_size, interpolation=cv2.INTER_LINEAR)

    logger.debug(f"Loaded image with shape {img.shape}")
    return img


def bgr_to_rgb(image: np.ndarray) -> np.ndarray:
    """Convert BGR (OpenCV) image to RGB."""
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def rgb_to_bgr(image: np.ndarray) -> np.ndarray:
    """Convert RGB image to BGR (OpenCV)."""
    return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)


def to_pil(image: np.ndarray) -> Image.Image:
    """Convert a BGR numpy array to a PIL Image (RGB)."""
    return Image.fromarray(bgr_to_rgb(image))


def compute_blur_score(image: np.ndarray) -> float:
    """Compute blur score using Laplacian variance.

    Higher values indicate sharper images.

    Args:
        image: BGR numpy array.

    Returns:
        Laplacian variance (blur score).
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def compute_brightness(image: np.ndarray) -> float:
    """Compute mean brightness of an image.

    Args:
        image: BGR numpy array.

    Returns:
        Mean pixel intensity (0–255).
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return float(np.mean(gray))


def compute_exposure_stats(image: np.ndarray) -> dict:
    """Compute exposure statistics for quality assessment.

    Args:
        image: BGR numpy array.

    Returns:
        Dictionary with brightness, contrast, and overexposure ratio.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    brightness = float(np.mean(gray))
    contrast = float(np.std(gray))
    overexposed_ratio = float(np.sum(gray > 240) / gray.size)
    underexposed_ratio = float(np.sum(gray < 15) / gray.size)

    return {
        "brightness": brightness,
        "contrast": contrast,
        "overexposed_ratio": overexposed_ratio,
        "underexposed_ratio": underexposed_ratio,
    }
