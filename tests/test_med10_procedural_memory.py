"""Тесты [MED-10]: ProceduralMemory success_rate gate."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from space1.memory.core import ProceduralMemory, Skill

def test_add_skill_above_threshold():
    pm = ProceduralMemory(min_success_rate=0.7)
    s = Skill("good", "desc", success_rate=0.8)
    assert pm.add_skill(s) is True
    assert "good" in pm._skills

def test_add_skill_below_threshold():
    pm = ProceduralMemory(min_success_rate=0.7)
    s = Skill("bad", "desc", success_rate=0.5)
    assert pm.add_skill(s) is False
    assert "bad" not in pm._skills

def test_get_active_skills_filters():
    pm = ProceduralMemory(min_success_rate=0.7)
    pm.add_skill(Skill("active", "desc", success_rate=0.8))
    pm.add_skill(Skill("inactive", "desc", success_rate=0.5))  # rejected
    pm._skills["inactive"] = Skill("inactive", "desc", success_rate=0.5)  # bypass
    active = pm.get_active_skills()
    assert len(active) == 1
    assert active[0].name == "active"

def test_record_usage_updates_rate():
    pm = ProceduralMemory()
    s = Skill("test", "desc", success_rate=0.5)
    pm._skills["test"] = s  # bypass gate for testing
    pm.record_usage("test", success=True)
    assert s.success_rate > 0.5  # increased
