"""
Tests for FactorRegistry

Reference: DEVELOPMENT_PLAN.md - G9
"""

import pytest
from space1.factors.registry import (
    FactorRegistry, FactorID, FactorResult,
    LLMFactor, CostTieringFactor, GuardrailsFactor, ContinualLearningFactor,
    create_mvp_registry
)


class TestLLMFactor:
    """Test LLM Factor (x₁)."""
    
    def test_compute_basic(self):
        """Test basic LLM computation."""
        factor = LLMFactor()
        context = {
            "benchmarks": {
                "quality": 0.8,
                "reasoning": 0.8,
                "coding": 0.8,
                "agentic": 0.8,
            }
        }
        
        result = factor.compute(context)
        
        assert result.factor_id == "x1"
        assert 0 <= result.value <= 1
        assert isinstance(result.delta_success, float)
    
    def test_higher_benchmark_higher_success(self):
        """Higher benchmarks should lead to higher success delta."""
        factor = LLMFactor()
        
        low_context = {
            "benchmarks": {
                "quality": 0.5, "reasoning": 0.5,
                "coding": 0.5, "agentic": 0.5,
            }
        }
        high_context = {
            "benchmarks": {
                "quality": 0.9, "reasoning": 0.9,
                "coding": 0.9, "agentic": 0.9,
            }
        }
        
        low_result = factor.compute(low_context)
        high_result = factor.compute(high_context)
        
        assert high_result.delta_success > low_result.delta_success


class TestCostTieringFactor:
    """Test Cost Tiering Factor (x₈)."""
    
    def test_low_budget_selects_free(self):
        """Low budget should select free tier."""
        factor = CostTieringFactor()
        context = {"budget": 0.5, "task_complexity": 0.5, "quality_requirement": 0.9}
        
        result = factor.compute(context)
        
        assert result.metadata["selected_tier"] in ["ollama", "free_api"]
    
    def test_high_budget_selects_paid(self):
        """High budget should select paid tier."""
        factor = CostTieringFactor()
        context = {"budget": 100.0, "task_complexity": 0.5, "quality_requirement": 0.9}
        
        result = factor.compute(context)
        
        assert result.metadata["selected_tier"] == "paid_api"


class TestGuardrailsFactor:
    """Test Guardrails Factor (x₁₂)."""
    
    def test_no_guardrails_low_effectiveness(self):
        """No guardrails = low effectiveness."""
        factor = GuardrailsFactor()
        context = {
            "active_guardrails": [],
            "risk_probabilities": {"financial": 0.3, "safety": 0.5}
        }
        
        result = factor.compute(context)
        
        assert result.value < 0.8  # Low G_eff
        assert result.delta_success < 0.05
    
    def test_active_guardrails_high_effectiveness(self):
        """Active guardrails = higher effectiveness."""
        factor = GuardrailsFactor()
        context = {
            "active_guardrails": ["financial", "safety"],
            "risk_probabilities": {"financial": 0.3, "safety": 0.5}
        }
        
        result = factor.compute(context)
        
        assert result.value > 0.5  # Higher G_eff


class TestContinualLearningFactor:
    """Test Continual Learning Factor (x₁₆)."""
    
    def test_more_tasks_higher_knowledge(self):
        """More completed tasks = higher knowledge."""
        factor = ContinualLearningFactor()
        
        low_context = {"n_completed_tasks": 10, "current_knowledge": 0.1, "base_success": 0.3}
        high_context = {"n_completed_tasks": 100, "current_knowledge": 0.1, "base_success": 0.3}
        
        low_result = factor.compute(low_context)
        high_result = factor.compute(high_context)
        
        assert high_result.value > low_result.value
        assert high_result.delta_success > low_result.delta_success


class TestFactorRegistry:
    """Test FactorRegistry."""
    
    def test_register_and_get(self):
        """Test factor registration."""
        registry = FactorRegistry()
        factor = LLMFactor()
        
        registry.register(factor)
        
        assert registry.get(FactorID.X1_LLM) is factor
    
    def test_compute_all(self):
        """Test computing all factors."""
        registry = create_mvp_registry()
        context = {
            "benchmarks": {"quality": 0.7, "reasoning": 0.7, "coding": 0.7, "agentic": 0.7},
            "budget": 10.0,
            "task_complexity": 0.5,
            "quality_requirement": 0.7,
            "active_guardrails": [],
            "risk_probabilities": {},
            "n_completed_tasks": 50,
            "current_knowledge": 0.2,
            "base_success": 0.3,
        }
        
        results = registry.compute_all(context)
        
        assert "x1" in results
        assert "x8" in results
        assert "x12" in results
        assert "x16" in results
        
        for result in results.values():
            assert isinstance(result, FactorResult)
    
    def test_enable_disable(self):
        """Test enabling/disabling factors."""
        registry = FactorRegistry()
        registry.register(LLMFactor())
        
        registry.disable(FactorID.X1_LLM)
        assert len(registry.get_enabled()) == 0
        
        registry.enable(FactorID.X1_LLM)
        assert len(registry.get_enabled()) == 1
    
    def test_compute_total_deltas(self):
        """Test computing total deltas."""
        registry = create_mvp_registry()
        context = {
            "benchmarks": {"quality": 0.7, "reasoning": 0.7, "coding": 0.7, "agentic": 0.7},
            "budget": 10.0,
            "task_complexity": 0.5,
            "quality_requirement": 0.7,
            "active_guardrails": ["safety"],
            "risk_probabilities": {"safety": 0.3},
            "n_completed_tasks": 50,
            "current_knowledge": 0.2,
            "base_success": 0.3,
        }
        
        deltas = registry.compute_total_deltas(context)
        
        assert "delta_success" in deltas
        assert "delta_time" in deltas
        assert isinstance(deltas["delta_success"], float)
        assert isinstance(deltas["delta_time"], float)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
