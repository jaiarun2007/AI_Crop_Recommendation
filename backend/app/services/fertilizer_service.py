"""Fertilizer Recommendation Engine.

Rule-based N-P-K balancing (per the Executive Summary's stated approach), not ML:
1. Look up each crop's ideal N/P/K/pH from a real per-crop reference table
   (Harvestify project's `Data-processed/fertilizer.csv`, itself derived from
   agronomic extension guidance).
2. Compare against the farmer's actual soil-test readings to find deficits/surpluses.
3. Translate a nutrient deficit into a dose of a real, standard fertilizer product
   using that product's published nutrient content (N / P2O5 / K2O percentage by
   weight — standard grades under India's Fertilizer Control Order).

This is a simplified elemental-nutrient approximation for advisory purposes (it does
not model soil nutrient availability, application timing/splits, or crop growth
stage) — not a substitute for a certified agronomist's prescription. That caveat is
also returned in the API response.
"""
import csv
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent.parent / "ml" / "data" / "fertilizer_reference.csv"

# Standard fertilizer grades and their nutrient content by weight (real, published values).
# P and K expressed as elemental-equivalent fractions for this simplified balance.
FERTILIZER_PRODUCTS = {
    "N": {"name": "Urea", "nutrient_fraction": 0.46},
    "P": {"name": "Single Super Phosphate (SSP)", "nutrient_fraction": 0.16},
    "K": {"name": "Muriate of Potash (MOP)", "nutrient_fraction": 0.50},
}

DEFICIT_THRESHOLD_KG_HA = 5.0  # below this, treat as "adequate" rather than flag noise
PH_TOLERANCE = 0.5


def _load_reference() -> dict:
    reference = {}
    with open(DATA_PATH, newline="") as f:
        for row in csv.DictReader(f):
            reference[row["Crop"].strip().lower()] = {
                "N": float(row["N"]),
                "P": float(row["P"]),
                "K": float(row["K"]),
                "pH": float(row["pH"]),
                "soil_moisture": float(row["soil_moisture"]),
            }
    return reference


_REFERENCE = _load_reference()


def known_crops() -> list[str]:
    return sorted(_REFERENCE.keys())


def _nutrient_advice(nutrient: str, actual: float, ideal: float) -> dict:
    delta = ideal - actual
    if abs(delta) <= DEFICIT_THRESHOLD_KG_HA:
        return {"nutrient": nutrient, "status": "adequate", "delta_kg_ha": round(delta, 1)}
    if delta > 0:
        product = FERTILIZER_PRODUCTS[nutrient]
        dose = delta / product["nutrient_fraction"]
        return {
            "nutrient": nutrient,
            "status": "deficient",
            "delta_kg_ha": round(delta, 1),
            "recommended_product": product["name"],
            "recommended_dose_kg_ha": round(dose, 1),
        }
    return {
        "nutrient": nutrient,
        "status": "surplus",
        "delta_kg_ha": round(delta, 1),
        "note": "No additional application needed; consider reducing next season's dose.",
    }


def recommend(crop: str, N: float, P: float, K: float, ph: float) -> dict:
    key = crop.strip().lower()
    if key not in _REFERENCE:
        raise KeyError(crop)

    ideal = _REFERENCE[key]
    nutrients = [
        _nutrient_advice("N", N, ideal["N"]),
        _nutrient_advice("P", P, ideal["P"]),
        _nutrient_advice("K", K, ideal["K"]),
    ]

    ph_delta = ideal["pH"] - ph
    if abs(ph_delta) <= PH_TOLERANCE:
        ph_advice = {"status": "adequate", "message": f"Soil pH {ph} is close to ideal ({ideal['pH']})."}
    elif ph_delta > 0:
        ph_advice = {
            "status": "too_acidic",
            "message": (
                f"Soil pH {ph} is below the ideal {ideal['pH']} for {crop}. "
                "Consider agricultural lime application to raise pH."
            ),
        }
    else:
        ph_advice = {
            "status": "too_alkaline",
            "message": (
                f"Soil pH {ph} is above the ideal {ideal['pH']} for {crop}. "
                "Consider elemental sulfur or organic matter to lower pH."
            ),
        }

    return {
        "crop": crop,
        "ideal_reference": ideal,
        "nutrients": nutrients,
        "ph_advice": ph_advice,
        "disclaimer": (
            "Simplified elemental N-P-K balance for advisory purposes; does not account for "
            "soil nutrient availability, application timing/splits, or growth stage. Consult a "
            "certified agronomist / local Soil Health Card guidance before large-scale application."
        ),
    }
