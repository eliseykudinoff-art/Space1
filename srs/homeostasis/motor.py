"""Homeostasis motor: drive D, U_urge, allostasis, mode, flags."""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Optional
from config import HomeostasisConfig

def _clip(x, lo, hi):
    return max(lo, min(hi, x))

def _sigmoid(x):
    return 1.0 / (1.0 + math.exp(-x))

@dataclass
class AxisState:
    resource: float = 0.0
    progress: float = 0.0
    compliance: float = 0.0
    competence: float = 0.0
    reputation: float = 0.0
    workload: float = 0.0

@dataclass
class MotorSnapshot:
    S: float
    G: float
    D: float
    S_def: float
    U_urge: float
    L: float
    rho: float
    tau_idle: float
    revision_needed: bool
    break_loop: bool
    mode: str
    m_urgent: float
    m_prospect: float
    n_deferred: int = 0

    def to_dict(self) -> dict:
        return {
            "S": round(self.S, 6), "G": round(self.G, 6), "D": round(self.D, 6),
            "S_def": round(self.S_def, 6), "U_urge": round(self.U_urge, 6),
            "L": round(self.L, 6), "rho": round(self.rho, 6),
            "tau_idle": self.tau_idle,
            "revision_needed": self.revision_needed, "break_loop": self.break_loop,
            "mode": self.mode, "m_urgent": round(self.m_urgent, 4),
            "m_prospect": round(self.m_prospect, 4), "n_deferred": self.n_deferred,
        }

class HomeostasisMotor:
    def __init__(self, config: Optional[HomeostasisConfig] = None):
        self.cfg = config or HomeostasisConfig()
        self.axes = AxisState()
        self.L = 0.0
        self.rho = self.cfg.rho0
        self.n_fail = 0.0
        self._tick = 0

    def update_axes(self, **kwargs: float) -> None:
        for k, v in kwargs.items():
            if hasattr(self.axes, k):
                setattr(self.axes, k, float(_clip(v, 0.0, 1.0)))

    def drive(self, tau_idle: float) -> float:
        c = self.cfg
        d_idle = 0.0
        if tau_idle >= c.tau_0:
            d_idle = (tau_idle - c.tau_0) / (c.tau_0 + tau_idle)
        D = c.w_resource * self.axes.resource + c.w_progress * self.axes.progress + c.w_idle * d_idle
        D += 0.05 * self.axes.compliance + 0.05 * self.axes.competence
        return float(D)

    def update_slow(self, S: float, D: float) -> None:
        c = self.cfg
        psi = c.beta_S * S + c.beta_D * min(1.0, D / max(c.D_ref, 1e-9)) + c.beta_f * min(1.0, self.n_fail / 3.0)
        self.L = (1.0 - c.alpha_L) * self.L + c.alpha_L * psi
        self.rho = _clip(c.rho0 + c.kappa_L * self.L, c.rho_min, c.rho_max)

    def note_failure(self, weight: float = 1.0) -> None:
        self.n_fail += weight

    def note_success_decay_fail(self) -> None:
        self.n_fail = max(0.0, self.n_fail - 0.05)

    def compute(self, S, G, S_def, tau_idle, trap=False, n_deferred=0) -> MotorSnapshot:
        c = self.cfg
        D = self.drive(tau_idle)
        U_raw = c.alpha_S * S + c.alpha_D * D + c.alpha_def * S_def
        U_urge = self.rho * U_raw
        revision_needed = U_urge >= c.theta_rev
        break_loop = trap or (S >= c.theta_break)
        m_u = _sigmoid(6.0 * (S - c.S_mid))
        m_p = _sigmoid(5.0 * (G - c.G_mid)) * _sigmoid(5.0 * (c.S_soft - S))
        if S >= c.theta_urgent or S_def >= 0.35:
            mode = "urgent"
        elif m_p > 0.45 and S < c.S_soft:
            mode = "prospective"
        elif S >= 0.22 or S_def >= 0.12:
            mode = "mixed"
        else:
            mode = "calm"
        return MotorSnapshot(S=S, G=G, D=D, S_def=S_def, U_urge=U_urge, L=self.L, rho=self.rho,
            tau_idle=tau_idle, revision_needed=revision_needed, break_loop=break_loop,
            mode=mode, m_urgent=m_u, m_prospect=m_p, n_deferred=n_deferred)

    def should_run_slow(self, force: bool = False) -> bool:
        self._tick += 1
        return force or (self._tick % max(1, self.cfg.K_slow) == 0)
