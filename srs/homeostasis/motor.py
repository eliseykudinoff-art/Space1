"""Homeostasis motor: drive, urgency, modes."""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Optional
from .config import HomeostasisConfig


@dataclass
class Axes:
    resource: float = 0.0
    progress: float = 0.0
    compliance: float = 0.0
    knowledge: float = 0.0


@dataclass
class MotorSnapshot:
    S: float = 0.0
    G: float = 0.0
    D: float = 0.0
    S_def: float = 0.0
    U_urge: float = 0.0
    L: float = 0.0
    rho: float = 1.0
    tau_idle: float = 0.0
    revision_needed: bool = False
    break_loop: bool = False
    mode: str = "calm"
    m_urgent: float = 0.0
    m_prospect: float = 0.0
    n_deferred: int = 0

    def to_dict(self) -> dict:
        return {
            "S": round(self.S, 6),
            "G": round(self.G, 6),
            "D": round(self.D, 6),
            "S_def": round(self.S_def, 6),
            "U_urge": round(self.U_urge, 6),
            "L": round(self.L, 6),
            "rho": round(self.rho, 6),
            "tau_idle": round(self.tau_idle, 6),
            "revision_needed": self.revision_needed,
            "break_loop": self.break_loop,
            "mode": self.mode,
            "m_urgent": round(self.m_urgent, 4),
            "m_prospect": round(self.m_prospect, 4),
            "n_deferred": self.n_deferred,
        }


class HomeostasisMotor:
    def __init__(self, cfg: Optional[HomeostasisConfig] = None):
        self.cfg = cfg or HomeostasisConfig()
        self.axes = Axes()
        self._slow_tick = 0
        self.L = 0.0
        self.rho = 1.0

    def update_axes(self, **kwargs: float) -> None:
        for k, v in kwargs.items():
            if hasattr(self.axes, k):
                setattr(self.axes, k, max(0.0, min(1.0, float(v))))

    def drive(self, tau_idle: float) -> float:
        a = self.axes
        w = self.cfg.w_axes if hasattr(self.cfg, "w_axes") else {
            "resource": 0.35, "progress": 0.25, "compliance": 0.25, "knowledge": 0.15
        }
        D = (
            w.get("resource", 0.35) * a.resource
            + w.get("progress", 0.25) * a.progress
            + w.get("compliance", 0.25) * a.compliance
            + w.get("knowledge", 0.15) * a.knowledge
        )
        return max(0.0, min(1.0, D))

    def note_failure(self, amount: float = 0.5) -> None:
        self.axes.progress = min(1.0, self.axes.progress + 0.1 * amount)

    def should_run_slow(self, force: bool = False) -> bool:
        self._slow_tick += 1
        return force or (self._slow_tick % 5 == 0)

    def update_slow(self, S: float, D: float) -> None:
        self.L = 0.9 * self.L + 0.1 * S
        self.rho = max(0.5, min(1.5, 1.0 + 0.2 * (D - 0.3)))

    def compute(
        self,
        S: float,
        G: float,
        S_def: float = 0.0,
        tau_idle: float = 0.0,
        trap: bool = False,
        n_deferred: int = 0,
    ) -> MotorSnapshot:
        D = self.drive(tau_idle)
        U = min(1.0, 0.55 * S + 0.25 * D + 0.20 * S_def)
        theta_rev = getattr(self.cfg, "theta_rev", 0.28)
        theta_break = getattr(self.cfg, "theta_break", 0.75)
        revision = U >= theta_rev or S >= theta_rev
        break_loop = trap or S >= theta_break
        m_u = min(1.0, S * 1.2 + U * 0.3)
        m_p = max(0.0, G * 0.8 - S * 0.4)
        if break_loop or S >= 0.55:
            mode = "urgent"
        elif G >= 0.25 and S < 0.25:
            mode = "prospective"
        elif S < 0.15 and G < 0.2:
            mode = "calm"
        else:
            mode = "mixed"
        return MotorSnapshot(
            S=S, G=G, D=D, S_def=S_def, U_urge=U, L=self.L, rho=self.rho,
            tau_idle=tau_idle, revision_needed=revision, break_loop=break_loop,
            mode=mode, m_urgent=m_u, m_prospect=m_p, n_deferred=n_deferred,
        )
