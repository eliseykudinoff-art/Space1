"""
Space1 — Autonomous AI Freelancer Agent Framework

Public API:
- GammaVeto, Rule, Action (compliance)
- MetricTracker (metrics)

Reference: DEVELOPMENT_PLAN.md
"""

__version__ = "0.1.0"

# Compliance Module (Γ - Gamma)
from .compliance.core import GammaVeto, Rule, Action

# Metrics Module (tracking)
from .metrics.tracker import MetricTracker

# Factors Module (x₁-x₁₇)
from .factors.registry import FactorRegistry, FactorID, create_mvp_registry

__all__ = [
    "GammaVeto",
    "Rule", 
    "Action",
    "MetricTracker",
    "FactorRegistry",
    "FactorID",
    "create_mvp_registry",
]