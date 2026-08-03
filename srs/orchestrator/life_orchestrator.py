"""LifeAwareOrchestrator — P0 IDLE_TICK + homeostasis hooks."""
from __future__ import annotations
from typing import Any, Dict, Optional
from ..compliance.core import GammaVeto
from ..models.agents import Agent
from .core import Orchestrator as _BaseOrchestrator
from .life_support import LifeSupport

class Orchestrator(_BaseOrchestrator):
    def __init__(self, core_agent: Agent, veto: Optional[GammaVeto] = None):
        super().__init__(core_agent, veto)
        self.life = LifeSupport()

    def dispatch_full_cycle(self, mission_profile: str = "BALANCED") -> Dict[str, Any]:
        if not self.scheduler.list_queue():
            return self.life.on_idle(self.core_agent)
        result = super().dispatch_full_cycle(mission_profile)
        status = result.get("status")
        if status == "SUCCESS":
            self.life.emit("EXEC.TASK_DONE")
            self.life.sync_from_agent(self.core_agent)
            result["homeostasis"] = self.life.snapshot()
        elif status == "REJECTED_BY_COMPLIANCE":
            self.life.emit("EXT.COMPLIANCE_HIT")
            result["homeostasis"] = self.life.snapshot()
        elif status == "FAILED_QUALITY_GOAL":
            self.life.emit("EXEC.VERIFIER_FAIL")
            result["homeostasis"] = self.life.snapshot()
        return result
