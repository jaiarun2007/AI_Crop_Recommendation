# Production Blueprint — Presentation Deck Summary

Title: AI-Based Crop Recommendation & Climate-Adaptive Farming Assistant — Production Blueprint.
A production-grade architecture and engineering blueprint for an end-to-end agri-AI platform
tailored to Indian agriculture.

## High-level System Architecture
Microservices per domain: auth, user, farm, crop-recommendation, cv/disease, yield, irrigation,
fertilizer, weather-intel, RAG assistant. Immutable model artifacts, separated control/data
plane, multi-region readiness for India.
- API Layer: FastAPI gateway behind a load balancer, route-level auth, rate limiting, request
  validation.
- AI Model Serving: KServe/TorchServe for image models, Triton for tensors, TensorFlow Serving
  for TF graphs; autoscale with Kubernetes HPA and GPU node pools.
- Data Plane: object store (S3-compatible), feature store (Feast), time-series DB
  (Timescale/Postgres) for sensor streams.
- Control Plane: CI/CD with GitHub Actions, MLOps (MLflow + DVC + W&B), model registry and
  approval gates.

## AI Pipeline Stages
Data Collection (Soil Health Card, IMD/ISRO weather feeds, Sentinel-2/Planet/NASA, PlantVillage,
ICAR trial data, farmer-uploaded photos, IoT sensors) -> Data Validation & Lineage (Great
Expectations, Deequ) -> Feature Engineering (Spark/Flink, Feast) -> Training & HPO (Kubeflow/
SageMaker, Ray Tune/Optuna, MLflow/W&B logging) -> Model Registry & Deployment (staging -> canary
-> production) -> Inference & Monitoring (Prometheus + Grafana, Evidently.ai drift detection) ->
Continuous Retraining (automated triggers, shadow inference, human-in-loop approval).

## Crop Recommendation
Multi-class + multi-objective (maximize yield/profit under risk constraint). Ensemble: gradient
boosted trees (XGBoost/LightGBM/CatBoost) + shallow NN, combined via stacking. Inputs: soil NPK/
pH/OC/texture, historical yields, season, IMD weather forecasts, NDVI trend, market price,
irrigation access, farmer budget, crop rotation constraints. Outputs: ranked crop
recommendations with expected yield distribution, profit estimate, risk score, planting window.
Evaluation: TimeSeriesSplit CV, top-k accuracy, expected profit MAE, calibration (Brier score),
SHAP explainability.

## Computer Vision — Disease Detection
Multi-task: patch-level classification, object detection, segmentation, severity estimation.
Backbones considered: ResNet50, EfficientNet, Vision Transformer (ViT), YOLOv8/YOLOv11. Image
pipeline: standardized capture metadata, sRGB conversion, resize to 512/640px, augmentations
(photometric, spatial, synthetic lesion overlays, MixUp/CutMix).

## Yield Prediction
Hybrid: gradient-boosted trees on seasonal features + sequence models for intra-season dynamics,
probabilistic (quantile) forecasts. Models: LSTM/Seq2Seq, Temporal Fusion Transformer,
XGBoost/CatBoost regression. Metrics: MAE, RMSE, R², prediction-interval coverage. Feature
engineering: GDD accumulations, antecedent rainfall windows, irrigation events, NDVI slope,
fertilizer timestamps, pest/disease flags from the CV module.

## Weather Intelligence
Multi-source ingestion (Tomorrow.io primary, OpenWeather fallback; NASA/NOAA/ISRO satellite).
Derived signals: ET0 (Penman-Monteith), soil moisture anomaly, SPI drought index. Alerts:
threshold-based + learned false-positive suppression, delivered via push/SMS/voice.

## Fertilizer & Irrigation Engines
Fertilizer: rule engine (nutrient uptake curves, critical windows) + ML layer predicting
yield-response to fertilizer and recommending N-P-K split with uncertainty; output includes
dose, timing, cost estimate, environmental risk score. Irrigation: decision-tree threshold
policies, LSTM demand forecasting, RL-like scheduler optimizing water under cost/availability
constraints; output includes start time, volume, pump run-time.

## LLM-based Farmer Assistant
RAG with a local knowledge base + government scheme DB + hallucination guardrails; multilingual
(English, Hindi, Tamil; TTS/STT for regional dialects). Components: document store
(FAISS/Milvus), multilingual semantic embeddings, RAG retriever, server-side LLM responder (with
a smaller on-edge LM for offline use), explainability module surfacing sources/confidence.
Capabilities: crop-calendar/disease Q&A with citations, actionable remedy workflows, voice with
SMS fallback for low-bandwidth users. Safety: provenance tags, conservative replies for
high-impact advice (fertilizer/pesticide dosing) with confirmation toggles, escalation to a live
agronomist.

## Backend, Data Model, MLOps, Deployment
Stack: FastAPI (async), Uvicorn+Gunicorn, PostgreSQL (Timescale extension), Redis, RabbitMQ +
Celery, MinIO/S3, Docker, Kubernetes (EKS/GKE/AKS). Representative endpoints: `/v1/auth/login`,
`/v1/farmers/{id}/fields`, `/v1/cv/detect`, `/v1/recommendation/crop`,
`/v1/weather/{field_id}/forecast`, `/v1/assistant/query`. Core tables: farmers, fields,
soil_profiles, crops, crop_history, disease_records, predictions, weather_observations,
notifications. MLOps: MLflow, DVC, W&B, GitHub Actions CI, canary deployment with manual
promotion gates. Deployment: Docker Compose for local/PoC, Kubernetes/Helm for production, edge
via TF Lite/ONNX OTA updates with mutual-TLS device auth.

## Presented by
Dhivakar K (Leader), Jaiarun K (Team Member), Aravind Kumar C (Team Member).
