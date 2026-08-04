"""
LifeAwareOrchestrator — P0: single life motor on top of core pipeline.

- Empty queue → IDLE_TICK (never STALL for public API)
- Pipeline statuses → hormone events
- Gauges synced from agent metrics
- notify(event_id) for router / protocols / owner
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
        status = result.get("status") or ""

        if status == "STALL":
            return self.life.on_idle(self.core_agent)

        self.life.on_status(status, self.core_agent)

        trace = result.get("trace") or []
        if any("Payment risk" in str(t) for t in trace):
            self.life.emit_external("EXT.PAYMENT_OVERDUE", self.core_agent)

        snap = self.life.snapshot()
        result["homeostasis"] = snap
        result["monitor_status"] = self.life.monitor.status.value
        result["life_mode"] = snap.get("mode")
        result["revision_needed"] = snap.get("revision_needed", False)
        result["break_loop"] = snap.get("break_loop", False)

        if result.get("mission_recalibrated") and snap.get("mode") == "calm":
            result["dual_homeostat_note"] = "legacy Stage XII flag set; life mode calm"

        return result

    def notify(self, event_id: str) -> Dict[str, Any]:
        """External systems (router, protocols, owner) push events into life motor."""
        return self.life.emit_external(event_id, self.core_agent)
