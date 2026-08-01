"""
Homeostasis V2 — draft implementation (does NOT replace existing H/Λ code).

Purpose:
  External metrics → internal pressures → non-empty ActionImpulse set.
  Equilibrium is NOT sleep: baseline exploration/maintenance drives remain.

See: docs/drafts/HOMEOSTASIS_DRAFT_v1.md
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class VarKind(str, Enum):
    HIGHER_BETTER = "higher_better"
    LOWER_BETTER = "lower_better"
    BAND = "band"


class ImpulseKind(str, Enum):
    EARN = "EARN"
    BID_SAFE = "BID_SAFE"
    CUT_SPEND = "CUT_SPEND"
    SCOUT = "SCOUT"
    SCOUT_LIGHT = "SCOUT_LIGHT"
    PROPOSAL = "PROPOSAL"
    FOCUS_QUALITY = "FOCUS_QUALITY"
    CLIENT_CARE = "CLIENT_CARE"
    THROTTLE_INTAKE = "THROTTLE_INTAKE"
    FINISH_CURRENT = "FINISH_CURRENT"
    LEARN = "LEARN"
    AUDIT_RISK = "AUDIT_RISK"
    RELATE = "RELATE"
    MAINTAIN = "MAINTAIN"


@dataclass
class HomeoVariable:
    id: str
    kind: VarKind
    current: float
    target: float
    weight: float = 1.0
    lo: Optional[float] = None
    hi: Optional[float] = None

    def band(self) -> tuple[float, float]:
        if self.lo is not None and self.hi is not None:
            return self.lo, self.hi
        if self.kind == VarKind.BAND:
            return 0.7 * self.target, 1.3 * self.target
        return self.target, self.target


@dataclass
class PressureBreakdown:
    variable_id: str
    deficit: float = 0.0
    overload: float = 0.0
    baseline: float = 0.0

    @property
    def total(self) -> float:
        return max(self.deficit, self.overload, self.baseline)


@dataclass
class ActionImpulse:
    kind: ImpulseKind
    urgency: float
    reason: str
    source_variable: str

    def to_dict(self) -> dict:
        return {
            "kind": self.kind.value,
            "urgency": round(self.urgency, 4),
            "reason": self.reason,
            "source_variable": self.source_variable,
        }


@dataclass
class HomeostasisV2Config:
    """Defaults = cold-start / debug. Production should load from external file."""

    p_max: float = 3.0
    beta_explore: float = 0.12
    eps: float = 1e-6
    complacency_cap: float = 0.25
    ensure_nonempty: bool = True
    baseline_rotation: int = 0


DEFAULT_WEIGHTS = {
    "cash": 1.2,
    "runway_months": 1.4,
    "reputation": 1.0,
    "workload": 1.0,
    "pipeline": 1.1,
    "quality": 0.9,
    "skill": 0.7,
}


def default_state(
    cash: float = 3000.0,
    runway_months: float = 4.0,
    reputation: float = 4.7,
    workload: float = 3.0,
    pipeline: float = 5.0,
    quality: float = 0.85,
    skill: float = 0.75,
) -> Dict[str, HomeoVariable]:
    return {
        "cash": HomeoVariable("cash", VarKind.HIGHER_BETTER, cash, 3000.0, DEFAULT_WEIGHTS["cash"]),
        "runway_months": HomeoVariable(
            "runway_months", VarKind.HIGHER_BETTER, runway_months, 3.0, DEFAULT_WEIGHTS["runway_months"]
        ),
        "reputation": HomeoVariable(
            "reputation", VarKind.HIGHER_BETTER, reputation, 4.7, DEFAULT_WEIGHTS["reputation"]
        ),
        "workload": HomeoVariable(
            "workload", VarKind.BAND, workload, 3.0, DEFAULT_WEIGHTS["workload"], lo=2.0, hi=4.0
        ),
        "pipeline": HomeoVariable(
            "pipeline", VarKind.HIGHER_BETTER, pipeline, 4.0, DEFAULT_WEIGHTS["pipeline"]
        ),
        "quality": HomeoVariable(
            "quality", VarKind.HIGHER_BETTER, quality, 0.8, DEFAULT_WEIGHTS["quality"]
        ),
        "skill": HomeoVariable("skill", VarKind.HIGHER_BETTER, skill, 0.7, DEFAULT_WEIGHTS["skill"]),
    }


class HomeostasisV2:
    """New homeostasis: pressures + action impulses. Old HomeostaticRegulator untouched."""

    def __init__(self, config: Optional[HomeostasisV2Config] = None):
        self.cfg = config or HomeostasisV2Config()

    def pressure_for(self, v: HomeoVariable) -> PressureBreakdown:
        cfg = self.cfg
        out = PressureBreakdown(variable_id=v.id)
        eps = cfg.eps

        if v.kind == VarKind.HIGHER_BETTER:
            gap = (v.target - v.current) / max(abs(v.target), eps)
            if gap > 0:
                out.deficit = v.weight * min(cfg.p_max, gap)
            else:
                over = min(cfg.complacency_cap, (-gap) * 0.5)
                out.baseline = v.weight * cfg.beta_explore * (1.0 + over)

        elif v.kind == VarKind.LOWER_BETTER:
            gap = (v.current - v.target) / max(abs(v.target), eps)
            if gap > 0:
                out.overload = v.weight * min(cfg.p_max, gap)
            else:
                out.baseline = v.weight * cfg.beta_explore

        elif v.kind == VarKind.BAND:
            lo, hi = v.band()
            mid = 0.5 * (lo + hi)
            if v.current < lo:
                gap = (lo - v.current) / max(abs(mid), eps)
                out.deficit = v.weight * min(cfg.p_max, gap)
            elif v.current > hi:
                gap = (v.current - hi) / max(abs(mid), eps)
                out.overload = v.weight * min(cfg.p_max, gap)
            else:
                out.baseline = v.weight * cfg.beta_explore

        return out

    def compute_pressures(self, state: Dict[str, HomeoVariable]) -> Dict[str, PressureBreakdown]:
        return {vid: self.pressure_for(v) for vid, v in state.items()}

    def comfort_h(self, pressures: Dict[str, PressureBreakdown]) -> float:
        stress = sum(max(p.deficit, p.overload) for p in pressures.values())
        return 1.0 - stress / max(1.0, len(pressures))

    def propose_impulses(
        self,
        state: Dict[str, HomeoVariable],
        pressures: Optional[Dict[str, PressureBreakdown]] = None,
    ) -> List[ActionImpulse]:
        pressures = pressures or self.compute_pressures(state)
        impulses: List[ActionImpulse] = []

        def add(kind: ImpulseKind, urgency: float, reason: str, src: str):
            if urgency <= 0:
                return
            impulses.append(ActionImpulse(kind, float(urgency), reason, src))

        for vid, p in pressures.items():
            if p.deficit > 0.05:
                if vid in ("cash", "runway_months"):
                    add(ImpulseKind.EARN, p.deficit * 1.2, f"{vid} below target", vid)
                    add(ImpulseKind.BID_SAFE, p.deficit * 1.0, f"{vid} needs safe inflow", vid)
                    if p.deficit > 0.8:
                        add(ImpulseKind.CUT_SPEND, p.deficit * 0.6, "severe financial deficit", vid)
                elif vid == "pipeline":
                    add(ImpulseKind.SCOUT, p.deficit * 1.1, "pipeline thin", vid)
                    add(ImpulseKind.PROPOSAL, p.deficit * 0.9, "need proposals", vid)
                elif vid == "reputation":
                    add(ImpulseKind.CLIENT_CARE, p.deficit * 1.0, "reputation lag", vid)
                    add(ImpulseKind.FOCUS_QUALITY, p.deficit * 0.8, "protect rating", vid)
                elif vid == "quality":
                    add(ImpulseKind.FOCUS_QUALITY, p.deficit * 1.1, "quality below target", vid)
                elif vid == "skill":
                    add(ImpulseKind.LEARN, p.deficit * 1.0, "skill currency low", vid)
                elif vid == "workload":
                    add(ImpulseKind.SCOUT, p.deficit * 1.0, "workload under band", vid)
                    add(ImpulseKind.LEARN, p.deficit * 0.5, "fill idle capacity", vid)

            if p.overload > 0.05:
                if vid == "workload":
                    add(ImpulseKind.THROTTLE_INTAKE, p.overload * 1.2, "overload", vid)
                    add(ImpulseKind.FINISH_CURRENT, p.overload * 1.1, "clear queue", vid)
                else:
                    add(ImpulseKind.THROTTLE_INTAKE, p.overload * 0.5, f"{vid} overload", vid)

        strong = [i for i in impulses if i.urgency >= 0.15]
        if not strong:
            rot = self.cfg.baseline_rotation % 4
            baseline_plan = [
                (ImpulseKind.SCOUT_LIGHT, "equilibrium: keep pipeline warm"),
                (ImpulseKind.LEARN, "equilibrium: invest in skill"),
                (ImpulseKind.AUDIT_RISK, "equilibrium: review risks"),
                (ImpulseKind.RELATE, "equilibrium: client/relationship hygiene"),
            ]
            base_u = max((p.baseline for p in pressures.values()), default=self.cfg.beta_explore)
            base_u = max(base_u, self.cfg.beta_explore)
            kind, reason = baseline_plan[rot]
            add(kind, base_u, reason, "baseline")
            add(ImpulseKind.MAINTAIN, base_u * 0.7, "equilibrium: maintain systems", "baseline")

        if self.cfg.ensure_nonempty and not impulses:
            add(ImpulseKind.MAINTAIN, self.cfg.beta_explore, "fallback non-empty", "system")

        impulses.sort(key=lambda x: x.urgency, reverse=True)
        return impulses

    def step(self, state: Dict[str, HomeoVariable]) -> dict:
        pressures = self.compute_pressures(state)
        impulses = self.propose_impulses(state, pressures)
        h = self.comfort_h(pressures)
        return {
            "H_v2": round(h, 4),
            "pressures": {
                k: {
                    "deficit": round(v.deficit, 4),
                    "overload": round(v.overload, 4),
                    "baseline": round(v.baseline, 4),
                    "total": round(v.total, 4),
                }
                for k, v in pressures.items()
            },
            "impulses": [i.to_dict() for i in impulses],
            "primary": impulses[0].to_dict() if impulses else None,
            "n_impulses": len(impulses),
            "idle": False,
        }


def apply_impulse_dynamics(
    state: Dict[str, HomeoVariable],
    primary: ActionImpulse,
    dt: float = 1.0,
) -> None:
    """Toy world dynamics for simulation only."""
    k = primary.kind
    u = min(primary.urgency, 2.0) * dt

    if k in (ImpulseKind.EARN, ImpulseKind.BID_SAFE):
        state["cash"].current += 200.0 * u
        state["runway_months"].current += 0.15 * u
        state["workload"].current += 0.2 * u
        state["pipeline"].current = max(0.0, state["pipeline"].current - 0.3 * u)
    elif k in (ImpulseKind.SCOUT, ImpulseKind.SCOUT_LIGHT, ImpulseKind.PROPOSAL):
        state["pipeline"].current += 0.5 * u
        state["skill"].current = min(1.0, state["skill"].current + 0.01 * u)
    elif k == ImpulseKind.LEARN:
        state["skill"].current = min(1.0, state["skill"].current + 0.04 * u)
    elif k == ImpulseKind.FOCUS_QUALITY:
        state["quality"].current = min(1.0, state["quality"].current + 0.03 * u)
        state["reputation"].current = min(5.0, state["reputation"].current + 0.02 * u)
    elif k == ImpulseKind.CLIENT_CARE:
        state["reputation"].current = min(5.0, state["reputation"].current + 0.03 * u)
    elif k == ImpulseKind.THROTTLE_INTAKE:
        state["workload"].current = max(0.0, state["workload"].current - 0.4 * u)
    elif k == ImpulseKind.FINISH_CURRENT:
        state["workload"].current = max(0.0, state["workload"].current - 0.5 * u)
        state["quality"].current = min(1.0, state["quality"].current + 0.01 * u)
    elif k == ImpulseKind.CUT_SPEND:
        state["runway_months"].current += 0.1 * u
    elif k in (ImpulseKind.AUDIT_RISK, ImpulseKind.RELATE, ImpulseKind.MAINTAIN):
        state["skill"].current = min(1.0, state["skill"].current + 0.005 * u)
        state["pipeline"].current += 0.05 * u

    state["cash"].current = max(0.0, state["cash"].current - 15.0 * dt)
    state["runway_months"].current = max(0.0, state["runway_months"].current - 0.02 * dt)
    state["pipeline"].current = max(0.0, state["pipeline"].current - 0.05 * dt)
    state["skill"].current = max(0.0, state["skill"].current - 0.002 * dt)
