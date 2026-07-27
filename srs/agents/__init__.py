"""
Specialized Specialist Agent and Single-Brain exports.

Per 04_ARCHITECTURE.md §V and 03_PIPELINE_MATH.md §VII.1:
- Role-based multi-agent is REJECTED
- Sub-agent = manifest (name, tool allowlist, action type)
- Single-level hierarchy
- Manifest pattern

Reference: 04_ARCHITECTURE.md §V, 03_PIPELINE_MATH.md §VII.1
"""

from .core import (
    # New canonical exports
    SubAgentManifest,
    SubAgentRegistry,
    UnifiedCognitiveAgent,
    create_sub_agent_registry,
    # Legacy (for backward compatibility)
    BaseSpecialistAgent,
    ScoutAgent,
    WorkerAgent,
    FinanceAgent,
)

__all__ = [
    # New canonical exports
    "SubAgentManifest",
    "SubAgentRegistry",
    "UnifiedCognitiveAgent",
    "create_sub_agent_registry",
    # Legacy
    "BaseSpecialistAgent",
    "ScoutAgent",
    "WorkerAgent",
    "FinanceAgent",
]
