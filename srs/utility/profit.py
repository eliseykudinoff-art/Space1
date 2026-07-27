"""
Profit Module — Risk-Adjusted Profit (Φ)

G7: Risk-adjusted Φ
    Φ_adj = Φ × (1 - Ψ/P)
    
Where:
    Φ = (R - C) / T  — base profit
    Ψ = risk pressure [0, 1]
    P = risk tolerance parameter (default: 1.0)

Reference: DEVELOPMENT_PLAN.md - G7
           MATHEMATICAL_FORMULAS.md - Risk-adjusted profit
"""

from dataclasses import dataclass
from typing import Any, Optional

from space1.config.loader import get_config
from space1.cost.token_tracker import TokenCostTracker
from space1.utility import compute_phi, compute_psi, _clamp


@dataclass
class ProfitComponents:
    """Components of risk-adjusted profit calculation."""
    base_phi: float
    risk_psi: float
    risk_tolerance: float
    adjustment_factor: float
    phi_adjusted: float
    
    def to_dict(self) -> dict:
        return {
            "base_phi": self.base_phi,
            "risk_psi": self.risk_psi,
            "risk_tolerance": self.risk_tolerance,
            "adjustment_factor": self.adjustment_factor,
            "phi_adjusted": self.phi_adjusted,
        }


class RiskAdjustedProfit:
    """
    Risk-Adjusted Profit calculator.
    
    Formula:
        Φ_adj = Φ × ρ_risk
        
    Where:
        Φ = base profit rate
        ρ_risk = ∏ (1 - P_k * w_k) across risk dimensions
    """
    
    def __init__(self, risk_tolerance: float = 1.0):
        """
        Args:
            risk_tolerance: Maximum acceptable risk (default: 1.0)
        """
        self.risk_tolerance = risk_tolerance
    
    def calculate(
        self,
        task: Any = None,
        agent: Any = None,
        agent_context: Any = None,
        token_tracker: Optional[TokenCostTracker] = None,
        **kwargs
    ) -> ProfitComponents:
        """
        Calculate risk-adjusted profit.
        
        Args:
            task: Task object
            agent: Agent object
            agent_context: AgentContext for risk calculation
            token_tracker: Optional TokenCostTracker
            **kwargs: Additional arguments for compute_phi
            
        Returns:
            ProfitComponents with all calculation details
        """
        # Base profit
        base_phi = compute_phi(task, agent, token_tracker=token_tracker, **kwargs)
        
        # Risk pressure & multiplicative ρ_risk
        if task is not None and agent_context is not None:
            ctx_agent = getattr(agent_context, "agent", agent_context)
            metrics = getattr(ctx_agent, "metrics", None)
            capabilities = getattr(ctx_agent, "capabilities", None)
            metadata = getattr(agent_context, "metadata", {}) if agent_context is not None else {}
            task_metadata = getattr(task, "metadata", {}) if task is not None else {}

            uncertainty = max(0.0, min(1.0, task_metadata.get("uncertainty", metadata.get("uncertainty", 0.5))))
            fatigue = max(0.0, min(1.0, (getattr(metrics, "n_active_tasks", 0.0) if hasattr(metrics, "n_active_tasks") else getattr(metrics, "active_tasks", 0.0)) / 10.0))
            novelty = max(0.0, min(1.0, task_metadata.get("novelty", metadata.get("novelty", 0.5))))
            deadline = max(0.0, min(1.0, getattr(task, "urgency_score", 0.5)))
            skill = max(0.0, min(1.0, 1.0 - getattr(capabilities, "llm_quality", 0.7)))
            
            alpha_u = 0.2
            alpha_f = 0.2
            alpha_n = 0.2
            alpha_d = 0.2
            alpha_s = 0.5
            
            rho_risk = (
                (1.0 - uncertainty * alpha_u)
                * (1.0 - fatigue * alpha_f)
                * (1.0 - novelty * alpha_n)
                * (1.0 - deadline * alpha_d)
                * (1.0 - skill * alpha_s)
            )
            
            adjustment = max(0.0, min(1.0, rho_risk))
            psi = compute_psi(task, agent_context)
        else:
            psi = compute_psi(task, agent_context) if agent_context else 0.0
            adjustment = max(0.0, 1.0 - (psi / max(self.risk_tolerance, 1e-9)))
            
        phi_adjusted = base_phi * adjustment
        
        return ProfitComponents(
            base_phi=base_phi,
            risk_psi=psi,
            risk_tolerance=self.risk_tolerance,
            adjustment_factor=adjustment,
            phi_adjusted=phi_adjusted,
        )
    
    def calculate_from_components(
        self,
        base_phi: float,
        psi: float,
    ) -> ProfitComponents:
        """
        Calculate risk-adjusted profit from pre-computed components.
        
        Args:
            base_phi: Base profit rate
            psi: Risk pressure [0, 1]
            
        Returns:
            ProfitComponents
        """
        adjustment = 1.0 - (psi / max(self.risk_tolerance, 1e-9))
        phi_adjusted = base_phi * adjustment
        
        return ProfitComponents(
            base_phi=base_phi,
            risk_psi=psi,
            risk_tolerance=self.risk_tolerance,
            adjustment_factor=adjustment,
            phi_adjusted=phi_adjusted,
        )


def compute_phi_risk_adjusted(
    task: Any = None,
    agent: Any = None,
    agent_context: Any = None,
    token_tracker: Optional[TokenCostTracker] = None,
    risk_tolerance: float = 1.0,
    **kwargs
) -> float:
    """
    Convenience function: compute risk-adjusted Φ in one call.
    
    Args:
        task: Task object
        agent: Agent object  
        agent_context: AgentContext for risk calculation
        token_tracker: Optional TokenCostTracker
        risk_tolerance: Maximum acceptable risk
        **kwargs: Additional arguments for compute_phi (revenue, cost, time_hours)
        
    Returns:
        Risk-adjusted profit rate
    """
    calculator = RiskAdjustedProfit(risk_tolerance=risk_tolerance)
    
    # Extract compute_phi kwargs
    phi_kwargs = {}
    for key in ["revenue", "cost", "time_hours"]:
        if key in kwargs:
            phi_kwargs[key] = kwargs.pop(key)
    
    result = calculator.calculate(task, agent, agent_context, token_tracker, **phi_kwargs)
    return result.phi_adjusted
