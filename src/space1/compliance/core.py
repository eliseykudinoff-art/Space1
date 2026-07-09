"""
Gamma (Γ) — Compliance Veto Function

Binary compliance check: action passes only if ALL rules PASS.
Γ(action) = 1 if all rules PASS else 0

Reference: MATHEMATICAL_FORMULAS.md, MATHEMATICAL_ANALYSIS.md:289
Decision: Binary veto for MVP (Graded for production)
"""

from abc import ABC, abstractmethod
from typing import List, Any, Dict
from dataclasses import dataclass, field


@dataclass
class Action:
    """Atomic action that can be checked for compliance."""
    name: str
    params: Dict[str, Any] = field(default_factory=dict)
    resource_cost: float = 0.0


class Rule(ABC):
    """Base class for compliance rules."""
    
    @abstractmethod
    def check(self, action: Action) -> bool:
        """Check if action passes this rule."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Rule name for logging/debugging."""
        pass


class RuleRegistry:
    """Registry for all compliance rules."""
    
    def __init__(self):
        self._rules: List[Rule] = []
    
    def register(self, rule: Rule) -> None:
        """Register a new rule."""
        self._rules.append(rule)
    
    def unregister(self, rule_name: str) -> bool:
        """Remove rule by name. Returns True if found."""
        for i, rule in enumerate(self._rules):
            if rule.name == rule_name:
                self._rules.pop(i)
                return True
        return False
    
    def get_rules(self) -> List[Rule]:
        """Get all registered rules."""
        return self._rules.copy()


class GammaVeto:
    """
    Gamma (Γ) — Compliance Veto Function
    
    Binary compliance: returns True only if ALL rules pass.
    
    Formula:
        Γ(action) = 1 if ∀r ∈ Rules: r.check(action) = True
                  = 0 otherwise
    
    Usage:
        veto = GammaVeto()
        veto.register(MaxCostRule(max_cost=100))
        veto.register(BlockedDomainsRule(domains=["evil.com"]))
        
        if veto.evaluate(action):
            # Execute action
        else:
            # Reject action
    """
    
    def __init__(self, rules: List[Rule] = None):
        self._registry = RuleRegistry()
        if rules:
            for rule in rules:
                self._registry.register(rule)
    
    def register(self, rule: Rule) -> None:
        """Register a compliance rule."""
        self._registry.register(rule)
    
    def evaluate(self, action: Action) -> bool:
        """
        Evaluate compliance for an action.
        
        Returns:
            True if ALL rules pass (action is compliant)
            False if ANY rule fails (action is rejected)
        """
        for rule in self._registry.get_rules():
            if not rule.check(action):
                return False
        return True
    
    def evaluate_with_details(self, action: Action) -> Dict[str, Any]:
        """
        Evaluate and return detailed results.
        
        Returns:
            {
                "pass": bool,
                "failed_rules": [rule names that failed],
                "passed_rules": [rule names that passed]
            }
        """
        passed = []
        failed = []
        
        for rule in self._registry.get_rules():
            if rule.check(action):
                passed.append(rule.name)
            else:
                failed.append(rule.name)
        
        return {
            "pass": len(failed) == 0,
            "failed_rules": failed,
            "passed_rules": passed
        }
    
    def get_rules(self) -> List[Rule]:
        """Get all registered rules."""
        return self._registry.get_rules()


# =============================================================================
# Common Rules Implementations
# =============================================================================

class MaxCostRule(Rule):
    """Rule: action cost must not exceed maximum."""
    
    def __init__(self, max_cost: float):
        self._max_cost = max_cost
    
    @property
    def name(self) -> str:
        return "max_cost"
    
    def check(self, action: Action) -> bool:
        return action.resource_cost <= self._max_cost


class BlockedActionsRule(Rule):
    """Rule: certain action names are blocked."""
    
    def __init__(self, blocked_names: List[str]):
        self._blocked = set(blocked_names)
    
    @property
    def name(self) -> str:
        return "blocked_actions"
    
    def check(self, action: Action) -> bool:
        return action.name not in self._blocked


class ParameterConstraintRule(Rule):
    """Rule: action parameters must satisfy constraints."""
    
    def __init__(self, constraints: Dict[str, callable]):
        """
        Args:
            constraints: Dict of param_name -> validation_function(value) -> bool
        """
        self._constraints = constraints
    
    @property
    def name(self) -> str:
        return "parameter_constraints"
    
    def check(self, action: Action) -> bool:
        for param_name, validator in self._constraints.items():
            if param_name not in action.params:
                return False
            if not validator(action.params[param_name]):
                return False
        return True


class RateLimitRule(Rule):
    """Rule: enforce rate limits on actions."""
    
    def __init__(self, action_name: str, max_per_minute: int):
        self._action_name = action_name
        self._max_per_minute = max_per_minute
        self._calls: List[float] = []  # timestamps
    
    @property
    def name(self) -> str:
        return f"rate_limit_{self._action_name}"
    
    def check(self, action: Action) -> bool:
        import time
        if action.name != self._action_name:
            return True  # Not our action
        
        now = time.time()
        # Keep only calls from last minute
        self._calls = [t for t in self._calls if now - t < 60]
        
        if len(self._calls) >= self._max_per_minute:
            return False
        
        self._calls.append(now)
        return True
