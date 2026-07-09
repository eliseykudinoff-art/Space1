"""
Mission → Compliance → Utility → Execution Pipeline

Архитектура:
    Mission → Compliance → Utility → Execution
         ↓           ↓           ↓         ↓
      calibrate   veto check   optimize   execute

Reference: DEVELOPMENT_PLAN.md - G16
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

from ..compliance.core import GammaVeto, Action, Rule


class PipelineStage(Enum):
    """Этапы конвейера обработки."""
    MISSION = "mission"      # Калибровка параметров
    COMPLIANCE = "compliance" # Проверка через GammaVeto
    UTILITY = "utility"      # Оптимизация выбора
    EXECUTION = "execution"  # Выполнение


@dataclass
class Mission:
    """
    Миссия — верхний уровень иерархии.
    
    Калибрует параметры для всех последующих этапов.
    """
    id: str
    name: str
    goals: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    max_budget: float = 100.0
    max_time: Optional[timedelta] = None
    priority: float = 1.0  # 0-1, выше = важнее
    
    def calibrate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Калибровать параметры миссии на основе контекста.
        
        Returns:
            Dict с откалиброванными параметрами для следующих этапов
        """
        calibrated = {
            "budget": min(self.max_budget, context.get("available_budget", self.max_budget)),
            "time_budget": self.max_time or timedelta(hours=context.get("default_hours", 24)),
            "priority": self.priority * context.get("urgency_multiplier", 1.0),
            "constraints": self.constraints,
            "goals": self.goals,
        }
        return calibrated


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
    """
    Utility Stage — оптимизация выбора действия.
    
    В MVP выбирает первое подходящее действие.
    Полная реализация (Phase 2) будет использовать FactorRegistry.
    """
    
    def __init__(self):
        super().__init__(PipelineStage.UTILITY)
    
    @property
    def name(self) -> str:
        return "Utility Optimization"
    
    def process(self, ctx: ExecutionContext) -> ExecutionContext:
        """Оптимизировать выбор действия (MVP: pass-through)."""
        # В MVP просто передаём действие дальше
        # Phase 2: использовать FactorRegistry для выбора оптимального
        ctx.stage_results[self.stage] = {
            "selected": ctx.selected_action.name if ctx.selected_action else None,
            "optimization": "none",  # MVP
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
        self._stages: List[BaseStage] = [
            MissionStage(),
            ComplianceStage(),
            UtilityStage(),
            ExecutionStage(),
        ]
        self._mission: Optional[Mission] = None
        self._compliance: Optional[ComplianceStage] = None
    
    def setup_mission(self, mission: Mission) -> None:
        """Установить миссию для выполнения."""
        self._mission = mission
        self._compliance = self._stages[1]  # ComplianceStage
    
    def add_compliance_rule(self, rule: Rule) -> None:
        """Добавить правило в Compliance Stage."""
        if self._compliance:
            self._compliance.register_rule(rule)
    
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
        
        # Run through all stages
        for stage in self._stages:
            ctx = stage.process(ctx)
            
            # Early exit on compliance failure (MVP behavior)
            if stage.stage == PipelineStage.COMPLIANCE:
                if not ctx.stage_results.get(PipelineStage.COMPLIANCE, {}).get("passed", True):
                    # In MVP: fail fast on compliance
                    # Phase 6: graded compliance allows partial execution
                    pass
        
        return ctx
    
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
    goals: Optional[List[str]] = None,
    max_budget: float = 100.0,
    max_hours: float = 24.0,
) -> Mission:
    """Create a new mission with default parameters."""
    return Mission(
        id=f"mission_{datetime.now().timestamp()}",
        name=name,
        goals=goals or [],
        max_budget=max_budget,
        max_time=timedelta(hours=max_hours),
    )
