"""
🧠 Management Core — Центральное ядро управления
==================================================
Это «мозг» экосистемы «Цифровой Сад».

Архитектура:
  [Пользователь] → [Management Core] → [Исполнители через MCP/API]
                         ↕
                    [Память + Граф]

Management Core НЕ выполняет работу сам. Он:
1. Понимает запрос (семантический роутинг)
2. Помнит контекст (память + граф знаний)
3. Разбивает на подзадачи (оркестрация)
4. Направляет исполнителям (MCP-протокол)
5. Собирает результат и обновляет память
"""

import asyncio
import json
import time
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("garden.manager")


# ═══════════════════════════════════════════════════════════════
# ТИПЫ И СТРУКТУРЫ
# ═══════════════════════════════════════════════════════════════

class Intent(Enum):
    """Семантические намерения пользователя."""
    # Информация
    SEARCH = "search"              # Найти информацию
    ANALYZE = "analyze"            # Проанализировать данные/текст
    SUMMARIZE = "summarize"        # Сжать/резюмировать
    
    # Создание
    GENERATE_TEXT = "generate_text"    # Написать текст/код/документ
    GENERATE_IMAGE = "generate_image"  # Создать изображение
    GENERATE_CODE = "generate_code"    # Написать код
    
    # Действия
    AUTOMATE = "automate"          # Автоматизировать процесс
    COMMUNICATE = "communicate"    # Написать сообщение/письмо
    SCHEDULE = "schedule"          # Запланировать задачу
    
    # Личное
    REFLECT = "reflect"            # Дневник/рефлексия
    TRACK_STATE = "track_state"    # Отслеживание состояния
    PLAN = "plan"                  # Планирование дня/задач
    
    # Система
    CONFIGURE = "configure"        # Настройка системы
    RECALL = "recall"              # Вспомнить из памяти
    
    # Неопределённое
    CHAT = "chat"                  # Просто разговор
    UNKNOWN = "unknown"            # Не удалось определить


@dataclass
class Task:
    """Единица работы в системе."""
    id: str
    intent: Intent
    original_query: str
    context: Dict[str, Any] = field(default_factory=dict)
    subtasks: List['Task'] = field(default_factory=list)
    executor: Optional[str] = None  # ID исполнителя
    status: str = "pending"  # pending → running → completed → failed
    result: Optional[Any] = None
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "intent": self.intent.value,
            "query": self.original_query,
            "executor": self.executor,
            "status": self.status,
            "subtasks": [st.to_dict() for st in self.subtasks],
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }


@dataclass
class Executor:
    """Описание исполнителя (внешнего сервиса/агента)."""
    id: str
    name: str
    type: str  # "llm", "tool", "agent", "mcp_server"
    capabilities: List[Intent]  # Какие намерения может обрабатывать
    endpoint: Optional[str] = None  # URL или MCP URI
    api_key: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    is_available: bool = True
    priority: int = 5  # 1=высший, 10=низший
    cost_per_call: float = 0.0  # 0 = бесплатно
    
    def can_handle(self, intent: Intent) -> bool:
        return intent in self.capabilities


# ═══════════════════════════════════════════════════════════════
# СЕМАНТИЧЕСКИЙ РОУТЕР
# ═══════════════════════════════════════════════════════════════

class SemanticRouter:
    """
    Определяет намерение пользователя и направляет к нужному исполнителю.
    
    Работает в два этапа:
    1. Быстрая классификация (по ключевым словам + паттернам)
    2. Если неоднозначно — уточнение через LLM
    """
    
    # Паттерны для быстрой классификации
    PATTERNS: Dict[Intent, List[str]] = {
        Intent.SEARCH: [
            "найди", "поищи", "search", "где найти", "что такое",
            "кто такой", "информация о", "расскажи о", "узнай",
        ],
        Intent.ANALYZE: [
            "проанализируй", "разбери", "оцени", "сравни",
            "analyze", "что думаешь о", "в чём разница",
        ],
        Intent.SUMMARIZE: [
            "резюмируй", "кратко", "суть", "итог", "summarize",
            "в двух словах", "основное",
        ],
        Intent.GENERATE_TEXT: [
            "напиши", "составь", "сочини", "создай текст",
            "write", "draft", "письмо", "статью",
        ],
        Intent.GENERATE_IMAGE: [
            "нарисуй", "изображение", "картинк", "image",
            "визуализ", "дизайн", "макет",
        ],
        Intent.GENERATE_CODE: [
            "код", "скрипт", "программ", "функци", "code",
            "python", "javascript", "запрограммируй",
        ],
        Intent.AUTOMATE: [
            "автоматизируй", "настрой бот", "парси", "скрейп",
            "мониторь", "automate", "по расписанию",
        ],
        Intent.COMMUNICATE: [
            "напиши сообщение", "ответь", "отправь",
            "сопроводительное", "отклик", "обращение",
        ],
        Intent.SCHEDULE: [
            "запланируй", "напомни", "расписание", "schedule",
            "через час", "завтра", "каждый день",
        ],
        Intent.REFLECT: [
            "дневник", "запиши мысль", "чувствую", "настроение",
            "рефлексия", "осознание", "инсайт",
        ],
        Intent.TRACK_STATE: [
            "состояние", "энергия", "самочувствие", "трекер",
            "как я", "прогресс", "статистика",
        ],
        Intent.PLAN: [
            "план на", "что делать", "приоритеты", "список дел",
            "режим дня", "распорядок",
        ],
        Intent.CONFIGURE: [
            "настрой", "измени настройки", "добавь провайдер",
            "подключи", "конфигурация",
        ],
        Intent.RECALL: [
            "вспомни", "я говорил", "мы обсуждали", "ранее",
            "в прошлый раз", "помнишь",
        ],
    }
    
    def __init__(self, executors: List[Executor]):
        self.executors = {e.id: e for e in executors}
    
    def classify_intent(self, query: str) -> Intent:
        """Быстрая классификация намерения по паттернам."""
        query_lower = query.lower().strip()
        
        scores: Dict[Intent, int] = {}
        for intent, patterns in self.PATTERNS.items():
            score = sum(1 for p in patterns if p in query_lower)
            if score > 0:
                scores[intent] = score
        
        if scores:
            return max(scores, key=scores.get)
        
        return Intent.CHAT
    
    def route(self, intent: Intent) -> Optional[Executor]:
        """Находит лучшего исполнителя для данного намерения."""
        candidates = [
            e for e in self.executors.values()
            if e.can_handle(intent) and e.is_available
        ]
        
        if not candidates:
            # Fallback: любой LLM может обработать CHAT
            candidates = [
                e for e in self.executors.values()
                if e.type == "llm" and e.is_available
            ]
        
        if not candidates:
            return None
        
        # Сортируем: бесплатные первые, затем по приоритету
        candidates.sort(key=lambda e: (e.cost_per_call, e.priority))
        return candidates[0]
    
    def route_query(self, query: str) -> tuple[Intent, Optional[Executor]]:
        """Полный цикл: классификация + маршрутизация."""
        intent = self.classify_intent(query)
        executor = self.route(intent)
        return intent, executor


# ═══════════════════════════════════════════════════════════════
# ОРКЕСТРАТОР ЗАДАЧ
# ═══════════════════════════════════════════════════════════════

class TaskOrchestrator:
    """
    Разбивает сложные запросы на подзадачи и координирует выполнение.
    
    Стратегии:
    - SIMPLE: один запрос → один исполнитель
    - CHAIN: последовательная цепочка (результат одного → вход другого)
    - PARALLEL: параллельное выполнение + агрегация
    - ADAPTIVE: система сама решает на основе контекста
    """
    
    def __init__(self, router: SemanticRouter):
        self.router = router
        self.task_history: List[Task] = []
        self._task_counter = 0
    
    def _next_id(self) -> str:
        self._task_counter += 1
        return f"task_{self._task_counter:04d}_{int(time.time())}"
    
    def create_task(self, query: str, context: Optional[Dict] = None) -> Task:
        """Создаёт задачу из пользовательского запроса."""
        intent, executor = self.router.route_query(query)
        
        task = Task(
            id=self._next_id(),
            intent=intent,
            original_query=query,
            context=context or {},
            executor=executor.id if executor else None,
        )
        
        self.task_history.append(task)
        logger.info(f"📋 Задача создана: [{intent.value}] → {executor.name if executor else 'нет исполнителя'}")
        
        return task
    
    def decompose(self, task: Task) -> List[Task]:
        """
        Разбивает сложную задачу на подзадачи.
        
        Пример: "Найди вакансии и напиши отклик" →
          1. SEARCH: найти вакансии
          2. GENERATE_TEXT: написать отклик
        """
        # Простая эвристика: если в запросе есть "и", "затем", "потом"
        connectors = [" и ", " затем ", " потом ", " после этого "]
        query = task.original_query
        
        for conn in connectors:
            if conn in query.lower():
                parts = query.lower().split(conn, 1)
                if len(parts) == 2:
                    subtask1 = self.create_task(parts[0].strip(), task.context)
                    subtask2 = self.create_task(parts[1].strip(), task.context)
                    task.subtasks = [subtask1, subtask2]
                    return task.subtasks
        
        # Не удалось разбить — задача атомарная
        return [task]
    
    async def execute(self, task: Task, execute_fn: Callable) -> Any:
        """
        Выполняет задачу (или цепочку подзадач).
        
        execute_fn — функция, которая принимает Task и возвращает результат.
        Это позволяет Management Core не знать деталей исполнения.
        """
        task.status = "running"
        
        if task.subtasks:
            # Выполняем подзадачи последовательно (chain)
            results = []
            for subtask in task.subtasks:
                # Передаём результат предыдущей подзадачи как контекст
                if results:
                    subtask.context["previous_result"] = results[-1]
                
                result = await execute_fn(subtask)
                subtask.result = result
                subtask.status = "completed"
                subtask.completed_at = time.time()
                results.append(result)
            
            task.result = results[-1]  # Финальный результат = последняя подзадача
        else:
            # Атомарная задача
            task.result = await execute_fn(task)
        
        task.status = "completed"
        task.completed_at = time.time()
        
        logger.info(f"✅ Задача {task.id} выполнена за {task.completed_at - task.created_at:.1f}с")
        return task.result
    
    def get_history(self, limit: int = 20) -> List[Dict]:
        """Возвращает историю задач."""
        return [t.to_dict() for t in self.task_history[-limit:]]


# ═══════════════════════════════════════════════════════════════
# MANAGEMENT CORE — ГЛАВНЫЙ КЛАСС
# ═══════════════════════════════════════════════════════════════

class ManagementCore:
    """
    Центральное ядро экосистемы «Цифровой Сад».
    
    Объединяет:
    - Память (Memory) — знает пользователя и контекст
    - Семантический роутер (SemanticRouter) — понимает намерения
    - Оркестратор (TaskOrchestrator) — координирует выполнение
    - Реестр исполнителей (Executors) — знает кто что умеет
    
    Использование:
        core = ManagementCore(config_path="config/garden.yaml")
        await core.start()
        
        result = await core.process("Найди вакансии дизайнера в Петербурге")
        # → Определит intent=SEARCH, найдёт исполнителя (Browser Use),
        #   обогатит контекст из памяти, выполнит, сохранит результат
    """
    
    def __init__(self, config_path: str = "config/garden.yaml"):
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        
        # Компоненты (инициализируются в start())
        self.memory = None
        self.router = None
        self.orchestrator = None
        self.executors: Dict[str, Executor] = {}
        
        # Состояние
        self._running = False
        self._llm_client = None  # Ссылка на LLM-клиент для внутренних нужд
    
    async def start(self):
        """Инициализация всех компонентов."""
        logger.info("🌱 Запуск Management Core «Цифровой Сад»...")
        
        # 1. Загрузка конфигурации
        self._load_config()
        
        # 2. Инициализация памяти
        mem_config = self.config.get("memory", {})
        self.memory = Memory(MemoryConfig(
            storage_dir=mem_config.get("storage_dir", "storage/memory"),
            max_session_messages=mem_config.get("max_session_messages", 50),
            max_context_messages=mem_config.get("max_context_messages", 10),
            auto_extract_facts=mem_config.get("auto_extract_facts", True),
        ))
        self.memory.start_session()
        
        # 3. Регистрация исполнителей
        self._register_executors()
        
        # 4. Инициализация роутера и оркестратора
        self.router = SemanticRouter(list(self.executors.values()))
        self.orchestrator = TaskOrchestrator(self.router)
        
        self._running = True
        active_executors = sum(1 for e in self.executors.values() if e.is_available)
        logger.info(f"✅ Management Core запущен: {active_executors} исполнителей готовы")
    
    async def stop(self):
        """Остановка и сохранение состояния."""
        if self.memory:
            self.memory.end_session()
        self._running = False
        logger.info("🌙 Management Core остановлен")
    
    async def process(self, query: str, user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Главный метод — обработка запроса пользователя.
        
        Полный цикл:
        1. Обогащение контекста из памяти
        2. Классификация намерения
        3. Создание задачи
        4. Выполнение (с fallback)
        5. Сохранение в память
        6. Возврат результата
        
        Args:
            query: Текст запроса пользователя
            user_context: Дополнительный контекст (энергия, время, настроение)
        
        Returns:
            {
                "response": str,         # Ответ для пользователя
                "intent": str,           # Определённое намерение
                "executor": str,         # Кто выполнил
                "task_id": str,          # ID задачи
                "memory_used": bool,     # Использовалась ли память
                "facts_recalled": int,   # Сколько фактов из памяти
            }
        """
        if not self._running:
            raise RuntimeError("Management Core не запущен. Вызовите await core.start()")
        
        # 1. Получаем контекст из памяти
        memory_context = self.memory.get_context(query)
        
        # 2. Объединяем контексты
        full_context = {
            "memory": memory_context,
            "user": user_context or {},
            "timestamp": time.time(),
        }
        
        # 3. Создаём задачу
        task = self.orchestrator.create_task(query, full_context)
        
        # 4. Выполняем
        try:
            result = await self.orchestrator.execute(task, self._execute_task)
        except Exception as e:
            logger.error(f"❌ Ошибка выполнения: {e}")
            result = f"Не удалось выполнить задачу: {e}"
            task.status = "failed"
        
        # 5. Сохраняем в память
        response_text = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
        self.memory.record_exchange(
            user_message=query,
            assistant_response=response_text,
            model=task.executor or "unknown",
            provider="management_core",
            tokens_used=len(response_text.split()) * 2,
        )
        
        # 6. Формируем ответ
        return {
            "response": response_text,
            "intent": task.intent.value,
            "executor": task.executor,
            "task_id": task.id,
            "memory_used": memory_context["metadata"]["facts_used"] > 0,
            "facts_recalled": memory_context["metadata"]["facts_used"],
            "status": task.status,
        }
    
    async def _execute_task(self, task: Task) -> str:
        """
        Выполняет атомарную задачу через соответствующего исполнителя.
        
        Это точка расширения — сюда подключаются MCP-серверы,
        API-клиенты, агенты и т.д.
        """
        executor = self.executors.get(task.executor) if task.executor else None
        
        if not executor:
            # Fallback: используем первый доступный LLM
            executor = next(
                (e for e in self.executors.values() if e.type == "llm" and e.is_available),
                None
            )
        
        if not executor:
            return "❌ Нет доступных исполнителей"
        
        # Формируем запрос в зависимости от типа исполнителя
        if executor.type == "llm":
            return await self._execute_llm(executor, task)
        elif executor.type == "mcp_server":
            return await self._execute_mcp(executor, task)
        elif executor.type == "tool":
            return await self._execute_tool(executor, task)
        elif executor.type == "agent":
            return await self._execute_agent(executor, task)
        else:
            return f"❌ Неизвестный тип исполнителя: {executor.type}"
    
    async def _execute_llm(self, executor: Executor, task: Task) -> str:
        """Выполнение через LLM (AI Super Router)."""
        # Импортируем клиент роутера
        from core.client import SuperRouterClient
        
        # Собираем messages из контекста памяти
        memory_ctx = task.context.get("memory", {})
        messages = []
        
        # System prompt с фактами из памяти
        system_prompt = memory_ctx.get("system_prompt", "")
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # История из памяти
        history_messages = memory_ctx.get("messages", [])
        messages.extend(history_messages)
        
        # Если текущий запрос не в messages — добавляем
        if not messages or messages[-1].get("content") != task.original_query:
            messages.append({"role": "user", "content": task.original_query})
        
        # Используем глобальный LLM-клиент
        if self._llm_client:
            response = await self._llm_client.complete(messages=messages)
            return response.text
        
        # Если клиент не настроен — возвращаем заглушку
        return f"[LLM не подключён] Задача: {task.original_query}"
    
    async def _execute_mcp(self, executor: Executor, task: Task) -> str:
        """
        Выполнение через MCP-сервер.
        
        MCP (Model Context Protocol) позволяет вызывать внешние инструменты
        через стандартизированный протокол.
        """
        # TODO: Реализация MCP-клиента
        # Формат: mcp://{server}/{tool}?{params}
        endpoint = executor.endpoint
        
        logger.info(f"🔌 MCP вызов: {executor.name} @ {endpoint}")
        
        # Заглушка — будет заменена реальным MCP-клиентом
        return f"[MCP: {executor.name}] Выполнение: {task.original_query}"
    
    async def _execute_tool(self, executor: Executor, task: Task) -> str:
        """Выполнение через внешний инструмент (API)."""
        endpoint = executor.endpoint
        
        logger.info(f"🔧 Tool вызов: {executor.name} @ {endpoint}")
        
        # Заглушка — будет заменена реальными API-вызовами
        return f"[Tool: {executor.name}] Выполнение: {task.original_query}"
    
    async def _execute_agent(self, executor: Executor, task: Task) -> str:
        """Выполнение через автономного агента (OpenHands, Browser Use)."""
        logger.info(f"🤖 Agent вызов: {executor.name}")
        
        # Заглушка — будет заменена реальными агентами
        return f"[Agent: {executor.name}] Выполнение: {task.original_query}"
    
    # ═══════════════════════════════════════════════════════════════
    # КОНФИГУРАЦИЯ И РЕГИСТРАЦИЯ
    # ═══════════════════════════════════════════════════════════════
    
    def _load_config(self):
        """Загружает конфигурацию из YAML."""
        if self.config_path.exists():
            import yaml
            with open(self.config_path) as f:
                self.config = yaml.safe_load(f) or {}
        else:
            logger.warning(f"⚠️ Конфиг не найден: {self.config_path}, используются значения по умолчанию")
            self.config = self._default_config()
    
    def _default_config(self) -> Dict:
        """Конфигурация по умолчанию."""
        return {
            "memory": {
                "storage_dir": "storage/memory",
                "max_session_messages": 50,
                "max_context_messages": 10,
                "auto_extract_facts": True,
            },
            "executors": {
                "llm_router": {
                    "type": "llm",
                    "name": "AI Super Router",
                    "endpoint": "http://localhost:8000/v1",
                    "priority": 1,
                    "capabilities": [
                        "search", "analyze", "summarize", 
                        "generate_text", "generate_code",
                        "communicate", "reflect", "plan", "chat",
                    ],
                },
                "browser_use": {
                    "type": "agent",
                    "name": "Browser Use",
                    "endpoint": "http://localhost:8001",
                    "priority": 3,
                    "capabilities": ["search", "automate"],
                },
                "openhands": {
                    "type": "agent",
                    "name": "OpenHands",
                    "endpoint": "http://localhost:3000",
                    "priority": 4,
                    "capabilities": ["generate_code", "automate"],
                },
            },
        }
    
    def _register_executors(self):
        """Регистрирует исполнителей из конфигурации."""
        executors_config = self.config.get("executors", {})
        
        for exec_id, cfg in executors_config.items():
            capabilities = [
                Intent(c) for c in cfg.get("capabilities", [])
                if c in [i.value for i in Intent]
            ]
            
            executor = Executor(
                id=exec_id,
                name=cfg.get("name", exec_id),
                type=cfg.get("type", "llm"),
                capabilities=capabilities,
                endpoint=cfg.get("endpoint"),
                api_key=cfg.get("api_key"),
                config=cfg.get("config", {}),
                priority=cfg.get("priority", 5),
                cost_per_call=cfg.get("cost", 0.0),
            )
            
            self.executors[exec_id] = executor
            logger.debug(f"  📎 Зарегистрирован: {executor.name} ({executor.type})")
    
    def register_executor(self, executor: Executor):
        """Динамическая регистрация нового исполнителя."""
        self.executors[executor.id] = executor
        # Обновляем роутер
        if self.router:
            self.router.executors[executor.id] = executor
        logger.info(f"➕ Новый исполнитель: {executor.name} ({executor.type})")
    
    def unregister_executor(self, executor_id: str):
        """Удаление исполнителя."""
        if executor_id in self.executors:
            name = self.executors[executor_id].name
            del self.executors[executor_id]
            if self.router and executor_id in self.router.executors:
                del self.router.executors[executor_id]
            logger.info(f"➖ Удалён исполнитель: {name}")
    
    # ═══════════════════════════════════════════════════════════════
    # ПУБЛИЧНЫЕ МЕТОДЫ УПРАВЛЕНИЯ
    # ═══════════════════════════════════════════════════════════════
    
    def get_status(self) -> Dict[str, Any]:
        """Полный статус системы."""
        return {
            "running": self._running,
            "executors": {
                eid: {
                    "name": e.name,
                    "type": e.type,
                    "available": e.is_available,
                    "capabilities": [c.value for c in e.capabilities],
                }
                for eid, e in self.executors.items()
            },
            "memory": {
                "session_active": self.memory._current_session is not None if self.memory else False,
                "facts_count": len(self.memory.facts) if self.memory else 0,
                "entities_count": len(self.memory.entities) if self.memory else 0,
            },
            "tasks_completed": len([
                t for t in self.orchestrator.task_history 
                if t.status == "completed"
            ]) if self.orchestrator else 0,
        }
    
    def add_fact(self, text: str, category: str = "manual"):
        """Добавить факт в память вручную."""
        if self.memory:
            self.memory.add_fact(text, category=category)
    
    def set_paradigm(self, paradigm: str):
        """Переключить парадигмальную линзу."""
        if self.memory:
            self.memory.set_paradigm(paradigm)
            logger.info(f"🔮 Парадигма: {paradigm}")
    
    def get_task_history(self, limit: int = 20) -> List[Dict]:
        """История выполненных задач."""
        if self.orchestrator:
            return self.orchestrator.get_history(limit)
        return []
