"""Tests for Risk-Adjusted Profit (G7)."""

import pytest
from space1.utility.profit import RiskAdjustedProfit, compute_phi_risk_adjusted, ProfitComponents


class TestRiskAdjustedProfit:
    """Test Risk-Adjusted Profit calculator."""
    
    def test_no_risk_full_profit(self):
        """When Ψ=0, Φ_adj = Φ."""
        calc = RiskAdjustedProfit(risk_tolerance=1.0)
        result = calc.calculate_from_components(base_phi=100.0, psi=0.0)
        
        assert abs(result.phi_adjusted - 100.0) < 0.01
        assert result.adjustment_factor == 1.0
    
    def test_full_risk_zero_profit(self):
        """When Ψ=P, Φ_adj = 0."""
        calc = RiskAdjustedProfit(risk_tolerance=1.0)
        result = calc.calculate_from_components(base_phi=100.0, psi=1.0)
        
        assert abs(result.phi_adjusted) < 0.01
        assert abs(result.adjustment_factor) < 0.01
    
    def test_excessive_risk_negative(self):
        """When Ψ > P, Φ_adj < 0."""
        calc = RiskAdjustedProfit(risk_tolerance=1.0)
        result = calc.calculate_from_components(base_phi=100.0, psi=1.5)
        
        assert result.phi_adjusted < 0
    
    def test_half_risk_half_adjustment(self):
        """When Ψ = P/2, adjustment = 0.5."""
        calc = RiskAdjustedProfit(risk_tolerance=1.0)
        result = calc.calculate_from_components(base_phi=100.0, psi=0.5)
        
        assert abs(result.adjustment_factor - 0.5) < 0.01
        assert abs(result.phi_adjusted - 50.0) < 0.01
    
    def test_custom_tolerance(self):
        """Custom risk tolerance changes behavior."""
        calc = RiskAdjustedProfit(risk_tolerance=2.0)
        result = calc.calculate_from_components(base_phi=100.0, psi=1.0)
        
        # With P=2, Ψ=1 → adjustment = 1 - 1/2 = 0.5
        assert abs(result.adjustment_factor - 0.5) < 0.01
    
    def test_returns_profit_components(self):
        """Returns structured components."""
        calc = RiskAdjustedProfit()
        result = calc.calculate_from_components(base_phi=50.0, psi=0.2)
        
        assert isinstance(result, ProfitComponents)
        assert hasattr(result, "base_phi")
        assert hasattr(result, "risk_psi")
        assert hasattr(result, "adjustment_factor")
        assert hasattr(result, "phi_adjusted")
    
    def test_to_dict(self):
        """Components can be serialized."""
        calc = RiskAdjustedProfit()
        result = calc.calculate_from_components(base_phi=50.0, psi=0.2)
        d = result.to_dict()
        
        assert "base_phi" in d
        assert "phi_adjusted" in d
        assert isinstance(d, dict)


def test_compute_phi_risk_adjusted_function():
    """Test convenience function."""
    result = compute_phi_risk_adjusted(
        revenue=100.0,
        cost=10.0,
        time_hours=2.0,
        risk_tolerance=1.0,
    )
    
    # Base phi = (100-10)/2 = 45
    # With no agent_context, psi defaults to ~0.5
    # adjustment = 1 - 0.5 = 0.5
    # phi_adj = 45 * 0.5 = 22.5
    assert isinstance(result, float)
    assert result > 0
