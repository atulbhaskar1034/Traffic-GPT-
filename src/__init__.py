"""GRIDLOCK — AI Illegal Parking Detection System for Bangalore."""

import os
from pathlib import Path

# Redirect caching to D: drive due to low space on C:
cache_dir = Path("D:/gridlock_cache")
try:
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = str(cache_dir / "huggingface")
    os.environ["TORCH_HOME"] = str(cache_dir / "torch")
    os.environ["EASYOCR_DOWNLOAD_PATH"] = str(cache_dir / "easyocr")
    os.environ["YOLO_CONFIG_DIR"] = str(cache_dir / "yolo")
except Exception:
    pass

__version__ = "0.1.0"
