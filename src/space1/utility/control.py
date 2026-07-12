"""
Control Module — PID Controller & Homeostatic Regulator

G6: PID Controller
    u(t) = Kp·e(t) + Ki·∫e·dt + Kd·de/dt

G19 (partial): Homeostatic weight calibration via PID

Reference: DEVELOPMENT_PLAN.md - G6, G19
           MATHEMATICAL_FORMULAS.md - PID section
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List
from collections import deque
import time

from space1.config.loader import get_config


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
    PID Controller для регуляции весов и параметров агента.
    
    Formula:
        u(t) = Kp·e(t) + Ki·∫e·dt + Kd·de/dt
    
    Usage:
        pid = PIDController(kp=1.0, ki=0.1, kd=0.05)
        control_signal = pid.update(setpoint=1.0, measured=0.8)
        # control_signal > 0 → need to increase
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
        """
        Update PID controller with new measurement.
        
        Args:
            setpoint: Target value
            measured: Current measured value
            
        Returns:
            Control signal u(t)
        """
        now = time.time()
        dt = now - self._state.last_time
        
        if dt <= 0:
            dt = 1e-6  # Prevent division by zero
        
        # Error
        error = setpoint - measured
        
        # Proportional
        p_term = self.kp * error
        
        # Integral (with anti-windup)
        self._state.integral += error * dt
        self._state.integral = max(
            -self.integral_limit,
            min(self.integral_limit, self._state.integral)
        )
        i_term = self.ki * self._state.integral
        
        # Derivative
        d_error = (error - self._state.last_error) / dt
        d_term = self.kd * d_error
        
        # Total control signal
        output = p_term + i_term + d_term
        
        # Clamp output
        output = max(-self.output_limit, min(self.output_limit, output))
        
        # Update state
        self._state.last_error = error
        self._state.last_time = now
        
        return output
    
    def reset(self) -> None:
        """Reset PID state."""
        self._state.reset()
    
    @property
    def error(self) -> float:
        """Current error."""
        return self._state.last_error


class HomeostaticRegulator:
    """
    Homeostatic Regulator — регулятор гомеостаза агента.
    
    Поддерживает 3 уровня целей:
    - Выживание (survival): критические метрики
    - Работоспособность (operation): текущая эффективность  
    - Развитие (growth): долгосрочное улучшение
    
    Для каждого уровня используется отдельный PID-регулятор,
    который выдаёт сигнал "давления" (pressure).
    
    Reference: DEVELOPMENT_PLAN.md - G6, G19
    """
    
    # Пороговые значения для уровней
    THRESHOLDS = {
        "survival": {
            "balance": 10.0,      # Минимальный баланс
            "success_rate": 0.2,  # Минимальный success rate
            "stress_level": 0.8,  # Максимальный stress
        },
        "operation": {
            "utilization": 0.7,
            "quality": 0.6,
        },
        "growth": {
            "knowledge": 0.5,
            "reputation": 0.7,
        }
    }
    
    def __init__(self):
        self._pids: Dict[str, PIDController] = {}
        self._pressures: Dict[str, float] = {}
        self._mode = "normal"  # normal, survival, growth
    
    def _get_pid(self, metric: str) -> PIDController:
        """Get or create PID controller for a metric."""
        if metric not in self._pids:
            self._pids[metric] = PIDController()
        return self._pids[metric]
    
    def update_metric(self, metric: str, setpoint: float, measured: float) -> float:
        """
        Update a single metric's PID and return pressure.
        
        Args:
            metric: Metric name
            setpoint: Target value
            measured: Current value
            
        Returns:
            Pressure signal (positive = need improvement)
        """
        pid = self._get_pid(metric)
        pressure = pid.update(setpoint, measured)
        self._pressures[metric] = pressure
        return pressure
    
    def update_all(self, metrics: Dict[str, float]) -> Dict[str, float]:
        """
        Update all metrics and compute pressures.
        
        Args:
            metrics: Dict[metric_name, current_value]
            
        Returns:
            Dict[metric_name, pressure]
        """
        for level, thresholds in self.THRESHOLDS.items():
            for metric, threshold in thresholds.items():
                if metric in metrics:
                    # For "bad" metrics (stress), lower is better
                    if metric in ["stress_level"]:
                        setpoint = threshold * 0.5  # Want half of threshold
                    else:
                        setpoint = threshold * 1.2  # Want 20% above threshold
                    
                    self.update_metric(metric, setpoint, metrics[metric])
        
        return self._pressures.copy()
    
    def get_mode(self) -> str:
        """
        Determine current operating mode based on pressures.
        
        Returns:
            "survival", "normal", or "growth"
        """
        survival_pressure = max(
            (self._pressures.get(m, 0) for m in self.THRESHOLDS["survival"]),
            default=0
        )
        
        if survival_pressure > 0.3:
            return "survival"
        
        growth_pressure = max(
            (self._pressures.get(m, 0) for m in self.THRESHOLDS["growth"]),
            default=0
        )
        
        if growth_pressure < -0.1:
            return "growth"
        
        return "normal"
    
    def get_pressures(self) -> Dict[str, float]:
        """Get all current pressures."""
        return self._pressures.copy()
    
    def get_weight_adjustment(self, base_weights: Dict[str, float]) -> Dict[str, float]:
        """
        Compute weight adjustments based on homeostatic pressures.
        
        Args:
            base_weights: Base utility weights
            
        Returns:
            Adjusted weights
        """
        mode = self.get_mode()
        adjusted = dict(base_weights)
        
        if mode == "survival":
            # Increase profit weight, decrease evolution
            adjusted["profit_weight"] = min(1.0, adjusted.get("profit_weight", 0.3) * 1.5)
            adjusted["evolution_weight"] = max(0.0, adjusted.get("evolution_weight", 0.2) * 0.5)
        elif mode == "growth":
            # Increase evolution, slightly decrease profit
            adjusted["evolution_weight"] = min(1.0, adjusted.get("evolution_weight", 0.2) * 1.3)
            adjusted["profit_weight"] = max(0.0, adjusted.get("profit_weight", 0.3) * 0.9)
        
        # Normalize to sum to 1
        total = sum(adjusted.values())
        if total > 0:
            adjusted = {k: v / total for k, v in adjusted.items()}
        
        return adjusted
    
    def reset(self) -> None:
        """Reset all PID controllers."""
        for pid in self._pids.values():
            pid.reset()
        self._pressures.clear()
        self._mode = "normal"
