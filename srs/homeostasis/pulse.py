"""Hormone pulse: S (stress) and G (reward)."""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Optional, Tuple
from .config import HomeostasisConfig
from .events import DEFAULT_AMPLITUDES, SIGNIFICANT_WORK_EVENTS


@dataclass
class PulseState:
    S: float = 0.08
    G: float = 0.12
    tau_idle: float = 0.0

    def clip(self) -> None:
        self.S = max(0.0, min(1.0, self.S))
        self.G = max(0.0, min(1.0, self.G))


class HormonePulse:
    def __init__(self, cfg: Optional[HomeostasisConfig] = None):
        self.cfg = cfg or HomeostasisConfig()
        self.state = PulseState()

    def decay_tick(self, dt: float = 1.0) -> None:
        self.state.S *= math.exp(-self.cfg.lambda_S * dt)
        self.state.G *= math.exp(-self.cfg.lambda_G * dt)
        self.state.clip()

    def boredom_tick(self, dt: float = 1.0) -> None:
        self.state.tau_idle += dt
        tau = self.state.tau_idle
        tau0 = getattr(self.cfg, "tau_0", getattr(self.cfg, "tau0", 10.0))
        add = self.cfg.b * (tau / (tau0 + tau))
        self.state.S = min(1.0, self.state.S + add)

    def apply_event(self, event_id: str, amplitude: Optional[Tuple[float, float]] = None) -> None:
        table = dict(DEFAULT_AMPLITUDES)
        table.update(getattr(self.cfg, "amplitude_overrides", {}) or {})
        a_s, a_g = amplitude if amplitude is not None else table.get(event_id, (0.0, 0.0))
        self.state.S = max(0.0, min(1.0, self.state.S + a_s))
        self.state.G = max(0.0, min(1.0, self.state.G + a_g))
        if event_id in SIGNIFICANT_WORK_EVENTS:
            self.state.tau_idle = 0.0

    def on_heartbeat(self, dt: float = 1.0) -> None:
        self.decay_tick(dt)
        self.boredom_tick(dt)

    def snapshot(self) -> dict:
        return {"S": self.state.S, "G": self.state.G, "tau_idle": self.state.tau_idle}
