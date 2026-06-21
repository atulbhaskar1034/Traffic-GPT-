<p align="center">
  <h1 align="center">🚦 GRIDLOCK — AI-Powered Illegal Parking Detection System</h1>
  <p align="center">
    <strong>An end-to-end smart city solution for Bangalore Traffic Police</strong><br>
    Citizen-submitted photos → 10-stage AI pipeline → Police enforcement dashboard
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.108+-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/YOLOv8-Ultralytics-FF6F00?logo=yolo&logoColor=white" alt="YOLOv8">
  <img src="https://img.shields.io/badge/Android-Java-3DDC84?logo=android&logoColor=white" alt="Android">
  <img src="https://img.shields.io/badge/Firebase-Firestore-FFCA28?logo=firebase&logoColor=black" alt="Firebase">
  <img src="https://img.shields.io/badge/PyTorch-2.1+-EE4C2C?logo=pytorch&logoColor=white" alt="PyTorch">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
</p>

---

## 📖 Table of Contents

- [Overview](#-overview)
- [System Architecture](#-system-architecture)
- [The 10-Stage AI Pipeline](#-the-10-stage-ai-pipeline)
- [Project Structure](#-project-structure)
- [Components in Detail](#-components-in-detail)
  - [Backend (Python / FastAPI)](#1-backend--python--fastapi)
  - [Police App (Android / Java)](#2-police-app--android--java)
  - [User App (Android / Java)](#3-user-app--android--java)
- [Astram Data Integration](#-astram-data-integration)
- [Rule Engine — 7 Violation Rules](#-rule-engine--7-violation-rules)
- [API Reference](#-api-reference)
- [How to Run](#-how-to-run)
- [Training Custom Models](#-training-custom-models)
- [Testing](#-testing)
- [Tech Stack](#-tech-stack)
- [License](#-license)

---

## 🌟 Overview

**GRIDLOCK** is an AI-powered illegal parking detection and enforcement platform built for Bangalore. It bridges the gap between citizens who report parking violations and the police who enforce them — using a sophisticated 10-stage computer vision pipeline to automatically verify every report.

### The Problem

Illegal parking in Bangalore causes:
- 🚗 Traffic congestion and bottlenecks
- 🚶 Blocked footpaths forcing pedestrians onto roads
- 🚌 Obstructed bus stops and zebra crossings
- 🚑 Emergency vehicle access issues

### The Solution

GRIDLOCK creates a closed-loop enforcement system:

```
┌──────────────┐     ┌──────────────────────┐     ┌──────────────────┐
│  👤 Citizen   │────▶│  🤖 AI Backend        │────▶│  👮 Police App    │
│  (User App)  │     │  (10-Stage Pipeline)  │     │  (Enforcement)   │
│              │     │                      │     │                  │
│ • Snap photo │     │ • Verify violation   │     │ • View hotspots  │
│ • GPS tagged │     │ • Detect vehicle     │     │ • Deploy patrols │
│ • Submit     │     │ • Read plate         │     │ • Track reports  │
│              │     │ • Check fraud        │     │ • Manage officers│
└──────────────┘     └──────────────────────┘     └──────────────────┘
```

---

## 🏗️ System Architecture

```
                            ┌─────────────────────────────────┐
                            │         GRIDLOCK SYSTEM          │
                            └──────────────┬──────────────────┘
                                           │
              ┌────────────────────────────┼────────────────────────────┐
              │                            │                            │
    ┌─────────▼─────────┐      ┌──────────▼──────────┐      ┌─────────▼─────────┐
    │    USER APP 📱     │      │   BACKEND SERVER 🖥️  │      │  POLICE APP 👮     │
    │   (Android/Java)   │      │  (Python/FastAPI)    │      │  (Android/Java)    │
    │                    │      │                      │      │                    │
    │ • Camera capture   │─────▶│ • 10-stage AI pipe   │      │ • Dashboard stats  │
    │ • GPS location     │ HTTP │ • YOLOv8 detection   │      │ • Hotspot viewer   │
    │ • Photo submission │      │ • DeepLabV3+ seg     │      │ • Deploy officers  │
    │ • QR code scan     │      │ • EasyOCR plates     │      │ • Community feed   │
    │ • TFLite on-device │      │ • Rule engine        │      │ • Officer profiles │
    │                    │      │ • Astram enrichment   │      │                    │
    └────────────────────┘      └──────────┬───────────┘      └─────────┬──────────┘
                                           │                            │
                                   ┌───────▼────────┐          ┌───────▼────────┐
                                   │  Astram CSV 📊  │          │  Firebase 🔥   │
                                   │  8,173 events   │          │  Firestore DB  │
                                   │  Bangalore data │          │  Auth + Storage│
                                   └────────────────┘          └────────────────┘
```

---

## 🔬 The 10-Stage AI Pipeline

Every citizen-submitted photo passes through a rigorous 10-stage verification pipeline before being accepted as a valid violation report. The pipeline uses **early-exit gates** — if a critical stage fails (e.g., no vehicle detected), later stages are skipped entirely.

```
📱 Smartphone Image + GPS + Timestamp
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  ┌─────────────────────┐    ┌─────────────────────┐                │
│  │ Stage 1             │    │ Stage 2             │                │
│  │ IMAGE QUALITY CHECK │───▶│ VEHICLE DETECTION   │                │
│  │ OpenCV              │    │ YOLOv8-L            │                │
│  │ • Blur detection    │    │ • Car, bike, truck   │                │
│  │ • Brightness check  │    │ • Bus, auto_rickshaw │                │
│  │ • Resolution check  │    │ • Bounding boxes     │                │
│  │ • Exposure analysis │    │ • Confidence scores  │                │
│  │                     │    │                      │                │
│  │ ❌ Fail → REJECT    │    │ ❌ No vehicle → REJECT│                │
│  └─────────────────────┘    └──────────┬──────────┘                │
│                                        │                           │
│  ┌─────────────────────┐    ┌──────────▼──────────┐                │
│  │ Stage 4             │    │ Stage 3             │                │
│  │ SIGN DETECTION      │◀───│ SCENE SEGMENTATION  │                │
│  │ YOLOv8-M            │    │ DeepLabV3+          │                │
│  │ • No-parking signs  │    │ • Road surface       │                │
│  │ • Tow-away signs    │    │ • Footpath           │                │
│  │ • Restricted zones  │    │ • Zebra crossing     │                │
│  │                     │    │ • Bus stop zone      │                │
│  │                     │    │ • Lane markings      │                │
│  └──────────┬──────────┘    └─────────────────────┘                │
│             │                                                      │
│  ┌──────────▼──────────┐    ┌─────────────────────┐                │
│  │ Stage 5             │    │ Stage 6             │                │
│  │ NUMBER PLATE OCR    │───▶│ RULE ENGINE         │                │
│  │ YOLOv8-S + EasyOCR  │    │ Geometric Reasoning │                │
│  │ • Plate detection   │    │ • 7 violation rules  │                │
│  │ • Text extraction   │    │ • Spatial analysis   │                │
│  │ • Format validation │    │ • Overlap detection  │                │
│  │ • Indian plate regex│    │ • Confidence scoring │                │
│  └─────────────────────┘    └──────────┬──────────┘                │
│                                        │                           │
│  ┌─────────────────────┐    ┌──────────▼──────────┐                │
│  │ Stage 8             │    │ Stage 7             │                │
│  │ FRAUD DETECTION     │◀───│ DUPLICATE DETECTION │                │
│  │ EXIF + ELA          │    │ CLIP + FAISS        │                │
│  │ • Metadata analysis │    │ • Image embeddings  │                │
│  │ • Tampering check   │    │ • Plate matching    │                │
│  │ • Authenticity score│    │ • Similarity scoring│                │
│  └──────────┬──────────┘    └─────────────────────┘                │
│             │                                                      │
│  ┌──────────▼──────────┐    ┌─────────────────────┐                │
│  │ Stage 9             │    │ Stage 10            │                │
│  │ GPS VALIDATION      │───▶│ FINAL DECISION      │                │
│  │ Geofencing + Astram │    │ Aggregate Verdict   │                │
│  │ • In Bangalore?     │    │                     │                │
│  │ • Hotspot boost     │    │ ✅ is_illegal AND    │                │
│  │ • Police station    │    │ ✅ is_authentic AND  │                │
│  │ • Junction mapping  │    │ ✅ !is_duplicate AND │                │
│  │ • Event history     │    │ ✅ location_valid    │                │
│  └─────────────────────┘    │ = VIOLATION CONFIRMED│                │
│                             └─────────────────────┘                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
         │
         ▼
   📄 JSON Verdict (DetectionResponse)
```

---

## 📁 Project Structure

```
GRIDLOCK/
│
├── backend/                          # 🖥️  Python AI Backend
│   ├── src/
│   │   ├── api/                      #     FastAPI application
│   │   │   ├── app.py                #     App entry point, CORS, lifecycle
│   │   │   ├── routes/
│   │   │   │   ├── detect.py         #     POST /api/v1/detect endpoint
│   │   │   │   └── health.py         #     GET  /api/v1/health endpoint
│   │   │   └── schemas/
│   │   │       ├── request.py        #     Input validation schemas
│   │   │       └── response.py       #     DetectionResponse schema
│   │   │
│   │   ├── stages/                   #     10 AI pipeline stages
│   │   │   ├── image_quality.py      #     Stage 1: OpenCV quality checks
│   │   │   ├── vehicle_detection.py  #     Stage 2: YOLOv8-L detection
│   │   │   ├── scene_segmentation.py #     Stage 3: DeepLabV3+ segmentation
│   │   │   ├── sign_detection.py     #     Stage 4: YOLOv8-M sign detection
│   │   │   ├── plate_ocr.py          #     Stage 5: YOLOv8-S + EasyOCR
│   │   │   ├── rule_engine.py        #     Stage 6: 7-rule geometric engine
│   │   │   ├── duplicate_detection.py#     Stage 7: CLIP + FAISS
│   │   │   ├── fraud_detection.py    #     Stage 8: EXIF + ELA analysis
│   │   │   ├── gps_validation.py     #     Stage 9: Geofencing + Astram
│   │   │   └── multi_image_verify.py #     Stage 10: Cross-view consistency
│   │   │
│   │   ├── pipeline/
│   │   │   └── inference_pipeline.py #     Orchestrator with early-exit gates
│   │   │
│   │   ├── data/
│   │   │   └── astram_loader.py      #     Bangalore traffic event data loader
│   │   │
│   │   └── utils/
│   │       ├── geo_utils.py          #     GPS, geofencing, Haversine distance
│   │       ├── image_utils.py        #     Image loading and preprocessing
│   │       ├── embedding_utils.py    #     CLIP/FAISS embedding helpers
│   │       └── logger.py             #     Loguru-based structured logging
│   │
│   ├── training/                     #     Model training scripts
│   │   ├── train_vehicle_detector.py #     YOLOv8-L on BDD100K + IDD
│   │   ├── train_segmentation.py     #     DeepLabV3+ urban segmentation
│   │   ├── train_sign_detector.py    #     No-parking sign detection
│   │   ├── train_plate_detector.py   #     License plate detection
│   │   ├── train_fraud_classifier.py #     Image fraud classifier
│   │   └── evaluate.py              #     Evaluation metrics
│   │
│   ├── configs/
│   │   ├── model_configs/            #     Model architecture configs
│   │   ├── training_configs/         #     Training hyperparameters
│   │   └── geofence/
│   │       └── bangalore_boundary.geojson  # City boundary polygon
│   │
│   ├── data/
│   │   └── Astram event data_anonymized*.csv  # 8,173 real traffic events
│   │
│   ├── tests/                        #     Unit and integration tests
│   │   ├── test_api.py
│   │   ├── test_astram_data.py
│   │   ├── test_quality.py
│   │   └── test_rule_engine.py
│   │
│   ├── yolov8l.pt                    #     Pretrained YOLOv8 weights
│   ├── yolov8m.pt
│   ├── yolov8s.pt
│   ├── yolov8x.pt
│   ├── pyproject.toml                #     Python project config
│   └── Makefile                      #     Build/serve/test commands
│
├── Police_app/                       # 👮  Police Android App (ParkIQPolice)
│   └── app/src/main/java/.../
│       ├── LoginActivity.java        #     Google Sign-In + role verification
│       ├── DashboardActivity.java    #     Stats, deployments, location
│       ├── HotspotsActivity.java     #     Sortable/searchable hotspot list
│       ├── HotspotDetailActivity.java#     Deployment plans + Google Maps
│       ├── CommunityActivity.java    #     Citizen violation feed
│       ├── ProfileActivity.java      #     Officer profile management
│       ├── BaseNavigationActivity.java#    Bottom navigation base class
│       └── ...adapters & models
│
├── User_app/                         # 📱  Citizen Android App (Traffic_GPT)
│   └── app/
│       ├── build.gradle.kts          #     Dependencies (CameraX, TFLite, Firebase)
│       └── google-services.json      #     Firebase configuration
│
├── ML_model/                         # 🧠  ML model artifacts (placeholder)
│
└── README.md                         #     ← You are here!
```

---

## 🔧 Components in Detail

### 1. Backend — Python / FastAPI

The brain of the system. Receives photos from citizen smartphones, runs them through a 10-stage AI pipeline, and returns a structured JSON verdict.

**Key Design Decisions:**
- **Lazy model loading** — Models are loaded on first request, not at startup, reducing cold-start memory usage
- **Early-exit gates** — If Stage 1 (quality) or Stage 2 (vehicle) fails, the pipeline short-circuits immediately
- **COCO fallback** — When custom-trained weights are unavailable, the system gracefully falls back to pretrained COCO models
- **Singleton pipeline** — Only one instance of the inference pipeline exists to avoid duplicating 500MB+ of model weights in memory

**Models Used:**

| Stage | Model | Size | Purpose |
|-------|-------|------|---------|
| 2 | YOLOv8-L | ~88 MB | Vehicle detection (car, bike, truck, bus, auto) |
| 3 | DeepLabV3+ (ResNet-101) | ~240 MB | Scene segmentation (road, footpath, zebra, bus stop) |
| 4 | YOLOv8-M | ~52 MB | No-parking sign & restriction sign detection |
| 5 | YOLOv8-S + EasyOCR | ~23 MB + OCR | License plate detection and text extraction |
| 7 | CLIP + FAISS | ~400 MB | Duplicate image detection (currently disabled for OOM) |
| 8 | ELA + EXIF | Pure logic | Image fraud/tampering detection |

---

### 2. Police App — Android / Java

**ParkIQPolice** is the enforcement dashboard for traffic police officers, built natively in Android (Java) with Firebase as the backend.

**Features:**

| Screen | Description |
|--------|-------------|
| **Login** | Google Sign-In with role-based access control. Only users with `role: "police"` in the Firestore `users` collection can access the app. Includes legacy migration from the old `police_users` collection. |
| **Dashboard** | Live stats showing total hotspots and critical hotspots (priority score ≥ 0.85). Displays recent deployments with options to edit officer count or undeploy. Shows current GPS location via geocoding. |
| **Hotspots** | Searchable and sortable list of violation hotspots from Firestore, ordered by `dynamic_priority_score`. Intelligently prioritizes hotspots within ±4 hours of their peak violation time. Supports 5 sort modes: Relevance, Nearest, Time, Score, High Risk. |
| **Hotspot Detail** | Drill-down view with junction name, police station, score, violations, and peak hour. Features an AI-powered **Deployment Plan Generator** that recommends officer count and vehicle type based on priority score. One-tap deployment approval writes directly to Firestore. Integrates Google Maps navigation. |
| **Community** | Feed of citizen-submitted violation reports from the `violations` collection. Sortable by newest, score, location, and status. |
| **Profile** | Officer profile management (name, age, badge number, department, phone) with Firestore persistence. Includes logout functionality. |

**Deployment Logic (Score-Based):**

| Priority Score | Officers | Vehicle | 
|---------------|----------|---------|
| ≥ 0.85 (Critical) | 4 | Tow Vehicle Required |
| ≥ 0.70 (High) | 3 | Tow Vehicle Recommended |
| ≥ 0.50 (Medium) | 2 | Bike Patrol |
| < 0.50 (Low) | 1 | Routine Patrol |

---

### 3. User App — Android / Java

**Traffic_GPT** is the citizen-facing app for submitting parking violation reports.

**Key Capabilities (from dependencies):**
- 📷 **CameraX** — In-app camera for capturing violation photos
- 📍 **Google Play Location Services** — GPS tagging of submissions
- 🔥 **Firebase Auth + Firestore + Storage** — User authentication, data storage, and image upload
- 🧠 **TensorFlow Lite** — On-device ML inference for preliminary analysis
- 📱 **ZXing** — QR code scanning capability
- 🖼️ **Glide** — Efficient image loading and caching
- 🌐 **Retrofit + OkHttp** — HTTP client for communicating with the backend API

---

## 📊 Astram Data Integration

GRIDLOCK is enriched with **8,173 real Bangalore traffic events** from the Astram traffic management system (Nov 2023 – Apr 2024).

```
┌──────────────────────────────────────────────────────────────┐
│                    ASTRAM DATA PIPELINE                       │
│                                                              │
│   📄 Raw CSV (4.5 MB)                                        │
│    │                                                         │
│    ├──▶ 🔥 Hotspot Detection                                 │
│    │    GPS grid clustering (200m cells)                      │
│    │    Cells with 5+ events = hotspot                       │
│    │                                                         │
│    ├──▶ 🏢 Police Station Index                              │
│    │    54 stations mapped to GPS centroids                   │
│    │                                                         │
│    ├──▶ 🚦 Junction Mapping                                  │
│    │    294 junctions with GPS coordinates                    │
│    │                                                         │
│    └──▶ 📈 Confidence Boosting                               │
│         Reports at known hotspots get +0.5% to +10%          │
│         confidence boost (capped)                            │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Enrichment Fields Added to API Response:**

| Field | Description |
|-------|-------------|
| `is_known_hotspot` | Whether the GPS location is a known violation hotspot |
| `nearest_police_station` | Jurisdiction lookup based on GPS proximity |
| `nearest_junction` | Nearest major junction (within 2km) |
| `nearby_event_count` | Number of historical traffic events within 500m |
| `hotspot_confidence_boost` | Confidence score boost (0.0–0.10) for known hotspots |

---

## ⚖️ Rule Engine — 7 Violation Rules

The rule engine (Stage 6) uses **pure geometric reasoning** — no ML involved — to determine if a detected vehicle is illegally parked:

| Rule | Name | How It Works | Threshold |
|------|------|--------------|-----------|
| **R1** | Footpath Parking | Vehicle bbox overlaps footpath mask | ≥ 30% overlap |
| **R2** | No-Parking Zone | Vehicle proximity to no-parking sign | ≤ 500px distance |
| **R3** | Zebra Crossing Blocked | Vehicle bbox overlaps zebra crossing mask | ≥ 20% overlap |
| **R4** | Traffic Lane Blocked | Vehicle width / road lane width ratio | > 40% occupancy |
| **R5** | Double Parking | Two vehicles at similar Y-position, adjacent X | < 50% width gap |
| **R6** | Bus Stop Blocked | Vehicle bbox overlaps bus stop zone mask | ≥ 20% overlap |
| **R7** | Restricted Zone | Presence of restriction/tow-away sign | Any detection |

> A violation is confirmed if **any** rule is violated. The overall confidence is the **maximum** confidence among violated rules.

---

## 📡 API Reference

### `POST /api/v1/detect`

Submit a photo for illegal parking analysis.

**Request (multipart/form-data):**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image` | File | ✅ | JPEG, PNG, or WebP image (1KB–20MB) |
| `latitude` | float | ❌ | GPS latitude (-90 to 90) |
| `longitude` | float | ❌ | GPS longitude (-180 to 180) |
| `timestamp` | string | ❌ | ISO 8601 timestamp |
| `device_id` | string | ❌ | Device identifier (max 128 chars) |
| `user_id` | string | ✅ | User identifier (max 128 chars) |

**Response (JSON):**

```json
{
  "is_illegal_parking": true,
  "confidence": 0.93,
  "vehicle_detected": true,
  "vehicle_type": "car",
  "vehicles": [
    { "vehicle_type": "car", "confidence": 0.95, "bbox": [120.0, 200.0, 450.0, 500.0] }
  ],
  "number_plate": "KA01AB1234",
  "plate_confidence": 0.88,
  "scene": {
    "road_detected": true,
    "footpath_detected": false,
    "zebra_crossing_detected": false,
    "bus_stop_detected": false,
    "lane_marking_detected": true
  },
  "no_parking_sign_detected": true,
  "duplicate_report": false,
  "image_authentic": true,
  "location_valid": true,
  "violated_rules": [
    "No-parking zone: Vehicle is 234px from no-parking sign",
    "Traffic lane blocked: Vehicle occupies 52% of traffic lane"
  ],
  "reasons": [],
  "image_quality_score": 0.87,
  "processing_time_ms": 1340.5,
  "is_known_hotspot": true,
  "nearest_police_station": "Indiranagar Traffic PS",
  "nearest_junction": "Sony World Junction",
  "nearby_event_count": 12
}
```

### `GET /api/v1/health`

Health check endpoint.

---

## 🚀 How to Run

### Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | ≥ 3.10 | Backend AI pipeline |
| Android Studio | Latest | Building mobile apps |
| Java JDK | 17 | Android development |
| Firebase Account | — | Auth, Firestore, Storage |
| CUDA (optional) | 11.8+ | GPU acceleration for inference |

---

### 1. Running the Backend

```bash
# Clone the repository
git clone https://github.com/atulbhaskar1034/Traffic-GPT-.git
cd Traffic-GPT-

# Navigate to the backend
cd backend

# Install Python dependencies
pip install -e .

# (Optional) Install dev dependencies for testing
pip install -e ".[dev]"

# Start the API server
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```

The API server will start at `http://localhost:8000`. Visit `http://localhost:8000/docs` for the interactive Swagger documentation.

**Using the Makefile (alternative):**

```bash
cd backend

# Install
make install

# Start server
make serve

# Run tests
make test

# Lint code
make lint
```

**Testing the API with curl:**

```bash
curl -X POST http://localhost:8000/api/v1/detect \
  -F "image=@parking_photo.jpg" \
  -F "latitude=12.9716" \
  -F "longitude=77.5946" \
  -F "user_id=USER-001"
```

---

### 2. Running the Police App (ParkIQPolice)

```bash
# Open in Android Studio
# File → Open → select the Police_app/ directory

# Prerequisites:
# 1. Ensure google-services.json is present in Police_app/app/
# 2. Set up a Firebase project with:
#    - Firebase Authentication (Google Sign-In provider enabled)
#    - Cloud Firestore database
#    - Collections: users, hotspots, deployments, violations
# 3. Register your police officer email in Firestore:
#    users/{uid} → { email: "officer@email.com", role: "police" }
```

**Firestore Collections Required:**

| Collection | Fields | Description |
|------------|--------|-------------|
| `users` | `email`, `role`, `name`, `badgeNumber`, `department`, `phone` | User profiles with role-based access |
| `hotspots` | `junction_name`, `police_station`, `dynamic_priority_score`, `peak_hour`, `violations`, `rank`, `latitude`, `longitude`, `priority_level` | AI-identified parking violation hotspots |
| `deployments` | `hotspot`, `police_station`, `officers_required`, `vehicle`, `status`, `violations`, `timestamp` | Active patrol deployments |
| `violations` | `location`, `type`, `status`, `timestamp`, `scoreAwarded`, `imageUrl` | Citizen-submitted violation reports |

**Build & Run:**
1. Sync Gradle files
2. Connect an Android device or start an emulator (API 26+)
3. Click **Run ▶️**

---

### 3. Running the User App (Traffic_GPT)

```bash
# Open in Android Studio
# File → Open → select the User_app/ directory

# Prerequisites:
# 1. Ensure google-services.json is present in User_app/app/
# 2. Same Firebase project as the Police App
# 3. Backend server must be running for full functionality

# Build & Run:
# 1. Sync Gradle files
# 2. Connect an Android device or start an emulator (API 26+)
# 3. Click Run ▶️
```

> **Note:** The User App communicates with the backend API via Retrofit. Update the base URL in the app's network configuration to point to your running backend server (e.g., `http://10.0.2.2:8000` for Android emulator, or use a tunneling service like Cloudflare Tunnel for physical devices).

---

## 🏋️ Training Custom Models

GRIDLOCK includes training scripts for all its ML models. Custom-trained models improve accuracy significantly over the COCO pretrained fallbacks.

```bash
cd backend

# Train vehicle detector (YOLOv8-L on BDD100K + IDD)
make train-vehicle

# Train scene segmentation (DeepLabV3+ on Cityscapes/custom)
make train-segmentation

# Train no-parking sign detector (YOLOv8-M)
make train-sign

# Train license plate detector (YOLOv8-S)
make train-plate

# Train fraud classifier
make train-fraud
```

> **Dataset Setup:** Each training script expects a YOLO-format dataset YAML in `data/`. See the [Ultralytics Dataset Guide](https://docs.ultralytics.com/datasets/detect/) for format details.

---

## 🧪 Testing

```bash
cd backend

# Run all tests
pytest tests/ -v

# Run specific test suites
pytest tests/test_quality.py -v       # Image quality stage
pytest tests/test_rule_engine.py -v   # Rule engine logic
pytest tests/test_astram_data.py -v   # Astram data loader
pytest tests/test_api.py -v           # API endpoint tests

# With coverage
pytest tests/ -v --cov=src --cov-report=term-missing
```

---

## 🛠️ Tech Stack

### Backend
| Technology | Version | Purpose |
|-----------|---------|---------|
| **Python** | ≥ 3.10 | Core language |
| **FastAPI** | ≥ 0.108 | REST API framework |
| **Uvicorn** | ≥ 0.25 | ASGI server |
| **PyTorch** | ≥ 2.1 | Deep learning framework |
| **Ultralytics** | ≥ 8.1 | YOLOv8 object detection |
| **OpenCV** | ≥ 4.8 | Image processing & quality checks |
| **EasyOCR** | ≥ 1.7 | License plate text extraction |
| **DeepLabV3+** (smp) | ≥ 0.3.3 | Semantic segmentation |
| **CLIP** (OpenCLIP) | ≥ 2.23 | Image embeddings for duplicate detection |
| **FAISS** | ≥ 1.7.4 | Vector similarity search |
| **Shapely** | ≥ 2.0 | GPS geofencing |
| **Pydantic** | ≥ 2.5 | Data validation & serialization |
| **Loguru** | ≥ 0.7 | Structured logging |

### Mobile (Android)
| Technology | Purpose |
|-----------|---------|
| **Java 17** | Core language |
| **Firebase Auth** | Google Sign-In authentication |
| **Cloud Firestore** | Real-time NoSQL database |
| **Firebase Storage** | Image upload storage |
| **CameraX 1.3** | In-app camera (User app) |
| **TensorFlow Lite** | On-device ML inference (User app) |
| **Retrofit + OkHttp** | HTTP client for API communication |
| **Glide 4.16** | Image loading and caching |
| **ZXing** | QR code scanning |
| **Material Design** | UI component library |
| **Google Play Location** | GPS location services |

---

## 📝 License

This project is licensed under the **MIT License**.

---

<p align="center">
  <strong>Built with 🚦 for Bangalore Traffic Police</strong><br>
  <em>Making streets safer, one AI-verified report at a time.</em>
</p>
