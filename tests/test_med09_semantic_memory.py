"""Тесты [MED-09]: SemanticMemory asymmetric confidence."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from space1.memory.core import SemanticMemory

def test_confirm_increases_less():
    sm = SemanticMemory()
    sm.add_fact("k", "v", confidence=0.5)
    sm.confirm("k")
    # 0.9 * 0.5 + 0.1 = 0.55 (small increase)
    assert sm._facts["k"].confidence == 0.55

def test_contradict_decreases_more():
    sm = SemanticMemory()
    sm.add_fact("k", "v", confidence=0.5)
    sm.contradict("k")
    # 0.7 * 0.5 = 0.35 (larger decrease than confirm increase)
    assert sm._facts["k"].confidence == 0.35

def test_asymmetric():
    sm = SemanticMemory()
    sm.add_fact("k", "v", confidence=0.5)
    # Confirm then contradict → net loss
    sm.confirm("k")  # 0.55
    sm.contradict("k")  # 0.7 * 0.55 = 0.385 < 0.5
    assert sm._facts["k"].confidence < 0.5

def test_contradiction_counter():
    sm = SemanticMemory()
    sm.add_fact("k", "v", confidence=1.0)
    sm.contradict("k")
    assert sm._facts["k"].contradictions == 1
