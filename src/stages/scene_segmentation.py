"""
Stage 3: Scene Understanding (Semantic Segmentation)

Segments the image into road, footpath, zebra crossing,
bus stop zone, and lane markings using DeepLabV3+.

Returns a pixel-wise segmentation mask and scene presence flags.
"""

from pathlib import Path
from typing import Dict, Optional, Tuple

import cv2
import numpy as np
import torch

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Segmentation class mapping
SCENE_CLASSES = {
    0: "background",
    1: "road",
    2: "footpath",
    3: "zebra_crossing",
    4: "bus_stop_zone",
    5: "lane_marking",
}


class SceneSegmenter:
    """DeepLabV3+-based scene segmentation for urban road scenes.

    Segments the input image into 6 classes to understand the
    spatial layout of the scene for rule engine evaluation.
    """

    def __init__(
        self,
        model_path: Optional[Path] = None,
        num_classes: int = 6,
        image_size: Tuple[int, int] = (512, 512),
        device: str = "cuda:0",
        presence_threshold: float = 0.01,
    ):
        """Initialize the scene segmenter.

        Args:
            model_path: Path to trained segmentation weights.
            num_classes: Number of segmentation classes.
            image_size: (H, W) input size for the model.
            device: Inference device.
            presence_threshold: Min pixel ratio to consider a class present.
        """
        self.model_path = model_path
        self.num_classes = num_classes
        self.image_size = image_size
        if "cuda" in device and not torch.cuda.is_available():
            logger.warning(f"CUDA requested ({device}) but not available. Falling back to CPU.")
            device = "cpu"
        self.device = device
        self.presence_threshold = presence_threshold
        self._model = None

    def _load_model(self):
        """Lazy-load the segmentation model."""
        if self._model is not None:
            return

        if self.model_path and Path(self.model_path).exists():
            import segmentation_models_pytorch as smp

            self._model = smp.DeepLabV3Plus(
                encoder_name="resnet101",
                encoder_weights=None,
                in_channels=3,
                classes=self.num_classes,
            )
            state_dict = torch.load(str(self.model_path), map_location=self.device)
            self._model.load_state_dict(state_dict)
            logger.info(f"Loaded custom segmentation model from {self.model_path}")
        else:
            # Fallback: use torchvision pretrained DeepLabV3 (21 COCO classes)
            from torchvision.models.segmentation import (
                deeplabv3_resnet101,
                DeepLabV3_ResNet101_Weights,
            )

            self._model = deeplabv3_resnet101(
                weights=DeepLabV3_ResNet101_Weights.DEFAULT
            )
            logger.warning("Custom weights not found. Using torchvision DeepLabV3 (COCO).")

        self._model.eval()
        self._model.to(self.device)

    def segment(self, image: np.ndarray) -> dict:
        """Run scene segmentation on an image.

        Args:
            image: BGR numpy array (OpenCV format).

        Returns:
            Dictionary with:
                - mask (np.ndarray): H×W segmentation mask (class indices)
                - scene_flags (dict): Boolean flags for each class presence
                - class_ratios (dict): Pixel ratio for each class
        """
        self._load_model()

        # Preprocess: resize, normalize, to tensor
        input_tensor = self._preprocess(image)

        # Inference
        with torch.no_grad():
            output = self._model(input_tensor)
            if isinstance(output, dict):
                logits = output["out"]  # torchvision format
            else:
                logits = output

        # Get prediction mask
        pred = torch.argmax(logits, dim=1).squeeze(0).cpu().numpy()

        # Resize mask back to original image dimensions
        h, w = image.shape[:2]
        mask = cv2.resize(pred.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST)

        # Compute class presence and ratios
        total_pixels = mask.size
        class_ratios = {}
        scene_flags = {}

        is_fallback = not (self.model_path and Path(self.model_path).exists())

        for cls_id, cls_name in SCENE_CLASSES.items():
            if cls_name == "background":
                continue
                
            if is_fallback:
                # The fallback model (Pascal VOC) predicts classes like aeroplane(1), bicycle(2), bird(3).
                # It does NOT predict roads or zebra crossings. Prevent hallucinated mappings!
                ratio = 0.0
            else:
                ratio = float(np.sum(mask == cls_id)) / total_pixels
                
            class_ratios[cls_name] = round(ratio, 4)
            scene_flags[f"{cls_name}_detected"] = ratio >= self.presence_threshold

        result = {
            "mask": mask,
            "scene_flags": scene_flags,
            "class_ratios": class_ratios,
        }

        logger.info(f"Scene segmentation: {scene_flags}")
        return result

    def _preprocess(self, image: np.ndarray) -> torch.Tensor:
        """Preprocess image for model input.

        Resizes, normalizes with ImageNet stats, and converts to tensor.
        """
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb, (self.image_size[1], self.image_size[0]))

        # Normalize with ImageNet mean/std
        tensor = torch.from_numpy(resized).float().permute(2, 0, 1) / 255.0
        mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
        std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
        tensor = (tensor - mean) / std

        return tensor.unsqueeze(0).to(self.device)

    def get_class_mask(self, full_mask: np.ndarray, class_name: str) -> np.ndarray:
        """Extract a binary mask for a specific class.

        Args:
            full_mask: Full segmentation mask (H×W with class indices).
            class_name: Name of the class to extract.

        Returns:
            Binary mask (H×W, uint8, 0 or 255).
        """
        cls_id = {v: k for k, v in SCENE_CLASSES.items()}.get(class_name)
        if cls_id is None:
            raise ValueError(f"Unknown class: {class_name}")
        return (full_mask == cls_id).astype(np.uint8) * 255
