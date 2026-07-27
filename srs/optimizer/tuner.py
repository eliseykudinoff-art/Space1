"""
AgentLoRATuner Module. Optimizes the agent scaffolding configuration (active modules and thresholds)
to maximize expected success, CQS, JSS, and overall revenue on the task dataset.
"""

import random
from typing import Dict, Any, Tuple, List, Set

from .models import AgentConfig, ModuleType
from .evaluator import Evaluator


class AgentLoRATuner:
    """
    AgentLoRATuner.
    Optimizes the active modules list and continuous parameters (safety_threshold, theta_accept)
    using optimization algorithms (Random Search, Hill Climbing).
    """
    
    def __init__(self, evaluator: Evaluator):
        self.evaluator = evaluator
        
    def tune_random_search(self, num_iterations: int = 100) -> Tuple[AgentConfig, Dict[str, float]]:
        """
        Optimize using Random Search.
        Explores the binary and continuous parameter space.
        """
        best_config = None
        best_metrics = {}
        best_score = -1.0
        
        # Modules pool to sample from (exclude distilled & cua default active unless specifically chosen)
        pool = [
            ModuleType.RAG, ModuleType.COT, ModuleType.MEMORY, ModuleType.WORKER_CRITIC,
            ModuleType.VISUAL_QA, ModuleType.CODEACT, ModuleType.SKILL_LIBRARY,
            ModuleType.WORKFLOW_PRIOR, ModuleType.SAFETY_FILTER
        ]
        
        for _ in range(num_iterations):
            # Sample active modules
            num_modules = random.randint(1, len(pool))
            active = set(random.sample(pool, num_modules))
            
            # Sample continuous parameters
            theta_accept = round(random.uniform(0.5, 0.85), 2)
            safety_threshold = round(random.uniform(0.6, 0.88), 2)
            
            config = AgentConfig(
                active_modules=active,
                theta_accept=theta_accept,
                safety_threshold=safety_threshold
            )
            
            metrics = self.evaluator.evaluate_dataset(config)
            score = metrics["score"]
            
            if score > best_score:
                best_score = score
                best_config = config
                best_metrics = metrics
                
        return best_config, best_metrics

    def tune_hill_climbing(self, start_config: AgentConfig, max_steps: int = 50) -> Tuple[AgentConfig, Dict[str, float]]:
        """
        Optimize using Hill Climbing.
        Starts at a configuration, then greedily wanders towards better adjacent states.
        """
        current_config = start_config.copy()
        current_metrics = self.evaluator.evaluate_dataset(current_config)
        current_score = current_metrics["score"]
        
        pool = [
            ModuleType.RAG, ModuleType.COT, ModuleType.MEMORY, ModuleType.WORKER_CRITIC,
            ModuleType.VISUAL_QA, ModuleType.CODEACT, ModuleType.SKILL_LIBRARY,
            ModuleType.WORKFLOW_PRIOR, ModuleType.SAFETY_FILTER
        ]
        
        improved = True
        step = 0
        
        while improved and step < max_steps:
            improved = False
            step += 1
            
            neighbors: List[AgentConfig] = []
            
            # Neighbor category 1: toggle a module on/off
            for m in pool:
                n_cfg = current_config.copy()
                if m in n_cfg.active_modules:
                    n_cfg.active_modules.remove(m)
                else:
                    n_cfg.active_modules.add(m)
                neighbors.append(n_cfg)
                
            # Neighbor category 2: fine-tune theta_accept slightly (+/- 0.05)
            for diff in [-0.05, 0.05]:
                n_cfg = current_config.copy()
                n_cfg.theta_accept = round(max(0.3, min(0.9, n_cfg.theta_accept + diff)), 2)
                neighbors.append(n_cfg)
                
            # Neighbor category 3: fine-tune safety_threshold slightly (+/- 0.05)
            for diff in [-0.05, 0.05]:
                n_cfg = current_config.copy()
                n_cfg.safety_threshold = round(max(0.5, min(0.95, n_cfg.safety_threshold + diff)), 2)
                neighbors.append(n_cfg)
                
            # Evaluate all neighbors and select the best
            best_neighbor_config = current_config
            best_neighbor_score = current_score
            best_neighbor_metrics = current_metrics
            
            for neighbor in neighbors:
                metrics = self.evaluator.evaluate_dataset(neighbor)
                score = metrics["score"]
                if score > best_neighbor_score:
                    best_neighbor_score = score
                    best_neighbor_config = neighbor
                    best_neighbor_metrics = metrics
                    
            if best_neighbor_score > current_score:
                current_config = best_neighbor_config
                current_score = best_neighbor_score
                current_metrics = best_neighbor_metrics
                improved = True
                
        return current_config, current_metrics
