"""
Composite Module — Ξ Coefficients & Φ_R Consistency

G17: Ξ coefficients
    Ξ = α·Q - β·(O_time + O_cost)
    
G18: Φ_R consistency
    Φ_R = Φ × Γ × (1 + α_rep·Υ) - λ_Ψ × Ψ

Reference: DEVELOPMENT_PLAN.md - G17, G18
           MATHEMATICAL_WORKSPACE.md
"""

from dataclasses import dataclass
from typing import Any, Optional

from space1.config.loader import get_config
from space1.utility import compute_phi, compute_psi, _clamp


@dataclass
class XiComponents:
    """Components of Ξ calculation."""
    quality_score: float
    opportunity_cost: float
    xi_value: float
    alpha: float
    beta: float
    
    def to_dict(self) -> dict:
        return {
            "quality_score": self.quality_score,
            "opportunity_cost": self.opportunity_cost,
            "xi_value": self.xi_value,
            "alpha": self.alpha,
            "beta": self.beta,
        }


@dataclass 
class PhiRComponents:
    """Components of Φ_R calculation."""
    base_phi: float
    gamma_compliance: float
    upsilon_reputation: float
    psi_risk: float
    phi_r: float
    alpha_rep: float
    lambda_psi: float
    
    def to_dict(self) -> dict:
        return {
            "base_phi": self.base_phi,
            "gamma_compliance": self.gamma_compliance,
            "upsilon_reputation": self.upsilon_reputation,
            "psi_risk": self.psi_risk,
            "phi_r": self.phi_r,
            "alpha_rep": self.alpha_rep,
            "lambda_psi": self.lambda_psi,
        }


class XiCoefficients:
    """
    Ξ Coefficients — оценка эффективности с учётом качества и возможностей.
    
    Formula:
        Ξ = α·Q - β·(O_time + O_cost)
        
    Where:
        Q = quality score [0, 1]
        O_time = time opportunity cost
        O_cost = cost opportunity cost
        α = quality weight (default: 0.7)
        β = opportunity weight (default: 0.3)
        
    Higher Ξ means better quality-to-opportunity ratio.
    """
    
    def __init__(self, alpha: Optional[float] = None, beta: Optional[float] = None):
        cfg = get_config().constants
        self.alpha = alpha if alpha is not None else cfg.xi_alpha
        self.beta = beta if beta is not None else cfg.xi_beta
    
    def calculate(
        self,
        quality_score: float,
        opportunity_time: float = 0.0,
        opportunity_cost: float = 0.0,
    ) -> XiComponents:
        """
        Calculate Ξ coefficient.
        
        Args:
            quality_score: Quality score [0, 1]
            opportunity_time: Time opportunity cost [0, 1]
            opportunity_cost: Cost opportunity cost [0, 1]
            
        Returns:
            XiComponents with calculation details
        """
        q = _clamp(quality_score)
        o_time = _clamp(opportunity_time)
        o_cost = _clamp(opportunity_cost)
        
        total_opportunity = o_time + o_cost
        
        xi = self.alpha * q - self.beta * total_opportunity
        
        return XiComponents(
            quality_score=q,
            opportunity_cost=total_opportunity,
            xi_value=xi,
            alpha=self.alpha,
            beta=self.beta,
        )
    
    def calculate_from_task(
        self,
        task: Any,
        quality: float,
        alternative_tasks: Optional[list] = None,
    ) -> XiComponents:
        """
        Calculate Ξ from task context.
        
        Args:
            task: Task object
            quality: Computed quality score
            alternative_tasks: List of alternative tasks for opportunity cost
            
        Returns:
            XiComponents
        """
        # Time opportunity: fraction of available time consumed
        est_hours = getattr(task, "estimated_hours", 1.0)
        o_time = _clamp(est_hours / 24.0)  # Normalize to day
        
        # Cost opportunity: fraction of budget consumed
        cost = getattr(task, "metadata", {}).get("cost", 0.0)
        budget = getattr(task, "metadata", {}).get("budget", 100.0)
        o_cost = _clamp(cost / max(budget, 1e-9))
        
        return self.calculate(quality, o_time, o_cost)


class PhiRCalculator:
    """
    Φ_R Consistency — согласованная прибыль с учётом комплаенса и репутации.
    
    Formula:
        Φ_R = Φ × Γ × (1 + α_rep·Υ) - λ_Ψ × Ψ
        
    Where:
        Φ = base profit
        Γ = compliance score [0, 1]
        Υ = reputation score [0, 1]
        Ψ = risk pressure [0, 1]
        α_rep = reputation amplification (default: 0.3)
        λ_Ψ = risk penalty weight (default: 0.5)
        
    Φ_R rewards compliant, reputable actions and penalizes risky ones.
    """
    
    def __init__(
        self,
        alpha_rep: Optional[float] = None,
        lambda_psi: Optional[float] = None,
    ):
        cfg = get_config().constants
        self.alpha_rep = alpha_rep if alpha_rep is not None else cfg.phi_r_alpha_rep
        self.lambda_psi = lambda_psi if lambda_psi is not None else cfg.phi_r_lambda_psi
    
    def calculate(
        self,
        phi: float,
        gamma: float = 1.0,
        upsilon: float = 0.0,
        psi: float = 0.0,
    ) -> PhiRComponents:
        """
        Calculate Φ_R consistency score.
        
        Args:
            phi: Base profit rate
            gamma: Compliance score [0, 1] (1 = fully compliant)
            upsilon: Reputation score [0, 1]
            psi: Risk pressure [0, 1]
            
        Returns:
            PhiRComponents with calculation details
        """
        g = _clamp(gamma)
        u = _clamp(upsilon)
        p = _clamp(psi)
        
        # Reputation multiplier: (1 + α_rep·Υ)
        rep_multiplier = 1.0 + self.alpha_rep * u
        
        # Risk penalty: λ_Ψ × Ψ
        risk_penalty = self.lambda_psi * p
        
        # Φ_R = Φ × Γ × (1 + α_rep·Υ) - λ_Ψ × Ψ
        phi_r = phi * g * rep_multiplier - risk_penalty
        
        return PhiRComponents(
            base_phi=phi,
            gamma_compliance=g,
            upsilon_reputation=u,
            psi_risk=p,
            phi_r=phi_r,
            alpha_rep=self.alpha_rep,
            lambda_psi=self.lambda_psi,
        )
    
    def calculate_from_context(
        self,
        task: Any,
        agent_context: Any,
        phi: Optional[float] = None,
        compliance_passed: bool = True,
        upsilon: Optional[float] = None,
    ) -> PhiRComponents:
        """
        Calculate Φ_R from task and agent context.
        
        Args:
            task: Task object
            agent_context: AgentContext
            phi: Pre-computed phi (optional)
            compliance_passed: Whether compliance check passed
            upsilon: Pre-computed upsilon (optional)
            
        Returns:
            PhiRComponents
        """
        if phi is None:
            agent = getattr(agent_context, "agent", None)
            phi = compute_phi(task, agent)
        
        gamma = 1.0 if compliance_passed else 0.0
        
        if upsilon is None:
            agent = getattr(agent_context, "agent", None)
            metrics = getattr(agent, "metrics", None)
            upsilon = getattr(metrics, "rating", 0.0) / 5.0  # Normalize to [0, 1]
        
        psi = compute_psi(task, agent_context)
        
        return self.calculate(phi, gamma, upsilon, psi)
