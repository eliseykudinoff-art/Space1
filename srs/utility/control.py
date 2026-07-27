"""
Control Module — PID Controller & Homeostatic Regulator

G6: PID Controller
    u(t) = Kp·e(t) + Ki·∫e·dt + Kd·de/dt

G19 (partial): Homeostatic weight calibration via PID with hysteresis buffer to avoid oscillations.

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
    
    def calculate_homeostasis(self, metrics: Dict[str, float]) -> tuple[float, float]:
        """
        Calculate canonical stress and homeostasis H according to 02_MATHEMATICAL_CORE.md.
        
        Formula:
            stress = w_B*(1 - balance_ratio) + w_R*(1 - rating_ratio) + w_L*workload_ratio + w_Q*(1 - quality_ratio)
            H = 1 - stress
            
        Where:
            w_B = w_R = 0.3, w_L = w_Q = 0.2
            
        Returns:
            Tuple[H, stress]
        """
        # Read metric values with safe defaults
        balance = metrics.get("balance", 20.0)
        rating = metrics.get("reputation", metrics.get("rating", 4.5))
        quality = metrics.get("quality", 0.8)
        active_tasks = metrics.get("active_tasks", metrics.get("n_active_tasks", 1.0))
        
        # Targets & limits
        balance_min = self.THRESHOLDS["survival"].get("balance", 10.0)
        budget_target = metrics.get("budget_target", 100.0)
        rating_target = metrics.get("rating_target", 4.5)
        quality_target = metrics.get("quality_target", 0.8)
        max_capacity = metrics.get("max_capacity", 5.0)
        
        # 1. Balance ratio
        if balance < balance_min:
            balance_ratio = 0.1
        elif balance < budget_target:
            balance_ratio = balance / max(budget_target, 1e-9)
        else:
            balance_ratio = 1.0
            
        # 2. Rating ratio (no upper min(1.0, ...) cap to allow rating_ratio > 1.0 and H > 1.2)
        rating_ratio = rating / max(rating_target, 1e-9)
        
        # 3. Quality ratio (no upper min(1.0, ...) cap to allow quality_ratio > 1.0 and H > 1.2)
        quality_ratio = quality / max(quality_target, 1e-9)
        
        # 4. Workload ratio
        workload_ratio = active_tasks / max(max_capacity, 1e-9)
        
        # Compute stress using canonical weights
        w_B, w_R, w_L, w_Q = 0.3, 0.3, 0.2, 0.2
        stress = (
            w_B * (1.0 - balance_ratio)
            + w_R * (1.0 - rating_ratio)
            + w_L * workload_ratio
            + w_Q * (1.0 - quality_ratio)
        )
        
        H = 1.0 - stress
        return H, stress

    def update_all(self, metrics: Dict[str, float]) -> Dict[str, float]:
        """
        Update all metrics and compute pressures.
        
        Args:
            metrics: Dict[metric_name, current_value]
            
        Returns:
            Dict[metric_name, pressure]
        """
        # Inject newly calculated canonical stress_level into metrics if not already present
        if "stress_level" not in metrics:
            _, stress = self.calculate_homeostasis(metrics)
            metrics["stress_level"] = max(0.0, stress)

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
        Determine current operating mode based on pressures with hysteresis.
        
        Reference: Prevents fast homeostatic state oscillations by using threshold bounds.
        
        Returns:
            "survival", "normal", or "growth"
        """
        survival_pressure = max(
            (self._pressures.get(m, 0) for m in self.THRESHOLDS["survival"]),
            default=0
        )
        
        # State Hysteresis logic
        if self._mode == "survival":
            # Harder to leave survival mode to avoid oscillation: pressure must drop below 0.15
            if survival_pressure > 0.15:
                self._mode = "survival"
                return "survival"
        else:
            # Enter survival mode if pressure breaches 0.3
            if survival_pressure > 0.3:
                self._mode = "survival"
                return "survival"
                
        growth_pressure = max(
            (self._pressures.get(m, 0) for m in self.THRESHOLDS["growth"]),
            default=0
        )
        
        if self._mode == "growth":
            # Harder to leave growth mode to avoid oscillation: pressure must rise above -0.05
            if growth_pressure < -0.05:
                self._mode = "growth"
                return "growth"
        else:
            # Enter growth mode if pressure is below -0.1
            if growth_pressure < -0.1:
                self._mode = "growth"
                return "growth"
                
        self._mode = "normal"
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
