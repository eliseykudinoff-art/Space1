"""
Space1 — Autonomous AI Freelancer Agent Framework

Public API:
- GammaVeto, Rule, Action (compliance)
- MetricTracker (metrics)
- compute_phi (utility)

Reference: DEVELOPMENT_PLAN.md
"""

__version__ = "0.1.0"

# Compliance Module (Γ - Gamma)
from .compliance.core import GammaVeto, Rule, Action

# Metrics Module (tracking)
from .metrics.tracker import MetricTracker

# Factors Module (x₁-x₁₇)
from .factors.registry import FactorRegistry, FactorID, create_mvp_registry

# Utility Module (Φ, Ψ, Υ, Q, Ω)
from .utility import (
    compute_phi,
    compute_psi,
    compute_quality,
    update_upsilon,
    rank_actions,
    score_action,
)

# Control Module (PID, Homeostasis)
from .utility.control import PIDController, HomeostaticRegulator

# Profit Module (Risk-adjusted Φ)
from .utility.profit import RiskAdjustedProfit, compute_phi_risk_adjusted

# Reputation Module (Soft-capped Υ)
from .utility.reputation import SoftCappedReputation

# Composite Module (Ξ coefficients, Φ_R)
from .utility.composite import XiCoefficients, PhiRCalculator

# Factor Aggregator
from .utility.factor_aggregator import FactorCalculator

__all__ = [
    # Compliance
    "GammaVeto",
    "Rule",
    "Action",
    # Metrics
    "MetricTracker",
    # Factors
    "FactorRegistry",
    "FactorID",
    "create_mvp_registry",
    # Utility Core
    "compute_phi",
    "compute_psi",
    "compute_quality",
    "update_upsilon",
    "rank_actions",
    "score_action",
    # Control
    "PIDController",
    "HomeostaticRegulator",
    # Profit
    "RiskAdjustedProfit",
    "compute_phi_risk_adjusted",
    # Reputation
    "SoftCappedReputation",
    # Composite
    "XiCoefficients",
    "PhiRCalculator",
    # Factors
    "FactorCalculator",
]
