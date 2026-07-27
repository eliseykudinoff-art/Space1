"""
FactorRegistry — Реестр факторов способностей (x₁-x₁₇)

Full Factors (G9):
- x₁: LLM Capability
- x₂: Prompt Engineering
- x₃: Episodic Memory Retrieval
- x₄: Memory Consolidation
- x₅: Multi-Agent Collaboration
- x₆: Self-Correction Loops
- x₇: Tool Calling/MCP
- x₈: Cost Tiering
- x₉: Grounding Verification
- x₁₀: Fine-tuning Adaptation
- x₁₁: Context Window management
- x₁₂: Guardrails & Safety
- x₁₃: Test-time Compute (scaling)
- x₁₄: Agentic Design Patterns
- x₁₅: Self-Evaluation Quality
- x₁₆: Continual Learning
- x₁₇: Inference Optimization

Reference: COMPARATIVE_ANALYSIS.md
           DEVELOPMENT_PLAN.md - G9
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class FactorID(Enum):
    """Enum всех 17 факторов."""
    X1_LLM = "x1"
    X2_PROMPT = "x2"
    X3_MEMORY = "x3"
    X4_MEMORY_SYSTEM = "x4"
    X5_MULTI_AGENT = "x5"
    X6_SELF_CORRECTION = "x6"
    X7_TOOL_CALLING = "x7"
    X8_COST_TIERING = "x8"
    X9_GROUNDING = "x9"
    X10_FINE_TUNING = "x10"
    X11_CONTEXT_MANAGEMENT = "x11"
    X12_GUARDRAILS = "x12"
    X13_TEST_TIME_COMPUTE = "x13"
    X14_DESIGN_PATTERNS = "x14"
    X15_EVALUATION = "x15"
    X16_CONTINUAL_LEARNING = "x16"
    X17_INFERENCE_OPT = "x17"


@dataclass
class FactorResult:
    """Результат вычисления фактора."""
    factor_id: str
    value: float
    delta_success: float  # Влияние на Success Rate
    delta_time: float    # Влияние на Time
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseFactor(ABC):
    """Базовый класс для всех факторов."""
    
    def __init__(self, factor_id: FactorID, enabled: bool = True):
        self.factor_id = factor_id
        self.enabled = enabled
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable название фактора."""
        pass
    
    @abstractmethod
    def compute(self, context: Dict[str, Any]) -> FactorResult:
        """
        Вычислить влияние фактора.
        
        Args:
            context: Контекст с данными для вычисления
            
        Returns:
            FactorResult с влиянием на S и T
        """
        pass
    
    @property
    def priority(self) -> str:
        """Приоритет фактора: HIGH, MEDIUM, LOW."""
        return "MEDIUM"


# =============================================================================
# Factors Implementation (1-17)
# =============================================================================

class LLMFactor(BaseFactor):
    """x₁: LLM Capability"""
    
    WEIGHTS = {
        "quality": 0.25,
        "reasoning": 0.30,
        "coding": 0.25,
        "agentic": 0.20,
    }
    
    def __init__(self):
        super().__init__(FactorID.X1_LLM)
        
    @property
    def name(self) -> str:
        return "LLM Capability"
        
    @property
    def priority(self) -> str:
        return "HIGH"
        
    def compute(self, context: Dict[str, Any]) -> FactorResult:
        benchmarks = context.get("benchmarks", {"quality": 0.7, "reasoning": 0.7, "coding": 0.7, "agentic": 0.7})
        c_llm = sum(self.WEIGHTS[k] * benchmarks.get(k, 0.7) for k in self.WEIGHTS)
        lambda_t = context.get("lambda_t", 5.0)
        tau_t = context.get("tau_t", 0.5)
        
        exp_term = -lambda_t * (c_llm - tau_t)
        s_m = c_llm / (1 + (2.71828 ** exp_term))
        delta_s = s_m - 0.3
        
        return FactorResult(
            factor_id=self.factor_id.value,
            value=c_llm,
            delta_success=delta_s,
            delta_time=0.0,
            metadata={"s_m": s_m, "benchmarks": benchmarks}
        )


class PromptFactor(BaseFactor):
    """x₂: Prompt Engineering"""
    
    def __init__(self):
        super().__init__(FactorID.X2_PROMPT)
        
    @property
    def name(self) -> str:
        return "Prompt Engineering"
        
    def compute(self, context: Dict[str, Any]) -> FactorResult:
        # Prompt optimization adds small positive success and reduces execution time slightly
        return FactorResult(
            factor_id=self.factor_id.value,
            value=0.8,
            delta_success=0.04,
            delta_time=-0.05
        )


class MemoryRetrievalFactor(BaseFactor):
    """x₃: Episodic Memory Retrieval"""
    
    def __init__(self):
        super().__init__(FactorID.X3_MEMORY)
        
    @property
    def name(self) -> str:
        return "Episodic Memory"
        
    def compute(self, context: Dict[str, Any]) -> FactorResult:
        # Recalling similar situations improves execution success
        return FactorResult(
            factor_id=self.factor_id.value,
            value=0.75,
            delta_success=0.05,
            delta_time=-0.02
        )


class MemorySystemFactor(BaseFactor):
    """x₄: Memory Consolidation System"""
    
    def __init__(self):
        super().__init__(FactorID.X4_MEMORY_SYSTEM)
        
    @property
    def name(self) -> str:
        return "Memory System"
        
    def compute(self, context: Dict[str, Any]) -> FactorResult:
        return FactorResult(
            factor_id=self.factor_id.value,
            value=0.7,
            delta_success=0.03,
            delta_time=0.01
        )


class MultiAgentFactor(BaseFactor):
    """x₅: Multi-Agent Collaboration"""
    
    def __init__(self):
        super().__init__(FactorID.X5_MULTI_AGENT)
        
    @property
    def name(self) -> str:
        return "Multi-Agent Collaboration"
        
    def compute(self, context: Dict[str, Any]) -> FactorResult:
        # Delegation of workload adds success but slightly adds communication time overhead
        return FactorResult(
            factor_id=self.factor_id.value,
            value=0.85,
            delta_success=0.08,
            delta_time=0.04
        )


class SelfCorrectionFactor(BaseFactor):
    """x₆: Self-Correction Loops"""
    
    def __init__(self):
        super().__init__(FactorID.X6_SELF_CORRECTION)
        
    @property
    def name(self) -> str:
        return "Self-Correction"
        
    def compute(self, context: Dict[str, Any]) -> FactorResult:
        # Multi-attempt loops drastically increase success but add time spent
        return FactorResult(
            factor_id=self.factor_id.value,
            value=0.9,
            delta_success=0.12,
            delta_time=0.15
        )


class ToolCallingFactor(BaseFactor):
    """x₇: Tool Calling/MCP"""
    
    def __init__(self):
        super().__init__(FactorID.X7_TOOL_CALLING)
        
    @property
    def name(self) -> str:
        return "Tool Calling"
        
    def compute(self, context: Dict[str, Any]) -> FactorResult:
        return FactorResult(
            factor_id=self.factor_id.value,
            value=0.8,
            delta_success=0.06,
            delta_time=-0.04
        )


class CostTieringFactor(BaseFactor):
    """x₈: Cost Tiering"""
    
    COSTS = {"ollama": 0.0, "free_api": 0.0, "paid_api": 2.0}
    QUALITY = {"ollama": 0.6, "free_api": 0.75, "paid_api": 0.95}
    
    def __init__(self):
        super().__init__(FactorID.X8_COST_TIERING)
        
    @property
    def name(self) -> str:
        return "Cost Tiering"
        
    @property
    def priority(self) -> str:
        return "HIGH"
        
    def compute(self, context: Dict[str, Any]) -> FactorResult:
        budget = context.get("budget", 100.0)
        task_complexity = context.get("task_complexity", 0.5)
        quality_requirement = context.get("quality_requirement", 0.7)
        
        if budget < 1.0:
            selected_tier = "ollama"
        elif budget < 10.0 and quality_requirement < 0.8:
            selected_tier = "free_api"
        else:
            selected_tier = "paid_api"
            
        quality = self.QUALITY[selected_tier]
        cost = self.COSTS[selected_tier]
        delta_s = (quality - 0.7) * 0.2
        delta_t = -0.1 * quality
        
        return FactorResult(
            factor_id=self.factor_id.value,
            value=quality,
            delta_success=delta_s,
            delta_time=delta_t,
            metadata={"selected_tier": selected_tier, "cost_per_1m": cost, "budget": budget}
        )


class GroundingFactor(BaseFactor):
    """x₉: Grounding Verification"""
    
    def __init__(self):
        super().__init__(FactorID.X9_GROUNDING)
        
    @property
    def name(self) -> str:
        return "Grounding Verification"
        
    def compute(self, context: Dict[str, Any]) -> FactorResult:
        return FactorResult(
            factor_id=self.factor_id.value,
            value=0.75,
            delta_success=0.05,
            delta_time=0.02
        )


class FineTuningFactor(BaseFactor):
    """x₁₀: Fine-tuning Adaptation"""
    
    def __init__(self):
        super().__init__(FactorID.X10_FINE_TUNING)
        
    @property
    def name(self) -> str:
        return "Fine-tuning"
        
    def compute(self, context: Dict[str, Any]) -> FactorResult:
        return FactorResult(
            factor_id=self.factor_id.value,
            value=0.82,
            delta_success=0.07,
            delta_time=-0.03
        )


class ContextManagementFactor(BaseFactor):
    """x₁₁: Context Management"""
    
    def __init__(self):
        super().__init__(FactorID.X11_CONTEXT_MANAGEMENT)
        
    @property
    def name(self) -> str:
        return "Context Management"
        
    def compute(self, context: Dict[str, Any]) -> FactorResult:
        return FactorResult(
            factor_id=self.factor_id.value,
            value=0.78,
            delta_success=0.04,
            delta_time=-0.01
        )


class GuardrailsFactor(BaseFactor):
    """x₁₂: Guardrails & Safety"""
    
    BASE_BETA = 0.05
    
    def __init__(self):
        super().__init__(FactorID.X12_GUARDRAILS)
        
    @property
    def name(self) -> str:
        return "Guardrails"
        
    @property
    def priority(self) -> str:
        return "HIGH"
        
    def compute(self, context: Dict[str, Any]) -> FactorResult:
        active_guardrails = context.get("active_guardrails", [])
        risk_probabilities = context.get("risk_probabilities", {})
        
        g_eff = 1.0
        for risk_name, p_risk in risk_probabilities.items():
            g_i = 1.0 if risk_name in active_guardrails else 0.0
            g_eff *= (1 - p_risk * (1 - g_i))
            
        delta_s = self.BASE_BETA * g_eff
        delta_t = 0.02 * len(active_guardrails)
        
        return FactorResult(
            factor_id=self.factor_id.value,
            value=g_eff,
            delta_success=delta_s,
            delta_time=delta_t,
            metadata={"active_count": len(active_guardrails), "g_eff": g_eff}
        )


class TestTimeComputeFactor(BaseFactor):
    """x₁₃: Test-time Compute"""
    
    def __init__(self):
        super().__init__(FactorID.X13_TEST_TIME_COMPUTE)
        
    @property
    def name(self) -> str:
        return "Test-time Compute"
        
    def compute(self, context: Dict[str, Any]) -> FactorResult:
        return FactorResult(
            factor_id=self.factor_id.value,
            value=0.85,
            delta_success=0.10,
            delta_time=0.20
        )


class DesignPatternsFactor(BaseFactor):
    """x₁₄: Agentic Design Patterns"""
    
    def __init__(self):
        super().__init__(FactorID.X14_DESIGN_PATTERNS)
        
    @property
    def name(self) -> str:
        return "Design Patterns"
        
    def compute(self, context: Dict[str, Any]) -> FactorResult:
        return FactorResult(
            factor_id=self.factor_id.value,
            value=0.8,
            delta_success=0.06,
            delta_time=-0.02
        )


class EvaluationFactor(BaseFactor):
    """x₁₅: Self-Evaluation Quality"""
    
    def __init__(self):
        super().__init__(FactorID.X15_EVALUATION)
        
    @property
    def name(self) -> str:
        return "Self-Evaluation"
        
    def compute(self, context: Dict[str, Any]) -> FactorResult:
        return FactorResult(
            factor_id=self.factor_id.value,
            value=0.74,
            delta_success=0.04,
            delta_time=0.01
        )


class ContinualLearningFactor(BaseFactor):
    """x₁₆: Continual Learning"""
    
    LEARNING_RATE = 0.01
    KNOWLEDGE_DECAY = 0.05
    GAMMA_CL = 0.12
    
    def __init__(self):
        super().__init__(FactorID.X16_CONTINUAL_LEARNING)
        
    @property
    def name(self) -> str:
        return "Continual Learning"
        
    @property
    def priority(self) -> str:
        return "MEDIUM"
        
    def compute(self, context: Dict[str, Any]) -> FactorResult:
        n_tasks = context.get("n_completed_tasks", 0)
        current_knowledge = context.get("current_knowledge", 0.0)
        base_success = context.get("base_success", 0.3)
        
        lambda_cl = 0.01
        k_cl = 1.0 - (2.71828 ** (-lambda_cl * n_tasks))
        delta_s = self.GAMMA_CL * k_cl * base_success
        delta_t = 0.01 * n_tasks * 0.001
        
        return FactorResult(
            factor_id=self.factor_id.value,
            value=k_cl,
            delta_success=delta_s,
            delta_time=delta_t,
            metadata={"n_tasks": n_tasks, "k_cl": k_cl, "current_knowledge": current_knowledge}
        )


class InferenceOptFactor(BaseFactor):
    """x₁₇: Inference Optimization"""
    
    def __init__(self):
        super().__init__(FactorID.X17_INFERENCE_OPT)
        
    @property
    def name(self) -> str:
        return "Inference Optimization"
        
    def compute(self, context: Dict[str, Any]) -> FactorResult:
        return FactorResult(
            factor_id=self.factor_id.value,
            value=0.7,
            delta_success=0.01,
            delta_time=-0.08
        )


# =============================================================================
# FactorRegistry
# =============================================================================

class FactorRegistry:
    """
    Registry для всех факторов способностей.
    
    Usage:
        registry = FactorRegistry()
        registry.register(LLMFactor())
        registry.register(CostTieringFactor())
        
        results = registry.compute_all(context)
        total_delta_s = sum(r.delta_success for r in results.values())
    """
    
    def __init__(self):
        self._factors: Dict[FactorID, BaseFactor] = {}
        self._enabled: Dict[FactorID, bool] = {}
    
    def register(self, factor: BaseFactor) -> None:
        """Register a factor."""
        self._factors[factor.factor_id] = factor
        self._enabled[factor.factor_id] = factor.enabled
    
    def unregister(self, factor_id: FactorID) -> bool:
        """Unregister a factor."""
        if factor_id in self._factors:
            del self._factors[factor_id]
            del self._enabled[factor_id]
            return True
        return False
    
    def enable(self, factor_id: FactorID) -> None:
        """Enable a factor."""
        self._enabled[factor_id] = True
    
    def disable(self, factor_id: FactorID) -> None:
        """Disable a factor."""
        self._enabled[factor_id] = False
    
    def get(self, factor_id: FactorID) -> Optional[BaseFactor]:
        """Get a factor by ID."""
        return self._factors.get(factor_id)
    
    def get_all(self) -> List[BaseFactor]:
        """Get all registered factors."""
        return list(self._factors.values())
    
    def get_enabled(self) -> List[BaseFactor]:
        """Get all enabled factors."""
        return [f for f in self._factors.values() if self._enabled.get(f.factor_id, False)]
    
    def compute_all(self, context: Dict[str, Any]) -> Dict[str, FactorResult]:
        """
        Compute all enabled factors.
        
        Returns:
            Dict[factor_id, FactorResult]
        """
        results = {}
        for factor in self.get_enabled():
            results[factor.factor_id.value] = factor.compute(context)
        return results
    
    def compute_total_deltas(self, context: Dict[str, Any]) -> Dict[str, float]:
        """
        Compute total deltas from all factors.
        
        Returns:
            {"delta_success": float, "delta_time": float}
        """
        results = self.compute_all(context)
        return {
            "delta_success": sum(r.delta_success for r in results.values()),
            "delta_time": sum(r.delta_time for r in results.values()),
        }


# =============================================================================
# Default Registry Factory
# =============================================================================

def create_mvp_registry() -> FactorRegistry:
    """Create FactorRegistry with MVP factors."""
    registry = FactorRegistry()
    registry.register(LLMFactor())
    registry.register(CostTieringFactor())
    registry.register(GuardrailsFactor())
    registry.register(ContinualLearningFactor())
    return registry


def create_full_registry() -> FactorRegistry:
    """Create FactorRegistry with all 17 factors enabled."""
    registry = FactorRegistry()
    registry.register(LLMFactor())
    registry.register(PromptFactor())
    registry.register(MemoryRetrievalFactor())
    registry.register(MemorySystemFactor())
    registry.register(MultiAgentFactor())
    registry.register(SelfCorrectionFactor())
    registry.register(ToolCallingFactor())
    registry.register(CostTieringFactor())
    registry.register(GroundingFactor())
    registry.register(FineTuningFactor())
    registry.register(ContextManagementFactor())
    registry.register(GuardrailsFactor())
    registry.register(TestTimeComputeFactor())
    registry.register(DesignPatternsFactor())
    registry.register(EvaluationFactor())
    registry.register(ContinualLearningFactor())
    registry.register(InferenceOptFactor())
    return registry
