"""Training script for fraud detection classifier (EfficientNet-B0)."""

from pathlib import Path
import yaml
from src.utils.logger import get_logger

logger = get_logger(__name__)


def train():
    with open("configs/training_configs/hyperparams.yaml") as f:
        full = yaml.safe_load(f)
    config = {**full["defaults"], **full["fraud_classifier"]}

    Path("models/fraud_detection").mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("GRIDLOCK — Fraud Classifier Training")
    logger.info("=" * 60)

    # TODO: Implement EfficientNet-B0 binary classifier
    # Dataset: real smartphone images vs edited/AI-generated/screenshots
    # Loss: Binary Cross Entropy
    # Metrics: ROC-AUC, Precision, Recall
    # Target: ROC-AUC > 0.95

    logger.info("Fraud classifier training script ready.")
    logger.info(f"Config: {config}")


if __name__ == "__main__":
    train()
