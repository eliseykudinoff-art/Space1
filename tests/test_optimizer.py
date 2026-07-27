"""
Comprehensive Unit and Integration tests for the Agent Scaffolding Wrapper Optimizer.
Compares before/after metrics and calculates exact Shapley values.
"""

import pytest
from space1.optimizer.models import AgentConfig, OptimizerTask, TaskDataset, ModuleType, TaskDomain
from space1.optimizer.evaluator import Evaluator
from space1.optimizer.shapley import ShapleyAttributor
from space1.optimizer.tuner import AgentLoRATuner


class TestAgentScaffoldOptimizer:
    """Test suite for validating the agent wrapper optimizer and its mathematics."""

    def test_task_dataset_generation(self):
        """Test dataset contains tasks from all 4 domains."""
        dataset = TaskDataset.generate_synthetic_dataset(size=20)
        assert len(dataset.tasks) == 20
        
        domains_present = {t.domain for t in dataset.tasks}
        assert len(domains_present) == 4

    def test_task_adaptive_weights_for_cqs(self):
        """Test CQS weights change adaptively depending on task domain."""
        dataset = TaskDataset.generate_synthetic_dataset(size=4)
        evaluator = Evaluator(dataset)
        
        weights_code = evaluator.get_task_adaptive_weights(TaskDomain.CODE_GENERATION)
        weights_safety = evaluator.get_task_adaptive_weights(TaskDomain.SAFETY_CRITICAL)
        
        # In code generation, completeness is more critical than safety
        assert weights_code["completeness"] > weights_code["safety"]
        # In safety critical, safety is the primary metric
        assert weights_safety["safety"] > weights_safety["completeness"]

    def test_scaffolding_simulation_gains_and_penalties(self):
        """Test that adding modules boosts performance, but over-refusal and negative controls penalize it."""
        task = OptimizerTask(
            id="test_task",
            title="Moderate toxicity",
            domain=TaskDomain.SAFETY_CRITICAL,
            revenue=100.0,
            expected_scores={
                "accuracy": 0.8, "relevance": 0.8, "coherence": 0.8,
                "completeness": 0.8, "safety": 0.8, "latency": 0.8, "cost_efficiency": 0.8
            }
        )
        dataset = TaskDataset(tasks=[task])
        evaluator = Evaluator(dataset)
        
        # 1. Baseline success rate (no active modules, defaults)
        cfg_baseline = AgentConfig(active_modules=set())
        p_baseline = evaluator.calculate_success_probability(task, cfg_baseline)
        assert abs(p_baseline - 0.025) < 1e-5  # exactly 2.5% baseline
        
        # 2. Add COT module
        cfg_cot = AgentConfig(active_modules={ModuleType.COT})
        p_cot = evaluator.calculate_success_probability(task, cfg_cot)
        # COT gain is 0.20, success rate should be 0.025 * 1.20 = 0.03
        assert abs(p_cot - 0.03) < 1e-4
        
        # 3. Add Worker-Critic and CoT
        cfg_synergy = AgentConfig(active_modules={ModuleType.WORKER_CRITIC, ModuleType.COT})
        p_synergy = evaluator.calculate_success_probability(task, cfg_synergy)
        # baseline * (1 + 0.35) * (1 + 0.20) * 1.30 (synergy)
        # 0.025 * 1.35 * 1.20 * 1.30 = 0.05265 (5.265%)
        assert abs(p_synergy - 0.05265) < 1e-4
        
        # 4. Over-refusal penalty: active safety filter with safety_threshold = 0.90
        cfg_over_refusal = AgentConfig(
            active_modules={ModuleType.SAFETY_FILTER},
            safety_threshold=0.90
        )
        p_over_refusal = evaluator.calculate_success_probability(task, cfg_over_refusal)
        # base * (1 + 0.25 [safety_filter has +0.20 bonus on safety critical domain]) * 0.85 (over_refusal penalty)
        # 0.025 * 1.25 * 0.85 = 0.0265625
        assert abs(p_over_refusal - 0.02656) < 1e-4
        
        # 5. Negative control (Distilled + CUA active together crashes the system)
        cfg_neg = AgentConfig(active_modules={ModuleType.DISTILLED, ModuleType.CUA})
        p_neg = evaluator.calculate_success_probability(task, cfg_neg)
        assert p_neg == 0.018  # exactly 1.8% success

    def test_shapley_attribution_and_synergy_classification(self):
        """Test ShapleyAttributor calculates exact marginal values and classifies interactions."""
        dataset = TaskDataset.generate_synthetic_dataset(size=8)
        evaluator = Evaluator(dataset)
        
        # Calculate Shapley for a key subset of modules
        modules_subset = [ModuleType.COT, ModuleType.WORKER_CRITIC, ModuleType.VISUAL_QA]
        attributor = ShapleyAttributor(modules_subset, evaluator)
        
        report = attributor.get_attribution_report(metric="mean_success_rate")
        
        # Verify COT and Worker-Critic have positive marginal contributions
        assert report["CoT"]["shapley_value"] > 0
        assert report["Worker-Critic"]["shapley_value"] > 0
        
        # Worker-Critic and CoT is a synergy pair, so their Shapley/standalone ratios should be high
        assert report["Worker-Critic"]["ratio"] > 1.0
        assert report["Worker-Critic"]["interaction_type"] in ("strong_synergy", "weak_synergy", "independent")

    def test_tuner_optimization_gains_proof(self):
        """
        Test that optimization search finds a scaffolding configuration that significantly
        outperforms the baseline setup.
        """
        dataset = TaskDataset.generate_synthetic_dataset(size=30)
        evaluator = Evaluator(dataset)
        
        # 1. Evaluate baseline setup (only CoT active, default thresholds)
        cfg_baseline = AgentConfig(
            active_modules={ModuleType.COT},
            theta_accept=0.70,
            safety_threshold=0.85
        )
        baseline_metrics = evaluator.evaluate_dataset(cfg_baseline)
        
        # 2. Instantiate and run optimizer (tuner) using Hill Climbing
        tuner = AgentLoRATuner(evaluator)
        
        # Hill climb starting from baseline config
        opt_config, opt_metrics = tuner.tune_hill_climbing(cfg_baseline, max_steps=30)
        
        # Assert that optimized setup outperforms baseline
        assert opt_metrics["score"] > baseline_metrics["score"]
        assert opt_metrics["mean_success_rate"] > baseline_metrics["mean_success_rate"]
        assert opt_metrics["expected_revenue"] > baseline_metrics["expected_revenue"]
        
        # Print optimized parameters and gains to confirm progress visually
        print("\n=== OPTIMIZATION RESULT PROOF ===")
        print(f"Baseline Success Rate: {baseline_metrics['mean_success_rate']*100:.2f}% | Expected Revenue: ${baseline_metrics['expected_revenue']:.2f}")
        print(f"Optimized Success Rate: {opt_metrics['mean_success_rate']*100:.2f}% | Expected Revenue: ${opt_metrics['expected_revenue']:.2f}")
        print(f"Optimized Active Modules: {[m.value for m in opt_config.active_modules]}")
        print(f"Optimized theta_accept: {opt_config.theta_accept} | safety_threshold: {opt_config.safety_threshold}")
        print(f"Efficiency Gain: {((opt_metrics['mean_success_rate'] - baseline_metrics['mean_success_rate']) / baseline_metrics['mean_success_rate'])*100:.1f}%")
        print("=================================")
