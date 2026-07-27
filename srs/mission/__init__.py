"""
Mission Module — Mission → Compliance → Utility → Execution Pipeline

Per 02_MATHEMATICAL_CORE.md §IV.12:
- MissionPolicy.calibrate() with 6 mission types
- State modifiers, gamma rules, thresholds
- PolicyParams with calibrated weights

Reference: 02_MATHEMATICAL_CORE.md §IV.12
"""

from .core import (
    # Mission types
    MissionType,
    # Core classes
    Mission,
    PolicyParams,
    StateModifier,
    # Legacy/Pipeline
    ExecutionContext,
    MissionProcessor,
    PipelineStage,
    BaseStage,
    MissionStage,
    ComplianceStage,
    UtilityStage,
    ExecutionStage,
    create_mission,
    # Constants
    MISSION_CALIBRATION,
)

__all__ = [
    # Mission types
    "MissionType",
    # Core classes
    "Mission",
    "PolicyParams",
    "StateModifier",
    # Legacy/Pipeline
    "ExecutionContext",
    "MissionProcessor",
    "PipelineStage",
    "BaseStage",
    "MissionStage",
    "ComplianceStage",
    "UtilityStage",
    "ExecutionStage",
    "create_mission",
    # Constants
    "MISSION_CALIBRATION",
]