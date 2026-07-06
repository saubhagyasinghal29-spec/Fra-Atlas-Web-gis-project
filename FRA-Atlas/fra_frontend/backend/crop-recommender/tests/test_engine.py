"""Tests for the rule engine. Run either way:

    python tests/test_engine.py      # standalone, no pytest needed
    pytest                           # if pytest is installed
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from croprec import DistrictConditions, load_crops, recommend  # noqa: E402
from croprec.water import available_water  # noqa: E402
from croprec.engine import (  # noqa: E402
    score_all, temperature_adjustment, groundwater_penalty, season_adjustment,
)

HISAR = DistrictConditions("Hisar", 450, "critical", 55, "sandy loam", "rabi", 22)


def _crop(name):
    return next(c for c in load_crops() if c.name == name)


def test_available_water_breakdown_adds_up():
    aw = available_water(450, 55)
    assert abs(aw.total_mm - (aw.effective_rain_mm + aw.irrigation_mm)) < 1e-6
    assert aw.effective_rain_mm > 0 and aw.irrigation_mm > 0


def test_water_rejects_bad_input():
    for bad in (lambda: available_water(-1, 50), lambda: available_water(400, 150)):
        try:
            bad()
            assert False, "expected ValueError"
        except ValueError:
            pass


def test_groundwater_penalty_scales_with_intensity():
    rice, mustard = _crop("Rice"), _crop("Mustard")
    # Rice is high-intensity, mustard low: same block, bigger penalty for rice.
    assert groundwater_penalty(HISAR, rice) > groundwater_penalty(HISAR, mustard)
    safe = DistrictConditions("X", 450, "safe", 55, "sandy loam", "rabi", 22).normalised()
    assert groundwater_penalty(safe, rice) == 0.0


def test_season_mismatch_is_penalised():
    rice = _crop("Rice")  # kharif crop
    assert season_adjustment(HISAR.normalised(), rice) < 0
    sugarcane = _crop("Sugarcane")  # annual -> always in season
    assert season_adjustment(HISAR.normalised(), sugarcane) == 0.0


def test_temperature_penalty_outside_band():
    rice = _crop("Rice")  # suited 20-37C
    cold = DistrictConditions("Cold", 1400, "safe", 80, "clay", "kharif", 8).normalised()
    warm = DistrictConditions("Warm", 1400, "safe", 80, "clay", "kharif", 28).normalised()
    assert temperature_adjustment(cold, rice) < 0
    assert temperature_adjustment(warm, rice) == 0.0


def test_hisar_ranks_low_water_rabi_crops_top():
    result = recommend(HISAR)
    top_names = [r.crop for r in result.top(3)]
    assert "Mustard" in top_names
    # Rice (kharif, thirsty, wrong soil) must score near zero and sit in the
    # bottom quartile (several thirsty/out-of-season crops tie at 0).
    rice = next(r for r in result.recommendations if r.crop == "Rice")
    assert rice.final_score <= 10.0
    rice_rank = [r.crop for r in result.recommendations].index("Rice")
    assert rice_rank >= 0.75 * len(result.recommendations)


def test_scores_are_bounded():
    _, results = score_all(HISAR, load_crops())
    for r in results:
        assert 0.0 <= r.rule_score <= 100.0


def test_season_flip_changes_ranking():
    rabi = recommend(DistrictConditions("D", 700, "safe", 60, "loam", "rabi", 22))
    kharif = recommend(DistrictConditions("D", 700, "safe", 60, "loam", "kharif", 28))
    assert [r.crop for r in rabi.top(3)] != [r.crop for r in kharif.top(3)]


def test_pure_rule_when_no_model():
    result = recommend(HISAR, model=None, ml_scores=None)
    # No model dir shipped -> rule-only.
    assert result.used_ml is False
    assert all(r.ml_score is None for r in result.recommendations)


def _run_standalone():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS  {fn.__name__}")
            passed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL  {fn.__name__}: {exc}")
    print(f"\n{passed}/{len(fns)} passed")
    return passed == len(fns)


if __name__ == "__main__":
    sys.exit(0 if _run_standalone() else 1)
