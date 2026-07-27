"""
Shapley Attributor Module. Measures the marginal contribution of each active module
to the agent's total performance (CQS, success rate, or expected revenue).
"""

import math
from itertools import combinations
from typing import List, Dict, Set, Any

from .models import AgentConfig, ModuleType
from .evaluator import Evaluator


class ShapleyAttributor:
    """
    ShapleyAttributor.
    Calculates exact Shapley values for agent wrapper modules.
    Identifies synergies, redundancies, and independent effects.
    """
    
    def __init__(self, modules: List[ModuleType], evaluator: Evaluator):
        self.modules = list(modules)
        self.evaluator = evaluator
        self.cache: Dict[frozenset, Dict[str, float]] = {}
        
    def _evaluate_subset(self, subset: Set[ModuleType], metric: str = "mean_success_rate") -> float:
        """Evaluate subset of modules using cached results."""
        f_subset = frozenset(subset)
        if f_subset not in self.cache:
            # Construct a temporary config with only subset modules active
            config = AgentConfig(
                active_modules=set(subset),
                theta_accept=0.70,
                theta_ask=0.40,
                safety_threshold=0.72,  # Optimized default
                risk_aversion=0.50
            )
            self.cache[f_subset] = self.evaluator.evaluate_dataset(config)
        return self.cache[f_subset].get(metric, 0.0)

    def compute_shapley(self, module: ModuleType, metric: str = "mean_success_rate") -> float:
        """
        Calculates the Shapley value (marginal contribution) of a single module.
        Formula:
            phi_i = sum_{S subset N \\ {i}} [|S|!(n - |S| - 1)! / n!] * [v(S U {i}) - v(S)]
        """
        n = len(self.modules)
        if module not in self.modules:
            return 0.0
            
        other_modules = [m for m in self.modules if m != module]
        shapley = 0.0
        
        for r in range(len(other_modules) + 1):
            for subset in combinations(other_modules, r):
                S = set(subset)
                S_with_i = S | {module}
                
                v_S_with_i = self._evaluate_subset(S_with_i, metric=metric)
                v_S = self._evaluate_subset(S, metric=metric)
                
                marginal = v_S_with_i - v_S
                
                # Calculate combinatorial weight
                weight = (math.factorial(len(S)) * math.factorial(n - len(S) - 1)) / math.factorial(n)
                shapley += weight * marginal
                
        return float(shapley)

    def get_attribution_report(self, metric: str = "mean_success_rate") -> Dict[str, Any]:
        """
        Generate a detailed attribution report for all modules.
        Includes Shapley values, standalone gains, and classified interaction types.
        """
        report = {}
        for m in self.modules:
            shapley = self.compute_shapley(m, metric=metric)
            # Standalone gain is v({m}) - v(empty)
            v_m = self._evaluate_subset({m}, metric=metric)
            v_empty = self._evaluate_subset(set(), metric=metric)
            standalone = v_m - v_empty
            
            # Classify interactions
            # strong_synergy: Shapley value is significantly higher than standalone gain
            # redundancy: Shapley value is significantly lower than standalone gain
            ratio = shapley / standalone if standalone > 0 else 1.0
            
            if ratio > 1.25:
                interaction = "strong_synergy"
            elif ratio > 1.05:
                interaction = "weak_synergy"
            elif ratio < 0.65:
                interaction = "strong_redundancy"
            elif ratio < 0.95:
                interaction = "weak_redundancy"
            else:
                interaction = "independent"
                
            report[m.value] = {
                "shapley_value": shapley,
                "standalone_gain": standalone,
                "ratio": ratio,
                "interaction_type": interaction
            }
            
        return report
