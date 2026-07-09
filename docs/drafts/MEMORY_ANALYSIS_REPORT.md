# 🧠 Проектирование памяти для AI-агента фрилансера: Глубокий анализ

> **Дата:** 2026-07-08  
> **Принцип:** От архитектуры системы → к методам организации памяти → к конкретным структурам данных

---

## Введение: Что значит "глубокий"?

Предыдущий анализ ответил на вопрос "что помнить". Теперь нужно ответить на вопросы:

1. **В каком ВИДЕ хранить** каждую часть памяти?
2. **КАК проводить** рефлексию, анализ ошибок, смену подхода?
3. **КАК формировать** промты из бинарного сигнала?
4. **КАК организовать** роутинг токенов и провайдеров?
5. **КАК собирать статистику** для баесовской оптимизации?

---

## Часть 1: Типы памяти по методам организации

### 1.1 Ассоциативная память (Content-Addressable)

**Принцип:** Доступ по содержанию, не по адресу. Нашёл "похожее" → получил связанные данные.

**Пример из системы:**
```
Ситуация: Новая задача "Исправить баг в API"
↓
Ассоциативный поиск: "похожая задача" → 
→ Все связанные данные: клиент, паттерн решения, оценка, затраты
```

**Структура данных:**
```python
class AssociativeMemory:
    """
    Память где доступ по "похожести", не по ID.
    Реализация: HAM (Hetero-associative Memory) + CAM
    """
    
    # Бинарный поиск ассоциаций: A → B
    hetero_associations: Dict[str, Set[str]]
    
    # Авто-ассоциации: похожесть хранит само себя
    patterns: Dict[str, EmbeddingVector]
    
    # Синаптические веса: A ↔ B связь
    weights: np.ndarray  # [n × n] матрица связей
    
    def retrieve(self, content: str, threshold: float = 0.7) -> List[MemoryItem]:
        """
        1. Находим embedding content
        2. Ищем похожие в patterns (cosine similarity)
        3. Возвращаем связанные items
        """
        query_emb = self.embed(content)
        
        # Ищем похожие паттерны
        similarities = cosine_similarity(query_emb, self.pattern_embeddings)
        similar_idx = np.where(similarities > threshold)[0]
        
        # Берём ассоциации
        results = []
        for idx in similar_idx:
            pattern_id = self.pattern_ids[idx]
            # Находим все связанные через hetero_associations
            linked = self.hetero_associations.get(pattern_id, set())
            for linked_id in linked:
                results.append(self.items[linked_id])
        
        return results
```

**Применение в системе:**
- Task → Похожие задачи + их исходы
- Error → Похожие ошибки + решения
- Client → Похожие клиенты + паттерны поведения

---

### 1.2 Векторная память (Embedding-Based)

**Принцип:** Всё представлено как вектор в n-мерном пространстве. Похожесть = близость в пространстве.

**Структура для нашей системы:**

```python
class VectorMemoryStore:
    """
    Векторная память для семантического поиска.
    Хранит embeddings для задач, клиентов, паттернов, результатов.
    """
    
    # Основное хранилище
    vectors: np.ndarray  # [N × D] где D = 768/1024/1536
    metadata: List[Dict]  # ID, timestamp, type, tags...
    
    # Индекс для быстрого поиска
    index: VectorIndex  # FAISS/HNSW/Qdrant
    
    # Временные ряды для decay
    temporal_decay: Dict[str, float]  # как быстро забываем
    
    def store(self, item: MemoryItem, embedding: np.ndarray):
        """Сохраняем с decay-фактором"""
        self.vectors.append(embedding)
        self.metadata.append({
            'id': item.id,
            'timestamp': time.time(),
            'type': item.type,
            'decay_factor': self._compute_decay(item),
        })
        self.index.add(embedding)
    
    def search(self, query: str, k: int = 10, 
               time_weight: float = 0.3) -> List[MemoryItem]:
        """
        Поиск с учётом времени (recency bias).
        Factor: similarity * recency
        """
        query_emb = self.embed(query)
        indices, distances = self.index.search(query_emb, k * 2)  # Берём больше
        
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            meta = self.metadata[idx]
            
            # Recency factor
            age = time.time() - meta['timestamp']
            recency = np.exp(-age / self.temporal_window)  # exp decay
            
            # Combined score
            score = (1 - dist) * (1 - time_weight) + recency * time_weight
            
            results.append((self.items[idx], score))
        
        # Сортируем и возвращаем top-k
        results.sort(key=lambda x: x[1], reverse=True)
        return [r[0] for r in results[:k]]
```

**Разные типы embeddings для разных сущностей:**

```python
class EmbeddingSchemas:
    """Разные схемы embeddings для разных типов данных"""
    
    # Задачи: текст + метрики
    task_schema = {
        'text': 'sentence-transformers/all-MiniLM-L6-v2',
        'metrics': 'numeric_normalized',  # [cost, time, quality] → [0,1]
        'combined': 'concat'  # [text_emb, metrics * 0.3]
    }
    
    # Клиенты: профиль + поведение
    client_schema = {
        'profile': 'sentence-transformers/all-MiniLM-L6-v2',
        'behavior': 'behavior_pattern_embedding',  # Специальный
        'preferences': 'keyword_vectors'
    }
    
    # Паттерны: подход + результат
    pattern_schema = {
        'approach': 'action_sequence_embedding',  # Цепочка действий
        'outcome': 'result_quality_embedding',
        'context': 'situation_embedding'
    }
```

---

### 1.3 Графовая память (Relationship-Based)

**Принцип:** Знания как сеть узлов и рёбер. "Пётр работает в X → X делает Y → Y связано с Z".

**Структура для клиентов и связей:**

```python
class KnowledgeGraph:
    """
    Граф знаний для сущностей и их связей.
    """
    
    # Узлы (entities)
    nodes: Dict[str, Entity]
    
    # Рёбра (relationships) 
    edges: Dict[str, List[Edge]]
    
    # Мультиграф: разные типы связей
    relation_types = [
        'WORKED_ON',      # клиент → задача
        'SIMILAR_TO',      # задача → задача  
        'PREFERS',         # клиент → предпочтение
        'FAILED_WITH',     # задача → ошибка
        'SOLVED_BY',       # ошибка → паттерн
        'DEPENDS_ON',      # задача → задача
    ]
    
    def add_triple(self, subject: str, predicate: str, object: str):
        """Добавляем тройку (subject, predicate, object)"""
        if subject not in self.nodes:
            self.nodes[subject] = Entity(subject)
        if object not in self.nodes:
            self.nodes[object] = Entity(object)
        
        edge = Edge(subject, predicate, object)
        self.edges[predicate].append(edge)
        
        # Обратная связь
        self.edges[self._inverse(predicate)].append(
            Edge(object, self._inverse(predicate), subject)
        )
    
    def query(self, pattern: str) -> List[Path]:
        """
        SPARQL-like запрос: "Кто работал над похожими задачами как X?"
        
        1. Найти задачи SIMILAR_TO X
        2. Найти WORKED_ON для этих задач
        3. Вернуть клиентов
        """
        # Паттерн через граф traversal
        return self.graph_traverse(pattern)
    
    def infer_new_edges(self):
        """
        Транзитивное замыкание: A → B → C означает A → C
        
        "Если клиент A работал с похожими задачами как клиент B,
        то они потенциально похожи"
        """
        # Находим транзитивные связи
        pass
```

**Пример графа для клиента:**

```
┌─────────────────────────────────────────────────────────────┐
│                        КЛИЕНТ: "Иван"                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Entity: Иван                                              │
│  └── type: Client                                          │
│  └── preferences: ["быстрые ответы", "детальные отчёты"]   │
│  └── rating_history: [5, 4, 5, 5, 4]                      │
│                                                              │
│  Edges:                                                     │
│  ├── WORKED_ON → Задача #123 (API integration)              │
│  │   └── WORKED_ON → Задача #456 (Bug fix)                │
│  │       └── WORKED_ON → Задача #789 (Refactoring)        │
│  │                                                            │
│  ├── PREFERS → "детальная документация"                      │
│  ├── PREFERS → "быстрые ответы"                           │
│  │                                                            │
│  ├── SIMILAR_TO → Клиент: "Пётр"                           │
│  │   └── PREFERS → "то же самое"                          │
│  │   └── WORKED_ON → похожие задачи                         │
│  │                                                            │
│  └── GAVE_FEEDBACK → Feedback #1                            │
│      └── quality: 5                                        │
│      └── comment: "Отлично, как всегда"                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

### 1.4 Временная память (Temporal/Sequence)

**Принцип:** Хронология событий. Что было ДО и ПОСЛЕ.

**Структура для episodic memory:**

```python
class EpisodicMemory:
    """
    Хронологическая память событий.
    Каждое событие = что + когда + контекст + эмоции/гормоны.
    """
    
    # Основной storage: временная линия событий
    timeline: List[Episode]
    
    # Индекс для поиска по времени
    time_index: IntervalTree  # Для range queries
    
    # Индекс для поиска по содержанию
    content_index: VectorIndex
    
    def add_episode(self, episode: Episode):
        """Добавляем событие в хронологию"""
        episode.start_time = time.time()
        self.timeline.append(episode)
        
        # Индексируем
        self.time_index.add(episode)
        self.content_index.add(episode.embedding)
    
    def get_episodes_between(self, t1: float, t2: float) -> List[Episode]:
        """Все события между t1 и t2"""
        return list(self.time_index.search(t1, t2))
    
    def get_recent_context(self, window_minutes: int = 30) -> str:
        """Контекст последних N минут для рефлексии"""
        cutoff = time.time() - window_minutes * 60
        recent = self.get_episodes_since(cutoff)
        
        # Группируем по типам
        grouped = defaultdict(list)
        for ep in recent:
            grouped[ep.type].append(ep)
        
        return self._summarize(grouped)
    
    def find_similar_sequence(self, current: Episode) -> Optional[Sequence]:
        """
        Находим похожую последовательность событий в прошлом.
        "Точно такая же ситуация была 3 недели назад"
        """
        # Ищем похожие отдельные эпизоды
        similar = self.content_index.search(current.embedding, k=20)
        
        # Ищем последовательности
        return self._find_sequences(similar)
```

**Episode структура:**

```python
@dataclass
class Episode:
    """Одно событие в хронологии"""
    
    # Идентификация
    id: str
    type: EpisodeType  # TASK_START, TASK_END, ERROR, TRIGGER, DECISION, ...
    
    # Время
    start_time: float
    end_time: float
    duration: float  # Вычисляется
    
    # Содержание
    summary: str  # Краткое описание
    embedding: np.ndarray  # Для семантического поиска
    
    # Контекст
    task_id: Optional[str]
    client_id: Optional[str]
    agent_state: AgentStateSnapshot  # Метрики в момент события
    
    # Эмоциональный окрас (через гормоны)
    hormones_snapshot: Dict[str, float]
    
    # Результат
    outcome: Outcome  # SUCCESS, FAILURE, PARTIAL
    lessons: List[str]  # Что извлекли
    
    # Связи
    causes: List[str]  # Что привело к этому
    effects: List[str]  # К чему привело
```

---

### 1.5 Рабочая память (Working/Scratchpad)

**Принцип:** Быстрый доступ, ограниченный размер, TTL.

```python
class WorkingMemory:
    """
    Быстрая память текущего состояния.
    In-memory, O(1) доступ, TTL ~5 минут.
    """
    
    # Основное хранилище: ключ → значение
    store: Dict[str, Any]
    
    # Метаданные для eviction
    last_access: Dict[str, float]
    access_count: Dict[str, int]
    
    # Размер
    max_size: int = 100  # Максимум записей
    ttl_seconds: float = 300  # 5 минут
    
    def put(self, key: str, value: Any, priority: int = 0):
        """Кладём в рабочую память"""
        # Eviction если полно
        if len(self.store) >= self.max_size:
            self._evict_lru()
        
        self.store[key] = value
        self.last_access[key] = time.time()
        self.access_count[key] = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Берём с обновлением LRU"""
        if key not in self.store:
            return None
        
        # Проверяем TTL
        if time.time() - self.last_access[key] > self.ttl_seconds:
            del self.store[key]
            return None
        
        self.last_access[key] = time.time()
        self.access_count[key] += 1
        return self.store[key]
    
    def _evict_lru(self):
        """LRU eviction"""
        oldest = min(self.last_access.items(), key=lambda x: x[1])
        del self.store[oldest[0]]
    
    def get_snapshot(self) -> Dict:
        """Снэпшот для записи в долгосрочную память"""
        return {
            'store': dict(self.store),
            'metrics': self._current_metrics(),
            'hormones': self._current_hormones(),
            'timestamp': time.time()
        }
```

---

### 1.6 Стековая память для цепочек действий

**Принцип:** LIFO для call stack'а действий. Позволяет откатываться.

```python
class ActionStack:
    """
    Стековая память для цепочек действий.
    Позволяет push/pop атомарных действий и undo.
    """
    
    # Основной стек
    stack: List[ActionFrame]
    
    # Состояние для каждого уровня
    state_checkpoints: List[StateSnapshot]
    
    def push(self, action: AtomicAction) -> ActionFrame:
        """Выполняем действие и пушим на стек"""
        # Сохраняем состояние ДО
        checkpoint = self._save_checkpoint()
        self.state_checkpoints.append(checkpoint)
        
        # Выполняем
        result = action.execute()
        
        # Пушим
        frame = ActionFrame(
            action=action,
            result=result,
            checkpoint_id=len(self.state_checkpoints) - 1
        )
        self.stack.append(frame)
        
        return frame
    
    def pop(self) -> bool:
        """Откатываем последнее действие (undo)"""
        if not self.stack:
            return False
        
        frame = self.stack.pop()
        checkpoint = self.state_checkpoints[frame.checkpoint_id]
        
        # Восстанавливаем состояние
        self._restore_checkpoint(checkpoint)
        
        return True
    
    def get_trace(self) -> List[ActionFrame]:
        """Полная трассировка для анализа"""
        return list(self.stack)
```

---

### 1.7 Очередь для задач и событий

```python
class TaskQueue:
    """
    Приоритетная очередь задач с состояниями.
    """
    
    # Состояния задач
    class TaskState(Enum):
        PENDING = "pending"
        IN_PROGRESS = "in_progress"
        BLOCKED = "blocked"
        COMPLETED = "completed"
        FAILED = "failed"
        CANCELLED = "cancelled"
    
    # Очереди по состояниям
    pending: heapq  # Приоритетная очередь
    in_progress: Dict[str, Task]
    completed: Dict[str, Task]
    failed: Dict[str, Task]
    
    # Dependencies DAG
    dag: nx.DiGraph  # NetworkX
    
    def enqueue(self, task: Task, priority: float, dependencies: List[str]):
        """Добавляем задачу"""
        # Проверяем dependencies
        for dep_id in dependencies:
            if self.get_state(dep_id) != self.TaskState.COMPLETED:
                self._add_blocked(task, dep_id)
                return
        
        heapq.heappush(self.pending, (priority, task))
    
    def get_next(self) -> Optional[Task]:
        """Берём следующую доступную задачу"""
        while self.pending:
            priority, task = heapq.heappop(self.pending)
            
            # Проверяем dependencies ещё раз
            if self._all_deps_satisfied(task):
                return task
            else:
                # Возвращаем в pending с тем же приоритетом
                heapq.heappush(self.pending, (priority, task))
        
        return None
```

---

### 1.8 Хэш-таблица для быстрого поиска по ID

```python
class IDIndex:
    """
    Быстрый поиск по ID сущностей.
    """
    
    # Основной индекс
    entities: Dict[str, Entity]
    
    # Вторичные индексы
    by_type: Dict[str, Set[str]]  # type → entity_ids
    by_client: Dict[str, Set[str]]  # client_id → entity_ids
    by_time: Dict[str, List[str]]  # date → entity_ids
    
    def get(self, entity_id: str) -> Optional[Entity]:
        return self.entities.get(entity_id)
    
    def get_by_type(self, entity_type: str) -> List[Entity]:
        return [self.entities[eid] for eid in self.by_type.get(entity_type, [])]
    
    def get_by_client_and_timerange(self, client_id: str, 
                                   t1: float, t2: float) -> List[Entity]:
        """Все сущности клиента за период"""
        client_entities = self.by_client.get(client_id, set())
        return [self.entities[eid] for eid in client_entities
                if t1 <= self.entities[eid].timestamp <= t2]
```

---

## Часть 2: Память состояния среды

### 2.1 Внутренняя среда (состояние агента)

```python
class InternalEnvironmentState:
    """
    Цифровой двойник внутреннего состояния агента.
    Обновляется в реальном времени.
    """
    
    # === МЕТРИКИ (time-series) ===
    
    # Прибыль
    profit_history: TimeSeriesBuffer  # [(timestamp, profit_value), ...]
    current_profit_rate: float  # $/hour
    
    # Репутация  
    reputation_score: float  # 0-1
    reputation_trend: float  # скользящий тренд
    
    # Качество
    quality_metrics: Dict[str, float]
    # {
    #   'completeness': 0.85,
    #   'accuracy': 0.92,
    #   'timeliness': 0.78,
    #   'overall': 0.85
    # }
    
    # Риск
    current_risk: float  # 0-1
    risk_budget: float  # оставшийся бюджет риска
    
    # === ГОМЕОСТАТ (setpoints + deviations) ===
    
    class HomeostatState:
        setpoints: Dict[str, float]  # целевые значения
        tolerances: Dict[str, float]  # допуски
        current: Dict[str, float]  # текущие
        deviations: Dict[str, float]  # отклонения
        
        def check_deviation(self, metric: str) -> DeviationType:
            """Тип отклонения"""
            current = self.current[metric]
            target = self.setpoints[metric]
            tolerance = self.tolerances[metric]
            
            if abs(current - target) < tolerance:
                return DeviationType.OK
            elif current > target + tolerance:
                return DeviationType.ABOVE
            else:
                return DeviationType.BELOW
    
    homeostat: HomeostatState
    
    # === ГОРМОНЫ ===
    
    class HormoneState:
        # Уровни (0-1)
        stress: float = 0.0
        energy: float = 1.0
        curiosity: float = 0.5
        focus: float = 0.7
        
        # Функции decay
        half_lives: Dict[str, float] = {
            'stress': 30 * 60,  # 30 минут
            'energy': 120 * 60,  # 2 часа
            'curiosity': 60 * 60,  # 1 час
            'focus': 45 * 60  # 45 минут
        }
        
        def decay(self, dt: float):
            """Распад гормонов со временем"""
            for name, level in vars(self).items():
                if name in self.half_lives:
                    t_half = self.half_lives[name]
                    new_level = level * np.exp(-dt * np.log(2) / t_half)
                    setattr(self, name, new_level)
        
        def boost(self, hormone: str, amount: float):
            """Увеличить гормон"""
            current = getattr(self, hormone)
            setattr(self, hormone, min(1.0, current + amount))
    
    hormones: HormoneState
    
    # === ВРЕМЕННЫЕ РЯДЫ (для анализа трендов) ===
    
    metrics_timeseries: Dict[str, TimeSeriesBuffer]
    
    def get_trend(self, metric: str, window: str = '7d') -> TrendLine:
        """Тренд метрики за период"""
        series = self.metrics_timeseries[metric]
        return series.fit_trend(window)
    
    def predict_next(self, metric: str) -> float:
        """Предсказать следующее значение (линейная экстраполяция)"""
        trend = self.get_trend(metric, '7d')
        return trend.predict(horizon=1)
```

---

### 2.2 Внешняя среда (факторы среды)

```python
class ExternalEnvironmentState:
    """
    Состояние внешней среды: рынок, конкуренты, возможности.
    """
    
    # === РЫНОЧНЫЕ ДАННЫЕ (time-series) ===
    
    class MarketData:
        """Данные о рынке"""
        
        prices_by_task_type: Dict[str, TimeSeriesBuffer]
        # {
        #   'web_development': [(timestamp, price), ...],
        #   'data_analysis': [...],
        # }
        
        demand_trends: Dict[str, TrendIndicator]
        # {
        #   'web_development': TrendIndicator(trend='up', velocity=0.3),
        # }
        
        competition_level: Dict[str, float]  # 0-1
        
        def get_avg_price(self, task_type: str, window: str = '30d') -> float:
            """Средняя цена за период"""
            return np.mean(self.prices_by_task_type[task_type].last(window))
        
        def is_good_time(self, task_type: str) -> bool:
            """Хорошее ли время для этого типа задач?"""
            trend = self.demand_trends.get(task_type)
            return trend.trend == 'up' and trend.velocity > 0.2
    
    market: MarketData
    
    # === КОНКУРЕНТЫ ===
    
    class Competitor:
        """Информация о конкуренте"""
        id: str
        avg_price: float
        rating: float
        response_time: float  # часы
        specializations: List[str]
        embedding: np.ndarray  # для семантического сравнения
    
    competitors: Dict[str, Competitor]
    
    def find_similar_competitors(self, task_type: str) -> List[Competitor]:
        """Найти похожих конкурентов"""
        # Семантический поиск
        pass
    
    # === ВОЗМОЖНОСТИ И УГРОЗЫ ===
    
    class Opportunity:
        """Обнаруженная возможность"""
        id: str
        type: OpportunityType  # NEW_CLIENT, PRICE_INCREASE, TREND_SHIFT, ...
        description: str
        potential_impact: float  # -1 to 1
        confidence: float  # 0-1
        discovered_at: float
        expires_at: float  # для временных возможностей
    
    class Threat:
        """Обнаруженная угроза"""
        id: str
        type: ThreatType  # NEW_COMPETITOR, PRICE_DUMP, BAD_CLIENT, ...
        severity: float  # 0-1
        mitigation_actions: List[str]
    
    opportunities: List[Opportunity]
    threats: List[Threat]
    
    # === СКАНЕР ВНЕШНЕЙ СРЕДЫ ===
    
    def scan_environment(self):
        """Периодический скан внешней среды"""
        # 1. Мониторим новые задачи на платформе
        new_tasks = self.platform_scanner.get_new_tasks()
        
        # 2. Обновляем цены
        self.market.update_prices(new_tasks)
        
        # 3. Ищем новых конкурентов
        self._detect_new_competitors()
        
        # 4. Анализируем тренды
        self._update_trends()
        
        # 5. Генерируем opportunities/threats
        self._generate_signals()
```

---

## Часть 3: Картотека задач и заказов

### 3.1 Структура задачи

```python
class Task:
    """
    Полная структура задачи с историей жизни.
    """
    
    # === ИДЕНТИФИКАЦИЯ ===
    id: str
    external_id: str  # ID на платформе клиента
    client_id: str
    
    # === ТИПОЛОГИЯ ===
    type: TaskType  # Enum: CODE, TEXT, DATA, DESIGN, ...
    subtype: str  # "web_development", "api_integration", ...
    complexity: float  # 0-1
    
    # === ВХОДНЫЕ ДАННЫЕ ===
    description: str
    requirements: List[Requirement]
    attachments: List[Attachment]
    budget: Budget
    deadline: datetime
    
    # === ИЕРАРХИЯ (для сложных задач) ===
    parent_id: Optional[str]  # Родительская задача
    subtasks: List[str]  # Дочерние задачи
    depth: int  # Глубина в дереве
    
    # === DAG ЗАВИСИМОСТЕЙ ===
    dependencies: List[str]  # От каких задач зависит
    dependents: List[str]  # Какие задачи зависят от этой
    
    # === СОСТОЯНИЕ ===
    state: TaskState
    progress: float  # 0-1
    
    # === ИСПОЛНЕНИЕ ===
    assigned_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    executor: Optional[str]  # Кто выполняет (agent_id)
    action_chain: List[AtomicAction]  # Цепочка действий
    
    # === РЕЗУЛЬТАТ ===
    result: Optional[TaskResult]
    quality_score: Optional[float]
    client_rating: Optional[int]  # 1-5
    client_feedback: Optional[str]
    
    # === МЕТРИКИ ===
    actual_cost: float
    actual_time: float
    token_usage: TokenUsage
    success: bool
    
    # === АНАЛИТИКА ===
    similar_tasks: List[str]  # Похожие задачи (IDs)
    lessons_learned: List[str]
    
    def get_full_embedding(self) -> np.ndarray:
        """
        Полный embedding задачи для поиска.
        Включает текст + метрики + результат.
        """
        text_emb = self.embed(self.description)
        metrics_emb = self._metrics_to_vector({
            'complexity': self.complexity,
            'budget': self.budget.normalized,
            'quality': self.quality_score or 0,
        })
        return np.concatenate([text_emb, metrics_emb])
```

### 3.2 Картотека клиентов

```python
class ClientCard:
    """
    Полная карточка клиента.
    """
    
    # === ОСНОВНЫЕ ДАННЫЕ ===
    id: str
    name: str
    platform_id: str  # ID на фриланс-платформе
    
    # === ПРОФИЛЬ ===
    class Profile:
        specializations: List[str]
        communication_style: CommunicationStyle
        preferred_response_time: str  # "fast", "medium", "relaxed"
        documentation_preference: DocPreference
        risk_tolerance: float  # 0-1
    
    profile: Profile
    
    # === ИСТОРИЯ РАБОТЫ ===
    tasks: List[TaskSummary]  # Сводка задач
    total_revenue: float
    avg_task_value: float
    
    # === РЕЙТИНГ И ОТЗЫВЫ ===
    class Reputation:
        avg_rating: float
        total_reviews: int
        reviews: List[Review]
        rating_trend: TrendLine
        flagged_issues: List[str]
    
    reputation: Reputation
    
    # === ПОВЕДЕНЧЕСКИЕ ПАТТЕРНЫ ===
    class Behavior:
        payment_speed: PaymentSpeed  # fast/medium/slow
        revision_requests: int  # Среднее количество правок
        clarity_of_requirements: float  # 0-1
        cooperation_level: float  # 0-1
        last_active: datetime
    
    behavior: Behavior
    
    # === ПРЕДПОЧТЕНИЯ ===
    class Preferences:
        communication_channel: str  # email/telegram/platform
        notification_level: str  # minimal/normal/detailed
        auto_approve_milestones: bool
        preferred_qualities: List[str]
        avoided_qualities: List[str]
        price_range: Tuple[float, float]
    
    preferences: Preferences
    
    # === ОЦЕНКА (для решений) ===
    def estimate_success_probability(self, task: Task) -> float:
        """Оценка вероятности успеха с этим клиентом"""
        # Анализируем похожие задачи
        similar = self._find_similar_tasks(task)
        
        if similar:
            success_rate = sum(1 for t in similar if t.success) / len(similar)
        else:
            success_rate = 0.5  # Baseline
        
        # Корректируем на паттерны поведения
        behavior_factor = self.behavior.cooperation_level
        
        return success_rate * behavior_factor
    
    def get_risk_score(self, task: Task) -> float:
        """Оценка риска работы с клиентом"""
        risk = 0.0
        
        # История провалов
        failures = [t for t in self.tasks if not t.success]
        if failures:
            risk += 0.3 * len(failures) / len(self.tasks)
        
        # Паттерны поведения
        if self.behavior.revision_requests > 5:
            risk += 0.2
        if self.reputation.avg_rating < 4.0:
            risk += 0.2
        
        # Флаггированные проблемы
        risk += 0.1 * len(self.reputation.flagged_issues)
        
        return min(1.0, risk)
```

---

## Часть 4: Поиск материала в сети

### 4.1 Кэш найденных ресурсов

```python
class WebSearchCache:
    """
    Кэш результатов веб-поиска.
    Не ищем одно и то же дважды.
    """
    
    # Хэш запроса → результат
    cache: Dict[str, CachedResult]
    
    # Эмбеддинги для семантической дедупликации
    query_embeddings: Dict[str, np.ndarray]
    
    class CachedResult:
        query_hash: str
        query: str
        results: List[SearchResult]
        found_at: float
        relevance_score: float  # Насколько релевантен был
        used_count: int  # Сколько раз использовался
        ttl_seconds: float  # Когда устаревает
    
    def search(self, query: str, fresh: bool = False) -> List[SearchResult]:
        """Поиск с кэшированием"""
        query_hash = self._hash(query)
        
        # Проверяем кэш
        if not fresh and query_hash in self.cache:
            cached = self.cache[query_hash]
            
            # Проверяем TTL
            if time.time() - cached.found_at < cached.ttl_seconds:
                cached.used_count += 1
                return cached.results
        
        # Иначе ищем в сети
        results = self._do_search(query)
        
        # Кэшируем
        self.cache[query_hash] = CachedResult(
            query_hash=query_hash,
            query=query,
            results=results,
            found_at=time.time(),
            relevance_score=self._score_results(results, query),
            used_count=0,
            ttl_seconds=self._compute_ttl(results),
        )
        
        return results
    
    def _compute_ttl(self, results: List[SearchResult]) -> float:
        """
        TTL зависит от типа информации:
        - Документация API: долгий TTL (1 неделя)
        - Новости: короткий TTL (1 час)
        - StackOverflow: средний TTL (1 день)
        """
        if self._is_documentation(results):
            return 7 * 24 * 3600  # неделя
        elif self._is_news(results):
            return 1 * 3600  # час
        else:
            return 24 * 3600  # день
```

### 4.2 Embedding для документации

```python
class DocumentationIndex:
    """
    Индекс документации: API docs, код, мануалы.
    """
    
    # Иерархический индекс
    tree: DocumentationTree
    
    class DocNode:
        title: str
        content: str
        embedding: np.ndarray
        children: List[DocNode]
        anchors: List[str]  # Якорные ссылки
        
        def get_chunk(self, anchor: str) -> str:
            """Получить чанк по якорю"""
            # Разбиваем на чанки по заголовкам
            pass
    
    def add_documentation(self, doc_path: str):
        """Индексируем документацию"""
        # Парсим
        structure = self._parse_doc(doc_path)
        
        # Векторизуем
        for node in structure.walk():
            node.embedding = self.embed(node.content)
        
        self.tree.add(structure)
    
    def search(self, query: str, context: str) -> List[DocChunk]:
        """Поиск с учётом контекста задачи"""
        query_emb = self.embed(query)
        
        # Семантический поиск
        candidates = self.tree.semantic_search(query_emb, k=10)
        
        # Рeranking по контексту
        context_emb = self.embed(context)
        reranked = self._rerank(candidates, context_emb)
        
        return reranked[:5]
```

---

## Часть 5: Рефлексия, анализ ошибок, смена подхода

### 5.1 Система рефлексии

```python
class ReflectionSystem:
    """
    Система рефлексии: анализ своих действий и их результатов.
    """
    
    # Триггеры для рефлексии
    reflection_triggers = [
        'task_completed',
        'task_failed',
        'repeated_error',
        'performance_degradation',
        'successful_innovation',
    ]
    
    def should_reflect(self, event: Event) -> bool:
        """Когда нужна рефлексия?"""
        if event.type in self.reflection_triggers:
            return True
        
        # Каждые N задач
        if event.task_number % 10 == 0:
            return True
        
        return False
    
    def reflect(self, context: ReflectionContext) -> ReflectionResult:
        """
        Проводим рефлексию.
        
        1. Что было сделано?
        2. Что сработало/не сработало?
        3. Почему?
        4. Что сделать иначе в следующий раз?
        """
        # 1. Реконструкция событий
        events = self._reconstruct_events(context.task_id)
        
        # 2. Анализ успехов/неудач
        successes = [e for e in events if e.outcome == SUCCESS]
        failures = [e for e in events if e.outcome == FAILURE]
        
        # 3. Поиск причин
        causes = self._analyze_causes(failures)
        
        # 4. Поиск похожих ситуаций в прошлом
        similar_situations = self._find_similar(context)
        past_outcomes = [s.outcome for s in similar_situations]
        
        # 5. Генерация insight'ов
        insights = self._generate_insights(
            successes=successes,
            failures=failures,
            causes=causes,
            past=past_outcomes
        )
        
        # 6. Планирование корректировок
        adjustments = self._plan_adjustments(insights)
        
        return ReflectionResult(
            summary=self._summarize(events),
            key_insights=insights,
            adjustments=adjustments,
            confidence=self._compute_confidence(insights),
        )
    
    def _analyze_causes(self, failures: List[Failure]) -> List[Cause]:
        """
        Анализ причин неудач.
        
        Категоризация:
        - Misunderstanding: неправильно понял задачу
        - Skill_gap: не хватило навыка
        - External: внешние факторы
        - Complexity: недооценка сложности
        - Execution: ошибка в исполнении
        """
        causes = []
        
        for failure in failures:
            # Сравниваем с ожиданиями
            expected = failure.task.expected
            actual = failure.task.actual
            
            if expected.quality != actual.quality:
                if expected.clarity < 0.7:
                    causes.append(Cause(
                        type='Misunderstanding',
                        weight=0.4,
                        description="Требования были нечёткими"
                    ))
                
                if failure.agent_skill_level < failure.task.required_skill:
                    causes.append(Cause(
                        type='Skill_gap',
                        weight=0.3,
                        description="Не хватило навыка"
                    ))
            
            if actual.external_factors:
                causes.append(Cause(
                    type='External',
                    weight=0.2,
                    description=f"Внешние факторы: {actual.external_factors}"
                ))
        
        return causes
```

### 5.2 Анализ ошибок

```python
class ErrorAnalysisSystem:
    """
    Систематический анализ ошибок и паттернов неудач.
    """
    
    # Классификация ошибок
    error_taxonomy = {
        'COGNITIVE': [
            'misunderstanding',
            'incorrect_assumption',
            'overconfidence',
            'underconfidence',
        ],
        'EXECUTION': [
            'syntax_error',
            'logic_error',
            'integration_error',
            'data_error',
        ],
        'PROCESS': [
            'scope_creep',
            'time_overrun',
            'resource_exceeded',
            'communication_breakdown',
        ],
        'EXTERNAL': [
            'requirement_change',
            'dependency_failure',
            'resource_unavailable',
        ],
    }
    
    def classify_error(self, error: Error) -> ErrorClassification:
        """Классифицируем ошибку"""
        
        # 1. Эмбеддинг ошибки
        error_emb = self.embed(error.description)
        
        # 2. Семантическая классификация
        for category, subcategories in self.error_taxonomy.items():
            for subcategory in subcategories:
                subcategory_emb = self.embed(subcategory)
                similarity = cosine_similarity(error_emb, subcategory_emb)
                
                if similarity > 0.7:
                    return ErrorClassification(
                        category=category,
                        subcategory=subcategory,
                        confidence=similarity
                    )
        
        return ErrorClassification(
            category='UNKNOWN',
            subcategory='unclassified',
            confidence=0.0
        )
    
    def find_root_cause(self, error_chain: List[Error]) -> RootCause:
        """
        Находим корневую причину цепочки ошибок.
        
        "Ошибка X вызвала ошибку Y, которая вызвала ошибку Z"
        → Корневая причина = X
        """
        # Строим DAG ошибок
        dag = self._build_error_dag(error_chain)
        
        # Находим корни (nodes без входящих рёбер)
        roots = [n for n in dag.nodes if dag.in_degree(n) == 0]
        
        # Если несколько корней, выбираем самый "глубокий"
        if len(roots) == 1:
            return roots[0]
        
        # Иначе анализируем
        return self._analyze_roots(roots)
    
    def suggest_fixes(self, error: Error) -> List[FixSuggestion]:
        """Предлагаем способы исправления"""
        
        # 1. Ищем похожие ошибки в прошлом
        similar_errors = self._find_similar_errors(error)
        
        # 2. Ищем что сработало тогда
        fixes_that_worked = []
        for sim_err in similar_errors:
            if sim_err.fix_applied:
                fixes_that_worked.append(sim_err.fix_applied)
        
        # 3. Ищем что НЕ сработало
        fixes_that_failed = []
        for sim_err in similar_errors:
            if sim_err.fix_attempted and not sim_err.fix_succeeded:
                fixes_that_failed.append(sim_err.fix_attempted)
        
        # 4. Генерируем предложения
        return self._rank_fixes(fixes_that_worked, fixes_that_failed)
```

### 5.3 Смена подхода (Strategy Switching)

```python
class StrategySwitcher:
    """
    Механизм смены стратегии при неэффективности текущей.
    """
    
    # Метрики эффективности
    class EffectivenessMetrics:
        success_rate: float  # Скорость успеха
        avg_quality: float
        avg_time: float
        avg_cost: float
    
    # Стратегии
    strategies = {
        'CONSERVATIVE': {
            'description': 'Минимальный риск, проверенные подходы',
            'when_to_use': 'Новый клиент, сложная задача',
            'parameters': {
                'risk_tolerance': 0.2,
                'exploration_rate': 0.1,
                'time_buffer': 1.5,
            }
        },
        'AGGRESSIVE': {
            'description': 'Быстрые решения, эксперименты',
            'when_to_use': 'Знакомый клиент, срочно',
            'parameters': {
                'risk_tolerance': 0.8,
                'exploration_rate': 0.4,
                'time_buffer': 1.0,
            }
        },
        'THOROUGH': {
            'description': 'Максимальное качество',
            'when_to_use': 'Премиум клиент, важная задача',
            'parameters': {
                'risk_tolerance': 0.3,
                'exploration_rate': 0.2,
                'time_buffer': 2.0,
            }
        },
    }
    
    def should_switch_strategy(self) -> bool:
        """
        Проверяем, нужно ли менять стратегию.
        
        Триггеры:
        - Success rate упал ниже threshold
        - Quality ухудшился
        - Появился паттерн ошибок
        """
        metrics = self._get_recent_metrics()
        
        if metrics.success_rate < self.thresholds.min_success_rate:
            return True, 'low_success_rate'
        
        if metrics.quality_trend == 'declining':
            return True, 'quality_degradation'
        
        if self._detect_error_pattern():
            return True, 'error_pattern'
        
        return False, None
    
    def switch_to(self, new_strategy: str):
        """Переключаем стратегию"""
        old_strategy = self.current_strategy
        self.current_strategy = new_strategy
        
        # Логируем
        self.history.append(StrategyChange(
            timestamp=time.time(),
            from_strategy=old_strategy,
            to_strategy=new_strategy,
            reason=self._get_switch_reason(),
        ))
        
        # Обновляем параметры агента
        self._apply_strategy_parameters(new_strategy)
    
    def _apply_strategy_parameters(self, strategy_name: str):
        """Применяем параметры стратегии к агенту"""
        params = self.strategies[strategy_name]['parameters']
        
        # Обновляем рабочие параметры
        self.agent.risk_tolerance = params['risk_tolerance']
        self.agent.exploration_rate = params['exploration_rate']
        self.agent.time_buffer = params['time_buffer']
```

---

## Часть 6: Анализ качества работы

### 6.1 Система метрик качества

```python
class QualityAnalysisSystem:
    """
    Полный анализ качества: метрики, бенчмарки, тренды.
    """
    
    # === МЕТРИКИ КАЧЕСТВА ===
    
    class QualityMetrics:
        # Компоненты
        completeness: float  # Выполнено / Запланировано
        accuracy: float  # Правильно / Всего
        timeliness: float  # В срок / Просрочено
        clarity: float  # Понятно / Всего
        efficiency: float  # Оптимально / Субоптимально
        
        # Агрегированные
        overall: float  # Взвешенная сумма
        
        def compute(self) -> float:
            weights = {
                'completeness': 0.25,
                'accuracy': 0.30,
                'timeliness': 0.15,
                'clarity': 0.15,
                'efficiency': 0.15,
            }
            return sum(
                getattr(self, k) * v 
                for k, v in weights.items()
            )
    
    # === БЕНЧМАРКИ ===
    
    benchmarks = {
        'industry_avg': {
            'completeness': 0.85,
            'accuracy': 0.90,
            'timeliness': 0.80,
        },
        'top_freelancers': {
            'completeness': 0.95,
            'accuracy': 0.98,
            'timeliness': 0.95,
        },
        'personal_baseline': None,  # Вычисляется
    }
    
    def compare_to_benchmark(self, metrics: QualityMetrics, 
                             benchmark: str) -> BenchmarkComparison:
        """Сравниваем с бенчмарком"""
        bench = self.benchmarks[benchmark]
        
        gaps = {}
        for metric_name in ['completeness', 'accuracy', 'timeliness']:
            my_value = getattr(metrics, metric_name)
            bench_value = getattr(bench, metric_name)
            gaps[metric_name] = my_value - bench_value
        
        overall_gap = metrics.overall - bench.overall
        
        return BenchmarkComparison(
            benchmark_name=benchmark,
            gaps=gaps,
            overall_gap=overall_gap,
            verdict=self._verdict(overall_gap),
        )
    
    # === АНАЛИЗ ТРЕНДОВ ===
    
    def analyze_quality_trend(self, window: str = '30d') -> QualityTrend:
        """Анализ тренда качества"""
        
        series = self.quality_history.last(window)
        
        # Линейная регрессия
        slope, intercept, r_value = self._linear_regression(series)
        
        # Детекция аномалий
        anomalies = self._detect_anomalies(series)
        
        # Корреляция с факторами
        correlations = self._correlate_with_factors(series)
        
        return QualityTrend(
            slope=slope,  # Положительный = улучшаемся
            r_squared=r_value**2,
            anomalies=anomalies,
            correlations=correlations,
            interpretation=self._interpret(slope, r_value, anomalies),
        )
    
    # === РАЗБОР КАЧЕСТВА ПО ЗАДАЧАМ ===
    
    def analyze_quality_by_task_type(self) -> Dict[str, QualityBreakdown]:
        """Разбор качества по типам задач"""
        
        breakdown = {}
        
        for task_type in self.task_types:
            tasks = self.tasks_by_type[task_type]
            
            qualities = [t.quality for t in tasks]
            
            breakdown[task_type] = QualityBreakdown(
                task_type=task_type,
                avg_quality=np.mean(qualities),
                median_quality=np.median(qualities),
                worst_tasks=self._get_worst(tasks, n=3),
                best_tasks=self._get_best(tasks, n=3),
                common_issues=self._find_common_issues(tasks),
            )
        
        return breakdown
    
    # === АНАЛИЗ УЗКИХ МЕСТ ===
    
    def find_bottlenecks(self) -> List[Bottleneck]:
        """Находим узкие места в процессе"""
        bottlenecks = []
        
        # 1. Где больше всего ошибок?
        error_locations = self._count_errors_by_location()
        if error_locations:
            top_location = max(error_locations, key=error_locations.get)
            bottlenecks.append(Bottleneck(
                type='HIGH_ERROR_RATE',
                location=top_location,
                suggestion=f"Уделить больше внимания {top_location}"
            ))
        
        # 2. Где тратим больше всего времени?
        time_locations = self._analyze_time_spent()
        if time_locations:
            slow_location = max(time_locations, key=time_locations.get)
            bottlenecks.append(Bottleneck(
                type='SLOW_PROCESS',
                location=slow_location,
                suggestion=f"Оптимизировать {slow_location}"
            ))
        
        # 3. Где больше всего переделок?
        revision_locations = self._count_revisions_by_location()
        if revision_locations:
            top_revision = max(revision_locations, key=revision_locations.get)
            bottlenecks.append(Bottleneck(
                type='MANY_REVISIONS',
                location=top_revision,
                suggestion=f"Улучшить процесс на этапе {top_revision}"
            ))
        
        return bottlenecks
```

---

## Часть 7: Формирование контекстов для LLM

### 7.1 Динамическое формирование промтов

```python
class PromptBuilder:
    """
    Динамическое формирование промтов из компонентов памяти.
    """
    
    # === БИБЛИОТЕКА ШАБЛОНОВ ===
    
    templates = {
        'task_analysis': """Проанализируй задачу:
        
Задача: {task_description}

Клиент: {client_profile}

История похожих задач:
{similar_tasks_summary}

Что сработало в похожих задачах:
{successful_patterns}

Что НЕ сработало:
{failed_patterns}

Ожидаемое качество: {expected_quality}
Бюджет: {budget}
Дедлайн: {deadline}""",
        
        'error_diagnosis': """Диагностируй ошибку:

Ошибка: {error_description}

Контекст выполнения:
{execution_context}

Похожие ошибки в прошлом:
{similar_errors}

Их решения:
{past_solutions}

Текущее состояние агента:
{agent_state}""",
        
        'reflection': """Проведи рефлексию:

Что было сделано:
{actions_taken}

Результат:
{outcome}

Отклонения от плана:
{deviations}

Качество результата:
{quality_metrics}

Как это сравнивается с прошлыми результатами:
{past_comparison}""",
    }
    
    # === СБОРЩИК КОНТЕКСТА ===
    
    def build_context(self, template_name: str, 
                     memory: AgentMemory,
                     current_state: AgentState) -> str:
        """Собираем контекст из памяти"""
        
        template = self.templates[template_name]
        
        # Собираем каждый компонент
        context_pieces = {}
        
        if '{task_description}' in template:
            context_pieces['task_description'] = self._get_task_description()
        
        if '{client_profile}' in template:
            context_pieces['client_profile'] = self._get_client_profile()
        
        if '{similar_tasks_summary}' in template:
            context_pieces['similar_tasks_summary'] = \
                self._get_similar_tasks(current_state.task)
        
        if '{successful_patterns}' in template:
            context_pieces['successful_patterns'] = \
                self._get_successful_patterns()
        
        # ... собираем остальные компоненты ...
        
        # Формируем промт
        prompt = template.format(**context_pieces)
        
        # Добавляем прагмы безопасности
        prompt = self._add_safety_pragmas(prompt)
        
        return prompt
    
    def _get_similar_tasks(self, task: Task) -> str:
        """Получаем похожие задачи из памяти"""
        similar = self.memory.task_memory.find_similar(task, k=3)
        
        if not similar:
            return "Нет похожих задач в истории."
        
        lines = []
        for t in similar:
            lines.append(f"""
Задача: {t.description}
Результат: {'✓ Успех' if t.success else '✗ Провал'}
Качество: {t.quality_score}
""")
        
        return "\n".join(lines)
```

### 7.2 Библиотека предустановленных инструкций

```python
class InstructionLibrary:
    """
    Библиотека предустановленных инструкций для разных ситуаций.
    Загружается в память, активируется по триггерам.
    """
    
    # === БАЗОВЫЕ ИНСТРУКЦИИ ===
    
    base_instructions = {
        'safety_first': """ВСЕГДА проверяй:
1. Лимиты API
2. Бюджет задачи
3. Юридические ограничения
4. Безопасность данных

ЕСЛИ что-то нарушено → ОСТАНОВИСЬ и сообщи.""",
        
        'quality_standard': """Стандарт качества:
- Код: читаемый, с type hints, с docstrings
- Тесты: основные кейсы покрыты
- Документация: изменения задокументированы
- Format: black, eslint""",
        
        'client_communication': """Общение с клиентом:
- Отвечай в течение 2 часов
- Объясняй ПРОСТЫМ языком
- Показывай ПРОГРЕСС
- Если непонятно → ПЕРЕСПРОСИ""",
    }
    
    # === СИТУАЦИОННЫЕ ИНСТРУКЦИИ ===
    
    situational_instructions = {
        # Когда клиент новый
        'new_client': """НОВЫЙ КЛИЕНТ:
- Будь особенно вежлив
- Задавай уточняющие вопросы
- Документируй предпочтения
- Не рискуй - работай консервативно""",
        
        # Когда проблемы с качеством
        'quality_issues': """ПРОБЛЕМЫ С КАЧЕСТВОМ:
- Остановись и подумай: что идёт не так?
- Проверь базовые требования
- Попроси обратную связь
- Скорректируй подход""",
        
        # Когда дедлайн близко
        'deadline_pressure': """ДАВЛЕНИЕ ДЕДЛАЙНА:
- Фокус на МИНИМАЛЬНОМ ВАРИАНТЕ
- Отбрось "nice-to-have"
- Если не успеваешь → СООБЩИ заранее
- Лучше сказать раньше, чем сдать плохо""",
        
        # Когда риск высокий
        'high_risk': """ВЫСОКИЙ РИСК:
- Двойная проверка каждого шага
- Минимальные изменения
- Частые checkpoints
- План отката""",
    }
    
    # === КАК АКТИВИРУЕТСЯ ===
    
    def get_active_instructions(self, 
                              agent_state: AgentState,
                              task: Task,
                              triggers: List[Trigger]) -> List[str]:
        """Активные инструкции для текущей ситуации"""
        active = []
        
        # Всегда базовые
        active.extend(self.base_instructions.values())
        
        # Ситуационные
        if task.client.is_new:
            active.append(self.situational_instructions['new_client'])
        
        if 'deadline_warning' in triggers:
            active.append(self.situational_instructions['deadline_pressure'])
        
        if agent_state.risk_level > 0.7:
            active.append(self.situational_instructions['high_risk'])
        
        # Специфические для клиента
        client_specific = self._get_client_instructions(task.client_id)
        active.extend(client_specific)
        
        return active
    
    # === ПРИМЕНЕНИЕ К ПРОМТУ ===
    
    def build_system_prompt(self, 
                           base_role: str,
                           instructions: List[str],
                           memory_context: str) -> str:
        """Собираем system prompt"""
        
        parts = [base_role]
        
        # Инструкции
        if instructions:
            parts.append("\n=== ОБЯЗАТЕЛЬНЫЕ ПРАВИЛА ===\n")
            parts.extend(f"- {inst}\n" for inst in instructions)
        
        # Контекст памяти
        if memory_context:
            parts.append(f"\n=== КОНТЕКСТ ИЗ ПАМЯТИ ===\n{memory_context}")
        
        return "\n\n".join(parts)
```

---

## Часть 8: Провайдеры, токены, роутинг

### 8.1 Мониторинг провайдеров

```python
class ProviderMonitor:
    """
    Мониторинг и метрики провайдеров LLM.
    """
    
    class ProviderMetrics:
        """Метрики одного провайдера"""
        
        # Доступность
        uptime: float  # %
        avg_latency: float  # ms
        latency_p95: float
        latency_p99: float
        
        # Качество
        avg_quality_score: float  # Оценка качества ответов
        error_rate: float
        
        # Стоимость
        cost_per_1k_tokens: float
        cost_per_successful_call: float
        
        # Надёжность
        retry_rate: float
        timeout_rate: float
        
        def compute_roi(self) -> float:
            """ROI провайдера"""
            return self.avg_quality_score / self.cost_per_successful_call
    
    # Метрики по провайдерам
    providers: Dict[str, ProviderMetrics]
    
    # История для трендов
    history: Dict[str, TimeSeriesBuffer]
    
    def select_provider(self, 
                      task_requirements: TaskRequirements) -> ProviderSelection:
        """
        Выбираем оптимального провайдера для задачи.
        
        Учитываем:
        - Требования к качеству
        - Бюджет
        - Дедлайн
        - Текущую нагрузку
        """
        candidates = []
        
        for provider_id, metrics in self.providers.items():
            # 1. Проверяем доступность
            if metrics.uptime < 0.95:
                continue
            
            # 2. Проверяем latency
            if metrics.latency_p95 > task_requirements.max_latency:
                continue
            
            # 3. Проверяем качество
            if metrics.avg_quality_score < task_requirements.min_quality:
                continue
            
            # 4. Проверяем бюджет
            estimated_cost = self._estimate_cost(provider_id, task_requirements)
            if estimated_cost > task_requirements.budget:
                continue
            
            # 5. Вычисляем score
            score = self._compute_selection_score(
                provider_id=provider_id,
                requirements=task_requirements,
            )
            
            candidates.append((provider_id, score))
        
        # Сортируем и возвращаем лучшего
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        if candidates:
            return ProviderSelection(
                provider_id=candidates[0][0],
                score=candidates[0][1],
                alternatives=candidates[1:4],
            )
        
        return None  # Ничего не подошло
    
    def _compute_selection_score(self, provider_id, requirements) -> float:
        """Вычисляем score для выбора провайдера"""
        metrics = self.providers[provider_id]
        
        # Взвешенная сумма
        weights = requirements.priorities
        
        score = (
            weights.quality * metrics.avg_quality_score +
            weights.speed * (1 / metrics.avg_latency) +  # Инвертируем
            weights.cost * (1 / metrics.cost_per_token) +  # Инвертируем
            weights.reliability * metrics.uptime
        )
        
        return score / sum(weights.values())
```

### 8.2 Роутер токенов

```python
class TokenRouter:
    """
    Роутинг токенов между провайдерами для оптимизации стоимости.
    """
    
    # Кэш эмбеддингов (не повторяемся)
    embedding_cache: LRUCache[str, np.ndarray]
    
    # Кэш ответов
    response_cache: SemanticCache
    
    # Распределение токенов по провайдерам
    token_budget: Dict[str, float]  # Провайдер → бюджет в $
    
    def route(self, 
              prompt: str,
              requirements: Requirements) -> RoutedRequest:
        """
        Роутим запрос между провайдерами.
        """
        # 1. Проверяем кэш
        if cached := self.response_cache.get(prompt):
            return RoutedRequest(
                provider_id='CACHE',
                cached_response=cached,
                cost_saved=True,
            )
        
        # 2. Проверяем embedding cache
        if prompt in self.embedding_cache:
            cached_emb = self.embedding_cache[prompt]
        else:
            # 3. Выбираем провайдер для эмбеддинга
            embedding_provider = self.provider_monitor.select_for_embedding()
            cached_emb = self._call_provider(embedding_provider, prompt, mode='embedding')
            self.embedding_cache[prompt] = cached_emb
        
        # 4. Выбираем провайдер для основного вызова
        main_provider = self.provider_monitor.select_provider(requirements)
        
        # 5. Роутим
        return RoutedRequest(
            prompt=prompt,
            provider_id=main_provider.provider_id,
            embedding=cached_emb,
            cost=self._estimate_cost(main_provider, prompt),
        )
    
    def optimize_budget_allocation(self) -> Dict[str, float]:
        """
        Оптимизируем распределение бюджета между провайдерами.
        
        Метод: пропорционально ROI
        """
        total_budget = sum(self.token_budget.values())
        
        # Собираем ROI всех провайдеров
        roi_scores = {}
        for provider_id, metrics in self.provider_monitor.providers.items():
            roi_scores[provider_id] = metrics.compute_roi()
        
        # Нормализуем
        total_roi = sum(roi_scores.values())
        
        # Распределяем пропорционально ROI
        allocation = {
            pid: (roi / total_roi) * total_budget
            for pid, roi in roi_scores.items()
        }
        
        return allocation
```

---

## Часть 9: Баесовская оптимизация

### 9.1 Система сбора статистики

```python
class BayesianStatsCollector:
    """
    Сбор статистики для баесовской оптимизации параметров.
    """
    
    # === НАБЛЮДЕНИЯ ===
    
    class Observation:
        """Одно наблюдение"""
        timestamp: float
        parameters: Dict[str, float]  # Какие параметры использовались
        outcome: float  # Результат (reward)
        context: Dict[str, Any]  # Дополнительный контекст
    
    # Хранилище наблюдений
    observations: List[Observation]
    
    # Индекс для быстрого поиска
    by_parameters: Dict[str, List[int]]  # parameter_combo → observation_ids
    
    # === ЧТО СЛЕДИМ ===
    
    tracked_parameters = {
        'lambda_phi': {
            'range': (0.1, 0.9),
            'prior': 'uniform',
            'description': 'Вес прибыли в utility',
        },
        'lambda_upsilon': {
            'range': (0.1, 0.9),
            'prior': 'uniform',
            'description': 'Вес репутации',
        },
        'risk_threshold': {
            'range': (0.1, 0.8),
            'prior': 'uniform',
            'description': 'Порог риска для отказа',
        },
        'quality_min': {
            'range': (0.6, 0.95),
            'prior': 'uniform',
            'description': 'Минимальное качество',
        },
        'curiosity_weight': {
            'range': (0.0, 0.5),
            'prior': 'uniform',
            'description': 'Вес любопытства в решениях',
        },
    }
    
    def record(self, 
               parameters: Dict[str, float],
               outcome: float,
               context: Dict[str, Any] = None):
        """Записываем наблюдение"""
        
        obs = Observation(
            timestamp=time.time(),
            parameters=parameters.copy(),
            outcome=outcome,
            context=context or {},
        )
        
        self.observations.append(obs)
        
        # Индексируем
        param_key = self._parameters_to_key(parameters)
        if param_key not in self.by_parameters:
            self.by_parameters[param_key] = []
        self.by_parameters[param_key].append(len(self.observations) - 1)
    
    def get_likelihood_history(self, parameter: str) -> List[float]:
        """История наблюдений для параметра"""
        return [o.outcome for o in self.observations]
    
    def get_context_conditions(self) -> Dict[str, List[Any]]:
        """Условия контекста для разных наблюдений"""
        return {
            'client_types': [o.context.get('client_type') for o in self.observations],
            'task_types': [o.context.get('task_type') for o in self.observations],
            'difficulty_levels': [o.context.get('difficulty') for o in self.observations],
        }
```

### 9.2 Баесовское обновление

```python
class BayesianOptimizer:
    """
    Баесовская оптимизация параметров агента.
    """
    
    def __init__(self, stats: BayesianStatsCollector):
        self.stats = stats
        
        # Priors для каждого параметра
        self.priors = {
            param: BetaPrior(alpha=1, beta=1)  # Uninformative
            for param in stats.tracked_parameters
        }
    
    def update(self, new_observations: List[Observation]):
        """
        Обновляем posterior на основе новых наблюдений.
        
        Using conjugate updates for Beta distribution:
        posterior ~ Beta(alpha + successes, beta + failures)
        """
        for obs in new_observations:
            for param_name, value in obs.parameters.items():
                # Определяем успех/неудачу
                if obs.outcome > self.target:
                    # Success
                    self.priors[param_name].alpha += obs.outcome
                else:
                    # Failure
                    self.priors[param_name].beta += 1 - obs.outcome
    
    def sample_posterior(self, parameter: str, n: int = 100) -> List[float]:
        """Сэмплируем из posterior distribution"""
        prior = self.priors[parameter]
        return prior.sample(n)
    
    def get_best_parameters(self) -> Dict[str, float]:
        """
        Получаем оптимальные параметры (MAP estimate).
        """
        best = {}
        
        for param_name, prior in self.priors.items():
            # MAP estimate = mode of Beta distribution
            if prior.alpha > 1 and prior.beta > 1:
                mode = (prior.alpha - 1) / (prior.alpha + prior.beta - 2)
            else:
                mode = prior.alpha / (prior.alpha + prior.beta)
            
            # Clamp к допустимому диапазону
            range_info = self.stats.tracked_parameters[param_name]
            best[param_name] = np.clip(
                mode,
                range_info['range'][0],
                range_info['range'][1]
            )
        
        return best
    
    def get_uncertainty(self, parameter: str) -> float:
        """
        Неопределённость параметра (для exploration).
        """
        prior = self.priors[parameter]
        # Standard deviation of Beta
        total = prior.alpha + prior.beta
        if total > 2:
            var = (prior.alpha * prior.beta) / (total**2 * (total + 1))
            return np.sqrt(var)
        return 1.0  # Высокая неопределённость если мало наблюдений
    
    def suggest_exploration(self) -> Dict[str, float]:
        """
        Предлагаем параметры для exploration.
        
        Используем UCB (Upper Confidence Bound):
        mean + beta * std
        """
        suggestions = {}
        
        for param_name, prior in self.priors.items():
            mean = prior.alpha / (prior.alpha + prior.beta)
            std = self.get_uncertainty(param_name)
            
            # UCB с exploration bonus
            ucb = mean + 0.5 * std
            
            range_info = self.stats.tracked_parameters[param_name]
            suggestions[param_name] = np.clip(
                ucb,
                range_info['range'][0],
                range_info['range'][1]
            )
        
        return suggestions
```

### 9.3 Планирование экспериментов

```python
class ExperimentPlanner:
    """
    Планирование A/B тестов для сбора данных.
    """
    
    def plan_experiment(self, 
                       parameter: str,
                       n_variations: int = 3) -> Experiment:
        """
        Планируем эксперимент для parameter.
        
        Выбираем n точек для тестирования.
        """
        range_info = self.stats.tracked_parameters[parameter]
        low, high = range_info['range']
        
        # Разбиваем на равные части
        step = (high - low) / n_variations
        values = [low + step * i for i in range(n_variations)]
        
        return Experiment(
            parameter=parameter,
            variations=values,
            duration_hours=24,  # Минимум день для статистики
            min_samples_per_variation=10,
        )
    
    def analyze_results(self, experiment: Experiment) -> AnalysisResult:
        """
        Анализируем результаты эксперимента.
        
        Используем ANOVA + pairwise comparisons.
        """
        groups = self._group_by_variation(experiment)
        
        # Статистический тест
        f_stat, p_value = self._anova(groups)
        
        if p_value < 0.05:
            # Значимые различия найдены
            winner = self._pairwise_winner(groups)
            return AnalysisResult(
                significant=True,
                winner=winner,
                confidence=self._compute_confidence(groups),
            )
        else:
            # Нет значимых различий
            return AnalysisResult(
                significant=False,
                winner=None,
                best_estimate=self._pooled_mean(groups),
            )
```

---

## Часть 10: Интеграция всех компонентов

### 10.1 Единая память агента

```python
class UnifiedAgentMemory:
    """
    Единая точка доступа ко всей памяти агента.
    """
    
    def __init__(self):
        # === ТИПЫ ПАМЯТИ ПО МЕТОДАМ ОРГАНИЗАЦИИ ===
        self.associative = AssociativeMemory()      # Похожесть
        self.vector = VectorMemoryStore()           # Embeddings
        self.graph = KnowledgeGraph()                # Связи
        self.temporal = EpisodicMemory()            # Хронология
        self.working = WorkingMemory()            # Быстрый доступ
        self.stack = ActionStack()               # Цепочки
        
        # === СПЕЦИФИЧЕСКИЕ ХРАНИЛИЩА ===
        self.tasks = TaskRepository()             # Картотека задач
        self.clients = ClientRepository()         # Карточки клиентов
        self.quality = QualityAnalysisSystem()   # Анализ качества
        self.reflection = ReflectionSystem()      # Рефлексия
        self.errors = ErrorAnalysisSystem()       # Ошибки
        self.providers = ProviderMonitor()        # Провайдеры
        self.strategy = StrategySwitcher()        # Смена стратегии
        self.bayesian = BayesianOptimizer()       # Баесовская оптимизация
        
        # === ПРОМПТЫ ===
        self.prompts = PromptBuilder()
        self.instructions = InstructionLibrary()
        
        # === ВНЕШНЯЯ СРЕДА ===
        self.internal_state = InternalEnvironmentState()
        self.external_state = ExternalEnvironmentState()
    
    # === УНИВЕРСАЛЬНЫЙ ПОИСК ===
    
    def search(self, query: Query) -> SearchResult:
        """
        Универсальный поиск по всей памяти.
        
        Автоматически выбирает метод поиска.
        """
        if query.type == 'semantic':
            return self.vector.search(query.text, k=query.limit)
        
        elif query.type == 'by_id':
            return self.tasks.get(query.id)
        
        elif query.type == 'by_client':
            return self.clients.get_by_id(query.client_id)
        
        elif query.type == 'by_time':
            return self.temporal.get_episodes_between(
                query.start_time, query.end_time
            )
        
        elif query.type == 'by_pattern':
            return self.patterns.find(query.pattern_type)
        
        elif query.type == 'by_error':
            return self.errors.find_similar(query.error_description)
        
        else:
            # Пробуем всё
            results = []
            results.extend(self.vector.search(query.text, k=5))
            results.extend(self.temporal.search(query.text, k=5))
            results.extend(self.graph.query(query.text))
            return self._rank_results(results)
    
    # === ЦИКЛ РАБОТЫ С ПАМЯТЬЮ ===
    
    def on_task_received(self, task: Task):
        """Обработка новой задачи"""
        # 1. Ищем похожее в памяти
        similar = self.vector.search(task.description, k=5)
        
        # 2. Получаем профиль клиента
        client = self.clients.get(task.client_id)
        
        # 3. Строим контекст
        context = self.prompts.build_context(
            'task_analysis',
            memory=self,
            current_state=self.internal_state,
            task=task,
            similar_tasks=similar,
            client=client,
        )
        
        # 4. Активируем инструкции
        instructions = self.instructions.get_active_instructions(
            agent_state=self.internal_state,
            task=task,
            triggers=self.internal_state.triggers.active,
        )
        
        return context, instructions
    
    def on_task_completed(self, task: Task, result: Result):
        """Обработка завершённой задачи"""
        # 1. Записываем в задачи
        self.tasks.add(task, result)
        
        # 2. Анализируем качество
        quality = self.quality.analyze(task, result)
        
        # 3. Обновляем клиента
        self.clients.update_after_task(task, quality)
        
        # 4. Записываем в эпизодическую память
        self.temporal.add_episode(Episode(
            type='TASK_COMPLETED',
            task_id=task.id,
            outcome=quality.success,
            quality=quality.overall,
        ))
        
        # 5. Если успех → записываем паттерн
        if quality.success:
            self.patterns.add_successful(task, result)
        
        # 6. Если провал → анализ ошибок
        else:
            causes = self.errors.analyze(task, result)
            self.errors.record(task, causes)
        
        # 7. Рефлексия
        reflection = self.reflection.reflect(ReflectionContext(task, result))
        
        # 8. Обновляем баесовскую статистику
        self.bayesian.record(
            parameters=self._current_parameters(),
            outcome=quality.overall,
            context={'task_type': task.type},
        )
        
        # 9. Проверяем метрики для стратегии
        if self.strategy.should_switch_strategy():
            new_strategy = self._suggest_new_strategy()
            self.strategy.switch_to(new_strategy)
        
        # 10. Обновляем состояние среды
        self.internal_state.update(quality.metrics)
    
    def on_trigger(self, trigger: Trigger):
        """Обработка триггера"""
        # 1. Ищем похожие триггеры в прошлом
        similar = self.temporal.find_similar_triggers(trigger)
        
        # 2. Получаем что сработало тогда
        if similar:
            past_actions = [s.suggested_action for s in similar]
            best_action = self._select_best_action(past_actions)
        else:
            best_action = None
        
        # 3. Контекст для решения
        context = self.prompts.build_context(
            'trigger_analysis',
            trigger=trigger,
            similar_past=similar,
            best_action=best_action,
            state=self.internal_state,
        )
        
        # 4. Возвращаем контекст + suggestions
        return TriggerResponse(
            context=context,
            suggested_action=best_action,
            confidence=self._compute_confidence(similar),
        )
```

---

## Заключение

Этот документ показал ГЛУБИНУ необходимой памяти:

1. **9+ методов организации памяти**: ассоциативная, векторная, графовая, временная, иерархическая, стековая, очередь, хэш-таблица

2. **Состояние среды** в реальном времени: метрики, гормоны, homeostat, рыночные данные, конкуренты

3. **Картотеки** задач и клиентов с полной историей и аналитикой

4. **Рефлексия и анализ ошибок**: классификация, поиск причин, предложение исправлений

5. **Формирование промтов**: библиотека шаблонов, динамическая сборка из памяти

6. **Провайдеры и роутинг**: метрики, оптимизация бюджета, кэширование

7. **Баесовская оптимизация**: сбор наблюдений, posterior distributions, exploration vs exploitation

Каждый компонент — это сложная система со своей логикой, которая должна быть реализована.

---

*Создано: 2026-07-08*
