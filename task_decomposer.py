"""
Математическая модель декомпозиции задач
=========================================

Реализация на основе:
- Hierarchical Task Planning (REACTREE)
- Select-Then-Decompose strategies
- DAG-based dependency modeling
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Set
from enum import Enum
from collections import deque


class SubtaskType(Enum):
    """Типы подзадач"""
    FEATURE = "feature"
    BUGFIX = "bugfix"
    REFACTOR = "refactor"
    TEST = "test"
    DOCS = "docs"
    CONFIG = "config"
    RESEARCH = "research"


class DependencyType(Enum):
    """Типы зависимостей"""
    REQUIRES = "requires"      # s_j требует результат s_i
    CONFLICTS = "conflicts"    # s_j конфликтует с s_i
    RELATED = "related"         # s_j связана с s_i (soft)


@dataclass
class Subtask:
    """Подзадача"""
    id: str
    title: str
    description: str
    type: SubtaskType
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    estimated_effort: float = 1.0
    confidence: float = 1.0
    
    def __hash__(self):
        return hash(self.id)


@dataclass
class Dependency:
    """Зависимость между подзадачами"""
    from_task: str
    to_task: str
    type: DependencyType
    strength: float  # [0, 1]


@dataclass 
class DecompositionResult:
    """Результат декомпозиции"""
    subtasks: List[Subtask]
    dependencies: List[Dependency]
    quality_score: float
    completeness: float
    independence: float
    granularity: float
    feasibility: float
    depth: int
    max_parallelism: int


# =============================================================================
# ЧАСТЬ 1: МОДЕЛЬ ДЕКОМПОЗИЦИИ
# =============================================================================

class TaskDecomposer:
    """
    Модель декомпозиции задач
    
    D*(T) = argmax_D Q(D)  при ограничениях depth ≤ D_max, |S| ≤ S_max
    
    где:
        D = (S, G) - результат декомпозиции
        S - множество подзадач
        G - DAG зависимостей
        Q - функция качества
    """
    
    def __init__(self, config=None):
        self.config = config or self._default_config()
        
    def _default_config(self):
        return {
            'tau_decomp': 0.5,        # Порог необходимости декомпозиции
            'tau_dep': 0.5,           # Порог зависимости
            'tau_feas': 0.3,          # Порог выполнимости
            'tau_quality': 0.7,       # Минимальное качество
            'S_max': 10,              # Макс. число подзадач
            'D_max': 5,               # Макс. глубина
            'alpha': 0.3,             # Вес полноты
            'beta': 0.3,             # Вес независимости
            'gamma': 0.2,            # Вес гранулярности
            'delta': 0.2,            # Вес выполнимости
        }
    
    def decompose(self, task_text: str, context: str = "") -> DecompositionResult:
        """
        Основная функция декомпозиции
        
        Args:
            task_text: Текст задачи
            context: Дополнительный контекст
            
        Returns:
            DecompositionResult: Результат декомпозиции
        """
        # Шаг 1: Оценка необходимости декомпозиции
        need_decomp = self._need_decompose(task_text, context)
        
        if not need_decomp:
            # Тривиальная задача - возвращаем как есть
            return self._trivial_decomposition(task_text)
        
        # Шаг 2: Оценка глубины декомпозиции
        depth = self._estimate_depth(task_text)
        
        # Шаг 3: Генерация подзадач (итеративно)
        subtasks = self._generate_subtasks(task_text, depth)
        
        # Шаг 4: Построение DAG зависимостей
        dependencies = self._build_dependency_graph(subtasks)
        
        # Шаг 5: Вычисление качества
        quality = self._compute_quality(subtasks, dependencies)
        
        # Шаг 6: Верификация и рефайнмент
        if quality < self.config['tau_quality']:
            subtasks = self._refine_decomposition(subtasks, dependencies)
            quality = self._compute_quality(subtasks, dependencies)
        
        # Вычисление метрик
        completeness = self._completeness(subtasks)
        independence = self._independence(len(subtasks), len(dependencies))
        granularity = self._granularity(len(subtasks))
        feasibility = self._feasibility(subtasks)
        
        # Вычисление параллелизма
        levels = self._compute_parallel_levels(subtasks, dependencies)
        
        return DecompositionResult(
            subtasks=subtasks,
            dependencies=dependencies,
            quality_score=quality,
            completeness=completeness,
            independence=independence,
            granularity=granularity,
            feasibility=feasibility,
            depth=depth,
            max_parallelism=max(len(l) for l in levels) if levels else 1
        )
    
    def _need_decompose(self, task_text: str, context: str) -> bool:
        """
        Оценка необходимости декомпозиции
        
        φ_decomp(T) = σ(w · [e_text; e_ctx] + b)
        
        Returns:
            bool: True если нужно декомпозировать
        """
        # Упрощённая эвристика
        text_len = len(task_text.split())
        has_context = len(context) > 100
        
        # Сигнальная функция от оценки сложности
        complexity_score = self._estimate_complexity(task_text, context)
        phi = 1 / (1 + np.exp(-complexity_score + 2))  # сигмоида смещённая
        
        return phi > self.config['tau_decomp']
    
    def _estimate_complexity(self, task_text: str, context: str) -> float:
        """
        Оценка сложности задачи
        
        complexity = f(text_len, keywords, context_size)
        """
        features = []
        
        # Длина текста (больше = сложнее)
        features.append(len(task_text.split()) / 100)
        
        # Ключевые слова сложности
        complex_keywords = [
            'refactor', 'redesign', 'migration', 'performance',
            'security', 'distributed', 'concurrent', 'async',
            'multiple', 'several', 'various', 'complex'
        ]
        word_count = sum(1 for w in complex_keywords if w in task_text.lower())
        features.append(word_count)
        
        # Размер контекста
        features.append(len(context) / 1000)
        
        # Простая взвешенная сумма
        weights = [0.3, 0.4, 0.3]
        return sum(w * f for w, f in zip(weights, features))
    
    def _estimate_depth(self, task_text: str) -> int:
        """
        Оценка оптимальной глубины декомпозиции
        
        depth* = round(log₂(|affected_files| · complexity / τ_task))
        
        Returns:
            int: Рекомендуемая глубина [1, D_max]
        """
        complexity = self._estimate_complexity(task_text, "")
        
        # Оценка числа затронутых аспектов
        affected_aspects = len(task_text.split()) / 20
        
        # Формула глубины
        depth_raw = np.log2(max(1, affected_aspects * complexity))
        depth = max(1, min(round(depth_raw), self.config['D_max']))
        
        return int(depth)
    
    def _generate_subtasks(self, task_text: str, depth: int) -> List[Subtask]:
        """
        Генерация подзадач
        
        s_i = G_θ(T, S_{<i})
        
        В реальной реализации здесь был бы LLM.
        Здесь - упрощённая эвристика.
        """
        # Анализ задачи для определения типов подзадач
        task_lower = task_text.lower()
        
        subtasks = []
        task_id = 1
        
        # Детекция типа задачи
        if 'bug' in task_lower or 'fix' in task_lower or 'error' in task_lower:
            # Bugfix workflow
            subtasks.extend([
                Subtask(
                    id=f"S{task_id:02d}",
                    title="Diagnose the bug",
                    description="Investigate root cause",
                    type=SubtaskType.RESEARCH,
                    estimated_effort=2.0
                ),
                task_id := task_id + 1,
                Subtask(
                    id=f"S{task_id:02d}",
                    title="Implement the fix",
                    description="Fix the identified issue",
                    type=SubtaskType.BUGFIX,
                    estimated_effort=3.0
                ),
                task_id := task_id + 1,
                Subtask(
                    id=f"S{task_id:02d}",
                    title="Write tests",
                    description="Add test cases for the fix",
                    type=SubtaskType.TEST,
                    estimated_effort=1.5
                ),
                task_id := task_id + 1,
                Subtask(
                    id=f"S{task_id:02d}",
                    title="Update documentation",
                    description="Document the fix if needed",
                    type=SubtaskType.DOCS,
                    estimated_effort=0.5
                ),
            ])
        
        elif 'implement' in task_lower or 'add' in task_lower or 'create' in task_lower:
            # Feature workflow
            subtasks.extend([
                Subtask(
                    id=f"S{task_id:02d}",
                    title="Design solution",
                    description="Create technical design",
                    type=SubtaskType.RESEARCH,
                    estimated_effort=1.5
                ),
                task_id := task_id + 1,
                Subtask(
                    id=f"S{task_id:02d}",
                    title="Implement core feature",
                    description="Implement the main functionality",
                    type=SubtaskType.FEATURE,
                    estimated_effort=4.0
                ),
                task_id := task_id + 1,
                Subtask(
                    id=f"S{task_id:02d}",
                    title="Add tests",
                    description="Write unit and integration tests",
                    type=SubtaskType.TEST,
                    estimated_effort=2.0
                ),
                task_id := task_id + 1,
                Subtask(
                    id=f"S{task_id:02d}",
                    title="Update documentation",
                    description="Document new feature",
                    type=SubtaskType.DOCS,
                    estimated_effort=1.0
                ),
            ])
        
        else:
            # Generic workflow
            subtasks.extend([
                Subtask(
                    id=f"S{task_id:02d}",
                    title="Analyze requirements",
                    description="Understand the task requirements",
                    type=SubtaskType.RESEARCH,
                    estimated_effort=1.0
                ),
                task_id := task_id + 1,
                Subtask(
                    id=f"S{task_id:02d}",
                    title="Implement changes",
                    description="Make necessary changes",
                    type=SubtaskType.FEATURE,
                    estimated_effort=3.0
                ),
                task_id := task_id + 1,
                Subtask(
                    id=f"S{task_id:02d}",
                    title="Test changes",
                    description="Verify the changes work correctly",
                    type=SubtaskType.TEST,
                    estimated_effort=1.5
                ),
            ])
        
        return subtasks
    
    def _build_dependency_graph(self, subtasks: List[Subtask]) -> List[Dependency]:
        """
        Построение графа зависимостей
        
        dep(s_i, s_j) = σ(w · [e(s_i); e(s_j)] - b)
        
        Returns:
            List[Dependency]: Список зависимостей
        """
        dependencies = []
        
        # Эвристика: RESEARCH -> FEATURE/BUGFIX -> TEST -> DOCS
        type_order = {
            SubtaskType.RESEARCH: 0,
            SubtaskType.CONFIG: 1,
            SubtaskType.FEATURE: 2,
            SubtaskType.BUGFIX: 2,
            SubtaskType.REFACTOR: 2,
            SubtaskType.TEST: 3,
            SubtaskType.DOCS: 4,
        }
        
        for i, s_i in enumerate(subtasks):
            for j, s_j in enumerate(subtasks):
                if i >= j:
                    continue
                    
                # Проверяем зависимость по типам и порядку
                if type_order[s_i.type] < type_order[s_j.type]:
                    # s_j требует s_i
                    strength = 0.9  # Высокая уверенность
                    dependencies.append(Dependency(
                        from_task=s_i.id,
                        to_task=s_j.id,
                        type=DependencyType.REQUIRES,
                        strength=strength
                    ))
        
        return dependencies
    
    def _compute_quality(self, subtasks: List[Subtask], 
                         dependencies: List[Dependency]) -> float:
        """
        Вычисление функции качества
        
        Q = α·Completeness + β·Independence + γ·Granularity + δ·Feasibility
        """
        completeness = self._completeness(subtasks)
        independence = self._independence(len(subtasks), len(dependencies))
        granularity = self._granularity(len(subtasks))
        feasibility = self._feasibility(subtasks)
        
        quality = (
            self.config['alpha'] * completeness +
            self.config['beta'] * independence +
            self.config['gamma'] * granularity +
            self.config['delta'] * feasibility
        )
        
        return quality
    
    def _completeness(self, subtasks: List[Subtask]) -> float:
        """
        Полнота покрытия
        
        Completeness = |CoveredAspects| / |AllAspects|
        """
        # Оценка: проверяем наличие ключевых аспектов
        covered_aspects = 0
        total_aspects = 5  # design, impl, test, docs, review
        
        types = {s.type for s in subtasks}
        
        if SubtaskType.RESEARCH in types or SubtaskType.CONFIG:
            covered_aspects += 1
        if SubtaskType.FEATURE in types or SubtaskType.BUGFIX in types:
            covered_aspects += 1
        if SubtaskType.TEST in types:
            covered_aspects += 1
        if SubtaskType.DOCS in types:
            covered_aspects += 1
        if SubtaskType.REFACTOR in types:
            covered_aspects += 1
        
        return covered_aspects / total_aspects
    
    def _independence(self, n_tasks: int, n_deps: int) -> float:
        """
        Независимость подзадач
        
        Independence = 1 - 2|E| / (|S|(|S|-1))
        """
        if n_tasks <= 1:
            return 1.0
        
        max_deps = n_tasks * (n_tasks - 1) / 2
        independence = 1 - (2 * n_deps) / (n_tasks * (n_tasks - 1))
        
        return max(0, min(1, independence))
    
    def _granularity(self, n_tasks: int, n_star: float = 5.0) -> float:
        """
        Гранулярность
        
        Granularity = σ(-( |S| - N* )² / 2σ²)
        
        Штрафует слишком мелкие или слишком крупные подзадачи
        """
        sigma = 3.0
        score = np.exp(-((n_tasks - n_star) ** 2) / (2 * sigma ** 2))
        return float(score)
    
    def _feasibility(self, subtasks: List[Subtask]) -> float:
        """
        Выполнимость
        
        Feasibility = средняя оценка выполнимости подзадач
        """
        if not subtasks:
            return 0.0
        
        # Оценка выполнимости на основе признаков
        feasibilities = []
        for s in subtasks:
            # Простая эвристика
            desc_len = len(s.description.split())
            effort = s.estimated_effort
            
            # Короткие описания с умеренным усилием = выполнимо
            if desc_len >= 3 and effort <= 5:
                feas = 0.8
            elif desc_len >= 1 and effort <= 8:
                feas = 0.5
            else:
                feas = 0.3
            
            feasibilities.append(feas)
        
        return np.mean(feasibilities)
    
    def _compute_parallel_levels(self, subtasks: List[Subtask],
                                  dependencies: List[Dependency]) -> List[List[Subtask]]:
        """
        Вычисление уровней параллелизма для DAG
        
        Returns:
            List[List[Subtask]]: Подзадачи, которые можно выполнить параллельно
        """
        # Построение списка потомков для каждой задачи
        children = {s.id: [] for s in subtasks}
        in_degree = {s.id: 0 for s in subtasks}
        
        for dep in dependencies:
            if dep.type == DependencyType.REQUIRES:
                children[dep.from_task].append(dep.to_task)
                in_degree[dep.to_task] += 1
        
        # Topological sort по уровням
        levels = []
        remaining = set(s.id for s in subtasks)
        
        while remaining:
            # Находим задачи без входящих зависимостей
            current_level = [s for s in subtasks 
                           if s.id in remaining and in_degree[s.id] == 0]
            
            if not current_level:
                break
            
            levels.append(current_level)
            
            # Уменьшаем in_degree для потомков
            for task in current_level:
                remaining.remove(task.id)
                for child_id in children[task.id]:
                    in_degree[child_id] -= 1
        
        return levels
    
    def _trivial_decomposition(self, task_text: str) -> DecompositionResult:
        """Обработка тривиальной задачи"""
        subtask = Subtask(
            id="S01",
            title=task_text[:50],
            description=task_text,
            type=SubtaskType.FEATURE,
            estimated_effort=1.0
        )
        
        return DecompositionResult(
            subtasks=[subtask],
            dependencies=[],
            quality_score=0.5,
            completeness=0.2,
            independence=1.0,
            granularity=1.0,
            feasibility=0.9,
            depth=1,
            max_parallelism=1
        )
    
    def _refine_decomposition(self, subtasks: List[Subtask],
                             dependencies: List[Dependency]) -> List[Subtask]:
        """
        Рефайнмент декомпозиции для улучшения качества
        """
        # В реальной реализации здесь был бы LLM с feedback
        # Упрощённо: возвращаем как есть
        return subtasks
    
    def get_execution_plan(self, result: DecompositionResult) -> str:
        """
        Генерация плана выполнения
        """
        levels = self._compute_parallel_levels(
            result.subtasks, result.dependencies
        )
        
        plan = "=" * 60 + "\n"
        plan += "ПЛАН ВЫПОЛНЕНИЯ\n"
        plan += "=" * 60 + "\n\n"
        
        for level_num, level_tasks in enumerate(levels):
            plan += f"📦 Уровень {level_num + 1} ({len(level_tasks)} задач параллельно):\n"
            for task in level_tasks:
                plan += f"   [{task.id}] {task.title}\n"
                plan += f"       Тип: {task.type.value}, Оценка: {task.estimated_effort}h\n"
            plan += "\n"
        
        plan += "-" * 60 + "\n"
        plan += f"📊 Метрики:\n"
        plan += f"   Качество: {result.quality_score:.2%}\n"
        plan += f"   Полнота: {result.completeness:.2%}\n"
        plan += f"   Независимость: {result.independence:.2%}\n"
        plan += f"   Гранулярность: {result.granularity:.2%}\n"
        plan += f"   Выполнимость: {result.feasibility:.2%}\n"
        plan += f"   Макс. параллелизм: {result.max_parallelism}\n"
        plan += f"   Общее время: {sum(s.estimated_effort for s in result.subtasks)}h\n"
        
        return plan


# =============================================================================
# ИТОГОВАЯ МАТЕМАТИЧЕСКАЯ ФОРМУЛА
# =============================================================================

"""
================================================================================
                    ИТОГОВАЯ МАТЕМАТИЧЕСКАЯ ФОРМУЛА
                    ДЕКОМПОЗИЦИИ ЗАДАЧ
================================================================================

┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   ОСНОВНАЯ ЦЕЛЕВАЯ ФУНКЦИЯ:                                                │
│   ─────────────────────────                                                 │
│                                                                             │
│        D*(T) = argmax_D  Q(D)                                               │
│                 s.t. |S| ≤ S_max,  depth(G) ≤ D_max                         │
│                                                                             │
│   где:                                                                      │
│     D = (S, G)     - результат декомпозиции                                  │
│     S = {s₁,...,sₙ} - множество подзадач                                    │
│     G = (S, E)    - DAG зависимостей                                        │
│     Q(D)          - функция качества                                        │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ФУНКЦИЯ КАЧЕСТВА:                                                         │
│   ─────────────────                                                         │
│                                                                             │
│   Q(D) = α · Completeness(S)                                               │
│          + β · Independence(S, E)                                          │
│          + γ · Granularity(S)                                              │
│          + δ · Feasibility(S)                                              │
│                                                                             │
│   где:                                                                      │
│     Completeness(S) = |C_cov| / |C|                                         │
│     Independence(S,E) = 1 - 2|E| / (|S|(|S|-1))                            │
│     Granularity(S) = exp(-(|S| - N*)² / 2σ²)                               │
│     Feasibility(S) = (1/|S|) Σ P_feas(s)                                    │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   РЕШЕНИЕ О ДЕКОМПОЗИЦИИ:                                                   │
│   ───────────────────────                                                   │
│                                                                             │
│   Decompose(s) ⟺ σ(w · e(s) + b) > τ_decomp                               │
│                                                                             │
│   Глубина:                                                                 │
│   depth* = round(log₂(|files| · complexity / τ_task))                      │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ЗАВИСИМОСТИ МЕЖДУ ПОДЗАДАЧАМИ:                                            │
│   ─────────────────────────                                                 │
│                                                                             │
│   e_ij ∈ E ⟺ σ(w_dep · [e(s_i); e(s_j)] - b_dep) > τ_dep                 │
│                                                                             │
│   Типы:                                                                    │
│     REQUIRES  - s_j требует результат s_i                                  │
│     CONFLICTS - s_j конфликтует с s_i                                      │
│     RELATED   - s_j связана с s_i (мягкая)                                 │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ВЫПОЛНЕНИЕ:                                                               │
│   ─────────                                                                 │
│                                                                             │
│   Levels(l) = {s : longest_path(s) = l}                                   │
│                                                                             │
│   execute = [s for l in topological_sort(G) for s in Levels(l)]           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
"""


# =============================================================================
# ПРИМЕР ИСПОЛЬЗОВАНИЯ
# =============================================================================

if __name__ == "__main__":
    # Пример задачи
    task = """
    Implement user authentication system with OAuth2 support.
    The system should support:
    - Login with Google, GitHub, and email/password
    - Session management with JWT tokens
    - Password reset functionality
    - Two-factor authentication (2FA)
    - User roles and permissions
    """
    
    print("=" * 70)
    print("ДЕКОМПОЗИЦИЯ ЗАДАЧИ")
    print("=" * 70)
    print(f"\n📋 Исходная задача:\n{task[:100]}...")
    
    # Инициализация декомпозитора
    decomposer = TaskDecomposer()
    
    # Декомпозиция
    result = decomposer.decompose(task)
    
    # Вывод плана
    print(decomposer.get_execution_plan(result))
    
    print("\n" + "=" * 70)
    print("МАТЕМАТИЧЕСКАЯ ФОРМУЛА")
    print("=" * 70)
    print("""
    D*(T) = argmax_S,Q  [α·C + β·I + γ·G + δ·F]
    
    где:
        C = |CoveredAspects| / |AllAspects|
        I = 1 - 2|E| / (|S|(|S|-1))
        G = exp(-(|S| - N*)² / 2σ²)
        F = (1/|S|) Σ P_feas(s)
    """)
