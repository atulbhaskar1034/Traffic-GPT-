# 🚦 GRIDLOCK — AI Illegal Parking Detection (Prototype)

**AI-powered illegal parking detection for Bangalore — local prototype**

GRIDLOCK uses a 10-stage AI pipeline to automatically verify illegal parking violations from citizen-submitted smartphone photos.

---

## 🏗️ Architecture

```
📱 Smartphone Image + GPS + Timestamp
         ↓
┌─────────────────────────────────┐
│  Stage 1: Image Quality Check   │ ← OpenCV
│  Stage 2: Vehicle Detection      │ ← YOLOv8-L
│  Stage 3: Scene Segmentation     │ ← DeepLabV3+
│  Stage 4: Sign Detection         │ ← YOLOv8-M
│  Stage 5: Plate OCR              │ ← YOLO + EasyOCR
│  Stage 6: Rule Engine            │ ← Geometric reasoning (7 rules)
│  Stage 7: Duplicate Detection    │ ← CLIP + FAISS
│  Stage 8: Fraud Detection        │ ← EXIF + ELA
│  Stage 9: GPS Validation         │ ← Geofencing + Astram data
│  Stage 10: Multi-Image Verify    │ ← Cross-view consistency
└─────────────────────────────────┘
         ↓
   ✅ JSON Verdict
```

## 📊 Astram Data Integration

Uses **8,173 real Bangalore traffic events** from the Astram traffic management system for:
- 🔥 Hotspot detection (GPS clusters of frequent violations)
- 🏢 Police station jurisdiction lookup (54 stations)
- 🚦 Junction mapping (294 junctions)
- 📈 Confidence boosting at known problem areas

## 🚀 Quick Start

```bash
# Install
pip install -e .

# Run API server
uvicorn src.api.app:app --reload --port 8000

# Open docs: http://localhost:8000/docs
```

## 📁 Project Structure

```
GRIDLOCK/
├── src/
│   ├── api/          # FastAPI endpoints
│   ├── stages/       # 10 pipeline stages
│   ├── pipeline/     # Orchestrator
│   ├── data/         # Astram data loader
│   └── utils/        # Logging, image, geo, embeddings
├── training/         # Training scripts
├── configs/          # Model & training configs
├── tests/            # Unit tests
└── data/             # Astram CSV dataset
```

## 🧪 Testing

```bash
pytest tests/ -v
```

## 📝 API Usage

```bash
curl -X POST http://localhost:8000/api/v1/detect \
  -F "image=@parking_photo.jpg" \
  -F "latitude=12.9716" \
  -F "longitude=77.5946" \
  -F "user_id=USER-001"
```

## 📝 License

MIT
