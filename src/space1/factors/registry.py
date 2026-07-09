"""
FactorRegistry — Реестр факторов способностей (x₁-x₁₇)

MVP Factors:
- x₁: LLM Capability
- x₈: Cost Tiering
- x₁₂: Guardrails
- x₁₆: Continual Learning

Reference: MATHEMATICAL_FORMULAS.md sections 6-7
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
# MVP Factors Implementation
# =============================================================================

class LLMFactor(BaseFactor):
    """
    x₁: LLM Capability
    
    C_llm = α_Q * Q_bench + α_R * R_bench + α_C * C_bench + α_A * A_bench
    
    Влияние на Success Rate:
    S(m, t) = C_llm(m) / (1 + exp(-λ_t * (C_llm(m) - τ_t)))
    """
    
    # Веса компонентов
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
        """
        Compute LLM capability factor.
        
        Context requirements:
        - llm_name: str
        - benchmarks: dict with quality, reasoning, coding, agentic scores [0, 1]
        """
        benchmarks = context.get("benchmarks", {
            "quality": 0.7,
            "reasoning": 0.7,
            "coding": 0.7,
            "agentic": 0.7,
        })
        
        # C_llm calculation
        c_llm = sum(
            self.WEIGHTS[k] * benchmarks.get(k, 0.7)
            for k in self.WEIGHTS
        )
        
        # S(m) - success rate contribution
        # Using sigmoid approximation
        lambda_t = context.get("lambda_t", 5.0)
        tau_t = context.get("tau_t", 0.5)
        
        exp_term = -lambda_t * (c_llm - tau_t)
        s_m = c_llm / (1 + (2.71828 ** exp_term))
        
        # Delta from base (S_0 = 0.3)
        delta_s = s_m - 0.3
        
        return FactorResult(
            factor_id=self.factor_id.value,
            value=c_llm,
            delta_success=delta_s,
            delta_time=0.0,  # LLM doesn't directly affect time in MVP
            metadata={"s_m": s_m, "benchmarks": benchmarks}
        )


class CostTieringFactor(BaseFactor):
    """
    x₈: Cost Tiering
    
    Динамический выбор LLM на основе cost/quality tradeoff.
    
    Tiers:
    1. Ollama (local, free)
    2. Free APIs (Groq, Together)
    3. Paid API (OpenAI, Anthropic)
    """
    
    # Cost tiers in $/1M tokens
    COSTS = {
        "ollama": 0.0,
        "free_api": 0.0,
        "paid_api": 2.0,  # Approximate
    }
    
    # Quality tiers (relative)
    QUALITY = {
        "ollama": 0.6,  # Depends on model
        "free_api": 0.75,
        "paid_api": 0.95,
    }
    
    def __init__(self):
        super().__init__(FactorID.X8_COST_TIERING)
    
    @property
    def name(self) -> str:
        return "Cost Tiering"
    
    @property
    def priority(self) -> str:
        return "HIGH"
    
    def compute(self, context: Dict[str, Any]) -> FactorResult:
        """
        Compute cost tiering factor.
        
        Context requirements:
        - budget: float (remaining budget)
        - task_complexity: float [0, 1]
        - quality_requirement: float [0, 1]
        """
        budget = context.get("budget", 100.0)
        task_complexity = context.get("task_complexity", 0.5)
        quality_requirement = context.get("quality_requirement", 0.7)
        
        # Select tier based on budget and requirements
        if budget < 1.0:
            selected_tier = "ollama"
        elif budget < 10.0 and quality_requirement < 0.8:
            selected_tier = "free_api"
        else:
            selected_tier = "paid_api"
        
        quality = self.QUALITY[selected_tier]
        cost = self.COSTS[selected_tier]
        
        # ΔS = quality adjustment
        delta_s = (quality - 0.7) * 0.2  # Normalize around 0.7 baseline
        
        # ΔT = time cost (inverse of quality for MVP simplicity)
        delta_t = -0.1 * quality  # Higher quality = slightly more time
        
        return FactorResult(
            factor_id=self.factor_id.value,
            value=quality,
            delta_success=delta_s,
            delta_time=delta_t,
            metadata={
                "selected_tier": selected_tier,
                "cost_per_1m": cost,
                "budget": budget,
            }
        )


class GuardrailsFactor(BaseFactor):
    """
    x₁₂: Guardrails & Safety
    
    G_eff = ∏_i (1 - p_i * (1 - G_i))
    
    ΔS_guardrails = β_g * G_eff
    
    Где G_i = 1 если guardrail активен, 0 если нет
    """
    
    BASE_BETA = 0.05  # Base benefit to success rate
    
    def __init__(self):
        super().__init__(FactorID.X12_GUARDRAILS)
    
    @property
    def name(self) -> str:
        return "Guardrails"
    
    @property
    def priority(self) -> str:
        return "HIGH"
    
    def compute(self, context: Dict[str, Any]) -> FactorResult:
        """
        Compute guardrails effectiveness.
        
        Context requirements:
        - active_guardrails: List[str] - names of active guardrails
        - risk_probabilities: Dict[str, float] - p_i for each risk
        """
        active_guardrails = context.get("active_guardrails", [])
        risk_probabilities = context.get("risk_probabilities", {})
        
        # Calculate G_eff
        g_eff = 1.0
        for risk_name, p_risk in risk_probabilities.items():
            # G_i = 1 if guardrail covers this risk
            g_i = 1.0 if risk_name in active_guardrails else 0.0
            g_eff *= (1 - p_risk * (1 - g_i))
        
        # Delta success = β_g * G_eff
        delta_s = self.BASE_BETA * g_eff
        
        # Guardrails add small time overhead
        delta_t = 0.02 * len(active_guardrails)
        
        return FactorResult(
            factor_id=self.factor_id.value,
            value=g_eff,
            delta_success=delta_s,
            delta_time=delta_t,
            metadata={
                "active_count": len(active_guardrails),
                "g_eff": g_eff,
            }
        )


class ContinualLearningFactor(BaseFactor):
    """
    x₁₆: Continual Learning
    
    Knowledge accumulation:
    K(t) = K_0 + η_learn * Σ ΔK(τ) * (1 - K(τ)/K_max)
    
    Knowledge growth:
    K_cl(t) = 1 - exp(-λ_cl * N_tasks)
    
    ΔS_cl = γ_cl * K_cl * S(x)
    """
    
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
        """
        Compute continual learning factor.
        
        Context requirements:
        - n_completed_tasks: int - number of completed tasks
        - current_knowledge: float [0, 1] - current knowledge level
        - base_success: float [0, 1] - base success rate
        """
        n_tasks = context.get("n_completed_tasks", 0)
        current_knowledge = context.get("current_knowledge", 0.0)
        base_success = context.get("base_success", 0.3)
        
        # K_cl(t) = 1 - exp(-λ_cl * N_tasks)
        lambda_cl = 0.01
        k_cl = 1.0 - (2.71828 ** (-lambda_cl * n_tasks))
        
        # ΔS_cl = γ_cl * K_cl * S(x)
        delta_s = self.GAMMA_CL * k_cl * base_success
        
        # Time: learning adds small overhead
        delta_t = 0.01 * n_tasks * 0.001  # Diminishing returns
        
        return FactorResult(
            factor_id=self.factor_id.value,
            value=k_cl,
            delta_success=delta_s,
            delta_time=delta_t,
            metadata={
                "n_tasks": n_tasks,
                "k_cl": k_cl,
                "current_knowledge": current_knowledge,
            }
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
