"""Тесты [HIGH-07]: MissionPolicy."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from space1.mission.core import MissionPolicy, MissionProfile

def test_preset_weights():
    p = MissionPolicy(profile=MissionProfile.SURVIVAL)
    assert p.profit_weight == 0.40
    assert p.risk_weight == 0.10

def test_calibrate_normalizes():
    p = MissionPolicy(profile=MissionProfile.GROWTH)
    w = p.calibrate()
    assert abs(sum(w.values()) - 1.0) < 0.001

def test_calibrate_with_pressures():
    p = MissionPolicy(profile=MissionProfile.GROWTH)
    w = p.calibrate({"balance": 50, "stress": 0.8})
    assert w["profit_weight"] > 0.30  # Increased due to low balance
    assert w["risk_weight"] < 0.20    # Decreased due to high stress

def test_all_profiles_sum_to_one():
    for profile in MissionProfile:
        p = MissionPolicy(profile=profile)
        assert abs(p.profit_weight + p.risk_weight + p.speed_weight + p.quality_weight - 1.0) < 0.001
