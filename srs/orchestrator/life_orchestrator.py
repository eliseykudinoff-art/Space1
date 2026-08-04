"""
LifeAwareOrchestrator — autonomy via life motor + optional inbound work units.

Primary: homeostasis on idle → seek work (revision_needed).
Secondary: inbound task perturbs hormones and may enter the queue.
Utility U exists only in decision/phi layer — motor uses `urge`, never U.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from ..compliance.core import GammaVeto
from ..models.agents import Agent
from ..monitoring.monitor import OperationalStatus
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
        self._legacy_calc_H = self.homeo.calculate_homeostasis
        self.homeo.calculate_homeostasis = self._life_calculate_homeostasis  # type: ignore

    def _life_calculate_homeostasis(self, metrics: Dict[str, float]):
        """Wellbeing H for Stage V thresholds — not utility U."""
        self.life.sync_from_agent(self.core_agent)
        snap = self.life.homeostasis.step()
        S = float(getattr(snap, "S", 0.1))
        urge = float(getattr(snap, "urge", S))
        stress = max(0.0, min(1.0, S))
        H = max(0.0, min(1.2, 1.0 - 0.7 * stress - 0.3 * max(0.0, min(1.0, urge))))
        return H, stress

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
