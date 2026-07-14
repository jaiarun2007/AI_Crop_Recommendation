"""Trains the yield-prediction model and saves it to backend/ml/models/.

Dataset: FAO/World-Bank-derived yield_df.csv (28,242 rows, 101 countries, 10 crop types).
Features: Area (country), Item (crop), Year, rainfall, pesticide use, avg temperature.
Target: hg/ha_yield (hectograms per hectare).

Compares RandomForestRegressor and XGBRegressor and keeps the one with the higher R^2.
"""
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

HERE = Path(__file__).resolve().parent
DATA_PATH = HERE / "data" / "yield_df.csv"
MODELS_DIR = HERE / "models"

NUMERIC_FEATURES = ["Year", "average_rain_fall_mm_per_year", "pesticides_tonnes", "avg_temp"]
CATEGORICAL_FEATURES = ["Area", "Item"]
FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES
TARGET = "hg/ha_yield"


def load_data():
    df = pd.read_csv(DATA_PATH, index_col=0)
    X = df[FEATURES]
    y = df[TARGET]
    return train_test_split(X, y, test_size=0.2, random_state=42)


def build_preprocessor():
    return ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ],
        remainder="passthrough",
    )


def build_candidates():
    candidates = {
        "random_forest": RandomForestRegressor(
            n_estimators=150, max_depth=14, min_samples_leaf=2, random_state=42, n_jobs=-1
        ),
    }
    try:
        from xgboost import XGBRegressor

        candidates["xgboost"] = XGBRegressor(
            n_estimators=300, max_depth=8, learning_rate=0.1, random_state=42
        )
    except ImportError:
        pass
    return candidates


def main():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    X_train, X_test, y_train, y_test = load_data()

    results = {}
    best_name, best_pipeline, best_r2 = None, None, -1e9

    for name, model in build_candidates().items():
        pipeline = Pipeline(
            steps=[("preprocess", build_preprocessor()), ("model", model)]
        )
        pipeline.fit(X_train, y_train)
        preds = pipeline.predict(X_test)
        r2 = r2_score(y_test, preds)
        mae = mean_absolute_error(y_test, preds)
        results[name] = {"r2": round(r2, 4), "mae": round(mae, 1)}
        print(f"[{name}] R^2={r2:.4f}  MAE={mae:.1f} hg/ha")
        if r2 > best_r2:
            best_name, best_pipeline, best_r2 = name, pipeline, r2

    print(f"\nBest model: {best_name} (R^2={best_r2:.4f})")

    joblib.dump(best_pipeline, MODELS_DIR / "yield_model.joblib")
    joblib.dump(FEATURES, MODELS_DIR / "yield_features.joblib")

    df = pd.read_csv(DATA_PATH, index_col=0)
    metadata = {
        "best_model": best_name,
        "r2": round(best_r2, 4),
        "all_results": results,
        "features": FEATURES,
        "target": TARGET,
        "target_unit": "hg/ha (hectograms per hectare; 1 hg/ha = 0.1 kg/ha)",
        "known_areas": sorted(df["Area"].unique().tolist()),
        "known_crops": sorted(df["Item"].unique().tolist()),
        "year_range": [int(df["Year"].min()), int(df["Year"].max())],
    }
    (MODELS_DIR / "yield_metadata.json").write_text(json.dumps(metadata, indent=2))
    print(f"Saved model artifacts to {MODELS_DIR}")


if __name__ == "__main__":
    main()
