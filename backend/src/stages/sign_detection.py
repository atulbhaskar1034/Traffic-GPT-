"""
Stage 4: No-Parking Sign Detection

Detects no-parking signs, restricted zone boards, and tow-away signs
using a YOLOv8-M model fine-tuned on Indian traffic signs.
"""

from pathlib import Path
from typing import List, Optional

import numpy as np

from src.utils.logger import get_logger

logger = get_logger(__name__)

SIGN_CLASSES = {
    0: "no_parking_sign",
    1: "restricted_zone_board",
    2: "tow_away_sign",
}


class SignDetector:
    """YOLOv8-M based no-parking sign detector.

    Detects traffic signs that indicate parking restrictions,
    used by the rule engine to determine violation context.
    """

    def __init__(
        self,
        model_path: Optional[Path] = None,
        confidence_threshold: float = 0.50,
        image_size: int = 640,
        device: str = "cuda:0",
    ):
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.image_size = image_size
        
        import torch
        if "cuda" in device and not torch.cuda.is_available():
            logger.warning(f"CUDA requested ({device}) but not available. Falling back to CPU.")
            device = "cpu"
        self.device = device
        self._model = None

    def _load_model(self):
        """Lazy-load the sign detection model."""
        if self._model is not None:
            return

        from ultralytics import YOLO

        if self.model_path and Path(self.model_path).exists():
            self._model = YOLO(str(self.model_path))
            logger.info(f"Loaded sign detector from {self.model_path}")
        else:
            # No good pretrained fallback for Indian signs — log warning
            self._model = YOLO("yolov8m.pt")
            logger.warning(
                "Custom sign detection weights not found. "
                "Using base YOLOv8m — sign detection will NOT work correctly. "
                "Train a custom model on Indian traffic sign data."
            )

    def detect(self, image: np.ndarray) -> dict:
        """Detect no-parking signs in the image.

        Args:
            image: BGR numpy array.

        Returns:
            Dictionary with:
                - no_parking_sign_detected (bool)
                - signs (list): Each with {sign_type, confidence, bbox}
        """
        self._load_model()

        results = self._model.predict(
            source=image,
            conf=self.confidence_threshold,
            imgsz=self.image_size,
            device=self.device,
            verbose=False,
        )

        is_coco = len(self._model.names) > 10 if self._model else False

        signs: List[dict] = []
        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                xyxy = box.xyxy[0].cpu().numpy().tolist()

                if is_coco:
                    # COCO model doesn't have no parking signs.
                    # Prevent mapping person(0), bicycle(1), car(2) to signs!
                    if cls_id == 11:  # COCO stop sign
                        sign_type = "restricted_zone_board"
                    else:
                        continue
                else:
                    sign_type = SIGN_CLASSES.get(cls_id)
                    if sign_type is None:
                        continue

                signs.append({
                    "sign_type": sign_type,
                    "confidence": round(conf, 3),
                    "bbox": [round(x, 1) for x in xyxy],
                })

        no_parking = any(s["sign_type"] == "no_parking_sign" for s in signs)
        any_restriction = len(signs) > 0

        result = {
            "no_parking_sign_detected": no_parking,
            "any_restriction_detected": any_restriction,
            "signs": signs,
        }

        logger.info(f"Sign detection: {len(signs)} signs found, no_parking={no_parking}")
        return result
