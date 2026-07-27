"""
Task Model — Модель задачи с декомпозицией и классификацией сложности

Reference: DEVELOPMENT_PLAN.md - G23
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
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


class TaskComplexityClassifier:
    """
    TaskComplexityClassifier (G10/G12).
    
    Classifier inspired by the drafts ordinal MLP. Evaluates task textual features 
    to output predicted complexity levels, entropy (uncertainty), and suggested routing decision.
    """
    
    def __init__(self):
        # Semantic labels and keywords associated with complexity
        self.complexity_keywords = {
            "critical": 1.0,
            "error": 0.8,
            "leak": 0.8,
            "refactor": 0.75,
            "database": 0.7,
            "api": 0.5,
            "fix": 0.4,
            "typo": 0.15,
            "update": 0.2,
        }

    def predict_complexity(self, title: str, description: str = "") -> Tuple[float, float, str]:
        """
        Predict complexity level, entropy (uncertainty) and suggest routing.
        
        Returns:
            Tuple[complexity_score [0.0, 1.0], entropy, suggested_routing_decision]
        """
        text = (title + " " + description).lower()
        score_sum = 0.0
        matches = 0
        
        for kw, val in self.complexity_keywords.items():
            if kw in text:
                score_sum += val
                matches += 1
                
        # Default complexity: если нет ключевых слов — эвристика по длине описания
        if matches > 0:
            complexity_score = score_sum / matches
        else:
            # Эвристика: длинные задачи обычно сложнее
            word_count = len(text.split())
            if word_count < 5:
                complexity_score = 0.2  # Очень короткая = простая
            elif word_count < 15:
                complexity_score = 0.4  # Короткая = средняя
            elif word_count < 30:
                complexity_score = 0.6  # Средняя = сложная
            else:
                complexity_score = 0.8  # Длинная = очень сложная
        complexity_score = max(0.1, min(1.0, complexity_score))
        
        # Calculate mock probabilities distribution across 5 ordinal classes to calculate entropy
        # Softmax-like distance from complexity_score
        classes_centers = [0.15, 0.35, 0.55, 0.75, 0.95]
        diffs = [abs(complexity_score - c) for c in classes_centers]
        import math
        exp_terms = [math.exp(-20 * d) for d in diffs]
        total = sum(exp_terms)
        probs = [e / total for e in exp_terms]
        
        # Calculate Entropy H = -sum(p * log(p))
        entropy = -sum(p * math.log2(p) for p in probs if p > 0)
        
        # Routing Decision based on both complexity score and prediction entropy
        if complexity_score < 0.4:
            decision = "AUTO_ASSIGN" if entropy < 1.1 else "HUMAN_REVIEW"
        elif complexity_score > 0.6:
            decision = "ESCALATE" if entropy < 0.8 else "HUMAN_REVIEW"
        else:
            decision = "AUTO_ASSIGN" if entropy < 0.8 else "HUMAN_REVIEW"
            
        return complexity_score, entropy, decision

    def predict_complexity_self_consistency(
        self,
        title: str,
        description: str = "",
        m_runs: int = 5,
        temperature: float = 0.0
    ) -> Tuple[float, float, str, float]:
        """
        Task Complexity Classification using the Self-Consistency method (m runs with temperature).
        Returns:
            Tuple[mean_complexity_score, entropy, suggested_routing_decision, std_deviation]
        """
        import random
        import math
        
        scores = []
        for _ in range(m_runs):
            base_score, _, _ = self.predict_complexity(title, description)
            # Inject temperature-based noise
            noise = random.gauss(0, temperature)
            scores.append(max(0.1, min(1.0, base_score + noise)))
            
        mean_score = sum(scores) / m_runs
        
        # Calculate standard deviation
        variance = sum((s - mean_score) ** 2 for s in scores) / m_runs
        std_dev = math.sqrt(variance)
        
        # Recalculate entropy and suggested routing using mean score
        classes_centers = [0.15, 0.35, 0.55, 0.75, 0.95]
        diffs = [abs(mean_score - c) for c in classes_centers]
        exp_terms = [math.exp(-20 * d) for d in diffs]
        total = sum(exp_terms)
        probs = [e / total for e in exp_terms]
        
        entropy = -sum(p * math.log2(p) for p in probs if p > 0)
        
        if mean_score < 0.4:
            decision = "AUTO_ASSIGN" if entropy < 1.1 else "HUMAN_REVIEW"
        elif mean_score > 0.6:
            decision = "ESCALATE" if entropy < 0.8 else "HUMAN_REVIEW"
        else:
            decision = "AUTO_ASSIGN" if entropy < 0.8 else "HUMAN_REVIEW"
            
        return mean_score, entropy, decision, std_dev


def platt_scale(conf_raw: float, alpha: float = 1.0, beta: float = 0.0) -> float:
    """Sigmoid calibration of raw confidence values (Platt Scaling)."""
    import math
    return 1.0 / (1.0 + math.exp(-(alpha * conf_raw + beta)))



class TaskSource(Enum):
    """Источник задачи — 01_CONCEPT.md §I.2"""
    MARKETPLACE = "MARKETPLACE"
    OWNER_DIRECT = "OWNER_DIRECT"


@dataclass
class Attachment:
    """Вложение к задаче — 04_ARCHITECTURE.md §IX"""
    filename: str
    content_type: str
    size_bytes: int
    url: Optional[str] = None
    content: Optional[str] = None

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
    source: TaskSource = TaskSource.MARKETPLACE
    
    
    # Typed fields (04_ARCHITECTURE.md §IX) — раньше были в metadata
    price: Optional[float] = None
    attachments: List[Attachment] = field(default_factory=list)
    capability_vector: Optional[Dict[str, float]] = None
    # Metadata
    estimated_hours: float = 1.0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Вычислить urgency_score, slack_time и авто-классифицировать сложность."""
        # Валидация: deadline не может быть в прошлом
        if self.deadline is not None and self.deadline < datetime.now():
            raise ValueError(f"deadline не может быть в прошлом: {self.deadline}")
        self._update_deadline_fields()
        
        # Auto-classify complexity if not already present
        if "complexity" not in self.metadata:
            classifier = TaskComplexityClassifier()
            comp, entropy, routing, std_dev = classifier.predict_complexity_self_consistency(self.title, self.description)
            self.metadata["complexity"] = comp
            self.metadata["complexity_entropy"] = entropy
            self.metadata["routing_decision"] = routing
            self.metadata["complexity_std"] = std_dev
            
            # Platt scale the confidence
            raw_conf = 1.0 - entropy
            self.metadata["platt_confidence"] = platt_scale(raw_conf, alpha=1.5, beta=0.2)
            
            # Set priority critical if classifier recommends escalate
            if routing == "ESCALATE":
                self.priority = TaskPriority.CRITICAL
    
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
            "source": self.source,
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
    source: TaskSource = TaskSource.MARKETPLACE,
    description: str = "",
    deadline: Optional[datetime] = None,
    priority: TaskPriority = TaskPriority.MEDIUM,
    estimated_hours: float = 1.0,
    tags: Optional[List[str]] = None,
) -> Task:
    """Create a new task with deadline awareness and auto-classification."""
    task_id = f"task_{datetime.now().timestamp()}"
    
    task = Task(
        id=task_id,
        title=title,
        description=description,
        deadline=deadline,
        source=source,
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
