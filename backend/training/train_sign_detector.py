"""Training script for no-parking sign detection (YOLOv8-M)."""

from pathlib import Path
import yaml
from src.utils.logger import get_logger

logger = get_logger(__name__)


def train():
    with open("configs/training_configs/hyperparams.yaml") as f:
        config = {**yaml.safe_load(f)["defaults"], **yaml.safe_load(open("configs/training_configs/hyperparams.yaml"))["sign_detection"]}

    Path("models/sign_detection").mkdir(parents=True, exist_ok=True)

    from ultralytics import YOLO
    model = YOLO(config["model"] + ".pt")

    dataset_yaml = Path("data/sign_detection.yaml")
    if not dataset_yaml.exists():
        logger.error(f"Dataset config not found: {dataset_yaml}")
        return

    model.train(
        data=str(dataset_yaml), epochs=config["epochs"],
        imgsz=config["image_size"], batch=config["batch_size"],
        lr0=config["learning_rate"], project="models/sign_detection",
        name="train", exist_ok=True,
    )
    logger.info("Sign detection training complete!")


if __name__ == "__main__":
    train()
