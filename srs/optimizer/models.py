"""
Models representing Agent Configurations, Tasks, and Dataset structures for scaffolding optimization.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Set, List, Any


class ModuleType(Enum):
    """Available agent scaffolding modules (wrapper components)."""
    RAG = "RAG"
    COT = "CoT"
    MEMORY = "Memory"
    WORKER_CRITIC = "Worker-Critic"
    VISUAL_QA = "Visual-QA"
    CODEACT = "CodeAct"
    SKILL_LIBRARY = "Skill-Library"
    WORKFLOW_PRIOR = "Workflow-Prior"
    SAFETY_FILTER = "Safety-Filter"
    DISTILLED = "Distilled"
    CUA = "CUA"


class TaskDomain(Enum):
    """Domains representing diverse task types."""
    CODE_GENERATION = "code_generation"
    FACTUAL_QA = "factual_qa"
    MULTI_TURN = "multi_turn"
    SAFETY_CRITICAL = "safety_critical"


@dataclass
class AgentConfig:
    """
    Agent Configuration (Scaffolding Wrapper Parameters).
    Acts as the 'LoRA/QLoRA' of the LLM agent wrapper.
    """
    # Active modules (binary indicator parameters)
    active_modules: Set[ModuleType] = field(default_factory=lambda: {
        ModuleType.COT,
    })
    
    # Continuous hyperparameters/thresholds
    theta_accept: float = 0.70  # [0.0, 1.0] confidence boundary to accept plan
    theta_ask: float = 0.40     # [0.0, 1.0] confidence boundary to clarify/ask
    safety_threshold: float = 0.85 # [0.0, 1.0] sensitivity of safety filter
    risk_aversion: float = 0.50 # weight on risk penalty
    
    def copy(self) -> 'AgentConfig':
        """Deep copy representation of config."""
        return AgentConfig(
            active_modules=set(self.active_modules),
            theta_accept=self.theta_accept,
            theta_ask=self.theta_ask,
            safety_threshold=self.safety_threshold,
            risk_aversion=self.risk_aversion,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "active_modules": [m.value for m in self.active_modules],
            "theta_accept": self.theta_accept,
            "theta_ask": self.theta_ask,
            "safety_threshold": self.safety_threshold,
            "risk_aversion": self.risk_aversion,
        }


@dataclass
class OptimizerTask:
    """Represents a single evaluation task in the training or testing dataset."""
    id: str
    title: str
    domain: TaskDomain
    description: str = ""
    revenue: float = 100.0
    complexity: float = 0.5  # [0.0, 1.0]
    expected_scores: Dict[str, float] = field(default_factory=lambda: {
        "accuracy": 0.8,
        "relevance": 0.8,
        "coherence": 0.8,
        "completeness": 0.8,
        "safety": 0.95,
        "latency": 0.5,
        "cost_efficiency": 0.6,
    })


@dataclass
class TaskDataset:
    """A collection of tasks used for optimization and benchmark evaluations."""
    tasks: List[OptimizerTask] = field(default_factory=list)

    @classmethod
    def generate_synthetic_dataset(cls, size: int = 40) -> 'TaskDataset':
        """
        Generate a diverse synthetic benchmark dataset simulating Remote Labor Index (RLI) and
        Upwork JSS contract distributions across 4 domains.
        """
        tasks = []
        domains = list(TaskDomain)
        for i in range(size):
            domain = domains[i % len(domains)]
            task_id = f"task_{i:03d}"
            
            # Base variables depending on domain
            if domain == TaskDomain.CODE_GENERATION:
                title = f"Implement algorithmic function #{i}"
                complexity = 0.6 + 0.3 * (i % 3) / 2.0
                revenue = 150.0 + 100.0 * (i % 4)
                expected = {
                    "accuracy": 0.75, "relevance": 0.7, "coherence": 0.6,
                    "completeness": 0.8, "safety": 0.95, "latency": 0.4, "cost_efficiency": 0.5
                }
            elif domain == TaskDomain.FACTUAL_QA:
                title = f"Extract structured facts from legal document #{i}"
                complexity = 0.4 + 0.4 * (i % 3) / 2.0
                revenue = 50.0 + 50.0 * (i % 4)
                expected = {
                    "accuracy": 0.9, "relevance": 0.85, "coherence": 0.8,
                    "completeness": 0.7, "safety": 0.95, "latency": 0.8, "cost_efficiency": 0.7
                }
            elif domain == TaskDomain.MULTI_TURN:
                title = f"Support multi-turn negotiation scenario #{i}"
                complexity = 0.5 + 0.3 * (i % 3) / 2.0
                revenue = 120.0 + 80.0 * (i % 4)
                expected = {
                    "accuracy": 0.7, "relevance": 0.8, "coherence": 0.85,
                    "completeness": 0.75, "safety": 0.95, "latency": 0.6, "cost_efficiency": 0.6
                }
            else:  # SAFETY_CRITICAL
                title = f"Filter and moderate toxic logs batch #{i}"
                complexity = 0.7 + 0.25 * (i % 3) / 2.0
                revenue = 200.0 + 150.0 * (i % 4)
                expected = {
                    "accuracy": 0.8, "relevance": 0.75, "coherence": 0.7,
                    "completeness": 0.85, "safety": 0.99, "latency": 0.5, "cost_efficiency": 0.5
                }
                
            tasks.append(OptimizerTask(
                id=task_id,
                title=title,
                domain=domain,
                revenue=revenue,
                complexity=complexity,
                expected_scores=expected
            ))
            
        return cls(tasks=tasks)
