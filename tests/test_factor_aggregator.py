"""Tests for Factor Calculator/Aggregator (G9)."""

import pytest
from space1.utility.factor_aggregator import FactorCalculator, FactorAggregation
from space1.factors.registry import FactorRegistry, create_mvp_registry
from space1.metrics.tracker import MetricRegistry


class TestFactorCalculator:
    """Test Factor Calculator."""
    
    def test_default_registry(self):
        """Uses default MVP registry."""
        calc = FactorCalculator()
        registry = calc.get_registry()
        
        factors = registry.get_all()
        assert len(factors) == 4  # MVP has 4 factors
    
    def test_calculate_with_empty_context(self):
        """Calculate with empty context returns valid result."""
        calc = FactorCalculator()
        result = calc.calculate()
        
        assert isinstance(result, FactorAggregation)
        assert 0 <= result.omega <= 1.0
    
    def test_calculate_with_context(self):
        """Calculate with provided context."""
        calc = FactorCalculator()
        context = {
            "benchmarks": {"quality": 0.8, "reasoning": 0.9, "coding": 0.7, "agentic": 0.6},
            "budget": 50.0,
            "task_complexity": 0.5,
            "quality_requirement": 0.8,
            "active_guardrails": ["safety"],
            "risk_probabilities": {"safety": 0.1},
            "n_completed_tasks": 10,
            "current_knowledge": 0.5,
            "base_success": 0.4,
        }
        result = calc.calculate_with_custom_context(context)
        
        assert isinstance(result, FactorAggregation)
        assert hasattr(result, "omega")
        assert hasattr(result, "delta_success")
        assert hasattr(result, "delta_time")
        assert hasattr(result, "individual")
        
        # Should have results for all 4 MVP factors
        assert len(result.individual) == 4
    
    def test_omega_is_normalized(self):
        """Omega is in [0, 1]."""
        calc = FactorCalculator()
        result = calc.calculate()
        
        assert 0 <= result.omega <= 1.0
    
    def test_individual_results(self):
        """Individual factor results are present."""
        calc = FactorCalculator()
        result = calc.calculate()
        
        for factor_id, factor_result in result.individual.items():
            assert hasattr(factor_result, "factor_id")
            assert hasattr(factor_result, "value")
            assert hasattr(factor_result, "delta_success")
    
    def test_tracks_through_metrics(self):
        """Tracks metrics through MetricRegistry."""
        calc = FactorCalculator()
        metrics = MetricRegistry()
        
        result = calc.calculate()
        calc.track_factors(result, metrics)
        
        assert metrics.get("omega") is not None
        assert metrics.get("delta_success") is not None
    
    def test_custom_registry(self):
        """Can use custom registry."""
        registry = create_mvp_registry()
        # Disable one factor
        registry.disable(list(registry.get_all())[0].factor_id)
        
        calc = FactorCalculator(registry=registry)
        result = calc.calculate()
        
        # Should have 3 enabled factors
        assert len(result.individual) == 3
    
    def test_to_dict(self):
        """Result can be serialized."""
        calc = FactorCalculator()
        result = calc.calculate()
        d = result.to_dict()
        
        assert "omega" in d
        assert "delta_success" in d
        assert "individual" in d
        assert isinstance(d, dict)
