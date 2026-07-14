"""Direct tests of the FAO-56 ETc calculation and irrigation-plan logic, independent of
any network call — these exercise real formulas against example inputs."""
import pytest

from app.services import irrigation_service


def test_compute_etc_is_et0_times_kc():
    assert irrigation_service.compute_etc(5.0, 1.2) == 6.0


def test_build_plan_irrigates_when_rainfall_below_demand():
    forecast = [{"date": "2026-07-15", "reference_et0_mm": 5.0, "precipitation_mm": 0.0}]
    plan = irrigation_service.build_plan("rice", "mid_season", forecast)
    day = plan["daily_plan"][0]
    # rice mid_season Kc = 1.20 -> ETc = 6.0mm; rainfall 0 -> irrigate 6.0mm
    assert day["crop_water_demand_mm"] == 6.0
    assert day["irrigation_needed_mm"] == 6.0
    assert day["action"] == "irrigate"


def test_build_plan_skips_when_rainfall_covers_demand():
    forecast = [{"date": "2026-07-15", "reference_et0_mm": 5.0, "precipitation_mm": 20.0}]
    plan = irrigation_service.build_plan("rice", "mid_season", forecast)
    day = plan["daily_plan"][0]
    assert day["irrigation_needed_mm"] == 0.0
    assert day["action"] == "skip"


def test_build_plan_scales_liters_with_field_size():
    forecast = [{"date": "2026-07-15", "reference_et0_mm": 5.0, "precipitation_mm": 0.0}]
    plan_1ha = irrigation_service.build_plan("rice", "mid_season", forecast, field_size_ha=1.0)
    plan_2ha = irrigation_service.build_plan("rice", "mid_season", forecast, field_size_ha=2.0)
    assert plan_2ha["total_irrigation_liters"] == pytest.approx(
        plan_1ha["total_irrigation_liters"] * 2
    )


def test_build_plan_unknown_crop_raises_keyerror():
    with pytest.raises(KeyError):
        irrigation_service.build_plan("dragonfruit", "mid_season", [])


def test_build_plan_unknown_growth_stage_raises_valueerror():
    with pytest.raises(ValueError):
        irrigation_service.build_plan("rice", "flowering", [])
