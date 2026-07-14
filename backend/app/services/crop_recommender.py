from pathlib import Path

import joblib
import pandas as pd

MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "ml" / "models"


class CropRecommender:
    def __init__(self):
        self.model = joblib.load(MODELS_DIR / "crop_model.joblib")
        self.label_encoder = joblib.load(MODELS_DIR / "label_encoder.joblib")
        self.features = joblib.load(MODELS_DIR / "features.joblib")
        self.model_name = type(self.model).__name__

    def predict(self, payload: dict, top_k: int = 3):
        row = pd.DataFrame([[payload[f] for f in self.features]], columns=self.features)
        probs = self.model.predict_proba(row)[0]
        ranked = sorted(
            zip(self.label_encoder.classes_, probs), key=lambda x: x[1], reverse=True
        )
        top = ranked[:top_k]
        return {
            "top_recommendation": top[0][0],
            "confidence": round(float(top[0][1]), 4),
            "alternatives": [
                {"crop": crop, "confidence": round(float(p), 4)} for crop, p in top
            ],
            "model_used": self.model_name,
        }


_recommender: CropRecommender | None = None


def get_recommender() -> CropRecommender:
    global _recommender
    if _recommender is None:
        _recommender = CropRecommender()
    return _recommender
