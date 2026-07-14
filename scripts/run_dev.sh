#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../backend"
if [ ! -f ml/models/crop_model.joblib ]; then
  echo "Training crop model (first run)..."
  python3 ml/train_crop_model.py
fi
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
