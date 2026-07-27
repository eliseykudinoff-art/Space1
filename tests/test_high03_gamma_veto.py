"""Тесты [HIGH-03]: GammaVeto soft rules."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import pytest
from space1.compliance.core import GammaVeto, Action, MaxCostRule

class TestGammaVetoSoftRules:
    def test_hard_veto_binary(self):
        gv = GammaVeto([MaxCostRule(max_cost=10.0)])
        assert gv.evaluate(Action("a", resource_cost=5.0)) is True
        assert gv.evaluate(Action("a", resource_cost=15.0)) is False

    def test_soft_graded_penalty(self):
        gv = GammaVeto([MaxCostRule(max_cost=10.0)])
        low = gv.evaluate_graded(Action("a", resource_cost=5.0))
        high = gv.evaluate_graded(Action("a", resource_cost=15.0))
        assert low == 0.0
        assert high == 0.5  # (15-10)/10 = 0.5
        assert low < high

    def test_soft_penalty_proportional(self):
        gv = GammaVeto([MaxCostRule(max_cost=10.0)])
        p1 = gv.evaluate_graded(Action("a", resource_cost=20.0))  # 1.0
        p2 = gv.evaluate_graded(Action("a", resource_cost=30.0))  # 2.0
        assert p1 == 1.0
        assert p2 == 2.0
        assert p1 < p2
