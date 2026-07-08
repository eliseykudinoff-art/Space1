"""
================================================================================
                АТОМНЫЙ ДЕКОМПОЗИТОР ЗАДАЧ ДЛЯ API-ВЫЗОВОВ
================================================================================

Математическая модель декомпозиции задач на атомарные действия с автоматическим
определением оптимальных параметров API: промт, формат, контекст, модель.

Основные функции:
    D*(T) = argmax_D [U(D) - λ·C(D)]
    
    δ(T) = σ(w_δ · f(T))                    - решение о декомпозиции
    f*   = argmax Softmax(w_f · g(a))        - выбор формата
    c*   = argmax [Relevance - λ·Cost]       - выбор контекста
    m*   = argmax [P(success|m)·Quality - λ·Cost]  - выбор модели
    p*   = [S] + [I] + [C(c*)] + [E] + [O(f*)]    - генерация промта
    φ    = σ(w_φ · h(a))                     - confidence score

"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set, Any
from enum import Enum
from collections import defaultdict
import json


# =============================================================================
# ТИПЫ И ПЕРЕЧИСЛЕНИЯ
# =============================================================================

class OutputFormat(Enum):
    """Типы выходных форматов"""
    JSON = "json"
    TEXT = "text"
    MARKDOWN = "markdown"
    CODE = "code"
    BINARY = "binary"
    URI = "uri"
    YAML = "yaml"
    

class ModelTier(Enum):
    """Уровни моделей по мощности"""
    FAST = "fast"           # Дешёвые быстрые модели
    MEDIUM = "medium"       # Средние модели
    POWERFUL = "powerful"    # Мощные модели (GPT-4, Claude-3-Opus)


class ActionType(Enum):
    """Типы атомарных действий"""
    READ = "read"           # Чтение файлов/данных
    WRITE = "write"         # Запись файлов
    EXECUTE = "execute"     # Выполнение команд
    ANALYZE = "analyze"     # Анализ кода/данных
    GENERATE = "generate"   # Генерация контента
    SEARCH = "search"       # Поиск информации
    TRANSFORM = "transform" # Трансформация данных
    VALIDATE = "validate"   # Валидация


# =============================================================================
# МОДЕЛЬ АТОМАРНОГО ДЕЙСТВИЯ
# =============================================================================

@dataclass
class AtomicAction:
    """
    Структура атомарного действия
    
    a = (p, f, c, m, o, φ, r)
    
    где:
        p - промт (prompt)
        f - формат вывода (output format)
        c - контекст (context)
        m - модель (model)
        o - выход (output)
        φ - confidence score
        r - ресурсы (cost, latency)
    """
    id: str
    title: str
    description: str
    action_type: ActionType
    
    # Параметры для API
    prompt: 'Prompt' = None
    output_format: OutputFormat = OutputFormat.JSON
    context: 'Context' = None
    model: ModelTier = ModelTier.MEDIUM
    
    # Результат
    output: Any = None
    confidence: float = 0.5
    error: Optional[str] = None
    
    def __hash__(self):
        return hash(self.id)


@dataclass
class Prompt:
    """
    Структура промта
    
    p = (role, instructions, context_data, examples, output_spec)
    """
    role: str = "user"
    instructions: str = ""
    context_data: Dict = field(default_factory=dict)
    examples: List[Dict] = field(default_factory=list)
    output_spec: str = ""
    
    def to_string(self) -> str:
        """Конвертация в строку для API"""
        parts = []
        if self.role:
            parts.append(f"[{self.role.upper()}]")
        if self.instructions:
            parts.append(self.instructions)
        if self.context_data:
            parts.append(f"Context: {json.dumps(self.context_data, indent=2)}")
        if self.examples:
            parts.append("Examples:")
            for ex in self.examples:
                parts.append(f"  Input: {ex.get('input', '')}")
                parts.append(f"  Output: {ex.get('output', '')}")
        if self.output_spec:
            parts.append(f"Output format: {self.output_spec}")
        return "\n\n".join(parts)
    
    def estimate_tokens(self) -> int:
        """Оценка числа токенов"""
        text = self.to_string()
        return len(text.split()) * 1.3  # ~1.3 токена на слово


@dataclass
class Context:
    """
    Структура контекста
    
    c = (code, docs, history, memory)
    """
    code_chunks: List[str] = field(default_factory=list)
    documentation: List[str] = field(default_factory=list)
    history: List[Dict] = field(default_factory=list)
    memory: List[str] = field(default_factory=list)
    
    # Метаданные
    max_tokens: int = 128000
    relevance_scores: Dict[str, float] = field(default_factory=dict)
    
    def total_tokens(self) -> int:
        """Общее число токенов"""
        total = 0
        for chunk in self.code_chunks:
            total += len(chunk.split()) * 1.3
        for doc in self.documentation:
            total += len(doc.split()) * 1.3
        return int(total)
    
    def is_empty(self) -> bool:
        return not (self.code_chunks or self.documentation or 
                    self.history or self.memory)
    
    def select_relevant(self, query: str, top_k: int = 5) -> 'Context':
        """Выбрать наиболее релевантные чанки"""
        if self.is_empty():
            return Context()
        
        # Простая BM25-подобная оценка
        query_words = set(query.lower().split())
        scores = []
        
        for i, chunk in enumerate(self.code_chunks):
            chunk_words = set(chunk.lower().split())
            score = len(query_words & chunk_words) / max(len(query_words), 1)
            scores.append((score, i))
        
        scores.sort(reverse=True)
        selected_indices = [i for _, i in scores[:top_k]]
        
        return Context(
            code_chunks=[self.code_chunks[i] for i in selected_indices if i < len(self.code_chunks)],
            documentation=self.documentation[:2],  # Без лимита для доков
            history=self.history[-5:],  # Последние 5
            memory=self.memory
        )


@dataclass
class Dependency:
    """Зависимость между действиями"""
    from_action: str
    to_action: str
    dependency_type: str = "requires"  # requires, conflicts, related
    
    def __hash__(self):
        return hash((self.from_action, self.to_action))


@dataclass
class DecompositionResult:
    """Результат декомпозиции"""
    actions: List[AtomicAction]
    dependencies: List[Dependency]
    quality_score: float
    total_cost: float
    total_latency: float
    execution_plan: List[List[AtomicAction]]  # Уровни параллелизма
    
    def summary(self) -> str:
        lines = [
            "=" * 60,
            "ДЕТАЛИ ДЕКОМПОЗИЦИИ",
            "=" * 60,
            f"\n📊 Общие метрики:",
            f"   Действий: {len(self.actions)}",
            f"   Зависимостей: {len(self.dependencies)}",
            f"   Качество: {self.quality_score:.1%}",
            f"   Стоимость: ${self.total_cost:.4f}",
            f"   Latency: {self.total_latency:.1f}s",
            f"\n📦 План выполнения:",
        ]
        
        for level_num, level_actions in enumerate(self.execution_plan):
            lines.append(f"\n   Уровень {level_num + 1} ({len(level_actions)} параллельно):")
            for action in level_actions:
                lines.append(f"   [{action.id}] {action.title}")
                lines.append(f"      Формат: {action.output_format.value}")
                lines.append(f"      Модель: {action.model.value}")
                lines.append(f"      Контекст: {action.context.total_tokens() if action.context else 0} tokens")
                lines.append(f"      Confidence: {action.confidence:.0%}")
        
        return "\n".join(lines)


# =============================================================================
# КОНФИГУРАЦИЯ МОДЕЛЕЙ
# =============================================================================

MODEL_CONFIG = {
    ModelTier.FAST: {
        "name": "gpt-3.5-turbo",
        "context_window": 16385,
        "price_per_1k_input": 0.0015,
        "price_per_1k_output": 0.002,
        "latency_ms": 500,
        "capability": 0.6
    },
    ModelTier.MEDIUM: {
        "name": "gpt-4o-mini",
        "context_window": 128000,
        "price_per_1k_input": 0.003,
        "price_per_1k_output": 0.012,
        "latency_ms": 1000,
        "capability": 0.8
    },
    ModelTier.POWERFUL: {
        "name": "gpt-4o",
        "context_window": 128000,
        "price_per_1k_input": 0.015,
        "price_per_1k_output": 0.060,
        "latency_ms": 2000,
        "capability": 0.95
    }
}


# =============================================================================
# ФУНКЦИИ ПРИНЯТИЯ РЕШЕНИЙ
# =============================================================================

class DecisionFunctions:
    """
    Функции принятия решений для декомпозиции
    
    Основные функции:
        δ(T) - решение о декомпозиции
        f*(a) - выбор формата
        c*(a) - выбор контекста
        m*(a) - выбор модели
        p*(a) - генерация промта
        φ(a)  - confidence score
    """
    
    def __init__(self):
        # Веса для δ(T) - решение о декомпозиции
        self.w_delta = np.array([0.3, 0.4, 0.2, 0.1])  # size, complexity, uncertainty, depth
        self.b_delta = -0.5
        
        # Веса для f*(a) - выбор формата
        self.w_format = np.array([0.4, 0.3, 0.2, 0.1])  # action_type, consumer, prev_format, size
        
        # Веса для φ(a) - confidence
        self.w_confidence = np.array([0.25, 0.25, 0.25, 0.25])  # complexity, coverage, model_fit, format_fit
    
    def sigmoid(self, x: float) -> float:
        """Сигмоида"""
        return 1 / (1 + np.exp(-x))
    
    def softmax(self, x: np.ndarray) -> np.ndarray:
        """Softmax для выбора"""
        exp_x = np.exp(x - np.max(x))
        return exp_x / exp_x.sum()
    
    # =========================================================================
    # ФУНКЦИЯ 1: Решение о декомпозиции
    # =========================================================================
    
    def need_decompose(self, task: str, features: Dict = None) -> Tuple[bool, float]:
        """
        δ(T) = σ(w_δ · f(T) + b_δ)
        
        Решение: нужно ли декомпозировать задачу?
        
        Args:
            task: Текст задачи
            features: Предвычисленные признаки (size, complexity, uncertainty, depth)
            
        Returns:
            (need_decompose: bool, probability: float)
        """
        if features is None:
            features = self._extract_task_features(task)
        
        # Вектор признаков
        f = np.array([
            features.get('size', 0),
            features.get('complexity', 0),
            features.get('uncertainty', 0),
            features.get('depth', 0)
        ])
        
        # Сигмоида
        prob = self.sigmoid(np.dot(self.w_delta, f) + self.b_delta)
        
        # Решение
        threshold = 0.5
        need = prob > threshold
        
        return need, prob
    
    def _extract_task_features(self, task: str) -> Dict:
        """Извлечение признаков из задачи"""
        words = task.split()
        task_lower = task.lower()
        
        # Размер (нормализованный)
        size = min(len(words) / 50, 1.0)
        
        # Сложность (по ключевым словам)
        complex_keywords = [
            'refactor', 'redesign', 'migration', 'performance',
            'security', 'distributed', 'concurrent', 'multiple',
            'complex', 'implement', 'build', 'create', 'system',
            'api', 'authentication', 'jwt', 'database', 'integration'
        ]
        complexity = min(sum(1 for w in complex_keywords if w in task_lower) / 5, 1.0)
        
        # Учитываем количество пунктов в списке
        bullet_count = task.count('\n-') + task.count('\n*')
        complexity += min(bullet_count * 0.1, 0.3)
        
        # Неопределённость
        uncertain_keywords = [
            'maybe', 'perhaps', 'possibly', 'might', 'consider',
            'if needed', 'as appropriate', 'flexible'
        ]
        uncertainty = min(sum(1 for w in uncertain_keywords if w in task_lower) / 3, 1.0)
        
        # Глубина (оценочная)
        depth = 1.0 + complexity * 2
        
        return {
            'size': size,
            'complexity': complexity,
            'uncertainty': uncertainty,
            'depth': depth
        }
    
    # =========================================================================
    # ФУНКЦИЯ 2: Выбор формата вывода
    # =========================================================================
    
    def choose_format(self, action_type: ActionType) -> OutputFormat:
        """
        f* = argmax_f Softmax(w_f · g(a))_f
        
        Выбор оптимального формата вывода для действия
        
        Эвристика:
            - READ → TEXT
            - WRITE → зависит от типа файла
            - EXECUTE → JSON
            - ANALYZE → JSON/MARKDOWN
            - GENERATE → CODE/JSON
        """
        action_format_scores = {
            ActionType.READ: {'text': 0.9, 'json': 0.5, 'code': 0.6},
            ActionType.WRITE: {'code': 0.9, 'text': 0.3, 'json': 0.4},
            ActionType.EXECUTE: {'json': 0.9, 'text': 0.7, 'uri': 0.3},
            ActionType.ANALYZE: {'json': 0.8, 'markdown': 0.9, 'text': 0.6},
            ActionType.GENERATE: {'code': 0.9, 'json': 0.7, 'markdown': 0.5},
            ActionType.SEARCH: {'json': 0.8, 'text': 0.7, 'uri': 0.6},
            ActionType.TRANSFORM: {'json': 0.9, 'code': 0.6, 'text': 0.4},
            ActionType.VALIDATE: {'json': 0.9, 'text': 0.8, 'markdown': 0.5},
        }
        
        scores = action_format_scores.get(action_type, {'json': 0.8})
        
        # Выбор формата с наибольшим score
        best_format = max(scores, key=scores.get)
        
        return OutputFormat(best_format)
    
    # =========================================================================
    # ФУНКЦИЯ 3: Выбор контекста
    # =========================================================================
    
    def choose_context(self, 
                       action: AtomicAction, 
                       available_context: Context,
                       budget_tokens: int = None) -> Context:
        """
        c* = argmax_c [Relevance(a, c) - λ · Cost(c)]
        
        Выбор оптимального контекста для действия
        
        Args:
            action: Действие
            available_context: Доступный контекст
            budget_tokens: Бюджет токенов
            
        Returns:
            Context: Оптимальный контекст
        """
        if available_context.is_empty():
            return Context()
        
        # Оценка relevance каждого компонента контекста
        query = action.title + " " + action.description
        
        # BM25-подобный scoring
        query_words = set(query.lower().split())
        
        code_relevance = 0.0
        if available_context.code_chunks:
            scores = []
            for chunk in available_context.code_chunks:
                chunk_words = set(chunk.lower().split())
                score = len(query_words & chunk_words) / max(len(query_words), 1)
                # Бонус за порядок слов
                ordered_bonus = sum(1 for i, w in enumerate(query_words) 
                                   if w in chunk and i < 5) * 0.1
                scores.append(score + ordered_bonus)
            code_relevance = max(scores) if scores else 0.0
        
        doc_relevance = 0.5  # Документация обычно полезна
        history_relevance = 0.3  # История менее релевантна
        memory_relevance = 0.4
        
        # Вычисление relevance score
        total_relevance = (
            code_relevance * len(available_context.code_chunks) / max(len(available_context.code_chunks), 1) +
            doc_relevance * len(available_context.documentation) / max(len(available_context.documentation), 1) +
            history_relevance * 0.3 +
            memory_relevance * 0.2
        ) / 4
        
        # Cost - пропорционален размеру
        cost = available_context.total_tokens() / 1000  # Нормализация
        
        # Trade-off
        lambda_cost = 0.1
        net_score = total_relevance - lambda_cost * cost
        
        # Решение
        if net_score < 0.3:
            # Слишком дорого относительно пользы
            if available_context.code_chunks:
                # Выбрать только top-1 код
                return Context(code_chunks=[available_context.code_chunks[0]])
            return Context()
        
        # Truncate если превышает бюджет
        if budget_tokens and available_context.total_tokens() > budget_tokens:
            return available_context.select_relevant(query, top_k=3)
        
        return available_context
    
    # =========================================================================
    # ФУНКЦИЯ 4: Выбор модели
    # =========================================================================
    
    def choose_model(self, 
                     action: AtomicAction,
                     confidence_threshold: float = 0.5,
                     cost_budget: float = None) -> ModelTier:
        """
        m* = argmax_m [P(success|m) · Quality(m) - λ · Cost(m)]
        
        Выбор оптимальной модели для действия
        
        Эвристика:
            - Высокий confidence → мощная модель
            - Ограниченный бюджет → дешёвая модель
            - Генерация кода → мощная модель
        """
        # Оценка сложности действия
        action_complexity = self._estimate_action_complexity(action)
        
        # Требования к capability
        required_capability = action_complexity
        
        # Доступные модели
        candidates = []
        for tier, config in MODEL_CONFIG.items():
            capability = config['capability']
            cost = config['price_per_1k_input'] + config['price_per_1k_output']
            
            # P(success|m) - вероятность успеха
            p_success = capability ** 2
            
            # Score
            score = p_success * capability - 0.1 * cost
            
            # Штраф за недостаточную capability
            if capability < required_capability:
                score *= 0.5
            
            candidates.append((tier, score, cost))
        
        # Выбор модели с наибольшим score
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Фильтрация по бюджету
        if cost_budget:
            candidates = [(t, s, c) for t, s, c in candidates if c <= cost_budget]
        
        return candidates[0][0] if candidates else ModelTier.MEDIUM
    
    def _estimate_action_complexity(self, action: AtomicAction) -> float:
        """Оценка сложности действия"""
        complexity = 0.0
        
        # По типу
        type_complexity = {
            ActionType.READ: 0.3,
            ActionType.VALIDATE: 0.4,
            ActionType.SEARCH: 0.4,
            ActionType.TRANSFORM: 0.5,
            ActionType.WRITE: 0.6,
            ActionType.ANALYZE: 0.7,
            ActionType.GENERATE: 0.8,
            ActionType.EXECUTE: 0.9,
        }
        complexity += type_complexity.get(action.action_type, 0.5)
        
        # По размеру описания
        desc_len = len(action.description.split())
        if desc_len > 50:
            complexity += 0.2
        elif desc_len > 20:
            complexity += 0.1
        
        return min(complexity, 1.0)
    
    # =========================================================================
    # ФУНКЦИЯ 5: Генерация промта
    # =========================================================================
    
    def generate_prompt(self, 
                        action: AtomicAction,
                        context: Context = None,
                        include_examples: bool = True) -> Prompt:
        """
        p* = [S] + [I(a)] + [C(c*)] + [E] + [O(f*)]
        
        Генерация оптимального промта для действия
        """
        # System role
        role = self._get_role_for_action(action.action_type)
        
        # Instructions
        instructions = self._build_instructions(action)
        
        # Context
        context_data = {}
        if context:
            if context.code_chunks:
                context_data['code'] = context.code_chunks[:2]  # Ограничить
            if context.documentation:
                context_data['docs'] = context.documentation[:1]
        
        # Examples (если нужно)
        examples = []
        if include_examples and action.confidence < 0.7:
            examples = self._get_examples(action.action_type)
        
        # Output specification
        output_spec = self._get_output_spec(action.output_format)
        
        return Prompt(
            role=role,
            instructions=instructions,
            context_data=context_data,
            examples=examples,
            output_spec=output_spec
        )
    
    def _get_role_for_action(self, action_type: ActionType) -> str:
        """Определение роли по типу действия"""
        roles = {
            ActionType.READ: "You are a code analysis assistant.",
            ActionType.WRITE: "You are a software engineer.",
            ActionType.EXECUTE: "You are a DevOps engineer.",
            ActionType.ANALYZE: "You are a technical analyst.",
            ActionType.GENERATE: "You are a code generation assistant.",
            ActionType.SEARCH: "You are a research assistant.",
            ActionType.TRANSFORM: "You are a data transformation expert.",
            ActionType.VALIDATE: "You are a quality assurance engineer.",
        }
        return roles.get(action_type, "You are a helpful assistant.")
    
    def _build_instructions(self, action: AtomicAction) -> str:
        """Построение инструкций"""
        instructions = []
        
        # Основная задача
        instructions.append(action.description)
        
        # Тип-специфичные инструкции
        type_instructions = {
            ActionType.READ: "Analyze the provided code and extract key information.",
            ActionType.WRITE: "Generate code following best practices and the provided specifications.",
            ActionType.EXECUTE: "Execute the command and return structured results.",
            ActionType.ANALYZE: "Perform a thorough analysis and provide actionable insights.",
            ActionType.GENERATE: "Create the requested content with high quality.",
            ActionType.SEARCH: "Find and summarize relevant information.",
            ActionType.TRANSFORM: "Transform the data according to the specified rules.",
            ActionType.VALIDATE: "Verify the data and report any issues.",
        }
        
        if action.action_type in type_instructions:
            instructions.append(type_instructions[action.action_type])
        
        return "\n".join(instructions)
    
    def _get_examples(self, action_type: ActionType) -> List[Dict]:
        """Получение примеров для few-shot learning"""
        examples = {
            ActionType.ANALYZE: [
                {
                    'input': 'Analyze this function for bugs',
                    'output': '{"issues": [], "quality_score": 0.9}'
                }
            ],
            ActionType.GENERATE: [
                {
                    'input': 'Generate a REST endpoint',
                    'output': '```python\n@app.route("/api/resource")\ndef handler():\n    pass\n```'
                }
            ],
        }
        return examples.get(action_type, [])
    
    def _get_output_spec(self, output_format: OutputFormat) -> str:
        """Спецификация выходного формата"""
        specs = {
            OutputFormat.JSON: "Output must be valid JSON object.",
            OutputFormat.TEXT: "Output should be clear, concise text.",
            OutputFormat.MARKDOWN: "Output in Markdown format with headers and lists.",
            OutputFormat.CODE: "Output should be executable code with comments.",
            OutputFormat.BINARY: "Output as binary data.",
            OutputFormat.URI: "Output as file path or URI.",
            OutputFormat.YAML: "Output must be valid YAML.",
        }
        return specs.get(output_format, "Output in appropriate format.")
    
    # =========================================================================
    # ФУНКЦИЯ 6: Confidence Score
    # =========================================================================
    
    def compute_confidence(self, action: AtomicAction) -> float:
        """
        φ(a) = σ(w_φ · h(a))
        
        Вычисление confidence score для действия
        """
        # Признаки
        h = np.array([
            self._estimate_action_complexity(action),  # complexity
            action.context.total_tokens() / 1000 if action.context else 0,  # context coverage
            MODEL_CONFIG[action.model]['capability'],  # model fit
            1.0 if action.output_format == OutputFormat.JSON else 0.7,  # format fit
        ])
        
        # Сигмоида
        score = self.sigmoid(np.dot(self.w_confidence, h) + 0.5)
        
        return float(score)


# =============================================================================
# ОСНОВНОЙ КЛАСС ДЕКОМПОЗИТОРА
# =============================================================================

class AtomicDecomposer:
    """
    Декомпозитор задач на атомарные API-действия
    
    D*(T) = argmax_D [U(D) - λ·C(D)]
    
    Pipeline:
        1. Анализ задачи → признаки, δ(T)
        2. Декомпозиция → подзадачи
        3. Для каждой подзадачи:
           - f* = choose_format(a)
           - c* = choose_context(a, available)
           - m* = choose_model(a)
           - p* = generate_prompt(a, c*, f*)
           - φ = compute_confidence(a)
        4. Dependencies → DAG
        5. Validation → Quality, Cost
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or self._default_config()
        self.decisions = DecisionFunctions()
        
    def _default_config(self) -> Dict:
        return {
            'tau_decompose': 0.45,       # Порог декомпозиции (немного ниже для сложных задач)
            'max_depth': 5,              # Макс. глубина
            'max_actions': 10,           # Макс. число действий
            'max_context_tokens': 32000, # Макс. токенов контекста
            'cost_budget': 1.0,          # Бюджет на задачу ($)
            'lambda_cost': 0.1,          # Вес стоимости
            'alpha_quality': 0.4,        # Вес качества
            'beta_cost': 0.3,            # Вес стоимости
            'gamma_speed': 0.3,          # Вес скорости
        }
    
    def decompose(self, 
                  task: str, 
                  available_context: Context = None) -> DecompositionResult:
        """
        Основная функция декомпозиции
        
        Args:
            task: Текст задачи
            available_context: Доступный контекст
            
        Returns:
            DecompositionResult: Результат декомпозиции
        """
        available_context = available_context or Context()
        
        # ===== STAGE 1: Анализ задачи =====
        need_decomp, prob = self.decisions.need_decompose(task)
        
        if not need_decomp:
            # Тривиальная задача - возвращаем как одно действие
            return self._trivial_decomposition(task, available_context)
        
        # ===== STAGE 2: Генерация атомарных действий =====
        actions = self._generate_atomic_actions(task)
        
        # ===== STAGE 3: Параметры для каждого действия =====
        for action in actions:
            # Формат
            action.output_format = self.decisions.choose_format(action.action_type)
            
            # Контекст
            context_budget = self.config['max_context_tokens'] // len(actions)
            action.context = self.decisions.choose_context(
                action, available_context, budget_tokens=context_budget
            )
            
            # Модель
            action.model = self.decisions.choose_model(
                action, 
                confidence_threshold=0.7,
                cost_budget=self.config['cost_budget'] / len(actions)
            )
            
            # Промт
            action.prompt = self.decisions.generate_prompt(
                action, action.context, include_examples=True
            )
            
            # Confidence
            action.confidence = self.decisions.compute_confidence(action)
        
        # ===== STAGE 4: Dependencies =====
        dependencies = self._infer_dependencies(actions)
        
        # ===== STAGE 5: Execution plan =====
        execution_plan = self._build_execution_plan(actions, dependencies)
        
        # ===== STAGE 6: Quality & Cost =====
        quality = self._compute_quality(actions, dependencies)
        cost, latency = self._compute_cost_latency(actions)
        
        return DecompositionResult(
            actions=actions,
            dependencies=dependencies,
            quality_score=quality,
            total_cost=cost,
            total_latency=latency,
            execution_plan=execution_plan
        )
    
    def _trivial_decomposition(self, task: str, context: Context) -> DecompositionResult:
        """Обработка тривиальной задачи"""
        action_type = ActionType.GENERATE
        action = AtomicAction(
            id="A01",
            title="Execute task",
            description=task,
            action_type=action_type,
            context=context if context and not context.is_empty() else None,
            model=ModelTier.MEDIUM,
            output_format=self.decisions.choose_format(action_type)
        )
        action.prompt = self.decisions.generate_prompt(action, action.context)
        action.confidence = 0.8
        
        return DecompositionResult(
            actions=[action],
            dependencies=[],
            quality_score=0.7,
            total_cost=0.01,
            total_latency=1.0,
            execution_plan=[[action]]
        )
    
    def _generate_atomic_actions(self, task: str) -> List[AtomicAction]:
        """
        Генерация атомарных действий из задачи
        
        В реальной реализации здесь был бы LLM.
        Здесь - rule-based эвристика.
        """
        # Анализ задачи
        task_lower = task.lower()
        actions = []
        action_id = 1
        
        # Определение типа задачи
        if any(w in task_lower for w in ['implement', 'create', 'build', 'add']):
            # Feature development workflow
            actions.extend([
                AtomicAction(
                    id=f"A{action_id:02d}",
                    title="Design solution",
                    description=f"Design architecture for: {task[:50]}",
                    action_type=ActionType.ANALYZE
                ),
            ])
            action_id += 1
            
            actions.extend([
                AtomicAction(
                    id=f"A{action_id:02d}",
                    title="Generate code",
                    description=f"Implement: {task[:80]}",
                    action_type=ActionType.GENERATE
                ),
            ])
            action_id += 1
            
            if 'test' in task_lower or 'spec' in task_lower:
                actions.append(AtomicAction(
                    id=f"A{action_id:02d}",
                    title="Write tests",
                    description="Create test cases",
                    action_type=ActionType.GENERATE
                ))
                action_id += 1
                
        elif any(w in task_lower for w in ['fix', 'bug', 'error', 'issue']):
            # Bugfix workflow
            actions.extend([
                AtomicAction(
                    id=f"A{action_id:02d}",
                    title="Diagnose bug",
                    description=f"Investigate: {task[:50]}",
                    action_type=ActionType.ANALYZE
                ),
            ])
            action_id += 1
            
            actions.extend([
                AtomicAction(
                    id=f"A{action_id:02d}",
                    title="Fix issue",
                    description=f"Fix bug: {task[:50]}",
                    action_type=ActionType.WRITE
                ),
            ])
            action_id += 1
            
        elif any(w in task_lower for w in ['read', 'get', 'fetch', 'retrieve']):
            actions.append(AtomicAction(
                id=f"A{action_id:02d}",
                title="Read data",
                description=task,
                action_type=ActionType.READ
            ))
            
        elif any(w in task_lower for w in ['search', 'find', 'look']):
            actions.append(AtomicAction(
                id=f"A{action_id:02d}",
                title="Search",
                description=task,
                action_type=ActionType.SEARCH
            ))
            
        else:
            # Generic
            actions.append(AtomicAction(
                id=f"A{action_id:02d}",
                title="Execute",
                description=task,
                action_type=ActionType.EXECUTE
            ))
        
        # Ограничение числа действий
        return actions[:self.config['max_actions']]
    
    def _infer_dependencies(self, actions: List[AtomicAction]) -> List[Dependency]:
        """Вывод зависимостей между действиями"""
        dependencies = []
        
        # Эвристика: ANALYZE → GENERATE/WRITE → VALIDATE/TEST
        type_order = {
            ActionType.ANALYZE: 0,
            ActionType.READ: 0,
            ActionType.SEARCH: 0,
            ActionType.TRANSFORM: 1,
            ActionType.GENERATE: 2,
            ActionType.WRITE: 2,
            ActionType.EXECUTE: 3,
            ActionType.VALIDATE: 4,
        }
        
        for i, a_i in enumerate(actions):
            for j, a_j in enumerate(actions):
                if i >= j:
                    continue
                    
                order_i = type_order.get(a_i.action_type, 5)
                order_j = type_order.get(a_j.action_type, 5)
                
                if order_i < order_j:
                    dependencies.append(Dependency(
                        from_action=a_i.id,
                        to_action=a_j.id,
                        dependency_type="requires"
                    ))
        
        return dependencies
    
    def _build_execution_plan(self, 
                               actions: List[AtomicAction],
                               dependencies: List[Dependency]) -> List[List[AtomicAction]]:
        """Построение плана выполнения (уровни параллелизма)"""
        # Построение графа
        children = defaultdict(list)
        in_degree = {a.id: 0 for a in actions}
        
        for dep in dependencies:
            if dep.dependency_type == "requires":
                children[dep.from_action].append(dep.to_action)
                in_degree[dep.to_action] += 1
        
        # Topological sort по уровням
        levels = []
        remaining = {a.id for a in actions}
        
        while remaining:
            # Найти действия без входящих зависимостей
            current = [a for a in actions 
                      if a.id in remaining and in_degree[a.id] == 0]
            
            if not current:
                break
                
            levels.append(current)
            
            for action in current:
                remaining.remove(action.id)
                for child_id in children[action.id]:
                    in_degree[child_id] -= 1
        
        return levels
    
    def _compute_quality(self, 
                          actions: List[AtomicAction],
                          dependencies: List[Dependency]) -> float:
        """Вычисление качества декомпозиции"""
        if not actions:
            return 0.0
        
        # Coverage - полнота
        types = {a.action_type for a in actions}
        coverage = min(len(types) / 5, 1.0)  # Макс 5 типов
        
        # Atomicity - атомарность
        avg_confidence = np.mean([a.confidence for a in actions])
        atomicity = avg_confidence
        
        # Independence - независимость
        n = len(actions)
        max_deps = n * (n - 1) / 2
        independence = 1 - len(dependencies) / max(max_deps, 1)
        
        # Weighted sum
        quality = (
            0.4 * coverage +
            0.3 * atomicity +
            0.3 * independence
        )
        
        return float(quality)
    
    def _compute_cost_latency(self, actions: List[AtomicAction]) -> Tuple[float, float]:
        """Вычисление стоимости и latency"""
        total_cost = 0.0
        total_latency = 0.0
        
        for action in actions:
            config = MODEL_CONFIG[action.model]
            
            # Стоимость = (input_tokens + output_tokens) * price
            input_tokens = action.prompt.estimate_tokens() if action.prompt else 100
            output_tokens = 200  # Ожидаемый вывод
            cost = (input_tokens + output_tokens) / 1000 * (
                config['price_per_1k_input'] + config['price_per_1k_output']
            )
            total_cost += cost
            
            # Latency
            total_latency += config['latency_ms'] / 1000
        
        return total_cost, total_latency


# =============================================================================
# ИТОГОВАЯ МАТЕМАТИЧЕСКАЯ ФОРМУЛА
# =============================================================================

"""
================================================================================
                    ИТОГОВАЯ МАТЕМАТИЧЕСКАЯ ФОРМУЛА
                    АТОМНОЙ ДЕКОМПОЗИЦИИ
================================================================================

┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   ЦЕЛЕВАЯ ФУНКЦИЯ:                                                          │
│   ─────────────────                                                          │
│                                                                             │
│        D*(T) = argmax_D [ U(D) - λ·C(D) ]                                   │
│                 s.t. |A| ≤ A_max,  depth ≤ D_max                            │
│                                                                             │
│   где:                                                                      │
│     U(D) = Π u(a_i) · Π ρ(a_i, a_j)                                        │
│     C(D) = Σ [α·price(m_i) + β·latency(m_i) + γ·|c_i|]                     │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ФУНКЦИИ ПРИНЯТИЯ РЕШЕНИЙ:                                                  │
│   ───────────────────────                                                   │
│                                                                             │
│   1. НУЖНА ЛИ ДЕКОМПОЗИЦИЯ:                                                 │
│      δ(T) = σ( w_δ · f(T) + b_δ )                                          │
│                                                                             │
│   2. ВЫБОР ФОРМАТА:                                                         │
│      f* = argmax_f Softmax( w_f · g(a) )_f                                 │
│                                                                             │
│   3. ВЫБОР КОНТЕКСТА:                                                       │
│      c* = argmax_c [ Relevance(a,c) - λ·Cost(c) ]                         │
│                                                                             │
│   4. ВЫБОР МОДЕЛИ:                                                          │
│      m* = argmax_m [ P(success|m)·Quality(m) - λ·Cost(m) ]                │
│                                                                             │
│   5. ГЕНЕРАЦИЯ ПРОМТА:                                                       │
│      p* = [S] + [I(a)] + [C(c*)] + [E] + [O(f*)]                          │
│                                                                             │
│   6. CONFIDENCE SCORE:                                                       │
│      φ(a) = σ( w_φ · h(a) )                                                 │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   КОМПОНЕНТЫ АТОМАРНОГО ДЕЙСТВИЯ:                                           │
│   ────────────────────────────                                             │
│                                                                             │
│      a = ( p, f, c, m, o, φ, r )                                           │
│                                                                             │
│      p = ( role, instructions, context, examples, output_spec )             │
│      f ∈ { json, text, markdown, code, binary, uri, yaml }                 │
│      c = ( code_chunks, docs, history, memory )                             │
│      m ∈ { fast, medium, powerful }                                        │
│      o = output (result of API call)                                        │
│      φ = confidence score [0, 1]                                           │
│      r = resources (cost, latency)                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
"""


# =============================================================================
# ПРИМЕР ИСПОЛЬЗОВАНИЯ
# =============================================================================

if __name__ == "__main__":
    # Пример задачи
    task = """
    Implement a REST API for user authentication with JWT tokens.
    The API should support:
    - User registration with email and password
    - Login with JWT token generation
    - Token refresh endpoint
    - Password reset functionality
    - Rate limiting for security
    """
    
    # Доступный контекст
    context = Context(
        code_chunks=[
            "def authenticate_user(username, password): pass",
            "class UserModel: id, email, password_hash",
            "def generate_jwt_token(user_id): return token",
            "api.py - FastAPI router for /auth endpoints",
        ],
        documentation=[
            "JWT authentication best practices",
            "FastAPI security middleware documentation",
        ],
        memory=["Previous auth implementation used sessions"]
    )
    
    print("=" * 70)
    print("ДЕКОМПОЗИЦИЯ ЗАДАЧИ НА АТОМНЫЕ API-ДЕЙСТВИЯ")
    print("=" * 70)
    print(f"\n📋 Задача:\n{task[:100]}...\n")
    
    # Инициализация декомпозитора
    decomposer = AtomicDecomposer()
    
    # Декомпозиция
    result = decomposer.decompose(task, context)
    
    # Вывод результата
    print(result.summary())
    
    # Детали по каждому действию
    print("\n" + "=" * 70)
    print("ДЕТАЛИ API-ВЫЗОВОВ")
    print("=" * 70)
    
    for action in result.actions:
        print(f"\n{'─' * 50}")
        print(f"▶ {action.id}: {action.title}")
        print(f"  Тип: {action.action_type.value}")
        print(f"  Формат: {action.output_format.value}")
        print(f"  Модель: {MODEL_CONFIG[action.model]['name']}")
        print(f"  Контекст: {action.context.total_tokens() if action.context else 0} tokens")
        print(f"  Confidence: {action.confidence:.0%}")
        
        if action.prompt:
            prompt_preview = action.prompt.to_string()[:150].replace('\n', ' ')
            print(f"  Промт: {prompt_preview}...")
    
    print("\n" + "=" * 70)
    print("МАТЕМАТИЧЕСКАЯ ФОРМУЛА")
    print("=" * 70)
    print("""
    D*(T) = argmax_D [ U(D) - λ·C(D) ]
    
    где для каждого действия a:
        f* = argmax_f Softmax(w_f · g(a))
        c* = argmax_c [Relevance - λ·Cost]
        m* = argmax_m [P(success|m)·Quality - λ·Cost]
        p* = [S] + [I] + [C(c*)] + [E] + [O(f*)]
        φ  = σ(w_φ · h(a))
    """)
