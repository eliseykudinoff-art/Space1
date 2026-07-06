"""
🌐 Граф Знаний — Модуль «Цифровой Сад»
=========================================
Полноценный граф знаний на NetworkX с поддержкой:
  - Сущности (узлы) и связи (рёбра) с типизацией
  - Временные метки (динамический граф)
  - Иерархическая декомпозиция задач (HTN)
  - Планирование с временными ограничениями (STN)
  - Деревья поведения (Behavior Trees) для реактивности
  - Blackboard-паттерн (общая память состояния мира)
  - Поиск путей, кластеров, паттернов
  - Парадигмальные overlay-графы
  - Персистентность (JSON-сериализация)
  - Интеграция с Memory (Entity/Fact → Node/Edge)
"""

import json
import time
import hashlib
import logging
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Any, Tuple, Set, Callable
from enum import Enum
from collections import defaultdict, deque

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

logger = logging.getLogger("digital_garden.knowledge_graph")


# ═══════════════════════════════════════════════════════════════
# КОНФИГУРАЦИЯ
# ═══════════════════════════════════════════════════════════════

@dataclass
class GraphConfig:
    """Настройки графа знаний."""
    storage_path: str = "./storage/graph"
    auto_sync_entities: bool = True       # Автосинхронизация с Memory entities
    auto_extract_relations: bool = True   # Авто-извлечение связей из текста
    max_nodes: int = 10000
    max_edges: int = 50000
    enable_temporal: bool = True          # Временные метки на рёбрах
    enable_htn: bool = True               # HTN-планирование
    enable_blackboard: bool = True        # Blackboard-паттерн
    paradigm_overlay: bool = True         # Парадигмальные overlay-графы
    graph_context_depth: int = 2          # Глубина обхода для контекста
    decay_factor: float = 0.95            # Затухание веса рёбер со временем


# ═══════════════════════════════════════════════════════════════
# ТИПЫ УЗЛОВ И РЁБЕР
# ═══════════════════════════════════════════════════════════════

class NodeType(str, Enum):
    """Типы узлов графа."""
    PERSON = "person"
    PROJECT = "project"
    CONCEPT = "concept"
    TOOL = "tool"
    PLACE = "place"
    ORGANIZATION = "organization"
    SKILL = "skill"
    GOAL = "goal"
    TASK = "task"
    EVENT = "event"
    RESOURCE = "resource"
    FACT = "fact"
    PARADIGM = "paradigm"
    STATE = "state"            # Состояние (энергия, настроение)
    PRACTICE = "practice"      # Практика (цигун, медитация)
    FINANCIAL = "financial"    # Финансовая сущность


class EdgeType(str, Enum):
    """Типы связей (рёбер) графа."""
    # Общие
    RELATED_TO = "related_to"
    PART_OF = "part_of"
    DEPENDS_ON = "depends_on"
    CAUSES = "causes"
    PREVENTS = "prevents"
    ENABLES = "enables"
    CONTRADICTS = "contradicts"
    SUPPORTS = "supports"
    # Люди
    KNOWS = "knows"
    WORKS_WITH = "works_with"
    CLIENT_OF = "client_of"
    # Задачи / HTN
    SUBTASK_OF = "subtask_of"
    PRECEDES = "precedes"
    FOLLOWS = "follows"
    BLOCKS = "blocks"
    # Знания
    LEARNED_FROM = "learned_from"
    APPLIES_TO = "applies_to"
    INSTANCE_OF = "instance_of"
    # Каузальные
    CORRELATES_WITH = "correlates_with"
    INFLUENCES = "influences"
    # Временные
    HAPPENED_BEFORE = "happened_before"
    HAPPENED_AFTER = "happened_after"
    CONCURRENT_WITH = "concurrent_with"


# ═══════════════════════════════════════════════════════════════
# BLACKBOARD — ОБЩАЯ ПАМЯТЬ СОСТОЯНИЯ МИРА
# ═══════════════════════════════════════════════════════════════

class Blackboard:
    """
    Blackboard-паттерн: общая память текущего состояния мира.
    
    Любой модуль может читать/писать сюда. Это «доска объявлений»
    для координации между компонентами без жёсткой связности.
    
    Секции:
    - user_state: энергия, настроение, доступное время
    - world_state: время суток, день недели, погода
    - system_state: доступные ресурсы, активные задачи
    - goals: текущие цели и приоритеты
    - constraints: ограничения (бюджет, железо, время)
    """
    
    def __init__(self, storage_path: str = "./storage/blackboard"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._data: Dict[str, Dict[str, Any]] = {
            "user_state": {},
            "world_state": {},
            "system_state": {},
            "goals": {},
            "constraints": {},
            "custom": {},
        }
        self._history: List[Dict] = []  # Лог изменений
        self._load()
    
    def read(self, section: str, key: Optional[str] = None) -> Any:
        """Прочитать значение с доски."""
        if section not in self._data:
            return None
        if key is None:
            return self._data[section]
        return self._data[section].get(key)
    
    def write(self, section: str, key: str, value: Any, source: str = "unknown"):
        """Записать значение на доску."""
        if section not in self._data:
            self._data[section] = {}
        
        old_value = self._data[section].get(key)
        self._data[section][key] = value
        
        # Логируем изменение
        self._history.append({
            "timestamp": time.time(),
            "section": section,
            "key": key,
            "old_value": old_value,
            "new_value": value,
            "source": source,
        })
        
        # Обрезаем историю (последние 500 записей)
        if len(self._history) > 500:
            self._history = self._history[-500:]
        
        self._save()
    
    def get_snapshot(self) -> Dict[str, Any]:
        """Полный снимок состояния доски."""
        return {
            "data": dict(self._data),
            "last_updated": self._history[-1]["timestamp"] if self._history else 0,
            "changes_count": len(self._history),
        }
    
    def get_recent_changes(self, limit: int = 10) -> List[Dict]:
        """Последние изменения."""
        return self._history[-limit:]
    
    def _save(self):
        filepath = self.storage_path / "blackboard.json"
        filepath.write_text(json.dumps({
            "data": self._data,
            "history": self._history[-100:],  # Сохраняем последние 100
        }, ensure_ascii=False, indent=2), encoding="utf-8")
    
    def _load(self):
        filepath = self.storage_path / "blackboard.json"
        if filepath.exists():
            try:
                raw = json.loads(filepath.read_text(encoding="utf-8"))
                self._data = raw.get("data", self._data)
                self._history = raw.get("history", [])
            except Exception as e:
                logger.warning(f"Ошибка загрузки Blackboard: {e}")


# ═══════════════════════════════════════════════════════════════
# HTN-ПЛАНИРОВЩИК (Hierarchical Task Networks)
# ═══════════════════════════════════════════════════════════════

class TaskStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"         # Все зависимости выполнены
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"     # Заблокирована зависимостями
    CANCELLED = "cancelled"


@dataclass
class HTNTask:
    """Задача в иерархической сети."""
    id: str
    name: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 5           # 1=высший, 10=низший
    # Временные ограничения (STN)
    earliest_start: Optional[float] = None
    latest_finish: Optional[float] = None
    estimated_duration: float = 0  # секунды
    actual_start: Optional[float] = None
    actual_finish: Optional[float] = None
    # Иерархия
    parent_id: Optional[str] = None
    subtask_ids: List[str] = field(default_factory=list)
    # Зависимости
    depends_on: List[str] = field(default_factory=list)  # task_ids
    blocks: List[str] = field(default_factory=list)       # task_ids
    # Контекст
    required_resources: List[str] = field(default_factory=list)
    required_energy: int = 5    # 1-10
    tags: List[str] = field(default_factory=list)
    result: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d
    
    @classmethod
    def from_dict(cls, data: Dict) -> "HTNTask":
        data["status"] = TaskStatus(data.get("status", "pending"))
        valid_fields = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


class HTNPlanner:
    """
    Иерархический планировщик задач.
    
    Возможности:
    - Декомпозиция целей в дерево подзадач
    - Учёт зависимостей (DAG)
    - Временные ограничения (STN-подобные)
    - Meta-reasoning: обнаружение петель и тупиков
    - Replanning: откат и перестроение при ошибках
    - Учёт энергии пользователя при выборе задачи
    """
    
    def __init__(self, blackboard: Blackboard):
        self.blackboard = blackboard
        self.tasks: Dict[str, HTNTask] = {}
        self._task_counter = 0
        
        if HAS_NETWORKX:
            self.task_graph = nx.DiGraph()  # DAG зависимостей
        else:
            self.task_graph = None
    
    def _next_id(self) -> str:
        self._task_counter += 1
        return f"htn_{self._task_counter:04d}_{int(time.time()) % 100000}"
    
    def create_goal(self, name: str, description: str = "", 
                    deadline: Optional[float] = None,
                    priority: int = 5) -> HTNTask:
        """Создать верхнеуровневую цель."""
        task = HTNTask(
            id=self._next_id(),
            name=name,
            description=description,
            priority=priority,
            latest_finish=deadline,
        )
        self.tasks[task.id] = task
        if self.task_graph is not None:
            self.task_graph.add_node(task.id, **task.to_dict())
        logger.info(f"🎯 Цель создана: {name}")
        return task
    
    def decompose(self, parent_id: str, subtasks: List[Dict[str, Any]]) -> List[HTNTask]:
        """
        Декомпозиция задачи на подзадачи.
        
        subtasks: [{"name": "...", "description": "...", "depends_on": [...], ...}]
        """
        parent = self.tasks.get(parent_id)
        if not parent:
            raise ValueError(f"Задача не найдена: {parent_id}")
        
        created = []
        for st_data in subtasks:
            task = HTNTask(
                id=self._next_id(),
                name=st_data["name"],
                description=st_data.get("description", ""),
                parent_id=parent_id,
                priority=st_data.get("priority", parent.priority),
                estimated_duration=st_data.get("duration", 0),
                required_energy=st_data.get("energy", 5),
                depends_on=st_data.get("depends_on", []),
                tags=st_data.get("tags", []),
            )
            self.tasks[task.id] = task
            parent.subtask_ids.append(task.id)
            
            if self.task_graph is not None:
                self.task_graph.add_node(task.id, **task.to_dict())
                self.task_graph.add_edge(parent_id, task.id, relation="subtask_of")
                # Добавляем рёбра зависимостей
                for dep_id in task.depends_on:
                    if dep_id in self.tasks:
                        self.task_graph.add_edge(dep_id, task.id, relation="precedes")
            
            created.append(task)
        
        return created
    
    def get_next_tasks(self, max_energy: int = 10, max_count: int = 5) -> List[HTNTask]:
        """
        Получить следующие задачи для выполнения.
        
        Учитывает:
        - Зависимости (все предшественники выполнены)
        - Энергию пользователя (из Blackboard)
        - Приоритет
        - Временные ограничения
        """
        # Получаем текущую энергию из Blackboard
        user_energy = self.blackboard.read("user_state", "energy") or max_energy
        
        ready_tasks = []
        for task in self.tasks.values():
            if task.status != TaskStatus.PENDING:
                continue
            
            # Проверяем зависимости
            deps_met = all(
                self.tasks.get(dep_id, HTNTask(id="", name="")).status == TaskStatus.COMPLETED
                for dep_id in task.depends_on
            )
            if not deps_met:
                continue
            
            # Проверяем энергию
            if task.required_energy > user_energy:
                continue
            
            # Проверяем временные ограничения
            now = time.time()
            if task.earliest_start and now < task.earliest_start:
                continue
            
            ready_tasks.append(task)
        
        # Сортируем: приоритет → дедлайн → энергия (меньше = легче начать)
        ready_tasks.sort(key=lambda t: (
            t.priority,
            t.latest_finish or float('inf'),
            t.required_energy,
        ))
        
        return ready_tasks[:max_count]
    
    def complete_task(self, task_id: str, result: Optional[str] = None):
        """Отметить задачу как выполненную."""
        task = self.tasks.get(task_id)
        if not task:
            return
        
        task.status = TaskStatus.COMPLETED
        task.actual_finish = time.time()
        task.result = result
        
        # Проверяем, все ли подзадачи родителя выполнены
        if task.parent_id:
            parent = self.tasks.get(task.parent_id)
            if parent:
                all_done = all(
                    self.tasks.get(sid, HTNTask(id="", name="")).status == TaskStatus.COMPLETED
                    for sid in parent.subtask_ids
                )
                if all_done:
                    parent.status = TaskStatus.COMPLETED
                    parent.actual_finish = time.time()
                    logger.info(f"✅ Цель достигнута: {parent.name}")
        
        logger.info(f"✅ Задача выполнена: {task.name}")
    
    def fail_task(self, task_id: str, reason: str = ""):
        """Отметить задачу как проваленную + replan."""
        task = self.tasks.get(task_id)
        if not task:
            return
        
        task.status = TaskStatus.FAILED
        task.result = f"FAILED: {reason}"
        
        # Блокируем зависимые задачи
        for other in self.tasks.values():
            if task_id in other.depends_on:
                other.status = TaskStatus.BLOCKED
        
        logger.warning(f"❌ Задача провалена: {task.name}. Причина: {reason}")
    
    def replan(self, failed_task_id: str) -> List[str]:
        """
        Перепланирование после провала.
        Возвращает список заблокированных задач, которые нужно пересмотреть.
        """
        blocked = [
            t.id for t in self.tasks.values()
            if t.status == TaskStatus.BLOCKED
        ]
        
        # Сбрасываем блокировку — пользователь решит что делать
        for tid in blocked:
            self.tasks[tid].status = TaskStatus.PENDING
        
        return blocked
    
    def detect_cycles(self) -> List[List[str]]:
        """Meta-reasoning: обнаружение петель в зависимостях."""
        if self.task_graph is None or not HAS_NETWORKX:
            return []
        try:
            cycles = list(nx.simple_cycles(self.task_graph))
            if cycles:
                logger.warning(f"⚠️ Обнаружены петли в графе задач: {len(cycles)}")
            return cycles
        except:
            return []
    
    def get_critical_path(self) -> List[str]:
        """Находит критический путь (самая длинная цепочка зависимостей)."""
        if self.task_graph is None or not HAS_NETWORKX:
            return []
        try:
            return nx.dag_longest_path(self.task_graph, weight="estimated_duration")
        except:
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Статистика планировщика."""
        status_counts = defaultdict(int)
        for task in self.tasks.values():
            status_counts[task.status.value] += 1
        
        return {
            "total_tasks": len(self.tasks),
            "by_status": dict(status_counts),
            "cycles_detected": len(self.detect_cycles()),
            "critical_path_length": len(self.get_critical_path()),
        }
    
    def to_dict(self) -> Dict:
        """Сериализация для сохранения."""
        return {
            "tasks": {tid: t.to_dict() for tid, t in self.tasks.items()},
            "counter": self._task_counter,
        }
    
    def load_from_dict(self, data: Dict):
        """Загрузка из сериализованных данных."""
        self._task_counter = data.get("counter", 0)
        for tid, tdata in data.get("tasks", {}).items():
            self.tasks[tid] = HTNTask.from_dict(tdata)
            if self.task_graph is not None:
                self.task_graph.add_node(tid, **tdata)


# ═══════════════════════════════════════════════════════════════
# BEHAVIOR TREE — ДЕРЕВО ПОВЕДЕНИЯ (реактивность)
# ═══════════════════════════════════════════════════════════════

class BTStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    RUNNING = "running"


class BTNode:
    """Базовый узел дерева поведения."""
    def __init__(self, name: str):
        self.name = name
        self.status = BTStatus.RUNNING
    
    def tick(self, blackboard: Blackboard) -> BTStatus:
        """Один тик выполнения. Переопределяется в подклассах."""
        return BTStatus.SUCCESS


class BTSequence(BTNode):
    """Последовательность: выполняет детей по порядку, останавливается при FAILURE."""
    def __init__(self, name: str, children: List[BTNode]):
        super().__init__(name)
        self.children = children
    
    def tick(self, blackboard: Blackboard) -> BTStatus:
        for child in self.children:
            status = child.tick(blackboard)
            if status != BTStatus.SUCCESS:
                self.status = status
                return status
        self.status = BTStatus.SUCCESS
        return BTStatus.SUCCESS


class BTSelector(BTNode):
    """Селектор: пробует детей по порядку, останавливается при SUCCESS."""
    def __init__(self, name: str, children: List[BTNode]):
        super().__init__(name)
        self.children = children
    
    def tick(self, blackboard: Blackboard) -> BTStatus:
        for child in self.children:
            status = child.tick(blackboard)
            if status != BTStatus.FAILURE:
                self.status = status
                return status
        self.status = BTStatus.FAILURE
        return BTStatus.FAILURE


class BTCondition(BTNode):
    """Условие: проверяет значение на Blackboard."""
    def __init__(self, name: str, section: str, key: str, 
                 check_fn: Callable[[Any], bool]):
        super().__init__(name)
        self.section = section
        self.key = key
        self.check_fn = check_fn
    
    def tick(self, blackboard: Blackboard) -> BTStatus:
        value = blackboard.read(self.section, self.key)
        if self.check_fn(value):
            self.status = BTStatus.SUCCESS
            return BTStatus.SUCCESS
        self.status = BTStatus.FAILURE
        return BTStatus.FAILURE


class BTAction(BTNode):
    """Действие: выполняет функцию."""
    def __init__(self, name: str, action_fn: Callable[[Blackboard], BTStatus]):
        super().__init__(name)
        self.action_fn = action_fn
    
    def tick(self, blackboard: Blackboard) -> BTStatus:
        self.status = self.action_fn(blackboard)
        return self.status


# ═══════════════════════════════════════════════════════════════
# ГЛАВНЫЙ КЛАСС — ГРАФ ЗНАНИЙ
# ═══════════════════════════════════════════════════════════════

class KnowledgeGraph:
    """
    Граф знаний экосистемы «Цифровой Сад».
    
    Объединяет:
    - NetworkX-граф сущностей и связей
    - HTN-планировщик задач
    - Blackboard (общая память состояния)
    - Behavior Trees (реактивное поведение)
    - Парадигмальные overlay-графы
    - Временные метки (динамический граф)
    
    Использование:
        kg = KnowledgeGraph(config)
        kg.add_node("Python", NodeType.SKILL, {"level": "beginner"})
        kg.add_node("Дизайн", NodeType.SKILL, {"level": "intermediate"})
        kg.add_edge("Python", "Дизайн", EdgeType.ENABLES, weight=0.7)
        
        # Поиск связей
        neighbors = kg.get_neighbors("Python", depth=2)
        
        # Контекст для LLM
        context = kg.get_context_for_query("как мне заработать на дизайне?")
        
        # Планирование
        goal = kg.planner.create_goal("Найти работу дизайнером")
        kg.planner.decompose(goal.id, [...])
        next_tasks = kg.planner.get_next_tasks(max_energy=6)
    """
    
    def __init__(self, config: Optional[GraphConfig] = None):
        self.config = config or GraphConfig()
        self.storage_path = Path(self.config.storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Основной граф
        if HAS_NETWORKX:
            self.graph = nx.MultiDiGraph()  # Направленный мультиграф
        else:
            self.graph = None
            logger.warning("⚠️ NetworkX не установлен. Граф работает в ограниченном режиме.")
        
        # Компоненты
        self.blackboard = Blackboard(str(self.storage_path / "blackboard"))
        self.planner = HTNPlanner(self.blackboard)
        
        # Парадигмальные overlay-графы
        self._paradigm_overlays: Dict[str, Dict[str, Any]] = {}
        
        # Индексы
        self._node_index: Dict[str, Dict[str, Any]] = {}  # name -> node_data
        self._type_index: Dict[str, Set[str]] = defaultdict(set)  # type -> {node_ids}
        
        # Загрузка
        self._load()
        
        logger.info(f"🌐 Граф знаний инициализирован: {self.node_count} узлов, {self.edge_count} связей")
    
    # ═══════════════════════════════════════════════════════════
    # ОСНОВНЫЕ ОПЕРАЦИИ С ГРАФОМ
    # ═══════════════════════════════════════════════════════════
    
    @property
    def node_count(self) -> int:
        if self.graph is not None:
            return self.graph.number_of_nodes()
        return len(self._node_index)
    
    @property
    def edge_count(self) -> int:
        if self.graph is not None:
            return self.graph.number_of_edges()
        return 0
    
    def add_node(self, name: str, node_type: NodeType, 
                 attributes: Optional[Dict] = None,
                 tags: Optional[List[str]] = None) -> str:
        """
        Добавить узел в граф.
        
        Returns: node_id
        """
        node_id = hashlib.md5(f"{node_type.value}:{name}".encode()).hexdigest()[:12]
        
        node_data = {
            "id": node_id,
            "name": name,
            "type": node_type.value,
            "attributes": attributes or {},
            "tags": tags or [],
            "created": time.time(),
            "updated": time.time(),
            "access_count": 0,
        }
        
        if self.graph is not None:
            self.graph.add_node(node_id, **node_data)
        
        self._node_index[node_id] = node_data
        self._type_index[node_type.value].add(node_id)
        
        logger.debug(f"➕ Узел: {name} ({node_type.value})")
        return node_id
    
    def add_edge(self, source_name: str, target_name: str, 
                 edge_type: EdgeType, weight: float = 1.0,
                 attributes: Optional[Dict] = None) -> bool:
        """
        Добавить связь между узлами (по имени).
        
        Returns: True если связь создана
        """
        source_id = self._find_node_id(source_name)
        target_id = self._find_node_id(target_name)
        
        if not source_id or not target_id:
            logger.warning(f"Узел не найден: {source_name if not source_id else target_name}")
            return False
        
        edge_data = {
            "type": edge_type.value,
            "weight": weight,
            "attributes": attributes or {},
            "created": time.time(),
        }
        
        if self.config.enable_temporal:
            edge_data["timestamp"] = time.time()
        
        if self.graph is not None:
            self.graph.add_edge(source_id, target_id, **edge_data)
        
        logger.debug(f"🔗 Связь: {source_name} --[{edge_type.value}]--> {target_name}")
        return True
    
    def remove_node(self, name: str) -> bool:
        """Удалить узел и все его связи."""
        node_id = self._find_node_id(name)
        if not node_id:
            return False
        
        if self.graph is not None:
            self.graph.remove_node(node_id)
        
        node_data = self._node_index.pop(node_id, {})
        node_type = node_data.get("type", "")
        self._type_index[node_type].discard(node_id)
        
        return True
    
    def _find_node_id(self, name: str) -> Optional[str]:
        """Найти ID узла по имени."""
        for nid, data in self._node_index.items():
            if data.get("name", "").lower() == name.lower():
                return nid
        return None
    
    # ═══════════════════════════════════════════════════════════
    # ЗАПРОСЫ К ГРАФУ
    # ═══════════════════════════════════════════════════════════
    
    def get_neighbors(self, name: str, depth: int = 1, 
                      edge_types: Optional[List[EdgeType]] = None) -> List[Dict]:
        """
        Получить соседей узла с заданной глубиной обхода.
        
        Returns: список узлов с расстоянием и типом связи
        """
        node_id = self._find_node_id(name)
        if not node_id or self.graph is None:
            return []
        
        result = []
        visited = {node_id}
        queue = deque([(node_id, 0)])
        
        while queue:
            current_id, current_depth = queue.popleft()
            if current_depth >= depth:
                continue
            
            # Исходящие рёбра
            for _, target_id, edge_data in self.graph.out_edges(current_id, data=True):
                if target_id in visited:
                    continue
                
                if edge_types and EdgeType(edge_data.get("type", "")) not in edge_types:
                    continue
                
                visited.add(target_id)
                target_data = self._node_index.get(target_id, {})
                result.append({
                    "node": target_data,
                    "distance": current_depth + 1,
                    "edge_type": edge_data.get("type", "related_to"),
                    "edge_weight": edge_data.get("weight", 1.0),
                })
                queue.append((target_id, current_depth + 1))
            
            # Входящие рёбра
            for source_id, _, edge_data in self.graph.in_edges(current_id, data=True):
                if source_id in visited:
                    continue
                
                if edge_types and EdgeType(edge_data.get("type", "")) not in edge_types:
                    continue
                
                visited.add(source_id)
                source_data = self._node_index.get(source_id, {})
                result.append({
                    "node": source_data,
                    "distance": current_depth + 1,
                    "edge_type": edge_data.get("type", "related_to"),
                    "edge_weight": edge_data.get("weight", 1.0),
                    "direction": "incoming",
                })
                queue.append((source_id, current_depth + 1))
        
        return result
    
    def find_path(self, source_name: str, target_name: str) -> List[Dict]:
        """Найти кратчайший путь между двумя узлами."""
        source_id = self._find_node_id(source_name)
        target_id = self._find_node_id(target_name)
        
        if not source_id or not target_id or self.graph is None:
            return []
        
        try:
            path_ids = nx.shortest_path(self.graph, source_id, target_id)
            path = []
            for i, nid in enumerate(path_ids):
                node_data = self._node_index.get(nid, {})
                edge_info = None
                if i > 0:
                    edges = self.graph.get_edge_data(path_ids[i-1], nid)
                    if edges:
                        edge_info = list(edges.values())[0] if edges else None
                path.append({
                    "node": node_data,
                    "edge_from_previous": edge_info,
                })
            return path
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []
    
    def find_clusters(self) -> List[List[str]]:
        """Найти кластеры (сообщества) в графе."""
        if self.graph is None or self.node_count < 3:
            return []
        
        # Конвертируем в неориентированный для поиска сообществ
        undirected = self.graph.to_undirected()
        components = list(nx.connected_components(undirected))
        
        clusters = []
        for component in components:
            cluster_names = [
                self._node_index.get(nid, {}).get("name", nid)
                for nid in component
            ]
            clusters.append(cluster_names)
        
        return sorted(clusters, key=len, reverse=True)
    
    def get_central_nodes(self, top_n: int = 10) -> List[Dict]:
        """Найти самые важные (центральные) узлы."""
        if self.graph is None or self.node_count == 0:
            return []
        
        try:
            centrality = nx.degree_centrality(self.graph)
            sorted_nodes = sorted(centrality.items(), key=lambda x: -x[1])[:top_n]
            
            result = []
            for nid, score in sorted_nodes:
                node_data = self._node_index.get(nid, {})
                result.append({
                    "name": node_data.get("name", nid),
                    "type": node_data.get("type", "unknown"),
                    "centrality": round(score, 4),
                    "connections": self.graph.degree(nid),
                })
            return result
        except:
            return []
    
    def get_causal_chain(self, start_name: str) -> List[Dict]:
        """
        Получить каузальную цепочку от узла.
        Следует только по рёбрам типа CAUSES, INFLUENCES, ENABLES.
        """
        causal_types = {EdgeType.CAUSES.value, EdgeType.INFLUENCES.value, EdgeType.ENABLES.value}
        
        node_id = self._find_node_id(start_name)
        if not node_id or self.graph is None:
            return []
        
        chain = []
        visited = {node_id}
        queue = deque([node_id])
        
        while queue:
            current = queue.popleft()
            current_data = self._node_index.get(current, {})
            
            for _, target, edge_data in self.graph.out_edges(current, data=True):
                if target in visited:
                    continue
                if edge_data.get("type") not in causal_types:
                    continue
                
                visited.add(target)
                target_data = self._node_index.get(target, {})
                chain.append({
                    "from": current_data.get("name", current),
                    "to": target_data.get("name", target),
                    "relation": edge_data.get("type"),
                    "weight": edge_data.get("weight", 1.0),
                })
                queue.append(target)
        
        return chain
    
    # ═══════════════════════════════════════════════════════════
    # КОНТЕКСТ ДЛЯ LLM
    # ═══════════════════════════════════════════════════════════
    
    def get_context_for_query(self, query: str, max_nodes: int = 15) -> Dict[str, Any]:
        """
        Формирует контекст из графа для LLM-запроса.
        
        Стратегия:
        1. Находим узлы, релевантные запросу (по ключевым словам)
        2. Расширяем контекст через соседей (BFS)
        3. Добавляем каузальные цепочки
        4. Добавляем активную парадигму
        5. Формируем текстовое описание для system prompt
        """
        # 1. Поиск релевантных узлов
        relevant_nodes = self._search_nodes(query, limit=5)
        
        # 2. Расширяем через соседей
        expanded = set()
        for node in relevant_nodes:
            expanded.add(node["id"])
            neighbors = self.get_neighbors(node["name"], depth=self.config.graph_context_depth)
            for n in neighbors[:3]:  # Макс 3 соседа на узел
                expanded.add(n["node"].get("id", ""))
        
        # 3. Собираем данные
        context_nodes = []
        for nid in expanded:
            if nid in self._node_index:
                context_nodes.append(self._node_index[nid])
        
        # 4. Собираем связи между контекстными узлами
        context_edges = []
        if self.graph is not None:
            for edge in self.graph.edges(data=True):
                if edge[0] in expanded and edge[1] in expanded:
                    src_name = self._node_index.get(edge[0], {}).get("name", "?")
                    tgt_name = self._node_index.get(edge[1], {}).get("name", "?")
                    context_edges.append({
                        "from": src_name,
                        "to": tgt_name,
                        "type": edge[2].get("type", "related_to"),
                    })
        
        # 5. Формируем текстовый контекст
        text_parts = []
        if context_nodes:
            text_parts.append("Связанные сущности из графа знаний:")
            for node in context_nodes[:max_nodes]:
                attrs = node.get("attributes", {})
                attrs_str = ", ".join(f"{k}={v}" for k, v in attrs.items()) if attrs else ""
                text_parts.append(f"  - {node.get('name')} [{node.get('type')}] {attrs_str}")
        
        if context_edges:
            text_parts.append("\nСвязи:")
            for edge in context_edges[:20]:
                text_parts.append(f"  - {edge['from']} --[{edge['type']}]--> {edge['to']}")
        
        # 6. Добавляем Blackboard-контекст
        user_state = self.blackboard.read("user_state")
        if user_state:
            text_parts.append(f"\nСостояние пользователя: {json.dumps(user_state, ensure_ascii=False)}")
        
        # 7. Парадигмальный overlay
        active_paradigm = self.blackboard.read("system_state", "active_paradigm")
        if active_paradigm and active_paradigm in self._paradigm_overlays:
            overlay = self._paradigm_overlays[active_paradigm]
            text_parts.append(f"\nАктивная парадигма: {active_paradigm}")
            if "interpretation_prompt" in overlay:
                text_parts.append(f"Линза восприятия: {overlay['interpretation_prompt']}")
        
        return {
            "text": "\n".join(text_parts),
            "nodes": context_nodes,
            "edges": context_edges,
            "node_count": len(context_nodes),
            "edge_count": len(context_edges),
            "paradigm": active_paradigm,
        }
    
    def _search_nodes(self, query: str, limit: int = 10) -> List[Dict]:
        """Поиск узлов по ключевым словам."""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        scored = []
        for nid, data in self._node_index.items():
            score = 0
            name_lower = data.get("name", "").lower()
            
            # Точное совпадение имени
            if query_lower in name_lower:
                score += 10
            
            # Совпадение слов
            name_words = set(name_lower.split())
            common = query_words & name_words
            score += len(common) * 5
            
            # Совпадение в атрибутах
            attrs_str = json.dumps(data.get("attributes", {}), ensure_ascii=False).lower()
            for word in query_words:
                if len(word) > 3 and word in attrs_str:
                    score += 2
            
            # Совпадение в тегах
            for tag in data.get("tags", []):
                if tag.lower() in query_lower or query_lower in tag.lower():
                    score += 3
            
            if score > 0:
                scored.append((score, data))
        
        scored.sort(key=lambda x: -x[0])
        return [d for _, d in scored[:limit]]
    
    # ═══════════════════════════════════════════════════════════
    # ПАРАДИГМАЛЬНЫЕ OVERLAY-ГРАФЫ
    # ═══════════════════════════════════════════════════════════
    
    def add_paradigm(self, name: str, description: str,
                     interpretation_prompt: str,
                     concept_mappings: Optional[Dict[str, str]] = None,
                     meta_nodes: Optional[List[Dict]] = None):
        """
        Добавить парадигмальный overlay.
        
        Парадигма НЕ меняет факты и архивы — она добавляет
        дополнительный слой интерпретации поверх данных.
        
        Args:
            name: Имя парадигмы (напр. "кибернетика", "И Цзин")
            description: Описание
            interpretation_prompt: Промпт для LLM, задающий линзу восприятия
            concept_mappings: Маппинг концепций (напр. {"цель" → "аттрактор"})
            meta_nodes: Дополнительные узлы парадигмы
        """
        self._paradigm_overlays[name] = {
            "description": description,
            "interpretation_prompt": interpretation_prompt,
            "concept_mappings": concept_mappings or {},
            "meta_nodes": meta_nodes or [],
            "created": time.time(),
        }
        
        # Добавляем мета-узлы парадигмы в граф
        paradigm_node_id = self.add_node(name, NodeType.PARADIGM, {
            "description": description,
            "is_overlay": True,
        })
        
        if meta_nodes:
            for mn in meta_nodes:
                mn_id = self.add_node(
                    mn["name"], 
                    NodeType.CONCEPT,
                    {"paradigm": name, **mn.get("attributes", {})},
                    tags=[f"paradigm:{name}"],
                )
                self.add_edge(name, mn["name"], EdgeType.PART_OF)
        
        logger.info(f"🔮 Парадигма добавлена: {name}")
    
    def set_active_paradigm(self, name: Optional[str]):
        """Активировать парадигму (или деактивировать если None)."""
        self.blackboard.write("system_state", "active_paradigm", name, source="paradigm_engine")
        if name:
            logger.info(f"🔮 Активная парадигма: {name}")
        else:
            logger.info("🔮 Парадигма деактивирована")
    
    def get_paradigm_lens(self, query: str) -> Optional[str]:
        """Получить парадигмальную интерпретацию для запроса."""
        active = self.blackboard.read("system_state", "active_paradigm")
        if not active or active not in self._paradigm_overlays:
            return None
        
        overlay = self._paradigm_overlays[active]
        prompt = overlay["interpretation_prompt"]
        
        # Подставляем маппинги концепций
        mappings = overlay.get("concept_mappings", {})
        for original, replacement in mappings.items():
            if original.lower() in query.lower():
                prompt += f"\n[Маппинг: '{original}' → '{replacement}']"
        
        return prompt
    
    # ═══════════════════════════════════════════════════════════
    # СИНХРОНИЗАЦИЯ С MEMORY
    # ═══════════════════════════════════════════════════════════
    
    def sync_from_memory_entities(self, entities: List[Dict]):
        """
        Синхронизация сущностей из Memory в граф.
        Вызывается при старте или периодически.
        """
        synced = 0
        for entity_data in entities:
            name = entity_data.get("name", "")
            if not name:
                continue
            
            # Маппинг типов
            etype = entity_data.get("entity_type", "concept")
            try:
                node_type = NodeType(etype)
            except ValueError:
                node_type = NodeType.CONCEPT
            
            node_id = self._find_node_id(name)
            if not node_id:
                self.add_node(name, node_type, 
                             entity_data.get("attributes", {}),
                             entity_data.get("tags", []))
                synced += 1
            
            # Синхронизируем связи
            for rel in entity_data.get("relations", []):
                target_name = rel.get("target_name", "")
                rel_type = rel.get("relation_type", "related_to")
                
                try:
                    edge_type = EdgeType(rel_type)
                except ValueError:
                    edge_type = EdgeType.RELATED_TO
                
                if target_name:
                    self.add_edge(name, target_name, edge_type)
        
        if synced > 0:
            logger.info(f"🔄 Синхронизировано из Memory: {synced} узлов")
    
    def sync_facts_to_graph(self, facts: List[Dict]):
        """
        Синхронизация фактов как узлов графа.
        Факты типа 'goal' и 'knowledge' становятся узлами.
        """
        for fact in facts:
            category = fact.get("category", "")
            content = fact.get("content", "")
            
            if category == "goal":
                self.add_node(content[:50], NodeType.GOAL, 
                             {"full_text": content},
                             tags=fact.get("tags", []))
            elif category == "knowledge":
                self.add_node(content[:50], NodeType.CONCEPT,
                             {"full_text": content},
                             tags=fact.get("tags", []))
    
    # ═══════════════════════════════════════════════════════════
    # ПЕРСИСТЕНТНОСТЬ
    # ═══════════════════════════════════════════════════════════
    
    def save(self):
        """Сохранить граф на диск."""
        # Сохраняем узлы
        nodes_file = self.storage_path / "nodes.json"
        nodes_file.write_text(
            json.dumps(self._node_index, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        # Сохраняем рёбра
        edges = []
        if self.graph is not None:
            for src, tgt, data in self.graph.edges(data=True):
                edges.append({"source": src, "target": tgt, **data})
        
        edges_file = self.storage_path / "edges.json"
        edges_file.write_text(
            json.dumps(edges, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        # Сохраняем парадигмы
        paradigms_file = self.storage_path / "paradigms.json"
        paradigms_file.write_text(
            json.dumps(self._paradigm_overlays, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        # Сохраняем планировщик
        planner_file = self.storage_path / "planner.json"
        planner_file.write_text(
            json.dumps(self.planner.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        # Сохраняем type_index
        type_index_file = self.storage_path / "type_index.json"
        type_index_file.write_text(
            json.dumps({k: list(v) for k, v in self._type_index.items()}, ensure_ascii=False),
            encoding="utf-8"
        )
        
        logger.info(f"💾 Граф сохранён: {self.node_count} узлов, {self.edge_count} связей")
    
    def _load(self):
        """Загрузить граф с диска."""
        # Узлы
        nodes_file = self.storage_path / "nodes.json"
        if nodes_file.exists():
            try:
                self._node_index = json.loads(nodes_file.read_text(encoding="utf-8"))
                if self.graph is not None:
                    for nid, data in self._node_index.items():
                        self.graph.add_node(nid, **data)
                # Восстанавливаем type_index
                for nid, data in self._node_index.items():
                    self._type_index[data.get("type", "concept")].add(nid)
            except Exception as e:
                logger.warning(f"Ошибка загрузки узлов: {e}")
        
        # Рёбра
        edges_file = self.storage_path / "edges.json"
        if edges_file.exists():
            try:
                edges = json.loads(edges_file.read_text(encoding="utf-8"))
                if self.graph is not None:
                    for edge in edges:
                        src = edge.pop("source")
                        tgt = edge.pop("target")
                        self.graph.add_edge(src, tgt, **edge)
            except Exception as e:
                logger.warning(f"Ошибка загрузки рёбер: {e}")
        
        # Парадигмы
        paradigms_file = self.storage_path / "paradigms.json"
        if paradigms_file.exists():
            try:
                self._paradigm_overlays = json.loads(paradigms_file.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning(f"Ошибка загрузки парадигм: {e}")
        
        # Планировщик
        planner_file = self.storage_path / "planner.json"
        if planner_file.exists():
            try:
                data = json.loads(planner_file.read_text(encoding="utf-8"))
                self.planner.load_from_dict(data)
            except Exception as e:
                logger.warning(f"Ошибка загрузки планировщика: {e}")
    
    # ═══════════════════════════════════════════════════════════
    # СТАТИСТИКА И ОТЛАДКА
    # ═══════════════════════════════════════════════════════════
    
    def get_stats(self) -> Dict[str, Any]:
        """Полная статистика графа."""
        stats = {
            "nodes": self.node_count,
            "edges": self.edge_count,
            "nodes_by_type": {k: len(v) for k, v in self._type_index.items()},
            "clusters": len(self.find_clusters()),
            "paradigms": list(self._paradigm_overlays.keys()),
            "active_paradigm": self.blackboard.read("system_state", "active_paradigm"),
            "planner": self.planner.get_stats(),
            "blackboard_sections": list(self.blackboard._data.keys()),
        }
        
        if self.graph is not None and self.node_count > 0:
            stats["density"] = round(nx.density(self.graph), 4)
            stats["is_connected"] = nx.is_weakly_connected(self.graph) if self.node_count > 1 else True
        
        return stats
    
    def export_for_visualization(self) -> Dict[str, Any]:
        """Экспорт графа в формате для визуализации (D3.js / vis.js)."""
        nodes = []
        for nid, data in self._node_index.items():
            nodes.append({
                "id": nid,
                "label": data.get("name", nid),
                "group": data.get("type", "concept"),
                "attributes": data.get("attributes", {}),
            })
        
        edges = []
        if self.graph is not None:
            for src, tgt, data in self.graph.edges(data=True):
                edges.append({
                    "from": src,
                    "to": tgt,
                    "label": data.get("type", ""),
                    "weight": data.get("weight", 1.0),
                })
        
        return {"nodes": nodes, "edges": edges}
