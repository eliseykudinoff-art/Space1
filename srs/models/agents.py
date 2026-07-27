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
    Возможности агента — 17 факторов (02_MATHEMATICAL_CORE.md Приложение A).
    
    x₁-x₁₇: llm_quality, code_gen, data_analysis, browser, code_exec,
    multimodal, negotiation, legal, design, research, testing, devops,
    i18n, accessibility, performance, security_audit, data_privacy
    """
    # Core LLM (x₁-x₄)
    llm_quality: float = 0.7
    code_gen: float = 0.7
    data_analysis: float = 0.7
    llm_reasoning: float = 0.7
    
    # Tools & Execution (x₅-x₇)
    browser: float = 0.0
    code_exec: float = 0.0
    multimodal: float = 0.0
    
    # Soft skills (x₈-x₁₀)
    negotiation: float = 0.5
    legal: float = 0.5
    design: float = 0.5
    
    # Domain expertise (x₁₁-x₁₃)
    research: float = 0.5
    testing: float = 0.5
    devops: float = 0.5
    
    # Specialized (x₁₄-x₁₇)
    i18n: float = 0.5
    accessibility: float = 0.5
    performance: float = 0.5
    security_audit: float = 0.5
    
    # Backward-compatible aliases
    llm_name: str = "unknown"
    llm_coding: float = 0.7
    llm_agentic: float = 0.7
    has_browser: bool = False
    has_file_system: bool = True
    has_mcp: bool = False
    n_completed_tasks: int = 0
    current_knowledge: float = 0.0
    
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "llm_name": self.llm_name,
            "capabilities": {
                "llm_quality": self.llm_quality,
                "code_gen": self.code_gen,
                "data_analysis": self.data_analysis,
                "llm_reasoning": self.llm_reasoning,
                "browser": self.browser,
                "code_exec": self.code_exec,
                "multimodal": self.multimodal,
                "negotiation": self.negotiation,
                "legal": self.legal,
                "design": self.design,
                "research": self.research,
                "testing": self.testing,
                "devops": self.devops,
                "i18n": self.i18n,
                "accessibility": self.accessibility,
                "performance": self.performance,
                "security_audit": self.security_audit,
            },
            "tools": {
                "has_browser": self.has_browser,
                "has_file_system": self.has_file_system,
                "has_mcp": self.has_mcp,
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
    
    # Репутация — 6-мерный вектор Υ (02_MATHEMATICAL_CORE.md §IV.5)
    # tech=техническая, econ=экономическая, comm=коммуникационная,
    # rel=реляционная, sec=безопасность, domain=доменная
    reputation_vector: Dict[str, float] = field(default_factory=lambda: {
        "tech": 0.5, "econ": 0.5, "comm": 0.5, "rel": 0.5, "sec": 0.5, "domain": 0.5
    })
    n_reviews: int = 0
    n_positive: int = 0

    # Backward-compatible scalar rating (computed from vector)
    @property
    def rating(self) -> float:
        """Scalar reputation: weighted average of 6 dimensions."""
        if not self.reputation_vector:
            return 0.0
        weights = {"tech": 0.20, "econ": 0.25, "comm": 0.15, "rel": 0.15, "sec": 0.15, "domain": 0.10}
        return sum(self.reputation_vector.get(k, 0.5) * w for k, w in weights.items())
    
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
            "reputation_vector": self.reputation_vector,
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
