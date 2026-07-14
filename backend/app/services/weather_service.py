"""Weather Intelligence: real forecasts + rule-based agro-alerts.

Alert thresholds follow published IMD (India Meteorological Department)
rainfall-intensity and heatwave classification bands, not arbitrary numbers:
  - Heavy rain:            64.5-115.5 mm/day
  - Very heavy rain:       115.6-204.4 mm/day
  - Extremely heavy rain:  > 204.4 mm/day
  - Heatwave (plains):     max temp >= 40 C
  - Severe heatwave:       max temp >= 45 C
  - High wind advisory:    sustained/gust wind >= 40 km/h
  - Dry-spell risk:        < 5 mm cumulative rain over the forecast window
"""
from app.services import weather_client
from app.services.weather_client import WeatherAPIError  # re-exported

HEAVY_RAIN_MM = 64.5
VERY_HEAVY_RAIN_MM = 115.6
EXTREME_RAIN_MM = 204.4
HEATWAVE_C = 40.0
SEVERE_HEATWAVE_C = 45.0
HIGH_WIND_KMH = 40.0
DRY_SPELL_TOTAL_RAIN_MM = 5.0


def resolve_location(location: str | None, lat: float | None, lon: float | None) -> dict:
    if lat is not None and lon is not None:
        return {"name": location or "custom location", "latitude": lat, "longitude": lon}
    if location:
        return weather_client.geocode(location)
    raise ValueError("Provide either `location` or both `lat` and `lon`.")


def get_forecast(location: str | None, lat: float | None, lon: float | None, days: int = 7) -> dict:
    place = resolve_location(location, lat, lon)
    raw = weather_client.fetch_forecast(place["latitude"], place["longitude"], days=days)
    daily = raw.get("daily", {})

    days_out = []
    dates = daily.get("time", [])
    for i, date in enumerate(dates):
        days_out.append(
            {
                "date": date,
                "temp_max_c": daily["temperature_2m_max"][i],
                "temp_min_c": daily["temperature_2m_min"][i],
                "precipitation_mm": daily["precipitation_sum"][i],
                "precipitation_probability_percent": daily["precipitation_probability_max"][i],
                "humidity_percent": daily["relative_humidity_2m_mean"][i],
                "wind_speed_max_kmh": daily["windspeed_10m_max"][i],
                "reference_et0_mm": daily["et0_fao_evapotranspiration"][i],
            }
        )

    return {
        "location": place,
        "timezone": raw.get("timezone"),
        "daily": days_out,
    }


def compute_alerts(daily: list[dict]) -> list[dict]:
    alerts = []
    total_rain = sum(d["precipitation_mm"] for d in daily)

    for d in daily:
        if d["temp_max_c"] >= SEVERE_HEATWAVE_C:
            alerts.append(
                _alert(d["date"], "severe_heatwave", "high",
                       f"Severe heatwave: forecast max {d['temp_max_c']}C.")
            )
        elif d["temp_max_c"] >= HEATWAVE_C:
            alerts.append(
                _alert(d["date"], "heatwave", "medium",
                       f"Heatwave conditions: forecast max {d['temp_max_c']}C.")
            )

        if d["precipitation_mm"] >= EXTREME_RAIN_MM:
            alerts.append(
                _alert(d["date"], "extremely_heavy_rain", "high",
                       f"Extremely heavy rain expected: {d['precipitation_mm']}mm.")
            )
        elif d["precipitation_mm"] >= VERY_HEAVY_RAIN_MM:
            alerts.append(
                _alert(d["date"], "very_heavy_rain", "high",
                       f"Very heavy rain expected: {d['precipitation_mm']}mm.")
            )
        elif d["precipitation_mm"] >= HEAVY_RAIN_MM:
            alerts.append(
                _alert(d["date"], "heavy_rain", "medium",
                       f"Heavy rain expected: {d['precipitation_mm']}mm.")
            )

        if d["wind_speed_max_kmh"] >= HIGH_WIND_KMH:
            alerts.append(
                _alert(d["date"], "high_wind", "medium",
                       f"High wind advisory: gusts up to {d['wind_speed_max_kmh']}km/h.")
            )

    if daily and total_rain < DRY_SPELL_TOTAL_RAIN_MM:
        alerts.append(
            _alert(daily[0]["date"], "dry_spell_risk", "medium",
                   f"Only {total_rain:.1f}mm total rain forecast over {len(daily)} days — "
                   "irrigation planning recommended.")
        )

    return alerts


def _alert(date: str, alert_type: str, severity: str, message: str) -> dict:
    return {"date": date, "type": alert_type, "severity": severity, "message": message}
