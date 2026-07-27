"""
Mission → Compliance → Utility → Execution Pipeline with Task Decomposition and Async Support

Per 02_MATHEMATICAL_CORE.md §IV.12:
- MissionPolicy.calibrate() with 6 mission types
- State modifiers, gamma rules, thresholds
- PolicyParams with calibrated weights

Reference: 02_MATHEMATICAL_CORE.md §IV.12, 05_MEMORY_AND_STATE.md
"""

from abc import ABC, abstractmethod
from typing import ClassVar, List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import asyncio

from ..compliance.core import GammaVeto, Action, Rule, ComplianceError
from ..metrics.tracker import MetricRegistry
from ..utility import rank_actions, score_action

# Phase 3 integration exports
from ..memory.core import OperationalMemory, StrategicMemory, MetaMemory, ConsolidationGate
from ..triggers.core import TriggerSystem


class MissionType(Enum):
    """
    Six mission types per 02_MATHEMATICAL_CORE.md §IV.12.
    Each type has different weight priorities for utility calculation.
    """
    SURVIVAL = "survival"      # Extreme risk aversion, minimal quality
    GROWTH = "growth"          # Higher risk tolerance, reputation building
    MAINTENANCE = "maintenance" # Balanced operations
    MAXIMIZE = "maximize"      # Profit optimization
    PREMIUM = "premium"        # High quality, high margin
    CHARITY = "charity"         # Low risk limits, social value


# =============================================================================
# Canonical Mission Calibration (02_MATHEMATICAL_CORE.md §IV.12)
# =============================================================================

# MISSION_CALIBRATION table: base weights for each mission type
# Weights: (lambda_phi, lambda_upsilon, lambda_omega, lambda_quality)
MISSION_CALIBRATION: Dict[MissionType, Tuple[float, float, float, float]] = {
    MissionType.SURVIVAL: (0.50, 0.20, 0.05, 0.25),
    MissionType.GROWTH: (0.25, 0.35, 0.25, 0.15),
    MissionType.MAINTENANCE: (0.30, 0.25, 0.20, 0.25),
    MissionType.MAXIMIZE: (0.55, 0.20, 0.10, 0.15),
    MissionType.PREMIUM: (0.20, 0.25, 0.15, 0.40),
    MissionType.CHARITY: (0.10, 0.30, 0.35, 0.25),
}


@dataclass
class PolicyParams:
    """
    Output of MissionPolicy.calibrate() — calibrated parameters for decision rule.
    
    Per 02_MATHEMATICAL_CORE.md §IV.12:
    - Weights: (lambda_phi, lambda_upsilon, lambda_omega, lambda_quality)
    - Thresholds: psi_max, q_min, c_max
    """
    # Weights for utility calculation
    lambda_phi: float = 0.30       # Profit weight
    lambda_upsilon: float = 0.25   # Reputation weight
    lambda_omega: float = 0.20     # Evolution weight
    lambda_quality: float = 0.25   # Quality weight
    
    # Thresholds
    psi_max: float = 5.0           # Maximum acceptable risk
    q_min: float = 0.5            # Minimum quality threshold
    c_min: float = 1.0            # Minimum budget
    c_max: float = 100.0           # Maximum budget
    
    # Additional parameters
    voi: float = 0.5              # Value of Information
    c_info: float = 2.0           # Cost of information
    h_clarify: float = 0.5        # Homeostasis threshold for clarification
    
    # Mission context
    mission_type: MissionType = MissionType.MAINTENANCE


@dataclass
class StateModifier:
    """
    State modifier rules per 05_MEMORY_AND_STATE.md Part V.
    Multiplicative modifiers for weights based on current agent state.
    """
    # Modifier thresholds (asymmetric)
    balance_high: float = 0.9   # Above this -> profit bonus
    balance_low: float = 0.3   # Below this -> profit penalty
    stress_high: float = 1.3   # Above this -> conservative
    reputation_low: float = 0.5  # Below this -> reputation bonus
    workload_high: float = 3.0  # Tasks in queue
    workload_low: float = 0.5   # Below this -> growth mode
    
    def compute_modifiers(self, state: Dict[str, float]) -> Dict[str, float]:
        """
        Compute weight modifiers based on agent state.
        Returns multiplicative factors for each weight type.
        """
        modifiers = {
            "phi": 1.0,
            "upsilon": 1.0,
            "omega": 1.0,
            "quality": 1.0,
        }
        
        # Balance modifiers
        balance = state.get("balance", 0.5)
        if balance > self.balance_high:
            modifiers["phi"] *= 1.2  # Can afford to optimize
        elif balance < self.balance_low:
            modifiers["phi"] *= 1.5  # Must prioritize profit
            modifiers["upsilon"] *= 0.7  # Less room for reputation building
        
        # Stress modifiers
        stress = state.get("stress_level", 0.5)
        if stress > self.stress_high:
            modifiers["phi"] *= 1.1  # Focus on profit
            modifiers["omega"] *= 0.5  # Reduce exploration
        
        # Reputation modifiers
        reputation = state.get("reputation", 0.5)
        if reputation < self.reputation_low:
            modifiers["upsilon"] *= 1.3  # Must build reputation
            modifiers["phi"] *= 0.9
        
        # Workload modifiers
        workload = state.get("workload", 1.0)
        if workload > self.workload_high:
            modifiers["quality"] *= 1.1  # Need to maintain quality under load
            modifiers["phi"] *= 0.9
        elif workload < self.workload_low:
            modifiers["omega"] *= 1.2  # Can invest in learning
        
        return modifiers


@dataclass
class Mission:
    """
    Mission — top level of the hierarchy with canonical calibration.
    
    Per 02_MATHEMATICAL_CORE.md §IV.12:
    PolicyParams = calibrate(MissionProfile, AgentState, MissionContext)
    
    Replaces generic Mission with full calibration support.
    """
    id: str
    name: str
    mission_type: MissionType = MissionType.MAINTENANCE
    
    # Optional principles for gamma rules
    hard_principles: List[str] = field(default_factory=list)
    soft_principles: Dict[str, float] = field(default_factory=dict)  # principle -> priority
    
    # Budget and time constraints
    max_budget: float = 100.0
    max_time: Optional[timedelta] = None
    priority: float = 1.0  # 0-1
    
    def calibrate(
        self,
        agent_state: Dict[str, float],
        mission_context: Optional[Dict[str, Any]] = None
    ) -> PolicyParams:
        """
        Calibrate policy parameters per 02_MATHEMATICAL_CORE.md §IV.12.
        
        Steps:
        1. Get base weights from MISSION_CALIBRATION table
        2. Apply state modifiers
        3. Normalize weights
        4. Compute thresholds
        
        Args:
            agent_state: Current agent state (balance, stress_level, reputation, etc.)
            mission_context: Additional context (optional)
            
        Returns:
            PolicyParams with calibrated weights and thresholds
        """
        mission_context = mission_context or {}
        
        # Step 1: Get base weights from calibration table
        base_weights = MISSION_CALIBRATION.get(
            self.mission_type, 
            MISSION_CALIBRATION[MissionType.MAINTENANCE]
        )
        lambda_phi, lambda_upsilon, lambda_omega, lambda_quality = base_weights
        
        # Step 2: Apply state modifiers
        state_modifier = StateModifier()
        modifiers = state_modifier.compute_modifiers(agent_state)
        
        # Apply modifiers multiplicatively
        lambda_phi *= modifiers["phi"]
        lambda_upsilon *= modifiers["upsilon"]
        lambda_omega *= modifiers["omega"]
        lambda_quality *= modifiers["quality"]
        
        # Step 3: Normalize weights (sum to 1.0)
        total = lambda_phi + lambda_upsilon + lambda_omega + lambda_quality
        if total > 0:
            lambda_phi /= total
            lambda_upsilon /= total
            lambda_omega /= total
            lambda_quality /= total
        
        # Step 4: Compute thresholds
        # q_min = base_quality * quality_boost(personality)
        q_min = 0.5 * (1.0 + modifiers.get("quality", 1.0) - 1.0)
        q_min = max(0.1, min(1.0, q_min))
        
        # psi_max = risk_tolerance * [1.2 if phi_historical < 0] * B_total * 0.5
        phi_historical = agent_state.get("phi_historical", 0.0)
        risk_tolerance = agent_state.get("risk_tolerance", 1.0)
        psi_max = risk_tolerance * (1.2 if phi_historical < 0 else 1.0) * self.max_budget * 0.5
        
        # c_max = C_remaining * (2.0 / cost_penalty)
        cost_penalty = agent_state.get("cost_penalty", 1.0)
        c_max = self.max_budget * (2.0 / max(cost_penalty, 0.1))
        
        return PolicyParams(
            lambda_phi=lambda_phi,
            lambda_upsilon=lambda_upsilon,
            lambda_omega=lambda_omega,
            lambda_quality=lambda_quality,
            psi_max=psi_max,
            q_min=q_min,
            c_min=self.max_budget * 0.01,  # 1% minimum
            c_max=c_max,
            voi=mission_context.get("voi", 0.5),
            c_info=mission_context.get("c_info", 2.0),
            h_clarify=agent_state.get("h_clarify", 0.5),
            mission_type=self.mission_type,
        )
    
    def principles_to_gamma_rules(
        self,
        available_actions: List[Action]
    ) -> Tuple[List[Rule], List[Rule]]:
        """
        Convert mission principles to gamma rules per §IV.12.
        
        hard_principles -> GammaHard rules (veto)
        soft_principles -> GammaSoft rules (penalty)
        
        Priority weights: critical=1.0, high=0.7, medium=0.4, low=0.2
        """
        hard_rules: List[Rule] = []
        soft_rules: List[Rule] = []
        
        # Map principle keywords to rule creation
        for principle in self.hard_principles:
            # Create hard rules based on principle
            if "no_code" in principle.lower():
                hard_rules.append(BlockedActionsRule(["write_code", "modify_code"]))
            elif "safe_only" in principle.lower():
                hard_rules.append(SafeModeRule())
        
        # Soft principles with priority weights
        for principle, priority in self.soft_principles.items():
            if priority >= 0.7:  # high or critical
                soft_rules.append(SoftPenaltyRule(principle, priority))
        
        return hard_rules, soft_rules


# =============================================================================
# Pipeline Stages (unchanged for now)
# =============================================================================

class PipelineStage(Enum):
    """Этапы конвейера обработки."""
    MISSION = "mission"      # Калибровка параметров
    COMPLIANCE = "compliance" # Проверка через GammaVeto
    UTILITY = "utility"      # Оптимизация выбора
    EXECUTION = "execution"  # Выполнение


@dataclass
class ExecutionContext:
    """
    Контекст выполнения — передаётся через все этапы pipeline.
    """
    mission: Mission
    calibrated_params: Dict[str, Any] = field(default_factory=dict)
    selected_action: Optional[Action] = None
    execution_result: Optional[Any] = None
    stage_results: Dict[PipelineStage, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseStage(ABC):
    """Базовый класс для этапов pipeline."""
    
    def __init__(self, stage: PipelineStage):
        self.stage = stage
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable название этапа."""
        pass
    
    @abstractmethod
    def process(self, ctx: ExecutionContext) -> ExecutionContext:
        """Обработать контекст и вернуть обновлённый."""
        pass


class MissionStage(BaseStage):
    """
    Mission Stage — калибровка параметров миссии.
    
    Вызывает Mission.calibrate() для подготовки параметров.
    """
    
    def __init__(self):
        super().__init__(PipelineStage.MISSION)
    
    @property
    def name(self) -> str:
        return "Mission Calibration"
    
    def process(self, ctx: ExecutionContext) -> ExecutionContext:
        """Калибровать параметры миссии."""
        ctx.calibrated_params = ctx.mission.calibrate(ctx.metadata.get("context", {}))
        ctx.stage_results[self.stage] = ctx.calibrated_params
        return ctx


class ComplianceStage(BaseStage):
    """
    Compliance Stage — проверка действий через GammaVeto.
    
    Использует бинарный veto: действие проходит только если ВСЕ правила пройдены.
    """
    
    def __init__(self, veto: Optional[GammaVeto] = None, rules: Optional[List[Rule]] = None):
        super().__init__(PipelineStage.COMPLIANCE)
        self._veto = veto or GammaVeto(rules or [])
    
    @property
    def name(self) -> str:
        return "Compliance Check"
    
    def register_rule(self, rule: Rule) -> None:
        """Добавить правило в GammaVeto."""
        self._veto.register(rule)
    
    def process(self, ctx: ExecutionContext) -> ExecutionContext:
        """Проверить действие на соответствие правилам."""
        if ctx.selected_action is None:
            ctx.errors.append("No action selected for compliance check")
            return ctx
        
        passed = self._veto.evaluate(ctx.selected_action)
        details = self._veto.evaluate_with_details(ctx.selected_action)
        
        ctx.stage_results[self.stage] = {
            "passed": passed,
            "details": details,
        }
        
        if not passed:
            ctx.errors.append(f"Action '{ctx.selected_action.name}' failed compliance: {details['failed_rules']}")
        
        return ctx


class UtilityStage(BaseStage):
    """Utility Stage — risk-adjusted action scoring for the Phase 2 loop."""
    
    def __init__(self, metrics: Optional[MetricRegistry] = None):
        super().__init__(PipelineStage.UTILITY)
        self.metrics = metrics or MetricRegistry()
    
    @property
    def name(self) -> str:
        return "Utility Optimization"
    
    def process(self, ctx: ExecutionContext) -> ExecutionContext:
        """Score the selected compliant action and persist utility metrics."""
        if ctx.selected_action is None:
            ctx.stage_results[self.stage] = {"selected": None, "optimization": "risk_adjusted"}
            return ctx

        decision = score_action(
            ctx.selected_action,
            task=ctx.metadata.get("task"),
            agent_context=ctx.metadata.get("agent_context"),
            token_tracker=ctx.metadata.get("token_tracker"),
            metrics=self.metrics,
        )
        ctx.stage_results[self.stage] = {
            "selected": ctx.selected_action.name,
            "optimization": "risk_adjusted",
            "score": decision.score,
            "phi": decision.phi,
            "psi": decision.psi,
            "quality": decision.quality,
            "upsilon": decision.upsilon,
            "omega": decision.omega,
            "factors": {k: v.value for k, v in decision.factors.items()},
        }
        return ctx


class ExecutionStage(BaseStage):
    """
    Execution Stage — выполнение действия.
    
    В MVP просто записывает результат.
    Полная реализация будет вызывать реальные инструменты.
    """
    
    def __init__(self):
        super().__init__(PipelineStage.EXECUTION)
    
    @property
    def name(self) -> str:
        return "Action Execution"
    
    def process(self, ctx: ExecutionContext) -> ExecutionContext:
        """Выполнить действие."""
        if ctx.selected_action is None:
            ctx.errors.append("No action to execute")
            return ctx
        
        # MVP: просто записываем как "выполнено"
        # Phase 2: реальное выполнение через tools
        ctx.execution_result = {
            "action": ctx.selected_action.name,
            "status": "executed" if not ctx.errors else "failed",
            "timestamp": datetime.now().isoformat(),
        }
        ctx.stage_results[self.stage] = ctx.execution_result
        return ctx




class MissionProfile(Enum):
    """6 типов миссий — 02_MATHEMATICAL_CORE.md §IV.12"""
    SURVIVAL = "survival"       # Выживание: минимум риска, быстрая прибыль
    GROWTH = "growth"           # Рост: баланс прибыли и репутации
    MAINTENANCE = "maintenance" # Поддержка: стабильность, качество
    MAXIMIZE = "maximize"       # Максимизация: максимум прибыли
    PREMIUM = "premium"         # Премиум: максимум качества
    CHARITY = "charity"         # Благотворительность: минимум прибыли


@dataclass
class MissionPolicy:
    """Политика миссии с 4 весами — заменяет WeightCalibrator.

    Таблица из 02_MATHEMATICAL_CORE.md §IV.12:

    | Профиль      | profit | risk | speed | quality |
    |--------------|--------|------|-------|---------|
    | SURVIVAL     | 0.40   | 0.10 | 0.30  | 0.20    |
    | GROWTH       | 0.30   | 0.20 | 0.20  | 0.30    |
    | MAINTENANCE  | 0.20   | 0.10 | 0.20  | 0.50    |
    | MAXIMIZE     | 0.50   | 0.30 | 0.10  | 0.10    |
    | PREMIUM      | 0.20   | 0.10 | 0.10  | 0.60    |
    | CHARITY      | 0.05   | 0.05 | 0.20  | 0.70    |
    """

    profile: MissionProfile = MissionProfile.GROWTH

    # Weights [0, 1], sum = 1.0
    profit_weight: float = 0.30
    risk_weight: float = 0.20
    speed_weight: float = 0.20
    quality_weight: float = 0.30

    # Preset table
    _PRESETS: ClassVar[Dict[MissionProfile, Dict[str, float]]] = {
        MissionProfile.SURVIVAL:    {"profit": 0.40, "risk": 0.10, "speed": 0.30, "quality": 0.20},
        MissionProfile.GROWTH:      {"profit": 0.30, "risk": 0.20, "speed": 0.20, "quality": 0.30},
        MissionProfile.MAINTENANCE: {"profit": 0.20, "risk": 0.10, "speed": 0.20, "quality": 0.50},
        MissionProfile.MAXIMIZE:    {"profit": 0.50, "risk": 0.30, "speed": 0.10, "quality": 0.10},
        MissionProfile.PREMIUM:     {"profit": 0.20, "risk": 0.10, "speed": 0.10, "quality": 0.60},
        MissionProfile.CHARITY:     {"profit": 0.05, "risk": 0.05, "speed": 0.20, "quality": 0.70},
    }

    def __post_init__(self):
        """Apply preset weights if profile is set."""
        preset = self._PRESETS.get(self.profile)
        if preset:
            self.profit_weight = preset["profit"]
            self.risk_weight = preset["risk"]
            self.speed_weight = preset["speed"]
            self.quality_weight = preset["quality"]

    def calibrate(self, pressures: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        """Calibrate weights based on pressures (backward-compatible with WeightCalibrator)."""
        weights = {
            "profit_weight": self.profit_weight,
            "risk_weight": self.risk_weight,
            "speed_weight": self.speed_weight,
            "quality_weight": self.quality_weight,
        }

        if not pressures:
            return weights

        # Apply pressure adjustments
        calibrated = dict(weights)
        if "balance" in pressures and pressures["balance"] < 100:
            # Low balance → increase profit, decrease quality
            calibrated["profit_weight"] = min(1.0, calibrated["profit_weight"] * 1.2)
            calibrated["quality_weight"] = max(0.0, calibrated["quality_weight"] * 0.8)
        if "stress" in pressures and pressures["stress"] > 0.7:
            # High stress → decrease risk
            calibrated["risk_weight"] = max(0.0, calibrated["risk_weight"] * 0.5)

        # Normalize to sum = 1.0
        total = sum(calibrated.values())
        if total > 0:
            calibrated = {k: v / total for k, v in calibrated.items()}

        return calibrated

    def to_dict(self) -> Dict[str, float]:
        """Export weights as dict."""
        return {
            "profit_weight": self.profit_weight,
            "risk_weight": self.risk_weight,
            "speed_weight": self.speed_weight,
            "quality_weight": self.quality_weight,
        }



class TaskDecomposer:
    """
    TaskDecomposer (G10/G2/D*).
    
    Decomposes a complex high-level task into a directed list of atomic Actions (subtasks).
    Optimizes decomposition quality using metrics coverage, atomicity, and independencies.
    """
    
    def __init__(self):
        pass
        
    def decompose(self, task_description, budget: float = 10.0) -> Tuple[List[Action], float]:
        """
        Decompose a high-level task description into atomic Actions (subtasks).

        Supports both str and Task objects.

        Returns:
            Tuple[List[Action], quality_score [0.0, 1.0]]
        """
        # Универсальная поддержка: str или Task
        if isinstance(task_description, str):
            text = task_description.lower()
            suffix = ''
        else:
            # Task object — безопасное извлечение строк
            _title = getattr(task_description, 'title', '') or ''
            _desc = getattr(task_description, 'description', '') or ''
            if callable(_title):
                _title = _title()
            if callable(_desc):
                _desc = _desc()
            text = (str(_title) + " " + str(_desc)).lower()
            _id = getattr(task_description, 'id', '')
            suffix = f'_{_id}' if _id else ''
        actions = []

        # Score-based keyword matching (supports overlaps)
        CATEGORIES = {
            "security": {
                "keywords": ["auth", "login", "jwt", "security", "encrypt", "password"],
                "actions": [
                    Action(name=f"security_audit{suffix}", resource_cost=0.15 * budget, params={"input": "RFI", "output": "SecuritySpecs"}),
                    Action(name=f"implement_auth{suffix}", resource_cost=0.35 * budget, params={"input": "SecuritySpecs", "output": "SecureCode"}),
                    Action(name=f"verify_encryption{suffix}", resource_cost=0.10 * budget, params={"input": "SecureCode", "output": "AuthQualityReport", "sensitive": True}),
                ]
            },
            "deploy": {
                "keywords": ["deploy", "aws", "cloud", "docker", "server", "infra"],
                "actions": [
                    Action(name=f"configure_infra{suffix}", resource_cost=0.20 * budget, params={"input": "CloudReqs", "output": "TerraformSpecs"}),
                    Action(name=f"provision_cloud{suffix}", resource_cost=0.40 * budget, params={"input": "TerraformSpecs", "output": "DeployedEndpoints"}),
                    Action(name=f"smoke_test_deploy{suffix}", resource_cost=0.15 * budget, params={"input": "DeployedEndpoints", "output": "InfrastructureReport"}),
                ]
            },
            "finance": {
                "keywords": ["invoice", "payment", "finance", "stripe", "billing"],
                "actions": [
                    Action(name=f"ledger_setup{suffix}", resource_cost=0.10 * budget, params={"input": "InvoicingRules", "output": "LedgerSpecs"}),
                    Action(name=f"payment_gateway_hook{suffix}", resource_cost=0.30 * budget, params={"input": "LedgerSpecs", "output": "WebhookSignatures"}),
                    Action(name=f"reconcile_accounts{suffix}", resource_cost=0.10 * budget, params={"input": "WebhookSignatures", "output": "FinancialReconciliation", "sensitive": True}),
                ]
            },
        }

        # Calculate score for each category
        scores = {}
        for cat_name, cat_data in CATEGORIES.items():
            score = sum(1 for kw in cat_data["keywords"] if kw in text)
            scores[cat_name] = score

        # Select categories with score > 0, or fallback to default
        selected = [name for name, score in scores.items() if score > 0]
        if not selected:
            # Default fallback
            actions = [
                Action(name=f"setup{suffix}", resource_cost=0.10 * budget, params={"input": "RFI", "output": "SetupSpecs"}),
                Action(name=f"execute{suffix}", resource_cost=0.30 * budget, params={"input": "SetupSpecs", "output": "CodeDeliverables"}),
                Action(name=f"verify{suffix}", resource_cost=0.10 * budget, params={"input": "CodeDeliverables", "output": "QualityReport", "sensitive": True}),
            ]
        else:
            # Combine actions from all matching categories
            for cat_name in selected:
                actions.extend(CATEGORIES[cat_name]["actions"])

        # Quality score = coverage * 0.4 + atomicity * 0.3 + budget_match * 0.3
        total_allocated = sum(a.resource_cost for a in actions)
        budget_match = 1.0 - abs(total_allocated - budget) / max(budget, 1e-9)
        budget_match = max(0.0, min(1.0, budget_match))

        quality = 0.4 * min(len(actions)/3, 1.0) + 0.3 * 0.8 + 0.3 * budget_match

        return actions, float(quality)


class MissionProcessor:
    """
    Mission → Compliance → Utility → Execution Pipeline.
    
    Orchestrates the full mission execution flow.
    
    Usage:
        processor = MissionProcessor()
        processor.setup_mission(mission)
        
        ctx = processor.execute(action)
        if ctx.errors:
            print(f"Errors: {ctx.errors}")
        else:
            print(f"Result: {ctx.execution_result}")
    """
    
    def __init__(self):
        self.metrics = MetricRegistry()
        self._stages: List[BaseStage] = [
            MissionStage(),
            ComplianceStage(),
            UtilityStage(self.metrics),
            ExecutionStage(),
        ]
        self._mission: Optional[Mission] = None
        self._compliance: Optional[ComplianceStage] = None
        
        # Phase 3: Memory and Triggers integration
        self.op_mem = OperationalMemory()
        self.strategic_mem = StrategicMemory()
        self.meta_mem = MetaMemory()
        self.consolidation_gate = ConsolidationGate(
            episodic_mem=self.strategic_mem,
            semantic_mem=self.meta_mem.semantic,
            procedural_mem=self.meta_mem.procedural
        )
        self.triggers = TriggerSystem()
        self.decomposer = TaskDecomposer()
    
    def setup_mission(self, mission: Mission) -> None:
        """Установить миссию для выполнения."""
        self._mission = mission
        self._compliance = self._stages[1]  # ComplianceStage
    
    def add_compliance_rule(self, rule: Rule) -> None:
        """Добавить правило в Compliance Stage."""
        if self._compliance:
            self._compliance.register_rule(rule)
            
    def decompose_task(self, task_description: str, budget: float = 10.0) -> Tuple[List[Action], float]:
        """Decompose a high-level task description into atomic Actions."""
        return self.decomposer.decompose(task_description, budget)
    
    def execute(self, action: Action, context: Optional[Dict[str, Any]] = None) -> ExecutionContext:
        """
        Execute action through the full pipeline.
        
        Args:
            action: Action to execute
            context: Additional context for calibration
            
        Returns:
            ExecutionContext with results from all stages
        """
        if self._mission is None:
            raise ValueError("Mission not set. Call setup_mission() first.")
        
        ctx = ExecutionContext(
            mission=self._mission,
            metadata=context or {},
        )
        ctx.selected_action = action
        
        # Phase 3 memory prep: Store active task details if available
        task = ctx.metadata.get("task")
        if task is not None:
            self.op_mem.set("task_id", getattr(task, "id", "task_unknown"))
            self.op_mem.set("title", getattr(task, "title", "Untitled Task"))
            self.op_mem.set("strategy", "Standard execution strategy via pipeline")
        
        # Run through all stages
        for stage in self._stages:
            ctx = stage.process(ctx)
            
            # Phase 3 triggers: alert triggers on compliance veto
            if stage.stage == PipelineStage.COMPLIANCE:
                passed = ctx.stage_results.get(PipelineStage.COMPLIANCE, {}).get("passed", True)
                if not passed:
                    self.triggers.handle_event("compliance_veto", {"action": action.name})
                    # BUG-004 FIX: Fail fast on compliance violation - raise exception instead of swallowing
                    raise ComplianceError(f"Action '{action.name}' vetoed by compliance rules")
                    
            # Record utility components into active OperationalMemory
            if stage.stage == PipelineStage.UTILITY:
                res = ctx.stage_results.get(PipelineStage.UTILITY, {})
                if "score" in res:
                    self.op_mem.update_metric("score", res.get("score", 0.0))
                    self.op_mem.update_metric("revenue", res.get("phi", 0.0))  # Φ is baseline profit
                    self.op_mem.update_metric("risk", res.get("psi", 0.0))
                    self.op_mem.update_metric("quality", res.get("quality", 0.7))
                    self.op_mem.update_metric("time_hours", getattr(task, "estimated_hours", 1.0) if task else 1.0)
                    
                    # Update MetricRegistry thresholds/triggers
                    self.triggers.handle_metric_change("utility_score", res.get("score", 0.0))
                    self.triggers.handle_metric_change("risk", res.get("psi", 0.0))
                    
        # Check execution stage outcome and triggers
        exec_res = ctx.stage_results.get(PipelineStage.EXECUTION)
        if exec_res:
            self.op_mem.set("status", "completed" if not ctx.errors else "failed")
            if ctx.errors:
                self.op_mem.set("failure_reason", ctx.errors[0])
                self.triggers.handle_event("execution_failure", {"action": action.name, "error": ctx.errors[0]})
            else:
                self.triggers.handle_event("execution_success", {"action": action.name})
                
        # Phase 3 memory consolidation: episodic → strategic memory
        if task is not None:
            self.consolidation_gate.consolidate(self.op_mem)
            
        return ctx

    async def execute_async(self, action: Action, context: Optional[Dict[str, Any]] = None) -> ExecutionContext:
        """Execute action asynchronously simulating latency delay."""
        await asyncio.sleep(0.01)
        return self.execute(action, context)

    def execute_best(self, actions: List[Action], context: Optional[Dict[str, Any]] = None) -> ExecutionContext:
        """Veto non-compliant candidates, rank survivors by utility, then execute the best action."""
        if self._mission is None:
            raise ValueError("Mission not set. Call setup_mission() first.")
        context = context or {}
        compliant = [action for action in actions if self._compliance is None or self._compliance._veto.evaluate(action)]
        if not compliant:
            ctx = ExecutionContext(mission=self._mission, metadata=context)
            ctx.errors.append("No compliant actions available")
            ctx.stage_results[PipelineStage.COMPLIANCE] = {"passed": False, "compliant_actions": []}
            # Fire event trigger for complete compliance failure
            self.triggers.handle_event("all_actions_vetoed", {"action_count": len(actions)})
            return ctx
        ranked = rank_actions(
            compliant,
            task=context.get("task"),
            agent_context=context.get("agent_context"),
            token_tracker=context.get("token_tracker"),
            metrics=self.metrics,
        )
        context = {**context, "ranked_actions": ranked}
        ctx = self.execute(ranked[0].action, context)
        ctx.stage_results[PipelineStage.UTILITY]["ranked_actions"] = [
            {"action": d.action.name, "score": d.score} for d in ranked
        ]
        return ctx

    async def execute_best_async(self, actions: List[Action], context: Optional[Dict[str, Any]] = None) -> ExecutionContext:
        """Veto non-compliant candidates, rank survivors by utility, then execute the best action asynchronously."""
        await asyncio.sleep(0.01)
        return self.execute_best(actions, context)
    
    def get_pipeline_status(self) -> List[Dict[str, str]]:
        """Get status of all pipeline stages."""
        return [
            {"stage": s.stage.value, "name": s.name}
            for s in self._stages
        ]


# =============================================================================
# Convenience Functions
# =============================================================================

def create_mission(
    name: str,
    max_budget: float = 100.0,
    max_hours: float = 24.0,
    mission_type: MissionType = MissionType.MAINTENANCE,
) -> Mission:
    """Create a new mission with default parameters per canonical spec."""
    return Mission(
        id=f"mission_{datetime.now().timestamp()}",
        name=name,
        mission_type=mission_type,
        max_budget=max_budget,
        max_time=timedelta(hours=max_hours),
    )
