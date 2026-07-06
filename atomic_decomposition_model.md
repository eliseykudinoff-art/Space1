# Математическая модель декомпозиции задач на атомарные API-действия

## Часть 1: Формальная постановка задачи

---

## 1.1 Введение и мотивация

Современные AI-агенты работают через API-вызовы к LLM. Задача состоит в том, чтобы:

1. **Разбить сложную задачу** на атомарные действия
2. **Автоматически определить** оптимальные параметры для каждого API-вызова:
   - Промт (инструкции)
   - Формат вывода (JSON, текст, код, и т.д.)
   - Размер контекста (от 0 до полного контекстного окна)
   - Модель (размер, стоимость)
3. **Минимизировать стоимость и latency** при заданном качестве
4. **Автоматически принимать решения** о необходимости декомпозиции

---

## 1.2 Формальная нотация

### Множества

| Множество | Обозначение | Описание |
|-----------|-----------|---------|
| Задачи | $\mathcal{T}$ | Входные задачи |
| Атомарные действия | $\mathcal{A}$ | Неделимые API-вызовы |
| Промты | $\mathcal{P}$ | Шаблоны промтов |
| Форматы | $\mathcal{F}$ | Типы вывода (JSON, text, code, ...) |
| Модели | $\mathcal{M}$ | LLM модели |
| Контексты | $\mathcal{C}$ | Векторы контекста |

### Переменные

| Переменная | Тип | Описание |
|-----------|-----|---------|
| $T$ | $\mathcal{T}$ | Исходная задача |
| $A_i$ | $\mathcal{A}$ | $i$-е атомарное действие |
| $p_i$ | $\mathcal{P}$ | Промт для $A_i$ |
| $f_i$ | $\mathcal{F}$ | Формат вывода для $A_i$ |
| $c_i$ | $\mathbb{R}^d$ | Вектор контекста для $A_i$ |
| $m_i$ | $\mathcal{M}$ | Модель для $A_i$ |
| $\phi_i$ | $\mathbb{R}$ | Confidence-score для $A_i$ |

---

## 1.3 Структура атомарного действия

Каждое атомарное действие $a \in \mathcal{A}$ определяется кортежем:

$$\boxed{a = (p, f, c, m, o, \phi, r)}$$

где:

| Компонент | Тип | Описание |
|-----------|-----|---------|
| $p$ | $\mathcal{P}$ | Промт (инструкции для LLM) |
| $f$ | $\mathcal{F}$ | Требуемый формат вывода |
| $c$ | $\mathcal{C}$ | Контекст (код, документация, история) |
| $m$ | $\mathcal{M}$ | Целевая модель |
| $o$ | $O$ | Выход (результат API-вызова) |
| $\phi$ | $[0,1]$ | Confidence score |
| $r$ | $\mathbb{R}^+$ | Ресурсы (стоимость, latency) |

### Подробности компонентов

**Промт $p$:**

$$p = (r_p, i_p, c_p, e_p)$$

| Компонент | Описание |
|-----------|---------|
| $r_p$ | Роль (system, user, assistant) |
| $i_p$ | Инструкции (что делать) |
| $c_p$ | Контекст (входные данные) |
| $e_p$ | Примеры (few-shot examples) |

**Формат $f$:**

$$f \in \{\text{json}, \text{text}, \text{markdown}, \text{code}, \text{binary}, \text{uri}\}$$

**Контекст $c$:**

$$c = (c_{code}, c_{docs}, c_{history}, c_{memory})$$

| Компонент | Описание |
|-----------|---------|
| $c_{code}$ | Релевантный код |
| $c_{docs}$ | Документация |
| $c_{history}$ | История диалога |
| $c_{memory}$ | Долгосрочная память |

---

## 1.4 Целевая функция

### Основная задача оптимизации

$$\boxed{D^*(T) = \underset{(A, \theta)}{\arg\max} \; \mathcal{U}(A, \theta) - \lambda \cdot \mathcal{C}(A, \theta)}$$

где:

| Функция | Описание |
|---------|---------|
| $\mathcal{U}(A, \theta)$ | Утилита (качество результата) |
| $\mathcal{C}(A, \theta)$ | Стоимость (финансовая + временная) |
| $\lambda$ | Коэффициент trade-off |
| $\theta$ | Параметры декомпозиции |

### Функция утилиты

$$\mathcal{U}(A, \theta) = \prod_{i=1}^{n} u(a_i) \cdot \prod_{(i,j) \in E} \rho(a_i, a_j)$$

где:
- $u(a_i)$ — утилита $i$-го действия
- $\rho(a_i, a_j)$ — корреляция результатов (учёт зависимостей)

### Функция стоимости

$$\mathcal{C}(A, \theta) = \sum_{i=1}^{n} \left[\alpha \cdot \text{cost}(m_i) + \beta \cdot \text{latency}(m_i) + \gamma \cdot |c_i|\right]$$

где:
- $\alpha$ — вес финансовой стоимости
- $\beta$ — вес latency
- $\gamma$ — вес размера контекста

---

## 1.5 Ограничения

$$D^*(T) = \underset{D}{\arg\max} \; \mathcal{U}(D) - \lambda \mathcal{C}(D)$$

при ограничениях:

$$\begin{aligned}
\text{s.t.} \quad & |A| \leq A_{max} && \text{(максимум действий)} \\
& \forall i: |c_i| \leq C_{max} && \text{(лимит контекста)} \\
& \forall i: \phi_i \geq \phi_{min} && \text{(минимальный confidence)} \\
& \forall i: \text{latency}(m_i) \leq L_{max} && \text{(лимит latency)} \\
& G = (A, E) \text{ is acyclic} && \text{(DAG зависимостей)}
\end{aligned}$$

---

## Часть 2: Модели принятия решений

---

## 2.1 Функция решения о декомпозиции

**Нужно ли декомпозировать задачу?**

$$\delta(T) = \sigma(\mathbf{w}_\delta^T \cdot \mathbf{f}(T) + b_\delta)$$

где $\mathbf{f}(T)$ — вектор признаков задачи.

**Вектор признаков:**

$$\mathbf{f}(T) = [\underbrace{|T|_{words}}_{\text{размер}}, \underbrace{\text{complexity}(T)}_{\text{сложность}}, \underbrace{\text{uncertainty}(T)}_{\text{неопределённость}}, \underbrace{\text{depth}(T)}_{\text{глубина}}, \ldots]$$

**Решение:**

$$\text{Decompose?} = \begin{cases} \text{Yes} & \delta(T) > \tau_\delta \\ \text{No} & \delta(T) \leq \tau_\delta \end{cases}$$

---

## 2.2 Функция выбора формата вывода

**Для каждого действия определить оптимальный формат:**

$$f^*(a) = \underset{f \in \mathcal{F}}{\arg\max} \; P(f | a, \theta_f)$$

**Модель выбора формата:**

$$P(f | a) = \text{Softmax}(\mathbf{w}_f^T \cdot \mathbf{g}(a))$$

**Признаки для выбора формата:**

$$\mathbf{g}(a) = [\underbrace{\text{type}(a)}_{\text{тип задачи}}, \underbrace{\text{consumer}(a)}_{\text{потребитель}}, \underbrace{\text{prev\_format}}_{\text{пред. формат}}, \ldots]$$

**Эвристика выбора:**

| Тип задачи | Рекомендуемый формат |
|-----------|---------------------|
| Генерация кода | `code`, `json` |
| Анализ текста | `text`, `markdown` |
| Структурированные данные | `json` |
| Файловые операции | `uri`, `binary` |
| Вычисления | `json`, `text` |

---

## 2.3 Функция выбора контекста

**Определение оптимального размера контекста:**

$$c^*(a) = \underset{c \subseteq \mathcal{R}}{\arg\max} \; \text{Score}(a, c)$$

$$\text{Score}(a, c) = \underbrace{\text{Relevance}(a, c)}_{\text{релевантность}} - \lambda_c \cdot \underbrace{\text{Cost}(c)}_{\text{стоимость}}$$

### Relevance Score

$$\text{Relevance}(a, c) = \frac{1}{|\mathcal{K}|} \sum_{k \in \mathcal{K}} \text{BM25}(a, c_k) \cdot \text{RRF}(k)$$

где $\mathcal{K}$ — типы контекста (code, docs, history).

### Cost функции

$$\text{Cost}(c) = \alpha_t \cdot \text{tokens}(c) + \alpha_l \cdot \text{latency}(c) + \alpha_m \cdot \text{memory}(c)$$

### Стратегии выбора контекста

| Стратегия | Формула | Применение |
|-----------|---------|-----------|
| **No context** | $c = \emptyset$ | Тривиальные задачи |
| **Selective** | $c = \text{TopK}(\text{relevant}, k)$ | Большинство задач |
| **Full** | $c = \text{All}($до лимита$\left.\right)$ | Сложные задачи |
| **Hierarchical** | $c = \text{Summarize}(c_{full})$ | Ограниченный контекст |

---

## 2.4 Функция выбора модели

**Выбор оптимальной модели для действия:**

$$m^*(a) = \underset{m \in \mathcal{M}}{\arg\max} \; \mathbb{E}[u(a, m)] - \lambda_m \cdot \text{cost}(m)$$

**Математическая формализация:**

$$m^*(a) = \underset{m}{\arg\max} \; \left[ \underbrace{P(\text{success} | a, m)}_{\text{вероятность успеха}} \cdot \underbrace{\text{quality}(m)}_{\text{качество}} \right] - \lambda \cdot \underbrace{\text{API\_cost}(m)}_{\text{стоимость}}$$

**Факторы выбора модели:**

| Фактор | Влияние |
|--------|--------|
| Размер задачи | Большие задачи → мощные модели |
| Confidence threshold | Низкий threshold → дешёвые модели |
| Тип задачи | Код → специализированные модели |
| Наличие примеров | Few-shot → меньшие модели |

**Heuristic:**

```
if confidence_threshold > 0.9:
    model = GPT-4 / Claude-3-Opus
elif confidence_threshold > 0.7:
    model = GPT-3.5-Turbo / Claude-3-Haiku
elif |a| < 100 tokens and has_examples:
    model = Smaller fine-tuned model
else:
    model = Medium model with reasoning
```

---

## 2.5 Функция генерации промта

**Для каждого действия сгенерировать оптимальный промт:**

$$p^*(a) = G_\theta(a, c, f)$$

где $G_\theta$ — генеративная модель.

**Структура промта:**

$$p = \underbrace{[S]}_{\text{system}} + \underbrace{[I(a)]}_{\text{instructions}} + \underbrace{[C(c)]}_{\text{context}} + \underbrace{[E]}_{\text{examples}} + \underbrace{[O(f)]}_{\text{output format}}$$

**Компоненты:**

| Компонент | Формула | Описание |
|-----------|---------|---------|
| System role | $[S] = \text{Template}(role, \text{behavior})$ | Роль агента |
| Instructions | $[I] = \text{Template}(task, \text{constraints})$ | Что делать |
| Context | $[C] = \text{Inject}(c)$ | Контекстные данные |
| Examples | $[E] = \text{SelectFewShot}(a)$ | Примеры (если нужно) |
| Output | $[O] = \text{Template}(f)$ | Формат вывода |

---

## Часть 3: Модель качества и метрики

---

## 3.1 Confidence Score

**Оценка уверенности в результате:**

$$\phi(a) = P(\text{success} | a, \theta) = \sigma(\mathbf{w}_\phi^T \cdot \mathbf{h}(a) + b_\phi)$$

**Признаки для confidence:**

$$\mathbf{h}(a) = [\text{complexity}, \text{context\_coverage}, \text{model\_capability}, \text{format\_fit}, \ldots]$$

### Калибровка confidence

$$\hat{P}(\text{success}) = \alpha \cdot \phi(a) + (1-\alpha) \cdot \text{hist\_accuracy}(a\_type)$$

---

## 3.2 Функции качества

### Полнота (Coverage)

$$\text{Coverage}(D) = \frac{|\{r \in \text{requirements}(T) : \exists a \in A : \text{satisfies}(a, r)\}|}{|\text{requirements}(T)|}$$

### Корректность (Correctness)

$$\text{Correctness}(a) = \mathbb{I}(\text{output}(a) \models \text{spec}(a))$$

### Атомарность (Atomicity)

$$\text{Atomicity}(a) = \begin{cases} 1 & \text{если } a \text{ неделим} \\ 0.5 & \text{если можно разделить} \\ 0 & \text{если содержит подзадачи} \end{cases}$$

---

## 3.3 Метрики стоимости

### Token Cost

$$\text{Cost}_{tokens}(A) = \sum_{i} [\underbrace{|p_i| + |c_i|}_{\text{input}} + \underbrace{|o_i|}_{\text{output}}] \cdot \text{price}(m_i)$$

### Latency Cost

$$\text{Cost}_{latency}(A) = \sum_i \text{latency}(m_i) + \sum_{(i,j) \in E} \text{wait}(a_i, a_j)$$

### Total Cost

$$\text{Cost}_{total}(A) = \alpha \cdot \text{Cost}_{tokens} + \beta \cdot \text{Cost}_{latency}$$

---

## 3.4 Trade-off Optimization

**Pareto-optimal решение:**

$$A^* \in \text{ParetoFront} \iff \not\exists A' : \mathcal{U}(A') \geq \mathcal{U}(A^*) \land \text{Cost}(A') < \text{Cost}(A^*)$$

**Scalarization (weighted sum):**

$$\mathcal{L}(A) = \omega_u \cdot \frac{\mathcal{U}(A)}{\mathcal{U}_{max}} - \omega_c \cdot \frac{\text{Cost}(A)}{\text{Cost}_{max}}$$

---

## Часть 4: Алгоритмы декомпозиции

---

## 4.1 REACTREE-style Decomposition

```
Алгоритм: REACTREE- Decompose(T, depth=0, max_depth)

Вход: Задача T
Выход: DAG подзадач

1. IF need_decompose(T) == False:
      RETURN Leaf(T)

2. IF depth >= max_depth:
      RETURN Leaf(T)  // Принудительный останов

3. candidates = generate_subtasks(T)
4. FOR EACH candidate IN candidates:
      IF is_atomic(candidate):
          subtasks += [candidate]
      ELSE:
          subtasks += REACTREE-Decompose(candidate, depth+1, max_depth)

5. dependencies = infer_dependencies(subtasks)
6. RETURN Node(T, subtasks, dependencies)
```

### Математика REACTREE

$$P(\text{decompose} | T) = \sigma(\mathbf{w}_d^T \cdot [\mathbf{e}(T); \text{depth}])$$

$$P(\text{atomic} | a) = \sigma(\mathbf{w}_a^T \cdot \mathbf{e}(a) - b_a)$$

---

## 4.2 Select-Then-Decompose

```
Алгоритм: Select-Then-Decompose(T, K)

1. Вычислить score для каждого кандидата
   score(a) = α·Impact(a) + β·(1/Feasibility(a))

2. Выбрать Top-K кандидатов для декомпозиции
   SELECT = TopK(candidates, K, score)

3. Декомпозировать выбранные
   FOR a IN SELECT:
       subtasks = decompose(a)
       merge(subtasks)

4. RETURN всех кандидатов
```

### Формула выбора

$$a^* = \underset{a \in \mathcal{C}}{\arg\max} \; \underbrace{\text{Impact}(a)}_{\text{влияние}} \cdot \underbrace{\text{Feasibility}(a)^{-1}}_{\text{сложность}}$$

---

## 4.3 Budget-Constrained Decomposition

**Оптимизация с учётом бюджета:**

$$\max_A \mathcal{U}(A) \quad \text{s.t.} \quad \text{Cost}(A) \leq B$$

**Решение через dynamic programming:**

```
For each possible cost level b ∈ [0, B]:
    For each action a:
        DP[b] = max(DP[b], U(a) + DP[b - Cost(a)])
```

---

## Часть 5: Интеграция — Полная архитектура

---

## 5.1 End-to-End Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                         INPUT: Complex Task T                               │
│                                                                             │
└─────────────────────────────┬───────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    STAGE 1: TASK ANALYSIS                                   │
│                                                                             │
│   f(T)      = [size, complexity, uncertainty, type, domain]                 │
│   δ(T)      = σ(w_δ · f(T))  →  Need Decompose?                            │
│   depth*(T) = log₂(|requirements| · complexity)                             │
│                                                                             │
└─────────────────────────────┬───────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
              ▼                               ▼
    ┌─────────────────┐            ┌─────────────────┐
    │   IS ATOMIC      │            │   DECOMPOSE     │
    │   Return [T]     │            │                 │
    └─────────────────┘            └────────┬────────┘
                                             │
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    STAGE 2: ACTION PLANNING                                 │
│                                                                             │
│   FOR EACH subtask s:                                                       │
│     ┌─────────────────────────────────────────────────────────────────┐     │
│     │  FORMAT:     f*(s)  = argmax P(f|s)                              │     │
│     │  CONTEXT:    c*(s)  = argmax [Relevance - λ·Cost]               │     │
│     │  MODEL:      m*(s)  = argmax [P(success|m)·Quality - λ·Cost]    │     │
│     │  PROMPT:     p*(s)  = G_θ(s, c*(s), f*(s))                      │     │
│     │  CONFIDENCE: φ(s)    = σ(w_φ · h(s))                             │     │
│     └─────────────────────────────────────────────────────────────────┘     │
│                                                                             │
└─────────────────────────────┬───────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    STAGE 3: DEPENDENCY ANALYSIS                              │
│                                                                             │
│   E = {(a_i, a_j) : σ(w_e · [e(a_i); e(a_j)]) > τ_e}                      │
│   G = (A, E)  →  Topological Sort                                          │
│   Levels = compute_parallel_levels(G)                                        │
│                                                                             │
└─────────────────────────────┬───────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    STAGE 4: QUALITY & COST VALIDATION                        │
│                                                                             │
│   Q(D) = α·Coverage + β·Correctness + γ·Atomicity                           │
│   C(D) = Σ [α·Tokens·Price + β·Latency]                                     │
│                                                                             │
│   IF Q < τ_quality OR C > C_max:                                            │
│       REFINE(D)                                                             │
│                                                                             │
└─────────────────────────────┬───────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                    OUTPUT: Execution Plan D*                                  │
│                                                                             │
│   D* = {                                                                      │
│       actions: A = [a_1, a_2, ..., a_n],                                     │
│       dependencies: E,                                                       │
│       execution_order: Levels,                                               │
│       total_cost: C(D*),                                                     │
│       expected_quality: Q(D*)                                               │
│   }                                                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5.2 Компактная форма всех формул

### Основные уравнения

$$\boxed{1. \quad \delta(T) = \sigma(\mathbf{w}_\delta^T \mathbf{f}(T) + b_\delta) \quad \text{: нужно ли декомпозировать?}}$$

$$\boxed{2. \quad f^*(a) = \underset{f}{\arg\max} \; \text{Softmax}(\mathbf{w}_f^T \mathbf{g}(a))_f \quad \text{: оптимальный формат}}$$

$$\boxed{3. \quad c^*(a) = \underset{c \subseteq \mathcal{R}}{\arg\max} \; \underbrace{\frac{1}{|\mathcal{K}|}\sum \text{BM25}(a, c_k) \cdot \text{RRF}(k)}_{\text{Relevance}} - \lambda_c \cdot \underbrace{(\alpha_t \cdot |c|)}_{\text{Cost}}}$$

$$\boxed{4. \quad m^*(a) = \underset{m}{\arg\max} \; P(\text{success}|a,m) \cdot \text{quality}(m) - \lambda_m \cdot \text{cost}(m)}$$

$$\boxed{5. \quad p^*(a) = [S] + [I(a)] + [C(c^*(a))] + [E] + [O(f^*(a))] \quad \text{: генерация промта}}$$

$$\boxed{6. \quad \phi(a) = \sigma(\mathbf{w}_\phi^T \mathbf{h}(a) + b_\phi) \quad \text{: confidence score}}$$

### Целевая функция

$$\boxed{D^*(T) = \underset{D}{\arg\max} \; \underbrace{\mathcal{U}(D)}_{\text{утилита}} - \lambda \cdot \underbrace{\mathcal{C}(D)}_{\text{стоимость}}}$$

где:

$$\mathcal{U}(D) = \prod_i u(a_i) \cdot \prod_{(i,j) \in E} \rho(a_i, a_j)$$

$$\mathcal{C}(D) = \sum_i [\alpha \cdot \text{price}(m_i) + \beta \cdot \text{latency}(m_i) + \gamma \cdot |c_i|]$$

---

## 5.3 Пример работы

**Задача:** "Implement a REST API for user authentication with JWT tokens"

### Stage 1: Анализ

```
δ(T) = σ(w · [size=20, complexity=0.7, uncertainty=0.4]) = 0.85 > 0.5
→ DECOMPOSE NEEDED
depth* = log₂(5 · 0.7) = 2
```

### Stage 2: Генерация действий

| Действие | Формат | Контекст | Модель | Confidence |
|---------|--------|----------|--------|------------|
| Design API schema | `json` | API docs | GPT-4 | 0.95 |
| Create User model | `code` | DB schema | GPT-4 | 0.90 |
| Implement auth logic | `code` | JWT docs | GPT-4 | 0.88 |
| Write unit tests | `code` | API spec | GPT-3.5 | 0.85 |
| Generate OpenAPI docs | `yaml` | Routes | GPT-3.5 | 0.92 |

### Stage 3: Dependencies

```
Design API schema → Create User model → Implement auth logic
                                    ↘
                                      Write unit tests
Design API schema → Generate OpenAPI docs
```

### Stage 4: Validation

```
Q(D*) = 0.95 · Coverage + 0.90 · Correctness + 0.85 · Atomicity = 0.90
C(D*) = $0.15 (API design) + $0.20 (model) + $0.18 (auth) + $0.05 (tests) = $0.58
→ ACCEPTABLE
```

---

## Часть 6: Практические аспекты

---

## 6.1 Каталог инструментов

Каждое атомарное действие маппится на инструмент:

```yaml
Tool Catalog:
  create_file:
    input_schema: {path: str, content: str}
    output_schema: {success: bool, file_id: str}
    allowed_formats: [text, code, binary]
    max_latency_ms: 5000
    cost_hint: low
    
  run_command:
    input_schema: {command: str, cwd: str, timeout: int}
    output_schema: {stdout: str, stderr: str, exit_code: int}
    allowed_formats: [json, text]
    max_latency_ms: 300000
    cost_hint: medium
    
  read_file:
    input_schema: {path: str, start_line: int, end_line: int}
    output_schema: {content: str, lines: int}
    allowed_formats: [text, code]
    max_latency_ms: 1000
    cost_hint: low
```

---

## 6.2 Правила принятия решений

| Условие | Действие | Параметры |
|---------|---------|-----------|
| $\delta(T) < 0.3$ | Return as-is | $f$ = auto-detect |
| $0.3 \leq \delta(T) < 0.7$ | Shallow decompose | depth = 2 |
| $\delta(T) \geq 0.7$ | Deep decompose | depth = 5 |
| Context relevance < 0.5 | No context | $c = \emptyset$ |
| $\phi(a) < 0.5$ | Use strong model | $m$ = GPT-4 |
| Cost > Budget | Reduce depth | Prune lowest-impact |

---

## 6.3 Формулы для квантизации

**Квантизация контекста:**

$$c_{quantized} = \text{Truncate}(c, \text{Round}(\text{TargetTokens} / \text{ChunkSize}) \times \text{ChunkSize})$$

**Квантизация модели:**

$$m_{quantized} = \begin{cases} \text{GPT-4} & \text{if } \phi < 0.3 \\ \text{GPT-3.5} & \text{if } 0.3 \leq \phi < 0.7 \\ \text{Fast-model} & \text{if } \phi \geq 0.7 \end{cases}$$

---

## 6.4 Мониторинг и адаптация

**Обновление весов на основе обратной связи:**

$$\mathbf{w} \leftarrow \mathbf{w} - \eta \cdot \nabla_\mathbf{w} \mathcal{L}(\text{feedback})$$

где $\mathcal{L}$ — функция потерь на основе результатов.

**Адаптивные пороги:**

$$\tau_\delta \leftarrow \tau_\delta + \alpha \cdot (\text{accuracy}_{recent} - \text{target\_accuracy})$$

---

## Заключение

### Ключевые математические формулы

| Компонент | Формула | Назначение |
|-----------|---------|-----------|
| Декомпозиция | $\delta(T) = \sigma(\mathbf{w}_\delta^T \mathbf{f}(T))$ | Решение о декомпозиции |
| Формат | $f^* = \arg\max \text{Softmax}(\mathbf{w}_f \mathbf{g}(a))$ | Выбор формата |
| Контекст | $c^* = \arg\max [\text{Relevance} - \lambda \cdot \text{Cost}]$ | Выбор контекста |
| Модель | $m^* = \arg\max [P(\text{success}) \cdot \text{Quality} - \lambda \cdot \text{Cost}]$ | Выбор модели |
| Промт | $p^* = [S] + [I] + [C(c^*)] + [E] + [O(f^*)]$ | Генерация промта |
| Confidence | $\phi = \sigma(\mathbf{w}_\phi^T \mathbf{h}(a))$ | Оценка уверенности |
| Цель | $D^* = \arg\max [\mathcal{U}(D) - \lambda \cdot \mathcal{C}(D)]$ | Оптимизация |

### Преимущества модели

✅ **Автоматическое принятие решений** — все параметры определяются автоматически  
✅ **Оптимизация стоимости** — баланс качества и ресурсов  
✅ **Гибкость** — адаптация к разным задачам  
✅ **Интерпретируемость** — все решения объяснимы  
✅ **Обучаемость** — веса обновляются на основе feedback
