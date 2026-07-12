"""Tests for Composite Metrics — Ξ Coefficients & Φ_R Consistency (G17, G18)."""

import pytest
from space1.utility.composite import XiCoefficients, PhiRCalculator, XiComponents, PhiRComponents


class TestXiCoefficients:
    """Test Ξ Coefficients calculator."""
    
    def test_high_quality_low_opportunity(self):
        """High quality, low opportunity → high Ξ."""
        calc = XiCoefficients(alpha=0.7, beta=0.3)
        result = calc.calculate(quality_score=1.0, opportunity_time=0.0, opportunity_cost=0.0)
        
        assert result.xi_value > 0
        assert abs(result.xi_value - 0.7) < 0.01
    
    def test_low_quality_high_opportunity(self):
        """Low quality, high opportunity → low Ξ."""
        calc = XiCoefficients(alpha=0.7, beta=0.3)
        result = calc.calculate(quality_score=0.0, opportunity_time=0.5, opportunity_cost=0.5)
        
        assert result.xi_value < 0
    
    def test_clamped_inputs(self):
        """Inputs are clamped to [0, 1]."""
        calc = XiCoefficients()
        result = calc.calculate(quality_score=2.0, opportunity_time=-1.0)
        
        assert result.quality_score == 1.0
        assert result.opportunity_cost == 0.0
    
    def test_alpha_beta_effect(self):
        """Higher alpha prioritizes quality."""
        calc_high_alpha = XiCoefficients(alpha=0.9, beta=0.1)
        calc_low_alpha = XiCoefficients(alpha=0.1, beta=0.9)
        
        r1 = calc_high_alpha.calculate(quality_score=1.0, opportunity_time=0.3)
        r2 = calc_low_alpha.calculate(quality_score=1.0, opportunity_time=0.3)
        
        assert r1.xi_value > r2.xi_value
    
    def test_returns_xi_components(self):
        """Returns structured components."""
        calc = XiCoefficients()
        result = calc.calculate(quality_score=0.8)
        
        assert isinstance(result, XiComponents)
        assert hasattr(result, "xi_value")
        assert hasattr(result, "quality_score")
    
    def test_to_dict(self):
        """Components can be serialized."""
        calc = XiCoefficients()
        result = calc.calculate(quality_score=0.8)
        d = result.to_dict()
        
        assert "xi_value" in d
        assert isinstance(d, dict)


class TestPhiRCalculator:
    """Test Φ_R Consistency calculator."""
    
    def test_full_compliance_no_reputation(self):
        """Γ=1, Υ=0 → Φ_R = Φ - λ·Ψ."""
        calc = PhiRCalculator(alpha_rep=0.3, lambda_psi=0.5)
        result = calc.calculate(phi=100.0, gamma=1.0, upsilon=0.0, psi=0.0)
        
        assert abs(result.phi_r - 100.0) < 0.01
    
    def test_full_compliance_full_reputation(self):
        """Γ=1, Υ=1 → Φ_R = Φ × 1.3 - λ·Ψ."""
        calc = PhiRCalculator(alpha_rep=0.3, lambda_psi=0.0)
        result = calc.calculate(phi=100.0, gamma=1.0, upsilon=1.0, psi=0.0)
        
        assert abs(result.phi_r - 130.0) < 0.01
    
    def test_no_compliance(self):
        """Γ=0 → Φ_R = -λ·Ψ (regardless of Φ)."""
        calc = PhiRCalculator(alpha_rep=0.3, lambda_psi=0.5)
        result = calc.calculate(phi=100.0, gamma=0.0, upsilon=1.0, psi=0.2)
        
        expected_penalty = -0.5 * 0.2
        assert abs(result.phi_r - expected_penalty) < 0.01
    
    def test_high_risk_penalty(self):
        """High Ψ reduces Φ_R."""
        calc = PhiRCalculator(alpha_rep=0.3, lambda_psi=0.5)
        
        low_risk = calc.calculate(phi=100.0, gamma=1.0, upsilon=0.5, psi=0.1)
        high_risk = calc.calculate(phi=100.0, gamma=1.0, upsilon=0.5, psi=0.8)
        
        assert high_risk.phi_r < low_risk.phi_r
    
    def test_clamped_inputs(self):
        """Inputs are clamped to [0, 1]."""
        calc = PhiRCalculator()
        result = calc.calculate(phi=100.0, gamma=2.0, upsilon=-1.0, psi=5.0)
        
        assert result.gamma_compliance == 1.0
        assert result.upsilon_reputation == 0.0
        assert result.psi_risk == 1.0
    
    def test_returns_phi_r_components(self):
        """Returns structured components."""
        calc = PhiRCalculator()
        result = calc.calculate(phi=50.0, gamma=1.0, upsilon=0.5, psi=0.2)
        
        assert isinstance(result, PhiRComponents)
        assert hasattr(result, "phi_r")
        assert hasattr(result, "base_phi")
    
    def test_to_dict(self):
        """Components can be serialized."""
        calc = PhiRCalculator()
        result = calc.calculate(phi=50.0, gamma=1.0, upsilon=0.5, psi=0.2)
        d = result.to_dict()
        
        assert "phi_r" in d
        assert isinstance(d, dict)
