"""
AIOS Context Manager Kernel Module.

Reference: 04_ARCHITECTURE.md (Part II / Part IV.2).
Manages task classification and renders the structured StatusBlock context.
"""

from typing import List, Dict, Any, Optional
from ..models.task import Task, TaskComplexityClassifier


class AIOSContextManager:
    """
    AIOSContextManager.
    Renders structured execution context (StatusBlock) and handles classification.
    """
    
    def __init__(self):
        self._classifier = TaskComplexityClassifier()
        
    def classify(self, task: Task) -> Dict[str, Any]:
        """Classify task complexity and recommend routing decision."""
        comp, entropy, routing = self._classifier.predict_complexity(task.title, task.description)
        return {
            "complexity_score": comp,
            "entropy": entropy,
            "routing_decision": routing,
        }
        
    def render_status_block(
        self,
        homeostasis_h: float,
        deviations: List[Dict[str, Any]],
        remaining_plan: List[str],
        memory_snippets: List[str],
        max_length: int = 1000
    ) -> str:
        """
        Pure formatting function. Compiles active state into a structured StatusBlock context string.
        Does NOT call LLMs internally.
        """
        lines = [
            "=== STATUS BLOCK ===",
            f"Homeostasis Index H: {homeostasis_h:.2f}",
        ]
        
        if deviations:
            lines.append("Active Deviations:")
            for dev in deviations:
                lines.append(f"  - {dev.get('metric', 'unknown')}: dev={dev.get('val', 0.0):.2f}")
                
        if remaining_plan:
            lines.append("Remaining Action Plan:")
            for step in remaining_plan:
                lines.append(f"  -> {step}")
                
        if memory_snippets:
            lines.append("Relevant Experience Snippets:")
            for snippet in memory_snippets:
                lines.append(f"  * {snippet}")
                
        lines.append("====================")
        status_block = "\n".join(lines)
        
        # Enforce max length constraint
        if len(status_block) > max_length:
            status_block = status_block[:max_length - 4] + "...\n"
            
        return status_block
