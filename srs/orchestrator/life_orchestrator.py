"""
LifeAwareOrchestrator — single HomeostasisService for life + Stage II/XII facade.

No seek_job. No second homeostat math.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from ..compliance.core import GammaVeto
from ..models.agents import Agent
from ..monitoring.monitor import OperationalStatus
from ..utility.control import HomeostaticRegulator
from .core import Orchestrator as _BaseOrchestrator
from .life_support import LifeSupport


def _accent_mission(profile: str, life_mode: Optional[str]) -> str:
    if profile and profile != "BALANCED":
        return profile
    if life_mode == "urgent":
        return "SURVIVAL"
    if life_mode == "prospective":
        return "GROWTH"
    return profile or "BALANCED"


class Orchestrator(_BaseOrchestrator):
    def __init__(self, core_agent: Agent, veto: Optional[GammaVeto] = None):
        super().__init__(core_agent, veto)
        self.life = LifeSupport()
        self.homeo = HomeostaticRegulator(service=self.life.homeostasis)

    def dispatch_full_cycle(self, mission_profile: str = "BALANCED") -> Dict[str, Any]:
        if not self.scheduler.list_queue():
            return self.life.on_idle(self.core_agent)

        self.life.monitor.set_status(OperationalStatus.ACTIVE)
        self.life.sync_from_agent(self.core_agent)
        pre = self.life.homeostasis.step()
        pre_mode = getattr(pre, "mode", None)
        profile = _accent_mission(mission_profile, pre_mode)

        result = super().dispatch_full_cycle(profile)
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
        result["mission_profile_used"] = profile
        result["revision_needed"] = snap.get("revision_needed", False)
        result["break_loop"] = snap.get("break_loop", False)
        result["pre_llm"] = {
            "life_mode_before": pre_mode,
            "mission_profile_used": profile,
            "H_source": "life",
        }
        return result

    def notify(self, event_id: str) -> Dict[str, Any]:
        return self.life.emit_external(event_id, self.core_agent)
