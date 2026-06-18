.PHONY: install dev serve test lint clean

# ─── Setup ────────────────────────────────────────────────────
install:
	pip install -e .

dev:
	pip install -e ".[dev]"

# ─── Training ─────────────────────────────────────────────────
train-vehicle:
	python training/train_vehicle_detector.py

train-segmentation:
	python training/train_segmentation.py

train-sign:
	python training/train_sign_detector.py

train-plate:
	python training/train_plate_detector.py

train-fraud:
	python training/train_fraud_classifier.py

# ─── Serving ──────────────────────────────────────────────────
serve:
	uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload

# ─── Testing ──────────────────────────────────────────────────
test:
	pytest tests/ -v --tb=short

# ─── Code Quality ────────────────────────────────────────────
lint:
	ruff check src/ tests/
	black --check src/ tests/

format:
	black src/ tests/
	ruff check --fix src/ tests/

# ─── Cleanup ──────────────────────────────────────────────────
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .ruff_cache dist build *.egg-info
