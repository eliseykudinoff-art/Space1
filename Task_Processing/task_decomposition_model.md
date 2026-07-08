# Математическая модель декомпозиции задач

## Введение

Декомпозиция задач — это процесс разбиения сложной задачи на меньшие, управляемые подзадачи. В контексте AI-агентов для разработки ПО это критически важный этап для:

- Преодоления ограничений контекстного окна
- Параллельного выполнения независимых подзадач
- Управления зависимостями между задачами
- Оценки времени и ресурсов
- Human-in-the-loop верификации

---

## 1. Постановка задачи

### 1.1 Входные данные

Задача $T$ характеризуется:

| Компонент | Обозначение | Описание |
|-----------|-------------|----------|
| Текст | $\mathbf{x}_{text}$ | Заголовок, описание, комментарии |
| Контекст | $\mathbf{x}_{ctx}$ | Кодовая база, существующие issues |
| Метаданные | $\mathbf{x}_{meta}$ | Labels, assignees, repo info |

### 1.2 Выходные данные

Результат декомпозиции:

$$D(T) = (\mathcal{S}, \mathcal{G})$$

где:
- $\mathcal{S} = \{s_1, s_2, \ldots, s_n\}$ — множество подзадач
- $\mathcal{G} = (\mathcal{S}, \mathcal{E})$ — DAG зависимостей, $\mathcal{E} \subseteq \mathcal{S} \times \mathcal{S}$

### 1.3 Критерии качества

$$\mathcal{Q}(D) = \alpha \cdot \underbrace{\text{Completeness}(\mathcal{S})}_{\text{полнота}} + \beta \cdot \underbrace{\text{Independence}(\mathcal{S}, \mathcal{G})}_{\text{независимость}} + \gamma \cdot \underbrace{\text{Granularity}(\mathcal{S})}_{\text{гранулярность}} + \delta \cdot \underbrace{\text{Feasibility}(\mathcal{S})}_{\text{выполнимость}}$$

при ограничениях:
- $|\mathcal{S}| \leq S_{max}$ — максимальное число подзадач
- $\text{depth}(\mathcal{G}) \leq D_{max}$ — максимальная глубина
- $\forall s \in \mathcal{S}: \text{Feasibility}(s) \geq \tau_{feas}$ — выполнимость каждой подзадачи

---

## 2. Формальная модель декомпозиции

### 2.1 Оценка необходимости декомпозиции

$$\phi_{decomp}(T) = \sigma(\mathbf{w}_\phi \cdot [\mathbf{e}_{text}; \mathbf{e}_{ctx}] + b_\phi)$$

где:
- $\mathbf{e}_{text} = \text{Encoder}(x_{text})$ — эмбеддинг задачи
- $\mathbf{e}_{ctx} = \text{Encoder}(x_{ctx})$ — эмбеддинг контекста
- $\sigma$ — сигмоида

**Решение:**
$$need\_decompose(T) = \begin{cases} \text{True} & \phi_{decomp}(T) > \tau_{decomp} \\ \text{False} & \text{иначе} \end{cases}$$

### 2.2 Оценка глубины декомпозиции

$$\text{depth}^* = \underset{d}{\arg\min} \; \mathcal{L}_{total}(d)$$

$$\mathcal{L}_{total}(d) = \underbrace{\text{Cost}(d)}_{\text{стоимость декомпозиции}} + \lambda \cdot \underbrace{\text{Latency}(d)}_{\text{ожидаемое время}}$$

**Факторы глубины:**
- Размер задачи (количество файлов для изменения)
- Сложность (число сущностей, связей)
- Неопределённость (clarity описания)

$$\text{depth}^* = \text{Round}\left(\log_2\left(\frac{|\text{affected\_files}| \cdot \text{complexity}}{\tau_{task}}\right)\right)$$

где $\tau_{task}$ — типичный размер задачи.

---

## 3. Генерация подзадач

### 3.1 Subtask Generator

$$s_i = G_\theta(T, \mathcal{S}_{<i})$$

где $G_\theta$ — генеративная модель (LLM), $\mathcal{S}_{<i}$ — ранее сгенерированные подзадачи.

### 3.2 Структура подзадачи

Каждая подзадача $s_i$ содержит:

$$s_i = \{\text{id}, \text{title}, \text{description}, \text{type}, \text{inputs}, \text{outputs}, \text{acceptance\_criteria}, \text{estimated\_effort}\}$$

### 3.3 Типы подзадач

| Тип | Обозначение | Описание |
|-----|-------------|----------|
| Feature | $t_{feat}$ | Новая функциональность |
| Bugfix | $t_{bug}$ | Исправление дефекта |
| Refactor | $t_{ref}$ | Рефакторинг кода |
| Test | $t_{test}$ | Написание тестов |
| Docs | $t_{doc}$ | Документация |
| Config | $t_{conf}$ | Конфигурация |

---

## 4. Модель зависимостей (DAG)

### 4.1 Функция зависимости

$$\text{dep}(s_i, s_j) = \sigma(\mathbf{w}_{dep}^T \cdot [\mathbf{e}(s_i); \mathbf{e}(s_j)] - b_{dep})$$

$$\text{Dep}(s_i, s_j) = \begin{cases} \text{True} & \text{dep}(s_i, s_j) > \tau_{dep} \\ \text{False} & \text{иначе} \end{cases}$$

### 4.2 Типы зависимостей

| Тип | Обозначение | Описание |
|-----|-------------|----------|
| `requires` | $e_{req}$ | $s_j$ требует результат $s_i$ |
| `conflicts` | $e_{conf}$ | $s_j$ конфликтует с $s_i$ |
| `related` | $e_{rel}$ | $s_j$ связана с $s_i$ (soft) |

### 4.3 Построение DAG

$$\mathcal{G} = \text{TopologicalSort}(\mathcal{S}, \mathcal{E})$$

где $\mathcal{E} = \{(s_i, s_j) : s_j \text{ requires } s_i\}$.

### 4.4 Уровни параллелизма

$$\text{Level}(l) = \{s \in \mathcal{S} : \text{longest\_path}(s) = l\}$$

$$\text{max\_parallelism} = \max_l |\text{Level}(l)|$$

---

## 5. Функции качества

### 5.1 Полнота (Completeness)

$$\text{Completeness}(\mathcal{S}) = \frac{|\text{CoveredAspects}(T, \mathcal{S})|}{|\text{AllAspects}(T)|}$$

где аспекты включают:
- Функциональные требования
- Edge cases
- Performance requirements
- Security requirements
- Совместимость

### 5.2 Независимость (Independence)

$$\text{Independence}(\mathcal{S}, \mathcal{G}) = 1 - \frac{2 \cdot |\mathcal{E}|}{|\mathcal{S}| \cdot (|\mathcal{S}| - 1)}$$

**Интерпретация:**
- $= 1$: все подзадачи независимы
- $= 0$: полная связанность

### 5.3 Гранулярность (Granularity)

$$\text{Granularity}(\mathcal{S}) = \text{Sigmoid}\left(-\frac{(|\mathcal{S}| - N^*)^2}{2\sigma^2}\right)$$

где $N^*$ — оптимальное число подзадач, зависящее от размера оригинальной задачи.

**Штрафы:**
- Слишком крупно ($|\mathcal{S}| \ll N^*$): подзадачи сложные
- Слишком мелко ($|\mathcal{S}| \gg N^*$): overhead на управление

### 5.4 Выполнимость (Feasibility)

$$\text{Feasibility}(s) = \prod_{c \in \text{constraints}(s)} \mathbb{I}(c \text{ satisfied})$$

или вероятностно:

$$P(\text{feasible}(s)) = \sigma(\mathbf{w}_{feas}^T \cdot \mathbf{e}(s) + b_{feas})$$

---

## 6. Итеративная декомпозиция

### 6.1 REACTREE-style планирование

```
Initialize: queue = [T]
while queue not empty and depth < D_max:
    task = queue.pop()
    if need_decompose(task):
        subtasks = generate(task)
        for s in subtasks:
            queue.push(s)
            record_dependency(s, parent=task)
    else:
        register_final(task)
```

### 6.2 Математическая формализация

$$D^*(T) = \text{Plan-Then-Execute}(T, \theta)$$

**Plan Phase:**
$$\mathcal{S}^{(0)} = \{T\}, \quad \mathcal{G}^{(0)} = \emptyset$$

**Iterate for }k = 1, 2, \ldots, K}:**

$$\mathcal{S}^{(k)} = \mathcal{S}^{(k-1)} \setminus \{s \in \mathcal{S}^{(k-1)} : \text{decompose}(s)\} \cup \text{GenerateSubtasks}(s)$$

$$\mathcal{E}^{(k)} = \mathcal{E}^{(k-1)} \cup \text{InferDependencies}(\mathcal{S}^{(k)})$$

**Execute Phase:**
$$\text{ExecuteOrder} = \text{TopologicalSort}(\mathcal{S}^{(K)}, \mathcal{E}^{(K)})$$

### 6.3 Select-Then-Decompose стратегия

$$s^* = \underset{s \in \mathcal{S}}{\arg\max} \; \text{SelectScore}(s)$$

$$\text{SelectScore}(s) = \alpha \cdot \text{Impact}(s) + \beta \cdot \text{Feasibility}(s)^{-1}$$

**Decompose если:**
$$\text{SelectScore}(s^*) > \tau_{select}$$

---

## 7. Оценка усилий (Effort Estimation)

### 7.1 Модель оценки

$$\widehat{\text{effort}}(s) = \mathbf{w}_{eff}^T \cdot \mathbf{f}(s) + b_{eff}$$

где $\mathbf{f}(s)$ — вектор признаков подзадачи:

| Признак | Описание |
|---------|----------|
| $\|s\|$ | Размер описания |
| $\|d(s)\|$ | Diff size |
| $n_{files}$ | Число файлов |
| $n_{tests}$ | Требуемых тестов |
| $\text{type}(s)$ | Тип задачи |
| $\text{context\_sim}$ | Сходство с историческими |

### 7.2 Агрегация для родительской задачи

$$\text{Effort}(T) = \sum_{s \in \mathcal{S}} \widehat{\text{effort}}(s) + \alpha \cdot \text{Overhead}(|\mathcal{S}|)$$

где $\text{Overhead}(n) = \gamma \cdot n$ — overhead на управление подзадачами.

---

## 8. Верификация и валидация

### 8.1 Контрольные точки (Checkpoints)

$$\text{Checkpoint}(k) = \{\text{Completeness} > \tau_{comp}, \text{Feasibility}(s) > \tau_{feas} \;\forall s\}$$

### 8.2 Conflict Detection

$$\text{Conflict}(s_i, s_j) = \mathbb{I}(\text{ModifiesOverlap}(s_i, s_j) \land \neg \text{Ordered}(s_i, s_j))$$

### 8.3 Human-in-the-loop

$$P(\text{approve}|D) = \sigma(\mathbf{w}_{approval}^T \cdot [\mathcal{Q}(D); \text{confidence}(D)] + b_{approval})$$

---

## 9. Итоговая архитектура

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│                         INPUT: Complex Task T                        │
│                                                                     │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  1. DECOMPOSITION DECIDER                           │
│      φ = σ(w · [e_text; e_ctx]) > τ_decomp?                        │
│      depth* = log₂(|files| · complexity / τ_task)                   │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
              ▼                               ▼
    ┌─────────────────┐              ┌─────────────────┐
    │    NO DECOMP    │              │    DECOMPOSE    │
    │   Return [T]    │              │                 │
    └─────────────────┘              └────────┬────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  2. SUBTASK GENERATOR                               │
│      s_i = G_θ(T, S_{<i})  for i = 1, ..., n                      │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  3. DEPENDENCY ANALYZER                             │
│      dep(s_i, s_j) = σ(w · [e(s_i); e(s_j)])                      │
│      G = TopoSort(S, E)                                             │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  4. QUALITY SCORER                                  │
│      Q = α·Completeness + β·Independence +                          │
│          γ·Granularity + δ·Feasibility                             │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  5. VERIFICATION LOOP                               │
│      if Q < τ_quality or conflicts exist:                          │
│          Refine(S, feedback)                                        │
│      if human_approval_needed:                                      │
│          Present to human                                           │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│                    OUTPUT: D* = (S, G)                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 10. Формулы в компактной записи

### Основная функция декомпозиции:

$$\boxed{D^*(T) = \underset{D}{\arg\max} \; \mathcal{Q}(D) \quad \text{s.t.} \quad |\mathcal{S}| \leq S_{max}, \; \text{depth}(\mathcal{G}) \leq D_{max}}$$

### Функция качества:

$$\boxed{\mathcal{Q}(\mathcal{S}, \mathcal{G}) = \alpha \cdot \frac{|C_{cov}|}{|C|} + \beta \cdot \left(1 - \frac{2|E|}{|S|(|S|-1)}\right) + \gamma \cdot \sigma\left(-\frac{(|S|-N^*)^2}{2\sigma^2}\right) + \delta \cdot \frac{1}{|S|}\sum_{s \in \mathcal{S}} P_{feas}(s)}$$

### Решение о декомпозиции:

$$\boxed{\text{Decompose}(s) \iff \sigma(\mathbf{w}_\phi^T \mathbf{e}(s) + b_\phi) > \tau_{decomp} \land \text{size}(s) > \tau_{size}}$$

### Условие зависимости:

$$\boxed{e_{ij} \in \mathcal{E} \iff \sigma(\mathbf{w}_{dep}^T[\mathbf{e}(s_i); \mathbf{e}(s_j)] - b_{dep}) > \tau_{dep}}$$

---

## 11. Практические применения

| Сценарий | Применение модели |
|----------|-------------------|
| GitHub Issue → Subtasks | Автоматическая разбивка issue на feature/bugfix/refactor/test |
| Sprint Planning | Оценка времени через декомпозицию |
| Code Review | Разбивка большого PR на модули |
| Bug Fix | Декомпозиция на diagnosis → fix → test |
| Feature Development | Epic → Stories → Tasks |

---

## 12. Инструменты и библиотеки

| Инструмент | Назначение |
|------------|------------|
| **Tree-Planner** | Иерархическое планирование |
| **LangChain Agents** | Loop engineering |
| **GitHub Toolkit** | Интеграция с issues/PRs |
| **SWE-bench** | Бенчмарк для SWE задач |

---

## Источники

- REACTREE: Hierarchical Task Planning with Dynamic Tree Expansion
- Select-Then-Decompose: Adaptive Task Decomposition Strategy
- Decompose, Plan in Parallel, and Merge (DPPM)
- Tree-Planner: Efficient Close-loop Task Planning with LLMs
