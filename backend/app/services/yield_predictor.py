import json
from pathlib import Path

import joblib
import pandas as pd

MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "ml" / "models"


class YieldPredictor:
    def __init__(self):
        self.pipeline = joblib.load(MODELS_DIR / "yield_model.joblib")
        self.features = joblib.load(MODELS_DIR / "yield_features.joblib")
        metadata = json.loads((MODELS_DIR / "yield_metadata.json").read_text())
        self.known_areas = set(metadata["known_areas"])
        self.known_crops = set(metadata["known_crops"])
        self.r2 = metadata["r2"]
        self.model_name = metadata["best_model"]

    def predict(self, payload: dict) -> dict:
        row = pd.DataFrame([[payload[f] for f in self.features]], columns=self.features)
        pred_hg_ha = float(self.pipeline.predict(row)[0])
        pred_kg_ha = pred_hg_ha * 0.1
        pred_tonnes_ha = pred_kg_ha / 1000

        warnings = []
        if payload["Area"] not in self.known_areas:
            warnings.append(
                f"'{payload['Area']}' was not in the training data; prediction may be unreliable."
            )
        if payload["Item"] not in self.known_crops:
            warnings.append(
                f"'{payload['Item']}' was not in the training data; prediction may be unreliable."
            )

        return {
            "predicted_yield_kg_per_ha": round(pred_kg_ha, 1),
            "predicted_yield_tonnes_per_ha": round(pred_tonnes_ha, 3),
            "model_used": self.model_name,
            "model_r2": self.r2,
            "warnings": warnings,
        }


_predictor: YieldPredictor | None = None


def get_predictor() -> YieldPredictor:
    global _predictor
    if _predictor is None:
        _predictor = YieldPredictor()
    return _predictor
