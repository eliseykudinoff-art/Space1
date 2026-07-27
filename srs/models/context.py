"""
Typed Contracts — BUG-024 FIX
================================
Заменяем dict на типизированные dataclass для внутренних объектов.

Reference: баги.txt BUG-024
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Literal
from enum import Enum


@dataclass
class AgentState:
    """
    BUG-024 FIX: Типизированное состояние агента.
    
    Заменяет свободный dict для состояния.
    """
    balance: float = 0.0          # Текущий баланс
    reputation: float = 0.5        # Репутация [0, 1]
    stress_level: float = 0.5      # Уровень стресса [0, 1]
    workload: int = 0             # Количество задач в очереди
    active_tasks: int = 0         # Активные задачи
    
    # Computed metrics
    health_score: float = 1.0     # Здоровье системы
    success_rate: float = 0.5     # История успехов
    
    def is_critical(self) -> bool:
        """Проверяет критическое состояние."""
        return (
            self.balance < 10.0 or
            self.reputation < 0.2 or
            self.stress_level > 0.9 or
            self.health_score < 0.3
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "balance": self.balance,
            "reputation": self.reputation,
            "stress_level": self.stress_level,
            "workload": self.workload,
            "active_tasks": self.active_tasks,
            "health_score": self.health_score,
            "success_rate": self.success_rate,
        }


@dataclass
class MissionExecutionContext:
    """
    BUG-024 FIX: Типизированный контекст выполнения.
    
    Заменяет свободный dict для контекста pipeline.
    """
    mission_id: str
    mission_name: str
    mission_type: str = "MAINTENANCE"
    
    # Action details
    action_name: str = ""
    action_params: Dict[str, Any] = field(default_factory=dict)
    
    # Task reference
    task_id: Optional[str] = None
    task_title: Optional[str] = None
    
    # State
    state: Optional[AgentState] = None
    
    # Results from pipeline stages
    compliance_passed: bool = True
    utility_score: Optional[float] = None
    
    # Metrics
    phi: float = 0.0    # Profit component
    psi: float = 0.0    # Risk component  
    upsilon: float = 0.5  # Reputation component
    quality: float = 0.7  # Quality score
    
    # Errors
    errors: List[str] = field(default_factory=list)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_error(self, error: str) -> None:
        """Добавить ошибку."""
        self.errors.append(error)
    
    def has_errors(self) -> bool:
        """Проверить наличие ошибок."""
        return len(self.errors) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "mission_name": self.mission_name,
            "mission_type": self.mission_type,
            "action_name": self.action_name,
            "compliance_passed": self.compliance_passed,
            "utility_score": self.utility_score,
            "errors": self.errors,
            "metadata": self.metadata,
        }


@dataclass
class TransformationContext:
    """
    BUG-024 FIX: Контекст трансформации данных.
    
    Используется для типизации context["state"], context["metadata"] и т.д.
    """
    state: AgentState
    actor: str                    # Кто выполняет трансформацию
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Source information
    source_module: str = ""
    source_operation: str = ""
    
    # Transformation metadata
    input_schema: Optional[str] = None
    output_schema: Optional[str] = None
    
    # Additional context
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state.to_dict(),
            "actor": self.actor,
            "timestamp": self.timestamp.isoformat(),
            "source_module": self.source_module,
            "source_operation": self.source_operation,
            "extra": self.extra,
        }


@dataclass
class EventRecord:
    """
    BUG-038 FIX: Запись события для history.
    
    Делает history replayable.
    """
    # Идентификация
    event_id: str = ""
    event_type: str = ""              # "task_created", "action_executed", etc.
    sequence_number: int = 0         # Порядковый номер в истории
    
    # Причина и следствие
    caused_by: Optional[str] = None   # event_id родительского события
    affects: List[str] = field(default_factory=list)  # Что изменилось
    
    # Данные
    actor: str = ""                   # Кто совершил
    action: str = ""            # Какое действие
    parameters: Dict[str, Any] = field(default_factory=dict)
    result: Dict[str, Any] = field(default_factory=dict)
    
    # Временная метка
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Snapshot состояния
    state_snapshot: Optional[AgentState] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "sequence_number": self.sequence_number,
            "caused_by": self.caused_by,
            "affects": self.affects,
            "actor": self.actor,
            "action": self.action,
            "parameters": self.parameters,
            "result": self.result,
            "timestamp": self.timestamp.isoformat(),
            "state_snapshot": self.state_snapshot.to_dict() if self.state_snapshot else None,
        }
