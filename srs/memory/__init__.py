"""
Memory and State exports — CoALA Four-Level Architecture.

Per 05_MEMORY_AND_STATE.md:
- Working Memory: OperationalMemory (current context)
- Episodic Memory: EpisodicMemory (past events with priority formula)
- Semantic Memory: SemanticMemory (facts with asymmetric update)
- Procedural Memory: ProceduralMemory / Skill Library

Reference: 05_MEMORY_AND_STATE.md
"""

from .core import (
    # Core classes
    OperationalMemory,  # Working Memory
    EpisodicMemory,     # Episodic Memory
    SemanticMemory,      # Semantic Memory
    ProceduralMemory,   # Procedural Memory / Skill Library
    ConsolidationGate,  # Episodic → Semantic bridge
    # Data classes
    Episode,           # Episodic memory entry
    SemanticFact,      # Semantic memory fact
    Skill,             # Procedural skill
    # Legacy aliases (deprecated, will be removed in v0.2)
    StrategicExperience,  # = Episode
    MetaRule,           # Legacy semantic rule
    StrategicMemory,     # = EpisodicMemory (alias)
    MetaMemory,          # Legacy combined semantic+procedural
    WorkingMemory,
    ProceduralMemory_Legacy,
)
from .transfer import TransferLearning
from .storage import AIOSStorageManager

__all__ = [
    # Core CoALA classes
    "OperationalMemory",
    "EpisodicMemory",
    "SemanticMemory",
    "ProceduralMemory",
    "ConsolidationGate",
    # Data classes
    "Episode",
    "SemanticFact",
    "Skill",
    # Legacy aliases (deprecated)
    "StrategicExperience",
    "MetaRule",
    "StrategicMemory",
    "MetaMemory",
    "WorkingMemory",
    "ProceduralMemory_Legacy",
    # Other
    "TransferLearning",
    "AIOSStorageManager",
]
