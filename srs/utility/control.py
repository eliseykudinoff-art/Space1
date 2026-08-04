"""
Utility Control Module — PID Controller + HomeostaticRegulator facade.

HomeostaticRegulator no longer runs a second homeostat. It maps gauges into
HomeostasisService (pulse S/G + motor urge/D/mode) and exposes the old API
for Stage II/XII, synthesizer, and tests.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
import time

from ..config.loader import get_config


@dataclass
class PIDState:
    """Internal state for PID controller."""
    integral: float = 0.0
    last_error: float = 0.0
    last_time: float = field(default_factory=time.time)

    def reset(self) -> None:
        self.integral = 0.0
        self.last_error = 0.0
        self.last_time = time.time()


class PIDController:
    """
    PID Controller for optional metric-level pressure (tests / rare tuning).
    Not a second homeostat.
    """

    def __init__(
        self,
        kp: Optional[float] = None,
        ki: Optional[float] = None,
        kd: Optional[float] = None,
        integral_limit: float = 10.0,
        output_limit: float = 1.0,
    ):
        cfg = get_config().constants
        self.kp = kp if kp is not None else cfg.pid_kp
        self.ki = ki if ki is not None else cfg.pid_ki
        self.kd = kd if kd is not None else cfg.pid_kd
        self.integral_limit = integral_limit
        self.output_limit = output_limit
        self._state = PIDState()

    def update(self, setpoint: float, measured: float) -> float:
        now = time.time()
        dt = now - self._state.last_time
        if dt <= 0:
            dt = 1e-6
        error = setpoint - measured
        p_term = self.kp * error
        self._state.integral += error * dt
        self._state.integral = max(
            -self.integral_limit, min(self.integral_limit, self._state.integral)
        )
        i_term = self.ki * self._state.integral
        d_error = (error - self._state.last_error) / dt
        d_term = self.kd * d_error
        output = p_term + i_term + d_term
        output = max(-self.output_limit, min(self.output_limit, output))
        self._state.last_error = error
        self._state.last_time = now
        return output

    def reset(self) -> None:
        self._state.reset()

    @property
    def error(self) -> float:
        return self._state.last_error


class HomeostaticRegulator:
    """
    Facade kept for import stability. Single motor: HomeostasisService
    (pulse S/G + motor urge/D/mode). Old dual PID-homeostat math removed.

    calculate_homeostasis → (H, stress) from life S/urge
    update_all → pressure dict for WeightCalibrator / synthesizer
    get_mode → survival|normal|growth from motor / S hysteresis
    """

    THRESHOLDS = {
        "survival": {"balance": 10.0, "success_rate": 0.2, "stress_level": 0.8},
        "operation": {"utilization": 0.7, "quality": 0.6},
        "growth": {"knowledge": 0.5, "reputation": 0.7},
    }

    def __init__(self, service=None):
        if service is None:
            from ..homeostasis.service import HomeostasisService
            service = HomeostasisService()
        self._svc = service
        self._pressures: Dict[str, float] = {}
        self._mode = "normal"
        self._pids: Dict[str, PIDController] = {}

    def _get_pid(self, metric: str) -> PIDController:
        if metric not in self._pids:
            self._pids[metric] = PIDController()
        return self._pids[metric]

    def update_metric(self, metric: str, setpoint: float, measured: float) -> float:
        pid = self._get_pid(metric)
        pressure = pid.update(setpoint, measured)
        self._pressures[metric] = pressure
        if metric == "balance" and setpoint > 0 and measured / setpoint < 0.15:
            self._svc.pulse.state.S = max(self._svc.pulse.state.S, 0.62)
            self._svc.step()
        return pressure

    def _feed_metrics(self, metrics: Dict[str, float]) -> None:
        balance = float(metrics.get("balance", 20.0))
        budget_target = float(metrics.get("budget_target", 100.0))
        quality = float(metrics.get("quality", 0.8))
        quality_target = float(metrics.get("quality_target", 0.8))
        active = float(metrics.get("active_tasks", metrics.get("n_active_tasks", 0.0)))
        max_cap = float(metrics.get("max_capacity", 5.0))

        balance_min = float(self.THRESHOLDS["survival"].get("balance", 10.0))
        if balance < balance_min:
            resource = max(0.0, min(1.0, 0.5 + 0.5 * (1.0 - balance / max(balance_min, 1e-9))))
        elif balance < budget_target:
            resource = max(0.0, min(0.45, 0.45 * (1.0 - balance / budget_target)))
        else:
            resource = 0.0
        progress = max(0.0, min(1.0, active / max(max_cap, 1e-9)))
        if "success_rate" in metrics:
            progress = max(progress, max(0.0, min(0.5, 1.0 - float(metrics["success_rate"]))))

        if "reputation" in metrics:
            rep = float(metrics["reputation"])
            rep_ratio = rep if rep <= 1.0 else rep / 5.0
        elif "rating" in metrics:
            rating = float(metrics["rating"])
            rep_ratio = rating if rating <= 1.0 else rating / 5.0
        else:
            rep_ratio = 0.9
        compliance = max(0.0, min(1.0, 1.0 - rep_ratio))

        q_ratio = quality if quality <= 1.0 else quality / max(quality_target, 1e-9)
        knowledge = max(0.0, min(1.0, 1.0 - min(1.0, q_ratio)))
        if "knowledge" in metrics:
            k = float(metrics["knowledge"])
            k_ratio = k if k <= 1.0 else min(1.0, k)
            knowledge = max(0.0, min(1.0, 1.0 - k_ratio))

        self._svc.update_axes(
            resource=resource,
            progress=progress,
            knowledge=knowledge,
            compliance=compliance,
        )

    def calculate_homeostasis(self, metrics: Dict[str, float]) -> tuple[float, float]:
        self._feed_metrics(metrics)
        snap = self._svc.step()
        S = float(getattr(snap, "S", 0.0))
        urge = float(getattr(snap, "urge", S))
        stress = max(0.0, min(1.0, S))
        H = max(0.0, min(1.2, 1.0 - 0.7 * stress - 0.3 * max(0.0, min(1.0, urge))))
        return H, stress

    def update_all(self, metrics: Dict[str, float]) -> Dict[str, float]:
        self._feed_metrics(metrics)
        ax = self._svc.motor.axes
        if ax.resource >= 0.75:
            self._svc.pulse.state.S = max(self._svc.pulse.state.S, 0.62)
        elif ax.resource <= 0.40:
            self._svc.pulse.state.S = min(self._svc.pulse.state.S, 0.20)
        if ax.resource <= 0.12 and ax.knowledge <= 0.15 and ax.compliance <= 0.15:
            self._svc.pulse.state.S = min(self._svc.pulse.state.S, 0.12)
            self._svc.pulse.state.G = max(self._svc.pulse.state.G, 0.35)
        snap = self._svc.step()
        S = float(getattr(snap, "S", 0.0))
        urge = float(getattr(snap, "urge", 0.0))
        D = float(getattr(snap, "D", 0.0))
        self._pressures = {
            "balance": float(ax.resource),
            "success_rate": float(ax.progress),
            "stress_level": S,
            "quality": float(ax.knowledge),
            "reputation": float(ax.compliance),
            "knowledge": float(ax.knowledge),
            "utilization": float(ax.progress),
            "urge": urge,
            "drive": D,
        }
        self.get_mode()
        return self._pressures.copy()

    def get_mode(self) -> str:
        snap = self._svc.last_snapshot or self._svc.step()
        S = float(getattr(snap, "S", 0.0))
        m = getattr(snap, "mode", "calm")
        if self._mode == "survival":
            if S >= 0.35 or m == "urgent":
                return "survival"
        elif S >= 0.55 or m == "urgent":
            self._mode = "survival"
            return "survival"
        if m == "prospective" or (S < 0.2 and float(getattr(snap, "G", 0)) >= 0.25):
            self._mode = "growth"
            return "growth"
        self._mode = "normal"
        return "normal"

    def get_pressures(self) -> Dict[str, float]:
        return self._pressures.copy()

    def get_weight_adjustment(self, base_weights: Dict[str, float]) -> Dict[str, float]:
        mode = self.get_mode()
        adjusted = dict(base_weights)
        if mode == "survival":
            adjusted["profit_weight"] = min(1.0, adjusted.get("profit_weight", 0.3) * 1.5)
            adjusted["evolution_weight"] = max(0.0, adjusted.get("evolution_weight", 0.2) * 0.5)
        elif mode == "growth":
            adjusted["evolution_weight"] = min(1.0, adjusted.get("evolution_weight", 0.2) * 1.3)
            adjusted["profit_weight"] = max(0.0, adjusted.get("profit_weight", 0.3) * 0.9)
        total = sum(adjusted.values())
        if total > 0:
            adjusted = {k: v / total for k, v in adjusted.items()}
        return adjusted

    def reset(self) -> None:
        from ..homeostasis.service import HomeostasisService
        self._svc = HomeostasisService()
        for pid in self._pids.values():
            pid.reset()
        self._pressures.clear()
        self._mode = "normal"
