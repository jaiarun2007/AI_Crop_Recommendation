# AI-Based Crop Recommendation & Climate-Adaptive Farming Assistant — Demo Prototype

A working prototype built for the AI for Social Impact Challenge 2026 pitch. It implements
two of the platform's core services end-to-end, matching the specs from the project's
Executive Summary and Production Blueprint deck:

1. **Crop Recommendation** — a trained ML classifier that suggests the best crop given soil
   nutrients (N, P, K) and climate readings (temperature, humidity, pH, rainfall).
2. **Leaf Disease Screening** — an image-upload endpoint that flags visible leaf discoloration.

A minimal web front-end calls both APIs so the whole thing is demoable in a browser.

## What's real vs. a documented baseline

- **Crop recommendation model is genuinely trained**, not mocked: RandomForest, XGBoost, and
  LightGBM are trained and compared on the public 2,200-row / 22-crop NPK-climate dataset (the
  same one referenced in the Executive Summary), and the best performer (RandomForest,
  ~99.5% held-out accuracy) is what's served.
- **Disease detection is a documented heuristic, not a trained CNN/YOLO model.** Training a real
  disease classifier requires a labeled image dataset (e.g. PlantVillage) and GPU time neither
  available in this session. Instead, `backend/app/services/disease_detector.py` uses OpenCV
  HSV colour-thresholding to estimate what fraction of the leaf shows yellow/brown/necrotic
  discoloration vs. healthy green, and reports that as a severity score. It is real, functional,
  and demoable on an actual photo — but it is not the YOLOv8/EfficientNet pipeline described in
  the architecture docs. The endpoint and response shape are already what a real model would
  return, so swapping in a trained model later is a drop-in change (see the file's docstring).

Be upfront about this distinction if asked by judges — claiming the heuristic is a trained CNN
would misrepresent the work.

## Project layout

```
backend/
  app/
    main.py                    FastAPI app (mounts routers + serves the frontend)
    schemas.py                 Pydantic request/response models
    routers/crop.py            POST /api/crop/recommend
    routers/disease.py         POST /api/disease/detect
    services/crop_recommender.py
    services/disease_detector.py
  ml/
    train_crop_model.py        Trains + compares RF/XGBoost/LightGBM, saves the best
    data/crop_recommendation.csv
    models/                    Saved model artifacts (committed so it runs out of the box)
  tests/
    test_crop_api.py
    test_disease_api.py
frontend/
  index.html / app.js / styles.css   Minimal UI calling both endpoints
scripts/run_dev.sh              One-command local run
```

## Running it locally

```bash
cd backend
pip install -r requirements.txt
cd ..
./scripts/run_dev.sh
```

Then open http://localhost:8000 in a browser. API docs (Swagger UI) are at
http://localhost:8000/docs.

If `backend/ml/models/crop_model.joblib` is missing, `run_dev.sh` retrains it automatically
(`python3 backend/ml/train_crop_model.py`, ~5 seconds).

## Running the tests

```bash
cd backend
python3 -m pytest tests/ -v
```

## API reference

### `POST /api/crop/recommend`

```json
{"N": 90, "P": 42, "K": 43, "temperature": 20.9, "humidity": 82.0, "ph": 6.5, "rainfall": 203.0}
```

→

```json
{
  "top_recommendation": "rice",
  "confidence": 0.935,
  "alternatives": [
    {"crop": "rice", "confidence": 0.935},
    {"crop": "jute", "confidence": 0.065},
    {"crop": "apple", "confidence": 0.0}
  ],
  "model_used": "RandomForestClassifier"
}
```

### `POST /api/disease/detect`

Multipart form upload, field name `file` (JPEG/PNG/WEBP, max 8MB) →

```json
{
  "status": "healthy",
  "severity_percent": 0.0,
  "confidence": 0.9,
  "message": "Leaf appears healthy — no significant discoloration or lesions detected.",
  "method": "opencv-hsv-heuristic-v1"
}
```

## Relationship to the full platform vision

This repo is a focused slice of the much larger microservices platform described in
`Executive_Summary_2.pdf` (10+ services: auth, yield prediction, weather intelligence, soil
health, fertilizer/irrigation engines, a multilingual RAG assistant, Kubernetes deployment,
etc.). Building all of that is a multi-week/production effort; this prototype exists to give
the team something real and runnable to demo today. Natural next slices, roughly in priority
order: yield prediction, weather-alert integration, then the fertilizer/irrigation engines.
