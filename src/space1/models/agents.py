"""
Agent Model — Состояние и возможности агента

Reference: DEVELOPMENT_PLAN.md - G11 (Data classes)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum


class AgentStatus(Enum):
    """Статус агента."""
    IDLE = "idle"
    WORKING = "working"
    BLOCKED = "blocked"
    ERROR = "error"


@dataclass
class AgentCapabilities:
    """
    Возможности агента (навыки, модели, инструменты).
    
    Соответствует x₁-x₁₇ факторам.
    """
    # LLM capabilities
    llm_name: str = "unknown"
    llm_quality: float = 0.7
    llm_reasoning: float = 0.7
    llm_coding: float = 0.7
    llm_agentic: float = 0.7
    
    # Tool capabilities
    has_browser: bool = False
    has_file_system: bool = True
    has_mcp: bool = False
    
    # Learning
    n_completed_tasks: int = 0
    current_knowledge: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "llm_name": self.llm_name,
            "benchmarks": {
                "quality": self.llm_quality,
                "reasoning": self.llm_reasoning,
                "coding": self.llm_coding,
                "agentic": self.llm_agentic,
            },
            "tools": {
                "browser": self.has_browser,
                "file_system": self.has_file_system,
                "mcp": self.has_mcp,
            },
            "learning": {
                "n_completed_tasks": self.n_completed_tasks,
                "current_knowledge": self.current_knowledge,
            },
        }


@dataclass
class AgentMetrics:
    """
    Текущие метрики агента.
    
    Соответствует гомеостатическим переменным.
    """
    # Финансы
    balance: float = 0.0
    total_earned: float = 0.0
    total_spent: float = 0.0
    
    # Репутация
    rating: float = 0.0
    n_reviews: int = 0
    n_positive: int = 0
    
    # Работа
    success_rate: float = 0.3
    avg_task_time: float = 1.0
    n_active_tasks: int = 0
    
    # Ресурсы
    token_budget: float = 100.0
    tokens_used: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "balance": self.balance,
            "total_earned": self.total_earned,
            "total_spent": self.total_spent,
            "rating": self.rating,
            "n_reviews": self.n_reviews,
            "success_rate": self.success_rate,
            "avg_task_time": self.avg_task_time,
            "n_active_tasks": self.n_active_tasks,
            "token_budget": self.token_budget,
            "tokens_used": self.tokens_used,
        }


@dataclass
class Agent:
    """
    Agent — автономный агент-фрилансер.
    
    Содержит:
    - Identity: базовая информация
    - Capabilities: что агент умеет
    - State: текущее состояние
    - Metrics: гомеостатические переменные
    """
    id: str
    name: str
    
    # Identity
    status: AgentStatus = AgentStatus.IDLE
    created_at: datetime = field(default_factory=datetime.now)
    
    # Capabilities
    capabilities: AgentCapabilities = field(default_factory=AgentCapabilities)
    
    # Metrics
    metrics: AgentMetrics = field(default_factory=AgentMetrics)
    
    # Mission alignment
    mission_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "capabilities": self.capabilities.to_dict(),
            "metrics": self.metrics.to_dict(),
            "mission_id": self.mission_id,
        }


@dataclass
class AgentContext:
    """
    AgentContext — контекст агента для принятия решений.
    
    Содержит всю информацию для работы агента в текущий момент.
    """
    # Текущий агент
    agent: Agent
    
    # Текущая миссия
    mission_id: Optional[str] = None
    mission_params: Dict[str, Any] = field(default_factory=dict)
    
    # Ресурсы
    available_budget: float = 100.0
    available_time: float = 24.0  # часы
    
    # Приоритеты
    urgency_multiplier: float = 1.0
    
    # Внешние сигналы
    external_signals: Dict[str, Any] = field(default_factory=dict)
    
    # Метаданные
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent.id,
            "mission_id": self.mission_id,
            "mission_params": self.mission_params,
            "available_budget": self.available_budget,
            "available_time": self.available_time,
            "urgency_multiplier": self.urgency_multiplier,
            "external_signals": self.external_signals,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


def create_agent(name: str) -> Agent:
    """Create a new agent with default capabilities."""
    import uuid
    return Agent(
        id=str(uuid.uuid4())[:8],
        name=name,
    )
