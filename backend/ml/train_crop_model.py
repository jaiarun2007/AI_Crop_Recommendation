"""Trains the crop-recommendation model and saves the best one to backend/ml/models/.

Dataset: N, P, K, temperature, humidity, pH, rainfall -> crop label (22 classes, 2200 rows).
Compares RandomForest, XGBoost, and LightGBM (if installed) and keeps the most accurate.
"""
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

HERE = Path(__file__).resolve().parent
DATA_PATH = HERE / "data" / "crop_recommendation.csv"
MODELS_DIR = HERE / "models"
FEATURES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]


def load_data():
    df = pd.read_csv(DATA_PATH)
    X = df[FEATURES]
    y = df["label"]
    return train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)


def build_candidates():
    candidates = {
        "random_forest": RandomForestClassifier(
            n_estimators=200, max_depth=None, random_state=42, n_jobs=-1
        ),
    }
    try:
        from xgboost import XGBClassifier

        candidates["xgboost"] = XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            eval_metric="mlogloss",
        )
    except ImportError:
        pass
    try:
        from lightgbm import LGBMClassifier

        candidates["lightgbm"] = LGBMClassifier(
            n_estimators=300, random_state=42, verbosity=-1
        )
    except ImportError:
        pass
    return candidates


def main():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    X_train, X_test, y_train, y_test = load_data()

    label_encoder = LabelEncoder()
    y_train_enc = label_encoder.fit_transform(y_train)
    y_test_enc = label_encoder.transform(y_test)

    results = {}
    best_name, best_model, best_acc = None, None, -1.0

    for name, model in build_candidates().items():
        model.fit(X_train, y_train_enc)
        preds = model.predict(X_test)
        acc = accuracy_score(y_test_enc, preds)
        results[name] = round(acc, 4)
        print(f"[{name}] accuracy = {acc:.4f}")
        if acc > best_acc:
            best_name, best_model, best_acc = name, model, acc

    report = classification_report(
        y_test_enc, best_model.predict(X_test), target_names=label_encoder.classes_
    )
    print(f"\nBest model: {best_name} (accuracy={best_acc:.4f})\n")
    print(report)

    joblib.dump(best_model, MODELS_DIR / "crop_model.joblib")
    joblib.dump(label_encoder, MODELS_DIR / "label_encoder.joblib")
    joblib.dump(FEATURES, MODELS_DIR / "features.joblib")

    metadata = {
        "best_model": best_name,
        "accuracy": best_acc,
        "all_results": results,
        "features": FEATURES,
        "n_classes": len(label_encoder.classes_),
        "classes": sorted(label_encoder.classes_.tolist()),
    }
    (MODELS_DIR / "metadata.json").write_text(json.dumps(metadata, indent=2))
    print(f"Saved model artifacts to {MODELS_DIR}")


if __name__ == "__main__":
    main()
