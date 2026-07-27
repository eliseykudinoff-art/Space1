"""
Evaluator Module. Computes Composite Quality Score (CQS), Market-Mapped Quality Score (MMQS),
and OptimizerTask Success rates based on agentic scaffolding configurations and hyperparameters.
"""

from typing import Dict, Any, Tuple
import math

from .models import AgentConfig, OptimizerTask, TaskDataset, ModuleType, TaskDomain


class Evaluator:
    """
    Evaluator Engine.
    Simulates task performance and calculates CQS, JSS, and MMQS based on empirical RLI research.
    """
    
    def __init__(self, dataset: TaskDataset):
        self.dataset = dataset
        
    def get_task_adaptive_weights(self, domain: TaskDomain) -> Dict[str, float]:
        """Return task-adaptive softmax-like weights for CQS based on OptimizerTask Domain."""
        if domain == TaskDomain.CODE_GENERATION:
            return {
                "accuracy": 0.25,
                "relevance": 0.10,
                "coherence": 0.10,
                "completeness": 0.35,
                "safety": 0.05,
                "latency": 0.05,
                "cost_efficiency": 0.10,
            }
        elif domain == TaskDomain.FACTUAL_QA:
            return {
                "accuracy": 0.45,
                "relevance": 0.20,
                "coherence": 0.10,
                "completeness": 0.15,
                "safety": 0.05,
                "latency": 0.02,
                "cost_efficiency": 0.03,
            }
        elif domain == TaskDomain.MULTI_TURN:
            return {
                "accuracy": 0.15,
                "relevance": 0.15,
                "coherence": 0.35,
                "completeness": 0.20,
                "safety": 0.05,
                "latency": 0.05,
                "cost_efficiency": 0.05,
            }
        else:  # TaskDomain.SAFETY_CRITICAL
            return {
                "accuracy": 0.10,
                "relevance": 0.05,
                "coherence": 0.05,
                "completeness": 0.10,
                "safety": 0.60,
                "latency": 0.05,
                "cost_efficiency": 0.05,
            }

    def evaluate_task_scores(self, task: OptimizerTask, config: AgentConfig) -> Dict[str, float]:
        """
        Simulates individual scores (accuracy, completeness, etc.) for a task
        under a given agent configuration.
        """
        # Base expected scores of the task
        scores = dict(task.expected_scores)
        
        # 1. Module gains on individual scores
        if ModuleType.RAG in config.active_modules:
            scores["accuracy"] = min(1.0, scores["accuracy"] + 0.10)
            scores["relevance"] = min(1.0, scores["relevance"] + 0.15)
            
        if ModuleType.COT in config.active_modules:
            scores["accuracy"] = min(1.0, scores["accuracy"] + 0.12)
            scores["completeness"] = min(1.0, scores["completeness"] + 0.05)
            
        if ModuleType.MEMORY in config.active_modules:
            scores["coherence"] = min(1.0, scores["coherence"] + 0.10)
            
        if ModuleType.WORKER_CRITIC in config.active_modules:
            scores["accuracy"] = min(1.0, scores["accuracy"] + 0.15)
            scores["completeness"] = min(1.0, scores["completeness"] + 0.10)
            
        if ModuleType.VISUAL_QA in config.active_modules:
            scores["accuracy"] = min(1.0, scores["accuracy"] + 0.08)
            
        if ModuleType.SAFETY_FILTER in config.active_modules:
            scores["safety"] = min(1.0, scores["safety"] + 0.15)
            
            # High safety threshold causing over-refusal penalty (matching research finding!)
            if config.safety_threshold > 0.80:
                scores["completeness"] = max(0.1, scores["completeness"] - 0.15)
                scores["accuracy"] = max(0.1, scores["accuracy"] - 0.05)
                
        # Confidence threshold penalties
        if config.theta_accept < 0.50:
            # Too careless -> lower accuracy and completeness
            scores["accuracy"] = max(0.1, scores["accuracy"] - 0.10)
            scores["completeness"] = max(0.1, scores["completeness"] - 0.10)
            
        # Cost and Latency penalties based on active module count
        num_modules = len(config.active_modules)
        scores["latency"] = max(0.1, scores["latency"] - 0.05 * num_modules)
        scores["cost_efficiency"] = max(0.1, scores["cost_efficiency"] - 0.06 * num_modules)
        
        return scores

    def compute_cqs(self, task: OptimizerTask, config: AgentConfig) -> float:
        """Compute the task-adaptive Composite Quality Score (CQS)."""
        scores = self.evaluate_task_scores(task, config)
        weights = self.get_task_adaptive_weights(task.domain)
        
        cqs = sum(weights[k] * scores[k] for k in weights)
        return float(cqs)

    def calculate_success_probability(self, task: OptimizerTask, config: AgentConfig) -> float:
        """
        Calculates the probability of task success (Market-Mapped Quality Score model)
        combining baseline, active module gains, synergy effects, hyperparameter tunings,
        negative controls, and diminishing returns.
        """
        # Baseline success (2.5%, matching Manus on RLI)
        p_success = 0.025
        
        # 1. Check Negative Control (Distilled + CUA together destroys the agent)
        if ModuleType.DISTILLED in config.active_modules and ModuleType.CUA in config.active_modules:
            return 0.018  # Near-zero 1.8% success
            
        # 2. Sum up active module gains
        module_gains = {
            ModuleType.RAG: 0.15,
            ModuleType.COT: 0.20,
            ModuleType.MEMORY: 0.12,
            ModuleType.WORKER_CRITIC: 0.35,
            ModuleType.VISUAL_QA: 0.18,
            ModuleType.CODEACT: 0.15,
            ModuleType.SKILL_LIBRARY: 0.30,
            ModuleType.WORKFLOW_PRIOR: 0.15,
            ModuleType.SAFETY_FILTER: 0.05,
            ModuleType.DISTILLED: 0.02,
            ModuleType.CUA: 0.02,
        }
        
        # Domain-specific modifications to gains
        if task.domain == TaskDomain.CODE_GENERATION:
            module_gains[ModuleType.CODEACT] += 0.10
            module_gains[ModuleType.SKILL_LIBRARY] += 0.10
        elif task.domain == TaskDomain.FACTUAL_QA:
            module_gains[ModuleType.RAG] += 0.15
        elif task.domain == TaskDomain.MULTI_TURN:
            module_gains[ModuleType.MEMORY] += 0.10
        elif task.domain == TaskDomain.SAFETY_CRITICAL:
            module_gains[ModuleType.SAFETY_FILTER] += 0.20
            
        # Cumulative gains multiplier
        gains_multiplier = 1.0
        for m in config.active_modules:
            gain = module_gains.get(m, 0.0)
            gains_multiplier *= (1.0 + gain)
            
        # Apply gains to baseline
        p_success *= gains_multiplier
        
        # 3. Apply Synergies (+30% bonus per synergy pair)
        synergies = [
            (ModuleType.WORKER_CRITIC, ModuleType.VISUAL_QA),
            (ModuleType.WORKER_CRITIC, ModuleType.COT),
            (ModuleType.RAG, ModuleType.MEMORY),
            (ModuleType.SKILL_LIBRARY, ModuleType.MEMORY)
        ]
        for m1, m2 in synergies:
            if m1 in config.active_modules and m2 in config.active_modules:
                p_success *= 1.30
                
        # 4. Apply Hyperparameter tuning impacts
        # Safety Over-refusal: If safety is active and threshold is too strict (>0.80), we penalize success
        if ModuleType.SAFETY_FILTER in config.active_modules and config.safety_threshold > 0.80:
            p_success *= 0.85  # 15% reduction due to over-refusal
            
        # Confidence threshold penalties:
        # If theta_accept is too low (< 0.5), we accept bad plans
        if config.theta_accept < 0.50:
            p_success *= 0.88
        # If theta_accept is too high (> 0.85), agent declines/escalates too much
        elif config.theta_accept > 0.85:
            p_success *= 0.90
            
        # 5. Apply Diminishing Returns penalty (if more than 6 modules are active)
        n_active = len(config.active_modules)
        if n_active > 6:
            diminishing_factor = 1.0 - 0.04 * (n_active - 6)
            p_success *= max(0.5, diminishing_factor)
            
        # Bound probability in [0.0, 0.95]
        return max(0.01, min(0.95, p_success))

    def evaluate_dataset(self, config: AgentConfig) -> Dict[str, float]:
        """
        Evaluate the entire dataset under a given AgentConfig.
        Returns aggregate metrics:
        - mean_cqs: Average CQS across all tasks
        - mean_success_rate: Average success probability across tasks (MMQS proxy)
        - expected_revenue: Sum of (success_prob * task_revenue)
        - effective_jss: Upwork JSS proxy score [0.0, 100.0]
        - score: Unified objective metric (e.g., success_rate * 100)
        """
        total_cqs = 0.0
        total_success_prob = 0.0
        total_revenue = 0.0
        
        for task in self.dataset.tasks:
            cqs = self.compute_cqs(task, config)
            p_success = self.calculate_success_probability(task, config)
            
            total_cqs += cqs
            total_success_prob += p_success
            total_revenue += p_success * task.revenue
            
        n = len(self.dataset.tasks) if self.dataset.tasks else 1
        mean_cqs = total_cqs / n
        mean_success_rate = total_success_prob / n
        
        # JSS formula proxy: base JSS depends heavily on success rate
        # 100% success -> 100 JSS. 15% success -> ~80 JSS. Baseline (2.5%) -> ~50 JSS.
        effective_jss = 50.0 + 50.0 * (mean_success_rate / 0.20)
        effective_jss = min(100.0, max(10.0, effective_jss))
        
        # Unified score used for the optimizer
        # Combining success rate and CQS
        score = mean_success_rate * 100.0 + mean_cqs * 10.0
        
        return {
            "mean_cqs": mean_cqs,
            "mean_success_rate": mean_success_rate,
            "expected_revenue": total_revenue,
            "effective_jss": effective_jss,
            "score": score,
        }
