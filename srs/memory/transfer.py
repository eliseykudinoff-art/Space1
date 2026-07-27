"""
Transfer Learning (G22)

Computes the success rate adjustments by leveraging past experiences
transferred to target tasks based on task semantic/profile similarity.

Formula:
    ΔS_transfer = γ_transfer × TaskSimilarity × K_past
"""

from typing import Any, Dict, List, Optional
from ..memory.core import StrategicMemory, StrategicExperience
from ..models.task import Task


class TransferLearning:
    """
    TransferLearning (G22).
    
    Responsible for measuring similarities with previously executed tasks (from StrategicMemory)
    and calculating dynamic success rate increments due to transferable knowledge.
    """
    
    def __init__(self, memory: StrategicMemory, gamma_transfer: float = 0.15):
        self.memory = memory
        self.gamma_transfer = gamma_transfer
        
    def calculate_similarity(self, task_a: Task, task_b_experience: StrategicExperience) -> float:
        """
        Compute a simple keyword-overlap similarity between a target Task and strategic memory log.
        
        Returns:
            Similarity float in [0.0, 1.0]
        """
        title_a = task_a.title.lower().split()
        title_b = task_b_experience.title.lower().split()
        
        if not title_a or not title_b:
            return 0.0
            
        common = set(title_a).intersection(set(title_b))
        
        # Jaccard index similarity
        total_unique = set(title_a).union(set(title_b))
        return len(common) / len(total_unique)
        
    def calculate_transfer_delta(self, target_task: Task, current_knowledge: float = 0.5) -> float:
        """
        Calculate delta success rate added due to transfer learning of past matching experiences.
        
        Formula:
            ΔS_transfer = γ_transfer × TaskSimilarity × K_past
        """
        experiences = self.memory.get_experiences()
        if not experiences:
            return 0.0
            
        # Find experience with maximum similarity to target task
        max_sim = 0.0
        best_exp: Optional[StrategicExperience] = None
        
        for exp in experiences:
            if exp.status == "completed":  # Transfer only from successfully completed projects
                sim = self.calculate_similarity(target_task, exp)
                if sim > max_sim:
                    max_sim = sim
                    best_exp = exp
                    
        if max_sim <= 0.0:
            return 0.0
            
        # Knowledge factor matches the best experience achieved quality
        k_past = best_exp.quality if best_exp else current_knowledge
        
        delta_s = self.gamma_transfer * max_sim * k_past
        return min(0.3, delta_s)  # cap learning boost at +30% success rate
