"""
LifeAwareOrchestrator — P0 integration (clean2).

Empty queue → IDLE_TICK (homeostasis + monitor).
Pipeline outcomes → hormone events.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from ..compliance.core import GammaVeto
from ..models.agents import Agent
from ..monitoring.monitor import OperationalStatus
from .core import Orchestrator as _BaseOrchestrator
from .life_support import LifeSupport


class Orchestrator(_BaseOrchestrator):
    """Drop-in replacement: core pipeline + life support."""

    def __init__(self, core_agent: Agent, veto: Optional[GammaVeto] = None):
        super().__init__(core_agent, veto)
        self.life = LifeSupport()

    def dispatch_full_cycle(self, mission_profile: str = "BALANCED") -> Dict[str, Any]:
        if not self.scheduler.list_queue():
            return self.life.on_idle(self.core_agent)

        self.life.monitor.set_status(OperationalStatus.ACTIVE)
        result = super().dispatch_full_cycle(mission_profile)
        status = result.get("status")

        if status == "SUCCESS":
            self.life.emit("EXEC.TASK_DONE")
            self.life.sync_from_agent(self.core_agent)
        elif status == "REJECTED_BY_COMPLIANCE":
            self.life.emit("EXT.COMPLIANCE_HIT")
        elif status == "FAILED_QUALITY_GOAL":
            self.life.emit("EXEC.VERIFIER_FAIL")
        elif status == "DECLINED_BY_DECISION_RULE":
            self.life.emit("EXT.ORDER_REJECTED")
        elif status == "CLARIFY_REQUIRED":
            self.life.emit("MEMORY.GAP")

        result["homeostasis"] = self.life.snapshot()
        result["monitor_status"] = self.life.monitor.status.value
        return result
