"""
Stage 5: Number Plate OCR

Two-stage pipeline:
1. License plate detection (YOLOv8-S)
2. Text extraction (EasyOCR)

Returns the extracted plate number with confidence score.
"""

import re
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Indian license plate format: KA01AB1234, KA01A1234, etc.
INDIAN_PLATE_REGEX = re.compile(r"^[A-Z]{2}\d{2}[A-Z]{1,3}\d{4}$")


class PlateOCR:
    """License plate detection and OCR pipeline.

    Stage 1: Detect plate bounding box using YOLOv8-S.
    Stage 2: Extract text from the cropped plate using EasyOCR.
    Stage 3: Validate against Indian plate format regex.
    """

    def __init__(
        self,
        plate_model_path: Optional[Path] = None,
        confidence_threshold: float = 0.50,
        device: str = "cuda:0",
    ):
        self.plate_model_path = plate_model_path
        self.confidence_threshold = confidence_threshold
        
        import torch
        if "cuda" in device and not torch.cuda.is_available():
            logger.warning(f"CUDA requested ({device}) but not available. Falling back to CPU.")
            device = "cpu"
        self.device = device
        self._plate_detector = None
        self._ocr = None

    def _load_plate_detector(self):
        """Lazy-load the plate detection model."""
        if self._plate_detector is not None:
            return

        from ultralytics import YOLO

        if self.plate_model_path and Path(self.plate_model_path).exists():
            self._plate_detector = YOLO(str(self.plate_model_path))
            logger.info(f"Loaded plate detector from {self.plate_model_path}")
        else:
            self._plate_detector = YOLO("yolov8s.pt")
            logger.warning("Custom plate detector not found. Using base YOLOv8s.")

    def _load_ocr(self):
        """Lazy-load EasyOCR."""
        if self._ocr is not None:
            return

        import easyocr

        self._ocr = easyocr.Reader(["en"], gpu="cuda" in self.device)
        logger.info("Loaded EasyOCR engine")

    def extract(self, image: np.ndarray, vehicle_bbox: Optional[list] = None) -> dict:
        """Extract license plate text from an image.

        Args:
            image: BGR numpy array.
            vehicle_bbox: Optional [x1, y1, x2, y2] to crop search area.

        Returns:
            Dictionary with plate_detected, number_plate, plate_confidence,
            plate_bbox, and format_valid fields.
        """
        self._load_plate_detector()
        self._load_ocr()

        # Optionally crop to vehicle region for better plate detection
        search_region = image
        offset = [0, 0]
        if vehicle_bbox:
            x1, y1, x2, y2 = [int(v) for v in vehicle_bbox]
            h, w = image.shape[:2]
            pad = 20
            x1, y1 = max(0, x1 - pad), max(0, y1 - pad)
            x2, y2 = min(w, x2 + pad), min(h, y2 + pad)
            search_region = image[y1:y2, x1:x2]
            offset = [x1, y1]

        # Step 1: Detect plate bounding box
        results = self._plate_detector.predict(
            source=search_region,
            conf=self.confidence_threshold,
            imgsz=640,
            device=self.device,
            verbose=False,
        )

        plate_crops = []
        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                xyxy = box.xyxy[0].cpu().numpy().astype(int)
                conf = float(box.conf[0])
                x1, y1, x2, y2 = xyxy
                crop = search_region[y1:y2, x1:x2]
                if crop.size > 0:
                    plate_crops.append((crop, conf, xyxy))

        if not plate_crops:
            return {
                "plate_detected": False,
                "number_plate": None,
                "plate_confidence": 0.0,
                "plate_bbox": None,
                "format_valid": False,
            }

        # Take highest confidence plate
        plate_crop, det_conf, plate_xyxy = plate_crops[0]

        # Step 2: Preprocess and run OCR
        plate_text, ocr_conf = self._run_ocr(plate_crop)

        # Step 3: Clean and validate
        cleaned = self._clean_plate_text(plate_text)
        format_valid = bool(INDIAN_PLATE_REGEX.match(cleaned)) if cleaned else False

        # Adjust bbox to full image coordinates
        abs_bbox = [
            float(plate_xyxy[0] + offset[0]),
            float(plate_xyxy[1] + offset[1]),
            float(plate_xyxy[2] + offset[0]),
            float(plate_xyxy[3] + offset[1]),
        ]

        result = {
            "plate_detected": True,
            "number_plate": cleaned if cleaned else plate_text,
            "plate_confidence": round(ocr_conf * det_conf, 3),
            "plate_bbox": abs_bbox,
            "format_valid": format_valid,
        }

        logger.info(f"Plate OCR: text='{cleaned}', valid={format_valid}, conf={result['plate_confidence']:.2f}")
        return result

    def _run_ocr(self, plate_image: np.ndarray) -> tuple:
        """Run EasyOCR on a cropped plate image. Returns (text, confidence)."""
        # Preprocess: grayscale → threshold → denoise
        gray = cv2.cvtColor(plate_image, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Convert back to BGR for OCR input
        ocr_input = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

        results = self._ocr.readtext(ocr_input)
        if results:
            texts = [r[1] for r in results]
            confs = [r[2] for r in results]
            return " ".join(texts), sum(confs) / len(confs) if confs else 0.0
        return "", 0.0

    @staticmethod
    def _clean_plate_text(text: str) -> str:
        """Clean OCR output to extract a valid plate number."""
        if not text:
            return ""

        # Remove all non-alphanumeric characters
        cleaned = re.sub(r"[^A-Za-z0-9]", "", text.upper())
        return cleaned
