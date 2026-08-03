"""Hormone pulse: S (stress), G (go)."""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Optional, Tuple
from config import HomeostasisConfig
from events import DEFAULT_AMPLITUDES, SIGNIFICANT_WORK_EVENTS

def _clip(x, lo, hi):
    return max(lo, min(hi, x))

@dataclass
class PulseState:
    S: float
    G: float
    tau_idle: float = 0.0

class HormonePulse:
    def __init__(self, config: Optional[HomeostasisConfig] = None):
        self.cfg = config or HomeostasisConfig()
        self.state = PulseState(S=self.cfg.S0, G=self.cfg.G0, tau_idle=0.0)

    def amplitudes(self, event_id: str) -> Tuple[float, float]:
        if event_id in self.cfg.amplitude_overrides:
            return self.cfg.amplitude_overrides[event_id]
        return DEFAULT_AMPLITUDES.get(event_id, (0.0, 0.0))

    def decay(self, dt: float = 1.0) -> None:
        self.state.S *= math.exp(-self.cfg.lambda_S * dt)
        self.state.G *= math.exp(-self.cfg.lambda_G * dt)

    def boredom_delta(self) -> float:
        tau = self.state.tau_idle
        if tau < self.cfg.tau_0:
            return 0.0
        return self.cfg.b * (tau - self.cfg.tau_0) / (self.cfg.tau_0 + tau)

    def apply_event(self, event_id: str) -> None:
        a_s, a_g = self.amplitudes(event_id)
        self.state.S = _clip(self.state.S + a_s, 0.0, self.cfg.S_max)
        self.state.G = _clip(self.state.G + a_g, 0.0, self.cfg.G_max)
        if event_id in SIGNIFICANT_WORK_EVENTS:
            self.state.tau_idle = 0.0

    def on_heartbeat(self, dt: float = 1.0) -> None:
        self.decay(dt)
        self.state.tau_idle += dt
        self.state.S = _clip(self.state.S + self.boredom_delta(), 0.0, self.cfg.S_max)

    def snapshot(self) -> dict:
        return {"S": round(self.state.S, 6), "G": round(self.state.G, 6), "tau_idle": self.state.tau_idle}
