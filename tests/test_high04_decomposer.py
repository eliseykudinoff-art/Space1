"""Тесты [HIGH-04]: TaskDecomposer score-based matching."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from space1.mission.core import TaskDecomposer

def test_overlapping_keywords():
    d = TaskDecomposer()
    actions, _ = d.decompose("Deploy auth system to AWS with JWT", budget=10.0)
    names = [a.name for a in actions]
    assert any("security" in n or "auth" in n for n in names)
    assert any("deploy" in n or "infra" in n for n in names)

def test_single_category():
    d = TaskDecomposer()
    actions, _ = d.decompose("Setup Stripe payments", budget=10.0)
    names = [a.name for a in actions]
    assert any("payment" in n or "ledger" in n for n in names)

def test_fallback():
    d = TaskDecomposer()
    actions, _ = d.decompose("Do something generic", budget=10.0)
    names = [a.name for a in actions]
    assert any("setup" in n for n in names)
