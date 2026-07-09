"""
Task Model — Модель задачи с deadline awareness

Поля:
- deadline: datetime — крайний срок выполнения
- urgency_score: float — оценка срочности [0, 1]
- slack_time: float — оставшееся время до deadline в часах

Reference: DEVELOPMENT_PLAN.md - G23
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum


class TaskStatus(Enum):
    """Статус задачи."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Приоритет задачи."""
    LOW = 0.25
    MEDIUM = 0.50
    HIGH = 0.75
    CRITICAL = 1.0


@dataclass
class Task:
    """
    Task — модель задачи с deadline awareness.
    
    Атрибуты deadline:
    - deadline: крайний срок
    - urgency_score: нормализованная срочность [0, 1]
    - slack_time: оставшееся время в часах
    
    Usage:
        task = Task(
            title="Complete PR review",
            deadline=datetime.now() + timedelta(hours=4),
        )
        
        if task.urgency_score > 0.8:
            print("Critical task!")
    """
    
    # Core fields
    id: str
    title: str
    description: str = ""
    
    # Deadline fields (G23)
    deadline: Optional[datetime] = None
    urgency_score: float = 0.5  # [0, 1] — вычисляется автоматически
    slack_time: float = 0.0     # часы до deadline
    
    # Priority & Status
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    
    # Metadata
    estimated_hours: float = 1.0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Вычислить urgency_score и slack_time после инициализации."""
        self._update_deadline_fields()
    
    def _update_deadline_fields(self) -> None:
        """Обновить urgency_score и slack_time на основе deadline."""
        if self.deadline is None:
            self.urgency_score = 0.5  # По умолчанию средняя срочность
            self.slack_time = 24.0    # По умолчанию 24 часа
            return
        
        now = datetime.now()
        
        if self.deadline <= now:
            # Deadline прошёл
            self.slack_time = 0.0
            self.urgency_score = 1.0
        else:
            # slack_time = время до deadline в часах
            delta = self.deadline - now
            self.slack_time = delta.total_seconds() / 3600.0
            
            # urgency_score: чем меньше slack_time, тем выше urgency
            # Используем сигмоиду для плавного перехода
            # При slack_time → 0: urgency → 1
            # При slack_time → 24h: urgency → 0.5
            # При slack_time → ∞: urgency → 0
            
            if self.slack_time <= 0:
                self.urgency_score = 1.0
            elif self.slack_time >= 24:
                # При slack > 24h urgency ниже среднего
                self.urgency_score = 0.5 * (1.0 - (self.slack_time - 24) / 100)
                self.urgency_score = max(0.1, self.urgency_score)
            else:
                # Линейная интерполяция для 0-24h
                self.urgency_score = 1.0 - (self.slack_time / 48.0)
                self.urgency_score = max(0.1, min(0.95, self.urgency_score))
    
    def refresh_deadline(self) -> None:
        """Пересчитать urgency и slack_time."""
        self._update_deadline_fields()
    
    @property
    def is_overdue(self) -> bool:
        """Проверить, просрочена ли задача."""
        if self.deadline is None:
            return False
        return datetime.now() > self.deadline
    
    @property
    def is_critical(self) -> bool:
        """Проверить, критична ли задача (urgency > 0.8)."""
        return self.urgency_score > 0.8
    
    @property
    def can_start(self) -> bool:
        """Проверить, можно ли начать задачу."""
        return self.status == TaskStatus.PENDING and not self.is_overdue
    
    def start(self) -> bool:
        """Начать выполнение задачи. Returns True если успешно."""
        if not self.can_start:
            return False
        self.status = TaskStatus.IN_PROGRESS
        self.started_at = datetime.now()
        return True
    
    def complete(self) -> bool:
        """Завершить задачу. Returns True если успешно."""
        if self.status not in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS):
            return False
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        return True
    
    def fail(self, reason: str = "") -> None:
        """Отметить задачу как проваленную."""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.metadata["failure_reason"] = reason
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализовать в словарь."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "urgency_score": self.urgency_score,
            "slack_time": self.slack_time,
            "priority": self.priority.name,
            "status": self.status.value,
            "estimated_hours": self.estimated_hours,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "is_overdue": self.is_overdue,
            "is_critical": self.is_critical,
        }


def create_task(
    title: str,
    deadline: Optional[datetime] = None,
    priority: TaskPriority = TaskPriority.MEDIUM,
    estimated_hours: float = 1.0,
    tags: Optional[List[str]] = None,
) -> Task:
    """Create a new task with deadline awareness."""
    task_id = f"task_{datetime.now().timestamp()}"
    
    task = Task(
        id=task_id,
        title=title,
        deadline=deadline,
        priority=priority,
        estimated_hours=estimated_hours,
        tags=tags or [],
    )
    
    return task


def calculate_schedule(tasks: List[Task], available_hours: float) -> Dict[str, Any]:
    """
    Рассчитать расписание задач на основе urgency и estimated_hours.
    
    Args:
        tasks: Список задач
        available_hours: Доступное время в часах
        
    Returns:
        Dict с scheduled и dropped задачами
    """
    # Сортировать по urgency_score (DESC)
    sorted_tasks = sorted(tasks, key=lambda t: t.urgency_score, reverse=True)
    
    scheduled = []
    dropped = []
    total_hours = 0.0
    
    for task in sorted_tasks:
        if total_hours + task.estimated_hours <= available_hours:
            scheduled.append(task)
            total_hours += task.estimated_hours
        else:
            dropped.append(task)
    
    return {
        "scheduled": scheduled,
        "dropped": dropped,
        "total_hours": total_hours,
        "utilization": total_hours / available_hours if available_hours > 0 else 0,
    }
