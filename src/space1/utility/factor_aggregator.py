"""
Factor Aggregator — Unified Factor Calculator

G9: Factor calculator/aggregator for x₁, x₈, x₁₂, x₁₆

Aggregates all MVP factors into a single composite score,
avoiding hardcoded weights in callers.

Reference: DEVELOPMENT_PLAN.md - G9
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from space1.config.loader import get_config
from space1.factors.registry import FactorRegistry, FactorResult, create_mvp_registry
from space1.metrics.tracker import MetricRegistry
from space1.utility import build_factor_context, _clamp


@dataclass
class FactorAggregation:
    """Result of factor aggregation."""
    omega: float          # Evolution composite score [0, 1]
    delta_success: float  # Total success delta
    delta_time: float     # Total time delta
    individual: Dict[str, FactorResult] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "omega": self.omega,
            "delta_success": self.delta_success,
            "delta_time": self.delta_time,
            "individual": {k: {
                "factor_id": v.factor_id,
                "value": v.value,
                "delta_success": v.delta_success,
                "delta_time": v.delta_time,
            } for k, v in self.individual.items()},
        }


class FactorCalculator:
    """
    Unified Factor Calculator — aggregates all MVP factors.
    
    Avoids duplicating factor weights in callers by centralizing
    the aggregation logic here.
    
    Usage:
        calculator = FactorCalculator()
        result = calculator.calculate(task, agent_context, action)
        
        # result.omega — composite evolution score
        # result.delta_success — total success delta
        # result.individual — per-factor results
    """
    
    def __init__(self, registry: Optional[FactorRegistry] = None):
        self._registry = registry or create_mvp_registry()
    
    def calculate(
        self,
        task: Any = None,
        agent_context: Any = None,
        action: Any = None,
    ) -> FactorAggregation:
        """
        Calculate factor aggregation.
        
        Args:
            task: Task object
            agent_context: AgentContext
            action: Action being evaluated
            
        Returns:
            FactorAggregation with composite scores
        """
        context = build_factor_context(task, agent_context, action)
        results = self._registry.compute_all(context)
        
        delta_success = sum(r.delta_success for r in results.values())
        delta_time = sum(r.delta_time for r in results.values())
        
        # Omega: normalized average factor value
        if results:
            omega = _clamp(sum(r.value for r in results.values()) / len(results))
        else:
            omega = 0.0
        
        return FactorAggregation(
            omega=omega,
            delta_success=delta_success,
            delta_time=delta_time,
            individual=results,
        )
    
    def calculate_with_custom_context(
        self,
        context: Dict[str, Any],
    ) -> FactorAggregation:
        """
        Calculate factor aggregation from pre-built context.
        
        Args:
            context: Pre-built factor context dict
            
        Returns:
            FactorAggregation
        """
        results = self._registry.compute_all(context)
        
        delta_success = sum(r.delta_success for r in results.values())
        delta_time = sum(r.delta_time for r in results.values())
        
        if results:
            omega = _clamp(sum(r.value for r in results.values()) / len(results))
        else:
            omega = 0.0
        
        return FactorAggregation(
            omega=omega,
            delta_success=delta_success,
            delta_time=delta_time,
            individual=results,
        )
    
    def track_factors(
        self,
        aggregation: FactorAggregation,
        metrics: MetricRegistry,
    ) -> None:
        """
        Track factor metrics through MetricRegistry.
        
        Args:
            aggregation: FactorAggregation result
            metrics: MetricRegistry to track to
        """
        metrics.track("omega", aggregation.omega, category="operational")
        metrics.track("delta_success", aggregation.delta_success, category="operational")
        metrics.track("delta_time", aggregation.delta_time, category="operational")
        
        for factor_id, result in aggregation.individual.items():
            metrics.track(f"factor_{factor_id}", result.value, category="operational")
    
    def get_registry(self) -> FactorRegistry:
        """Get underlying FactorRegistry."""
        return self._registry
