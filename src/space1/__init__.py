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

__all__ = [
    "GammaVeto",
    "Rule", 
    "Action",
    "MetricTracker",
]