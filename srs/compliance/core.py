"""
Gamma (Γ) — Compliance Veto Function

Binary compliance check: action passes only if ALL rules PASS.
Γ(action) = 1 if all rules PASS else 0

G1_prod: Graded compliance for production
U_final = U_base - lambda_gamma * max(0.0, penalty)

Reference: MATHEMATICAL_FORMULAS.md, MATHEMATICAL_ANALYSIS.md:289
"""

from abc import ABC, abstractmethod
from typing import List, Any, Dict
from dataclasses import dataclass, field


class ComplianceError(Exception):
    """
    Exception raised when an action violates compliance rules.
    
    This exception implements the Γ_hard contract: when raised, it indicates
    that the action was vetoed by hard compliance rules and execution must stop.
    """
    def __init__(self, message: str, failed_rules: List[str] = None):
        super().__init__(message)
        self.failed_rules = failed_rules or []


@dataclass
class Action:
    """Atomic action that can be checked for compliance."""
    name: str
    params: Dict[str, Any] = field(default_factory=dict)
    resource_cost: float = 0.0


class Rule(ABC):
    """Base class for compliance rules."""
    
    is_hard: bool = True  # Canonical distinction: HardRules vs SoftRules
    weight: float = 1.0   # Weight w_s for soft rules
    
    @abstractmethod
    def check(self, action: Action) -> bool:
        """Check if action passes this rule."""
        pass
        
    def check_graded(self, action: Action) -> float:
        """
        Check graded penalty for this rule.
        
        Returns:
            0.0 if passes perfectly, or a positive penalty float representing severity.
            By default, returns 1.0 (binary penalty) if check fails, else 0.0.
        """
        return 0.0 if self.check(action) else 1.0
    
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
    Graded compliance: calculates accumulated severity penalty for soft decision modeling.
    
    Formula (Binary):
        Γ(action) = 1 if ∀r ∈ Rules: r.check(action) = True
                  = 0 otherwise
                  
    Formula (Graded):
        U_final = U_base - λ_Γ × max(0, -Γ)
    """
    
    def __init__(self, rules: List[Rule] = None, lambda_gamma: float = 1.0):
        self._registry = RuleRegistry()
        self.lambda_gamma = lambda_gamma
        if rules:
            for rule in rules:
                self._registry.register(rule)
    
    def register(self, rule: Rule) -> None:
        """Register a compliance rule."""
        self._registry.register(rule)
        
    def gamma_hard(self, action: Action) -> float:
        """
        Γ_hard(action) = 0 if all HardRules pass, else -inf.
        """
        for rule in self._registry.get_rules():
            if getattr(rule, "is_hard", True):
                if not rule.check(action):
                    return float('-inf')
        return 0.0

    def gamma_soft(self, action: Action) -> float:
        """
        Γ_soft(action) = sum( w_s * violation_s(action) )
        """
        total = 0.0
        for rule in self._registry.get_rules():
            if not getattr(rule, "is_hard", True):
                weight = getattr(rule, "weight", 1.0)
                total += weight * rule.check_graded(action)
        return total
    
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
        
    def evaluate_graded(self, action: Action) -> float:
        """
        Evaluate graded compliance penalty.
        
        Returns:
            The accumulated total compliance penalty of the action [0, inf).
        """
        total_penalty = 0.0
        for rule in self._registry.get_rules():
            total_penalty += rule.check_graded(action)
        return total_penalty
        
    def apply_graded_utility(self, base_utility: float, action: Action) -> float:
        """
        Apply graded penalty to base utility score.
        
        Formula:
            U_final = U_base - λ_Γ × penalty
        """
        penalty = self.evaluate_graded(action)
        return base_utility - self.lambda_gamma * penalty
    
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
        
    def check_graded(self, action: Action) -> float:
        """Graded cost penalty matches the fraction of cost exceeding limit."""
        if self.check(action):
            return 0.0
        # Penalty is proportional to the excess budget ratio
        excess = action.resource_cost - self._max_cost
        return excess / max(self._max_cost, 1e-9)


class BlockedActionsRule(Rule):
    """Rule: certain action names are blocked."""
    
    def __init__(self, blocked_names: List[str]):
        self._blocked = set(blocked_names)
    
    @property
    def name(self) -> str:
        return "blocked_actions"
    
    def check(self, action: Action) -> bool:
        return action.name not in self._blocked
        
    def check_graded(self, action: Action) -> float:
        """Blocked actions are absolutely vetoed (infinite penalty)."""
        if self.check(action):
            return 0.0
        return float('inf')


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
