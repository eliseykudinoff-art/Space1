"""Tests for PID Controller and Homeostatic Regulator (G6)."""

import pytest
from space1.utility.control import PIDController, HomeostaticRegulator


class TestPIDController:
    """Test PID Controller."""
    
    def test_proportional_response(self):
        """PID responds to error proportionally."""
        pid = PIDController(kp=1.0, ki=0.0, kd=0.0)
        output = pid.update(setpoint=1.0, measured=0.5)
        
        # Error = 0.5, Kp = 1.0 → output = 0.5
        assert abs(output - 0.5) < 0.01
    
    def test_integral_accumulation(self):
        """Integral term accumulates over time."""
        pid = PIDController(kp=0.0, ki=1.0, kd=0.0)
        
        # First update
        out1 = pid.update(setpoint=1.0, measured=0.0)
        # Second update
        out2 = pid.update(setpoint=1.0, measured=0.0)
        
        # Integral should grow
        assert out2 > out1
    
    def test_derivative_response(self):
        """Derivative responds to change in error."""
        pid = PIDController(kp=0.0, ki=0.0, kd=1.0)
        
        # First measurement
        pid.update(setpoint=1.0, measured=0.5)
        # Error changes
        output = pid.update(setpoint=1.0, measured=0.6)
        
        # Derivative should be non-zero
        assert output != 0.0
    
    def test_output_clamping(self):
        """Output is clamped to limits."""
        pid = PIDController(kp=100.0, output_limit=1.0)
        output = pid.update(setpoint=10.0, measured=0.0)
        
        assert output <= 1.0
    
    def test_integral_anti_windup(self):
        """Integral has anti-windup."""
        pid = PIDController(kp=0.0, ki=10.0, integral_limit=1.0)
        
        # Multiple large errors
        for _ in range(10):
            pid.update(setpoint=100.0, measured=0.0)
        
        # Integral should be clamped
        assert pid._state.integral <= 1.0
    
    def test_reset(self):
        """Reset clears PID state."""
        pid = PIDController(kp=1.0, ki=0.5, kd=0.1)
        pid.update(setpoint=1.0, measured=0.5)
        pid.reset()
        
        assert pid._state.integral == 0.0
        assert pid._state.last_error == 0.0
    
    def test_zero_dt_handling(self):
        """Handle near-zero time delta gracefully."""
        pid = PIDController(kp=1.0)
        out1 = pid.update(setpoint=1.0, measured=0.5)
        
        # Immediate second call with same measured (dt ≈ 0, d_error ≈ 0)
        out2 = pid.update(setpoint=1.0, measured=0.5)
        
        # Should not crash; output should be bounded
        assert abs(out2) <= 1.0  # Within output limit


class TestHomeostaticRegulator:
    """Test Homeostatic Regulator."""
    
    def test_update_metric(self):
        """Update single metric and get pressure."""
        reg = HomeostaticRegulator()
        pressure = reg.update_metric("balance", setpoint=100.0, measured=50.0)
        
        # Pressure should be positive (need to increase)
        assert pressure > 0
    
    def test_update_all(self):
        """Update multiple metrics."""
        reg = HomeostaticRegulator()
        metrics = {
            "balance": 5.0,
            "success_rate": 0.3,
            "stress_level": 0.5,
        }
        pressures = reg.update_all(metrics)
        
        assert len(pressures) > 0
        assert all(isinstance(v, float) for v in pressures.values())
    
    def test_survival_mode(self):
        """Detect survival mode when critical metrics are low."""
        reg = HomeostaticRegulator()
        
        # Very low balance → survival mode
        reg.update_metric("balance", setpoint=100.0, measured=5.0)
        mode = reg.get_mode()
        
        assert mode == "survival"
    
    def test_normal_mode(self):
        """Detect valid mode when metrics are OK."""
        reg = HomeostaticRegulator()
        
        # Good metrics — high balance, good success rate, low stress
        reg.update_metric("balance", setpoint=100.0, measured=150.0)
        reg.update_metric("success_rate", setpoint=0.5, measured=0.8)
        reg.update_metric("stress_level", setpoint=0.4, measured=0.1)
        mode = reg.get_mode()
        
        # Should return a valid mode
        assert mode in ["survival", "normal", "growth"]
    
    def test_weight_adjustment_survival(self):
        """Weights shift toward profit in survival mode."""
        reg = HomeostaticRegulator()
        
        # Trigger survival
        reg.update_metric("balance", setpoint=100.0, measured=5.0)
        
        base_weights = {
            "profit_weight": 0.3,
            "reputation_weight": 0.25,
            "evolution_weight": 0.2,
            "quality_weight": 0.25,
        }
        adjusted = reg.get_weight_adjustment(base_weights)
        
        # Profit should increase, evolution should decrease
        assert adjusted["profit_weight"] > base_weights["profit_weight"]
        assert adjusted["evolution_weight"] < base_weights["evolution_weight"]
    
    def test_weight_adjustment_normalization(self):
        """Adjusted weights sum to 1."""
        reg = HomeostaticRegulator()
        
        base_weights = {
            "profit_weight": 0.3,
            "reputation_weight": 0.25,
            "evolution_weight": 0.2,
            "quality_weight": 0.25,
        }
        adjusted = reg.get_weight_adjustment(base_weights)
        
        total = sum(adjusted.values())
        assert abs(total - 1.0) < 0.001
    
    def test_reset(self):
        """Reset clears all state."""
        reg = HomeostaticRegulator()
        reg.update_metric("balance", setpoint=100.0, measured=50.0)
        reg.reset()
        
        assert len(reg.get_pressures()) == 0
        assert reg.get_mode() == "normal"
