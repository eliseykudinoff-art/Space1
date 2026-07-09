"""
Tests for GammaVeto (Compliance Veto Function)

Reference: DEVELOPMENT_PLAN.md - G1
"""

import pytest
from space1.compliance.core import (
    GammaVeto, Action, Rule, RuleRegistry,
    MaxCostRule, BlockedActionsRule, ParameterConstraintRule
)


class TestGammaVeto:
    """Test GammaVeto binary compliance."""
    
    def test_empty_rules_passes(self):
        """No rules = all actions pass."""
        veto = GammaVeto()
        action = Action(name="test", params={"value": 1})
        
        assert veto.evaluate(action) is True
    
    def test_single_rule_passes(self):
        """Action passes when single rule passes."""
        veto = GammaVeto()
        veto.register(MaxCostRule(max_cost=100))
        
        action = Action(name="test", resource_cost=50)
        assert veto.evaluate(action) is True
    
    def test_single_rule_fails(self):
        """Action fails when single rule fails."""
        veto = GammaVeto()
        veto.register(MaxCostRule(max_cost=100))
        
        action = Action(name="test", resource_cost=150)
        assert veto.evaluate(action) is False
    
    def test_multiple_rules_all_pass(self):
        """Action passes when ALL rules pass."""
        veto = GammaVeto()
        veto.register(MaxCostRule(max_cost=100))
        veto.register(BlockedActionsRule(blocked_names=["delete_all"]))
        
        action = Action(name="read", resource_cost=10)
        assert veto.evaluate(action) is True
    
    def test_multiple_rules_one_fails(self):
        """Action fails when ANY rule fails."""
        veto = GammaVeto()
        veto.register(MaxCostRule(max_cost=100))
        veto.register(BlockedActionsRule(blocked_names=["delete_all"]))
        
        action = Action(name="delete_all", resource_cost=10)
        assert veto.evaluate(action) is False
    
    def test_evaluate_with_details(self):
        """Test detailed evaluation results."""
        veto = GammaVeto()
        veto.register(MaxCostRule(max_cost=100))
        veto.register(BlockedActionsRule(blocked_names=["delete_all"]))
        
        action = Action(name="delete_all", resource_cost=10)
        result = veto.evaluate_with_details(action)
        
        assert result["pass"] is False
        assert "blocked_actions" in result["failed_rules"]
        assert "max_cost" in result["passed_rules"]


class TestRuleRegistry:
    """Test RuleRegistry functionality."""
    
    def test_register_rule(self):
        """Test rule registration."""
        registry = RuleRegistry()
        rule = MaxCostRule(max_cost=50)
        
        registry.register(rule)
        
        assert len(registry.get_rules()) == 1
    
    def test_unregister_rule(self):
        """Test rule removal."""
        registry = RuleRegistry()
        rule = MaxCostRule(max_cost=50)
        registry.register(rule)
        
        result = registry.unregister("max_cost")
        
        assert result is True
        assert len(registry.get_rules()) == 0
    
    def test_unregister_nonexistent(self):
        """Test removing non-existent rule."""
        registry = RuleRegistry()
        
        result = registry.unregister("nonexistent")
        
        assert result is False


class TestBlockedActionsRule:
    """Test BlockedActionsRule."""
    
    def test_action_not_blocked(self):
        """Action not in blocklist passes."""
        rule = BlockedActionsRule(blocked_names=["delete", "drop"])
        action = Action(name="read")
        
        assert rule.check(action) is True
    
    def test_action_blocked(self):
        """Action in blocklist fails."""
        rule = BlockedActionsRule(blocked_names=["delete", "drop"])
        action = Action(name="delete")
        
        assert rule.check(action) is False


class TestParameterConstraintRule:
    """Test ParameterConstraintRule."""
    
    def test_valid_params(self):
        """Action with valid params passes."""
        rule = ParameterConstraintRule({
            "count": lambda x: 0 <= x <= 100,
            "name": lambda x: len(x) > 0
        })
        action = Action(name="test", params={"count": 50, "name": "valid"})
        
        assert rule.check(action) is True
    
    def test_invalid_param(self):
        """Action with invalid param fails."""
        rule = ParameterConstraintRule({
            "count": lambda x: 0 <= x <= 100
        })
        action = Action(name="test", params={"count": 150})
        
        assert rule.check(action) is False
    
    def test_missing_param(self):
        """Action missing required param fails."""
        rule = ParameterConstraintRule({
            "count": lambda x: x > 0
        })
        action = Action(name="test", params={})
        
        assert rule.check(action) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
