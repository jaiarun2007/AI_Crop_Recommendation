"""Irrigation Recommendation Engine.

Uses the FAO-56 crop-coefficient method (Allen et al., 1998 — "Crop
evapotranspiration - Guidelines for computing crop water requirements",
FAO Irrigation and Drainage Paper 56), the globally standard method for
estimating crop water demand:

    ETc = ET0 x Kc

  - ET0 (reference evapotranspiration) comes from live weather data
    (`reference_et0_mm` in the weather service's forecast, itself FAO-56
    Penman-Monteith, computed by Open-Meteo).
  - Kc (crop coefficient) varies by growth stage; values below are the
    standard FAO-56 Table 12 single-crop coefficients for each crop's
    initial / development / mid-season / late-season stages.

Net irrigation requirement for a day is the shortfall between crop water
demand and rainfall that day:

    irrigation_mm = max(0, ETc - precipitation_mm)

This is a simplifying assumption (it does not model soil water storage
carried over between days, or the fraction of heavy rain lost to runoff) —
documented as such in the API response, consistent with the fertilizer
engine's disclaimer.
"""
GROWTH_STAGES = ["initial", "development", "mid_season", "late_season"]

# FAO-56 Table 12 single crop coefficients (Kc), standard published values.
KC_TABLE = {
    "rice": {"initial": 1.05, "development": 1.10, "mid_season": 1.20, "late_season": 0.90},
    "maize": {"initial": 0.30, "development": 0.70, "mid_season": 1.20, "late_season": 0.60},
    "wheat": {"initial": 0.30, "development": 0.70, "mid_season": 1.15, "late_season": 0.40},
    "cotton": {"initial": 0.35, "development": 0.70, "mid_season": 1.18, "late_season": 0.60},
    "chickpea": {"initial": 0.40, "development": 0.70, "mid_season": 1.00, "late_season": 0.35},
    "kidneybeans": {"initial": 0.50, "development": 0.75, "mid_season": 1.05, "late_season": 0.90},
    "pigeonpeas": {"initial": 0.40, "development": 0.70, "mid_season": 1.00, "late_season": 0.40},
    "mothbeans": {"initial": 0.40, "development": 0.70, "mid_season": 1.00, "late_season": 0.35},
    "mungbean": {"initial": 0.40, "development": 0.70, "mid_season": 1.05, "late_season": 0.60},
    "blackgram": {"initial": 0.40, "development": 0.70, "mid_season": 1.05, "late_season": 0.60},
    "lentil": {"initial": 0.40, "development": 0.70, "mid_season": 1.10, "late_season": 0.30},
    "pomegranate": {"initial": 0.50, "development": 0.65, "mid_season": 1.00, "late_season": 0.80},
    "banana": {"initial": 0.50, "development": 0.80, "mid_season": 1.10, "late_season": 1.00},
    "mango": {"initial": 0.50, "development": 0.65, "mid_season": 0.75, "late_season": 0.70},
    "grapes": {"initial": 0.30, "development": 0.55, "mid_season": 0.85, "late_season": 0.45},
    "watermelon": {"initial": 0.40, "development": 0.70, "mid_season": 1.00, "late_season": 0.75},
    "muskmelon": {"initial": 0.40, "development": 0.70, "mid_season": 1.00, "late_season": 0.75},
    "apple": {"initial": 0.55, "development": 0.70, "mid_season": 1.00, "late_season": 0.85},
    "orange": {"initial": 0.55, "development": 0.65, "mid_season": 0.70, "late_season": 0.70},
    "papaya": {"initial": 0.50, "development": 0.70, "mid_season": 1.05, "late_season": 1.00},
    "coconut": {"initial": 0.70, "development": 0.70, "mid_season": 0.80, "late_season": 0.80},
    "coffee": {"initial": 0.90, "development": 0.95, "mid_season": 1.00, "late_season": 0.95},
    "jute": {"initial": 0.30, "development": 0.65, "mid_season": 1.10, "late_season": 0.60},
}

# Water-content unit conversions (real, not approximated): 1 mm over 1 ha = 10,000 L.
LITERS_PER_MM_PER_HECTARE = 10_000
LITERS_PER_MM_PER_ACRE = 4_046.86


def known_crops() -> list[str]:
    return sorted(KC_TABLE.keys())


def compute_etc(et0_mm: float, kc: float) -> float:
    return round(et0_mm * kc, 2)


def build_plan(crop: str, growth_stage: str, daily_forecast: list[dict], field_size_ha: float = 1.0) -> dict:
    key = crop.strip().lower()
    if key not in KC_TABLE:
        raise KeyError(crop)
    if growth_stage not in GROWTH_STAGES:
        raise ValueError(growth_stage)

    kc = KC_TABLE[key][growth_stage]
    days_out = []
    total_irrigation_mm = 0.0

    for day in daily_forecast:
        et0 = day.get("reference_et0_mm") or 0.0
        rain = day.get("precipitation_mm") or 0.0
        etc = compute_etc(et0, kc)
        irrigation_mm = max(0.0, round(etc - rain, 2))
        total_irrigation_mm += irrigation_mm

        days_out.append(
            {
                "date": day["date"],
                "reference_et0_mm": et0,
                "crop_coefficient": kc,
                "crop_water_demand_mm": etc,
                "rainfall_mm": rain,
                "irrigation_needed_mm": irrigation_mm,
                "irrigation_needed_liters": round(
                    irrigation_mm * LITERS_PER_MM_PER_HECTARE * field_size_ha, 1
                ),
                "action": "irrigate" if irrigation_mm > 0 else "skip",
            }
        )

    return {
        "crop": crop,
        "growth_stage": growth_stage,
        "crop_coefficient": kc,
        "field_size_ha": field_size_ha,
        "daily_plan": days_out,
        "total_irrigation_mm": round(total_irrigation_mm, 2),
        "total_irrigation_liters": round(
            total_irrigation_mm * LITERS_PER_MM_PER_HECTARE * field_size_ha, 1
        ),
        "method": "FAO-56 single crop coefficient (ETc = ET0 x Kc)",
        "disclaimer": (
            "Assumes irrigation_mm = max(0, ETc - rainfall) per day with no carry-over soil "
            "water storage between days and no runoff losses on heavy rain. Refine with local "
            "soil-moisture sensor data for production use."
        ),
    }
