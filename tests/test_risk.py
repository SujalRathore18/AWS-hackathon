import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import risk


def test_hot_humid_is_dangerous():
    assert risk.heat_index_c(40, 40) > 45


def test_cool_day_is_low():
    assert risk.heat_index_c(25, 40) < 32
    assert risk.assess(25, 40, "commute", 30, 9)["level"] == "Low"


def test_harder_activity_never_lowers_risk():
    easy = risk.assess(35, 50, "commute", 60, 13)["level_index"]
    hard = risk.assess(35, 50, "sports", 60, 13)["level_index"]
    assert hard >= easy


def test_imd_alert_raises_level():
    assert risk.assess(25, 40, "commute", 30, 9, "red")["level"] == "Extreme"


def test_safe_minutes_shrink_with_level():
    low = risk.assess(25, 40, "walking", 30, 9)["safe_minutes"]
    high = risk.assess(42, 40, "walking", 30, 13)["safe_minutes"]
    assert high < low


def test_best_windows_prefers_cooler_hours():
    forecast = [
        {"time": "2026-04-20T08:00", "temp_c": 30, "humidity": 40},
        {"time": "2026-04-20T14:00", "temp_c": 43, "humidity": 30},
    ]
    _, best = risk.best_windows(forecast, "commute", 60)
    assert best == ["08:00"]


def test_assessment_exposes_heuristic_limit_and_note():
    result = risk.assess(35, 50, "walking", 60, 9)
    assert result["planning_limit_minutes"] == result["safe_minutes"]
    assert "awareness estimate" in result["model_note"]


def test_assessment_rejects_invalid_inputs():
    import pytest

    with pytest.raises(ValueError):
        risk.assess(35, 120, "walking", 60, 9)
    with pytest.raises(ValueError):
        risk.assess(35, 50, "unknown", 60, 9)
    with pytest.raises(ValueError):
        risk.assess(35, 50, "walking", 601, 9)
