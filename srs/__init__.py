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
from .compliance.core import GammaVeto, Rule, Action, MaxCostRule, BlockedActionsRule
from .compliance.security import AIOSAccessManager

# Metrics Module (tracking)
from .metrics.tracker import MetricTracker

# Factors Module (x₁-x₁₇)
from .factors.registry import FactorRegistry, FactorID

# Utility Module (Φ, Ψ, Υ, Q, Ω)
from .utility import (
    compute_phi,
    compute_psi,
    compute_quality,
    update_upsilon,
    rank_actions,
    score_action,
    Decision,
)

# Control Module (PID, Homeostasis)
from .utility.control import PIDController, HomeostaticRegulator

# Profit Module (Risk-adjusted Φ)
from .utility.profit import compute_phi_risk_adjusted

from .utility.reputation import SoftCappedReputation

# Reputation Module (Soft-capped Υ)




# Composite Module (Ξ coefficients, Φ_R)




# Factor Aggregator


# Memory Module (Phase 3 G21)
from .memory import (
    StrategicExperience,
    MetaRule,
    OperationalMemory,
    StrategicMemory,
    MetaMemory,
    ConsolidationGate,
    TransferLearning,
    AIOSStorageManager,
)

# Triggers Module (Phase 3 G12)
from .triggers import TriggerSystem

# Orchestrator Module (Phase 4 G2, G10, G19)
from .orchestrator import (
    OrchestratorContext,
    SignalToContextSynthesizer,
    HomeostaticUtilityModulator,
    WeightCalibrator,
    Orchestrator,
    AIOSScheduler,
    AIOSContextManager,
    AIOSToolManager,
)

# Specialized Agents Module (Phase 5 G13)
from .agents import (
    BaseSpecialistAgent,
    ScoutAgent,
    WorkerAgent,
    FinanceAgent,
    UnifiedCognitiveAgent,
)

# Environment Module (Phase 5 G3)




# Parameter Calibration Module (Phase 6 G17)


__all__ = [
    # Compliance
    "GammaVeto",
    "Rule",
    "Action",
    "MaxCostRule",
    "AIOSAccessManager",
    # Metrics
    "MetricTracker",
    # Factors
    "FactorRegistry",
    "FactorID",
    # Utility Core
    "compute_phi",
    "compute_psi",
    "compute_quality",
    "update_upsilon",
    "rank_actions",
    "score_action",
    "Decision",
    # Control
    "PIDController",
    "HomeostaticRegulator",
    # Profit
    "compute_phi_risk_adjusted",
    # Reputation
    # Composite
    # Factors
    # Memory
    "StrategicExperience",
    "MetaRule",
    "OperationalMemory",
    "StrategicMemory",
    "MetaMemory",
    "ConsolidationGate",
    "TransferLearning",
    "AIOSStorageManager",
    "ParameterCalibrator",
    # Triggers
    "TriggerSystem",
    # Orchestrator
    "OrchestratorContext",
    "SignalToContextSynthesizer",
    "HomeostaticUtilityModulator",
    "WeightCalibrator",
    "Orchestrator",
    "AIOSScheduler",
    "AIOSContextManager",
    "AIOSToolManager",
    # Specialized Agents
    "BaseSpecialistAgent",
    "ScoutAgent",
    "WorkerAgent",
    "FinanceAgent",
    "UnifiedCognitiveAgent",
    # Environment
    # Calibration
]



from .utility.calibration import ParameterCalibrator

# Phase 3 subsystems
from space1.verifier import Verifier, Verdict, CriticType
from space1.client_psychometrics import compute_ccrs, risk_premium, ClientRiskProfile, RiskZone
from space1.cold_start import ColdStartState, initialize_agent_state, get_ensemble_weights
from space1.market_protocols import ProtocolRegistry, ProtocolState, ProtocolOutcome
