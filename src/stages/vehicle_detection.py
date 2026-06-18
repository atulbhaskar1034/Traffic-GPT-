"""
Stage 2: Vehicle Detection

Detects and classifies vehicles in the image using YOLOv8.
Classes: car, bike, truck, bus, auto_rickshaw.

Returns bounding boxes, class labels, and confidence scores.
"""

from pathlib import Path
from typing import List, Optional

import numpy as np

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Class mapping for vehicle detection
VEHICLE_CLASSES = {
    0: "car",
    1: "bike",
    2: "truck",
    3: "bus",
    4: "auto_rickshaw",
}


class VehicleDetector:
    """YOLOv8-based vehicle detector for Indian road vehicles.

    Supports lazy model loading, configurable confidence thresholds,
    and returns structured detection results.
    """

    def __init__(
        self,
        model_path: Optional[Path] = None,
        confidence_threshold: float = 0.20,
        iou_threshold: float = 0.5,
        image_size: int = 640,
        device: str = "cuda:0",
    ):
        """Initialize the vehicle detector.

        Args:
            model_path: Path to trained YOLOv8 weights (.pt file).
                        If None, uses pretrained COCO weights as fallback.
            confidence_threshold: Minimum confidence to keep a detection.
            iou_threshold: NMS IoU threshold.
            image_size: Input image size for the model.
            device: Inference device ('cuda:0', 'cpu').
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.image_size = image_size
        
        import torch
        if "cuda" in device and not torch.cuda.is_available():
            logger.warning(f"CUDA requested ({device}) but not available. Falling back to CPU.")
            device = "cpu"
        self.device = device
        self._model = None

    def _load_model(self):
        """Lazy-load the YOLO model on first inference."""
        if self._model is not None:
            return

        from ultralytics import YOLO

        if self.model_path and Path(self.model_path).exists():
            self._model = YOLO(str(self.model_path))
            logger.info(f"Loaded custom vehicle detector from {self.model_path}")
        else:
            # Fallback to pretrained COCO model (has vehicle classes)
            self._model = YOLO("yolov8l.pt")
            logger.warning("Custom weights not found. Using pretrained YOLOv8l (COCO).")

    def detect(self, image: np.ndarray) -> dict:
        """Run vehicle detection on an image.

        Args:
            image: BGR numpy array (OpenCV format).

        Returns:
            Dictionary with:
                - vehicle_detected (bool)
                - vehicles (list): Each with {vehicle_type, confidence, bbox}
                - primary_vehicle (dict or None): Highest-confidence detection
        """
        self._load_model()

        results = self._model.predict(
            source=image,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            imgsz=self.image_size,
            device=self.device,
            verbose=False,
        )

        vehicles = []
        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                xyxy = box.xyxy[0].cpu().numpy().tolist()

                logger.info(f"Raw YOLO detection: cls_id={cls_id}, conf={conf}")

                # Map class ID to vehicle type
                # For COCO pretrained: car=2, motorcycle=3, bus=5, truck=7
                vehicle_type = self._map_class(cls_id)
                logger.info(f"Mapped vehicle_type: {vehicle_type}")
                
                if vehicle_type is None:
                    continue

                vehicles.append({
                    "vehicle_type": vehicle_type,
                    "confidence": round(conf, 3),
                    "bbox": [round(x, 1) for x in xyxy],
                })

        # Sort by confidence descending
        vehicles.sort(key=lambda v: v["confidence"], reverse=True)

        primary = vehicles[0] if vehicles else None
        result = {
            "vehicle_detected": len(vehicles) > 0,
            "vehicles": vehicles,
            "primary_vehicle": primary,
        }

        logger.info(f"Vehicle detection: {len(vehicles)} vehicles found")
        return result

    def _map_class(self, cls_id: int) -> Optional[str]:
        """Map model class ID to vehicle type string.

        Handles both custom-trained (5-class) and COCO pretrained models.
        """
        is_coco = len(self._model.names) > 10 if self._model else False
        
        if is_coco:
            coco_vehicle_map = {
                2: "car",
                3: "bike",       # motorcycle
                5: "bus",
                7: "truck",
            }
            return coco_vehicle_map.get(cls_id, None)

        # Custom model mapping
        if cls_id in VEHICLE_CLASSES:
            return VEHICLE_CLASSES[cls_id]
        return None
