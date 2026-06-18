"""
Training script for the vehicle detection model (YOLOv8-L).

Usage:
    python training/train_vehicle_detector.py

Trains YOLOv8-L on BDD100K + IDD + custom Bangalore data.
Uses transfer learning from COCO pretrained weights.
"""

from pathlib import Path

import yaml

from src.utils.logger import get_logger

logger = get_logger(__name__)

# ─── Configuration ────────────────────────────────────────────
CONFIG_PATH = Path("configs/training_configs/hyperparams.yaml")
DATA_DIR = Path("data")
MODEL_DIR = Path("models/vehicle_detection")


def load_config():
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)
    return {**config["defaults"], **config["vehicle_detection"]}


def train():
    """Train the YOLOv8-L vehicle detection model."""
    config = load_config()
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("GRIDLOCK — Vehicle Detection Training")
    logger.info("=" * 60)
    logger.info(f"Config: {config}")

    from ultralytics import YOLO

    # Load pretrained model
    model = YOLO(config["model"] + ".pt")

    # Dataset YAML must be prepared in data/vehicle_detection.yaml
    # Format: https://docs.ultralytics.com/datasets/detect/
    dataset_yaml = DATA_DIR / "vehicle_detection.yaml"

    if not dataset_yaml.exists():
        logger.error(f"Dataset config not found: {dataset_yaml}")
        logger.info("Create a YOLO dataset YAML with train/val paths and class names.")
        logger.info("See: https://docs.ultralytics.com/datasets/detect/")
        return

    # Train
    results = model.train(
        data=str(dataset_yaml),
        epochs=config["epochs"],
        imgsz=config["image_size"],
        batch=config["batch_size"],
        lr0=config["learning_rate"],
        weight_decay=config.get("weight_decay", 0.0005),
        patience=config.get("early_stopping_patience", 15),
        mosaic=config.get("mosaic", 1.0),
        mixup=config.get("mixup", 0.15),
        degrees=config.get("degrees", 10.0),
        translate=config.get("translate", 0.1),
        scale=config.get("scale", 0.5),
        fliplr=config.get("fliplr", 0.5),
        project=str(MODEL_DIR),
        name="train",
        exist_ok=True,
        seed=config.get("seed", 42),
        amp=config.get("mixed_precision", True),
        workers=config.get("num_workers", 4),
    )

    logger.info("Training complete!")
    logger.info(f"Best weights: {MODEL_DIR / 'train' / 'weights' / 'best.pt'}")


if __name__ == "__main__":
    train()
