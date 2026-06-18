"""Training script for license plate detection (YOLOv8-S)."""

from pathlib import Path
import yaml
from src.utils.logger import get_logger

logger = get_logger(__name__)


def train():
    with open("configs/training_configs/hyperparams.yaml") as f:
        full = yaml.safe_load(f)
    config = {**full["defaults"], **full["plate_detection"]}

    Path("models/plate_ocr").mkdir(parents=True, exist_ok=True)

    from ultralytics import YOLO
    model = YOLO(config["model"] + ".pt")

    dataset_yaml = Path("data/plate_detection.yaml")
    if not dataset_yaml.exists():
        logger.error(f"Dataset config not found: {dataset_yaml}")
        return

    model.train(
        data=str(dataset_yaml), epochs=config["epochs"],
        imgsz=config["image_size"], batch=config["batch_size"],
        lr0=config["learning_rate"], project="models/plate_ocr",
        name="train", exist_ok=True,
    )
    logger.info("Plate detection training complete!")


if __name__ == "__main__":
    train()
