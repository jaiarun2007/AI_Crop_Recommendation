# AI-Based Crop Recommendation & Climate-Adaptive Farming Assistant — Demo Prototype

A working prototype built for the AI for Social Impact Challenge 2026 pitch. It implements
several of the platform's core services end-to-end, matching the specs from the project's
Executive Summary and Production Blueprint deck:

1. **Crop Recommendation** — a trained ML classifier that suggests the best crop given soil
   nutrients (N, P, K) and climate readings (temperature, humidity, pH, rainfall).
2. **Leaf Disease Screening** — an image-upload endpoint that flags visible leaf discoloration.
3. **Yield Prediction** — a trained regressor that estimates crop yield (tonnes/ha) given
   region, crop, year, rainfall, pesticide use, and temperature.
4. **Weather Intelligence** — live forecasts + rule-based agro-alerts (heatwave, heavy rain,
   high wind, dry-spell risk) from the free Open-Meteo API.

A minimal web front-end calls all of these APIs so the whole thing is demoable in a browser.

## What's real vs. a documented baseline

- **Crop recommendation model is genuinely trained**, not mocked: RandomForest, XGBoost, and
  LightGBM are trained and compared on the public 2,200-row / 22-crop NPK-climate dataset (the
  same one referenced in the Executive Summary), and the best performer (RandomForest,
  ~99.5% held-out accuracy) is what's served.
- **Yield prediction model is also genuinely trained**, on a real public FAO/World-Bank-derived
  dataset (28,242 rows, 101 countries incl. India, 10 crop types, 1990–2013). XGBoost was chosen
  over RandomForest (R² = 0.984 held-out — exceeding the R² = 0.77–0.81 range cited in the
  Executive Summary's literature review — at ~2MB vs. RandomForest's ~140MB artifact size).
  Predictions for a region/crop combo not seen in training still run, but the API returns an
  explicit `warnings` field flagging that.
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

- **Weather Intelligence calls a real, free, public API (Open-Meteo, no key required)** — no
  synthetic weather data. `backend/app/services/weather_client.py` makes real HTTP calls; if the
  upstream API is unreachable or errors, the endpoint returns a `502` with the real error message
  rather than inventing a forecast. Alert thresholds (heatwave, heavy-rain bands, high wind,
  dry-spell) follow published IMD (India Meteorological Department) classification bands, not
  arbitrary numbers — see the docstring in `weather_service.py`.
  **Note:** this was developed in a sandboxed build environment whose outbound network is
  restricted to GitHub/package registries — Open-Meteo itself could not be reached from inside
  that sandbox. The weather module's tests mock the HTTP transport layer with a fixture matching
  Open-Meteo's real documented response schema, to verify parsing/alert logic deterministically.
  **Do a live check** in an environment with normal internet access before the demo:
  `curl "https://api.open-meteo.com/v1/forecast?latitude=11.0168&longitude=76.9558&daily=temperature_2m_max&timezone=auto"`.

## Project layout

```
backend/
  app/
    main.py                    FastAPI app (mounts routers + serves the frontend)
    config.py                  Central settings (API URLs, JWT secret, DB URL; env-overridable)
    schemas.py                 Pydantic request/response models
    routers/crop.py            POST /api/crop/recommend
    routers/disease.py         POST /api/disease/detect
    routers/yield_.py          POST /api/yield/predict, GET /api/yield/known-values
    routers/weather.py         GET /api/weather/forecast, GET /api/weather/alerts
    services/crop_recommender.py
    services/disease_detector.py
    services/yield_predictor.py
    services/weather_client.py     Raw Open-Meteo HTTP calls
    services/weather_service.py    Forecast parsing + alert-threshold logic
  ml/
    train_crop_model.py        Trains + compares RF/XGBoost/LightGBM, saves the best
    train_yield_model.py       Trains + compares RF/XGBoost regressors, saves the best
    data/crop_recommendation.csv
    data/yield_df.csv
    models/                    Saved model artifacts (committed so it runs out of the box)
  tests/
    test_crop_api.py
    test_disease_api.py
    test_yield_api.py
    test_weather_api.py
frontend/
  index.html / app.js / styles.css   Minimal UI calling all endpoints
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

If the model artifacts are missing, `run_dev.sh` retrains them automatically
(`train_crop_model.py` / `train_yield_model.py`, a few seconds each).

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

### `POST /api/yield/predict`

```json
{
  "Area": "India",
  "Item": "Rice, paddy",
  "Year": 2013,
  "average_rain_fall_mm_per_year": 1083.0,
  "pesticides_tonnes": 46765.0,
  "avg_temp": 24.5
}
```

→

```json
{
  "predicted_yield_kg_per_ha": 3543.3,
  "predicted_yield_tonnes_per_ha": 3.543,
  "model_used": "random_forest",
  "model_r2": 0.9862,
  "warnings": []
}
```

`GET /api/yield/known-values` lists the 101 countries and 10 crop types seen during training —
useful for populating a dropdown instead of free-text input.

### `GET /api/weather/forecast?location=Coimbatore&days=7`

(or `?lat=11.0168&lon=76.9558&days=7`) →

```json
{
  "location": {"name": "Coimbatore", "country": "India", "latitude": 11.0168, "longitude": 76.9558},
  "timezone": "Asia/Kolkata",
  "daily": [
    {"date": "2026-07-15", "temp_max_c": 32.0, "temp_min_c": 24.0, "precipitation_mm": 2.0,
     "precipitation_probability_percent": 10, "humidity_percent": 65, "wind_speed_max_kmh": 12.0,
     "reference_et0_mm": 4.1}
  ]
}
```

### `GET /api/weather/alerts?location=Coimbatore&days=7`

```json
{
  "location": {"name": "Coimbatore", "country": "India", "latitude": 11.0168, "longitude": 76.9558},
  "alerts": [
    {"date": "2026-07-16", "type": "heatwave", "severity": "medium",
     "message": "Heatwave conditions: forecast max 41.0C."}
  ]
}
```

## Relationship to the full platform vision

This repo is a focused slice of the much larger microservices platform described in
`Executive_Summary_2.pdf` (10+ services: auth, soil health, fertilizer/irrigation engines, a
multilingual RAG assistant, Kubernetes deployment, etc.). Building all of that is a
multi-week/production effort; this prototype exists to give the team something real and runnable
to demo today. Remaining slices, in priority order: fertilizer engine, irrigation engine, RAG
assistant, auth, and Docker/Kubernetes deployment manifests.
