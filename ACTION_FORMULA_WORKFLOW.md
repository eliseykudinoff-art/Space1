# ACTION → FORMULA: Полный маппинг для кодинга

## Документ для имплементации

> **Цель:** Каждая формула → конкретное действие → код
> **Принцип:** Максимальная детализация, без обобщений
> **Аудитория:** Разработчик (ты)

---

## СТРУКТУРА ДОКУМЕНТА

```
ФОРМУЛА
  └─ Код формулы (LaTeX)
  └─ Входные переменные (что нужно измерить/вычислить)
  └─ Выход (что получаем)
  └─ ДЕЙСТВИЕ: Что делаем с этим выходом
  └─ ПРАВИЛО: if/else логика принятия решения
  └─ ПСЕВДОКОД: Как это закодить
```

---

# ЧАСТЬ 1: БАЗОВЫЕ АКСИОМЫ (входные данные для всех расчётов)

---

## A1: Φ = (R - C) / T — Базовая прибыль

### Формула
$$\Phi = \frac{R - C}{T}$$

### Входы
```
R = P × S × Q              (Revenue = цена × успех × пропускная способность)
C = C₀ + C_ops + C_risk    (Cost = базовый + операционный + рисковый)
T = T₀ × ∏f_i              (Time = базовое × модификаторы)
```

### Выход
```
Φ = float  ($/час) — почасовая прибыль агента
```

### ДЕЙСТВИЕ: Оценить profitability задачи/агента

### ПРАВИЛО
```
if Φ > 0:
    → Задача генерирует прибыль
elif Φ < 0:
    → Задача убыточна, требует переоценки
else:
    → Break-even, решения нет
```

### ПСЕВДОКОД
```python
def compute_profit(task: Task, agent: AgentState) -> float:
    # R = Price × Success × Throughput
    R = task.price * compute_success_rate(task, agent) * compute_throughput(agent)
    
    # C = Base + Ops + Risk
    C = BASE_COST + compute_ops_cost(task) + compute_risk_cost(task, agent)
    
    # T = Base × Modifiers
    T = BASE_TIME * compute_time_modifiers(task, agent)
    
    return (R - C) / T
```

---

## A2: R = P × S × Q — Revenue

### Формула
$$R = P \cdot S \cdot Q$$

### Входы
```
P = task.price           ($/задача)
S = success_rate        [0, 1]
Q = throughput          (задач/час)
```

### Выход
```
R = float ($) — ожидаемый доход
```

### ДЕЙСТВИЕ: Рассчитать ожидаемый доход от задачи

### ПРАВИЛО
```
R_threshold = agent.monthly_expenses × target_margin

if R > R_threshold:
    → Задача интересна для рассмотрения
```

---

## A3: C = C₀ + C_ops + C_risk — Cost

### Формула
$$C = C_0 + C_{ops} + C_{risk}$$

### Входы
```
C₀ = BASE_COST = 0.0     (базовые затраты)
C_ops = API_cost + tool_cost + context_cost
C_risk = P_fail × (C_direct + C_reputation)
```

### Выход
```
C = float ($) — полная стоимость задачи
```

### ДЕЙСТВИЕ: Рассчитать стоимость выполнения

### ПРАВИЛО
```
C_max = task.price × 0.8    # Максимум 80% от цены

if C > C_max:
    → Задача невыгодна, отклонить
```

---

## A4: T = T₀ × ∏f_i — Time modifier

### Формула
$$T = T_0 \cdot \prod_i f_i$$

### Входы
```
T₀ = BASE_TIME = 1.0          (час/задача)
f_i ∈ {f_Q, f_T} по x₁-x₁₇    (модификаторы от факторов)
```

### Выход
```
T = float (час) — ожидаемое время выполнения
```

### ДЕЙСТВИЕ: Оценить время выполнения задачи

### ПРАВИЛО
```
T_deadline = task.deadline - current_time

if T > T_deadline:
    → Задача не укладывается в deadline
```

---

## A5-A7: Bound checks

### Формулы
```
S ∈ [0, 1]
Q > 0
C ≥ 0
```

### ДЕЙСТВИЕ: Валидация корректности расчётов

### ПСЕВДОКОД
```python
def validate_state(S: float, Q: float, C: float) -> bool:
    assert 0 <= S <= 1, f"Success rate out of bounds: {S}"
    assert Q > 0, f"Throughput must be positive: {Q}"
    assert C >= 0, f"Cost cannot be negative: {C}"
    return True
```

---

# ЧАСТЬ 2: УПРАВЛЯЮЩИЕ ФУНКЦИИ

---

## Φ(x) = (P × S(x) × Q(x) - C(x)) / T(x) — Profit с факторами

### Формула
$$\Phi(\mathbf{x}) = \frac{P \cdot S(\mathbf{x}) \cdot Q(\mathbf{x}) - C(\mathbf{x})}{T(\mathbf{x})}}$$

где $\mathbf{x} = (x_1, x_2, \ldots, x_{17})$

### Входы
```
S(x) = S₀ + Σβᵢxᵢ + Σγᵢⱼxᵢxⱼ         (Success Rate с факторами)
Q(x) = Q₀ × ∏f_Q,i(xᵢ)                  (Throughput с факторами)
C(x) = C₀ + ΣΔCᵢ(xᵢ)                   (Cost с факторами)
T(x) = T₀ × ∏f_T,i(xᵢ)                  (Time с факторами)
```

### Выход
```
Φ = float ($/час) — прибыль с учётом всех 17 факторов
```

### ДЕЙСТВИЕ: Финальная оценка прибыльности с учётом capability агента

### ПРАВИЛО
```
Φ > 0        → task is profitable
Φ = 0        → break-even
Φ < 0        → task is loss-making
Φ > Φ_avg    → task is above average profitability
```

### ПСЕВДОКОД
```python
def compute_capability_adjusted_profit(
    task: Task, 
    agent: AgentState,
    factors: List[float]  # x₁...x₁₇
) -> float:
    S = compute_S_with_factors(factors)
    Q = compute_Q_with_factors(factors)
    C = compute_C_with_factors(factors)
    T = compute_T_with_factors(factors)
    
    return (task.price * S * Q - C) / T
```

---

## S(x) = S₀ + Σβᵢxᵢ + Σγᵢⱼxᵢxⱼ — Success Rate с факторами

### Формула
$$S(\mathbf{x}) = S_0 + \sum_{i=1}^{17} \beta_i \cdot x_i + \sum_{i<j} \gamma_{ij} \cdot x_i \cdot x_j$$

### Входы
```
xᵢ ∈ [0, 1] или {0, 1}  (17 факторов)
βᵢ                      (коэффициент влияния i-го фактора)
γᵢⱼ                    (синергия между i и j)
```

### Выход
```
S ∈ [0, 1] — вероятность успеха
```

### ДЕЙСТВИЕ: Оценить вероятность успешного выполнения

### ПСЕВДОКОД
```python
def compute_success_rate_with_factors(factors: np.array) -> float:
    beta = np.array([β₁, β₂, ..., β₁₇])
    base = S_0
    
    # Линейная часть
    linear = np.sum(beta * factors)
    
    # Синергии (верхний треугольник матрицы)
    gamma_matrix = get_gamma_matrix()  # 17×17 symmetric
    synergy = 0
    for i in range(17):
        for j in range(i+1, 17):
            synergy += gamma_matrix[i,j] * factors[i] * factors[j]
    
    return np.clip(base + linear + synergy, 0, 1)
```

---

# ЧАСТЬ 3: КАЧЕСТВО (Q)

---

## Q = α·Q_comp + β·Q_acc + γ·Q_full + δ·Q_time — Quality Function

### Формула
$$Q = \alpha \cdot Q_{comp} + \beta \cdot Q_{acc} + \gamma \cdot Q_{full} + \delta \cdot Q_{time}$$

где α + β + γ + δ = 1

### Входы
```
Q_comp  = |covered| / |total|       (полнота)
Q_acc   = 1 - KL_div(intent, result) (точность)
Q_full  = completeness_ratio         (завершённость)
Q_time  = 1 - min(1, (t_actual - t_deadline) / t_deadline)
```

### Выход
```
Q ∈ [0, 1] —的综合质量评分
```

### ДЕЙСТВИЕ: Оценить качество результата

### ПРАВИЛО
```
Q_min = 0.7  # Порог приемлемости

if Q >= Q_min:
    → Результат принят
elif Q >= Q_min - 0.1:
    → Требуется доработка
else:
    → Результат отклонён, retry
```

### ПСЕВДОКОД
```python
def compute_quality(
    task: Task,
    result: Result,
    weights: tuple = (0.25, 0.25, 0.25, 0.25)
) -> float:
    alpha, beta, gamma, delta = weights
    
    # Q_comp: полнота
    covered = count_covered_aspects(task.requirements, result)
    total = count_total_aspects(task.requirements)
    Q_comp = covered / total if total > 0 else 0
    
    # Q_acc: точность (cosine similarity эмбеддингов)
    Q_acc = compute_intent_accuracy(task.intent, result)
    
    # Q_full: завершённость
    Q_full = compute_completeness_ratio(result)
    
    # Q_time: своевременность
    Q_time = compute_timeliness(result.timestamp, task.deadline)
    
    return alpha * Q_comp + beta * Q_acc + gamma * Q_full + delta * Q_time
```

---

## Q_comp = |CoveredAspects| / |AllAspects| — Полнота

### Формула
$$Q_{comp} = \frac{|\text{CoveredAspects}|}{|\text{AllAspects}|}$$

### Входы
```
CoveredAspects = set(требования что покрыты в результате)
AllAspects = set(все требования задачи)
```

### Выход
```
Q_comp ∈ [0, 1]
```

### ДЕЙСТВИЕ: Измерить насколько полно покрыты требования

---

## Q_acc = 1 - KL(P_intent || P_result) — Точность

### Формула
$$Q_{acc} = 1 - \frac{D_{KL}(P_{intent} | P_{result})}{D_{max}}$$

### Аппроксимация
$$Q_{acc} \approx \text{cosine\_sim}(\text{embed}(intent), \text{embed}(result))$$

### Входы
```
intent_embedding = embed(task.intent)
result_embedding = embed(result)
```

### Выход
```
Q_acc ∈ [0, 1]
```

### ДЕЙСТВИЕ: Измерить семантическое соответствие результата намерению

### ПСЕВДОКОД
```python
def compute_accuracy(intent: str, result: str) -> float:
    intent_emb = embedding_model.encode(intent)
    result_emb = embedding_model.encode(result)
    
    similarity = cosine_similarity(intent_emb, result_emb)
    return similarity  # Уже в [0, 1]
```

---

## Q_time = 1 - min(1, (t_actual - t_deadline) / t_deadline) — Своевременность

### Формула
$$Q_{time} = 1 - \min\left(1, \frac{t_{actual} - t_{deadline}}{t_{deadline}}\right)$$

### Входы
```
t_actual  = timestamp выполнения
t_deadline = deadline задачи
```

### Выход
```
Q_time ∈ [0, 1]
  1.0 = точно в срок
  0.5 = 50% просрочки относительно deadline
  0.0 = просрочка в 2 раза больше deadline
```

### ДЕЙСТВИЕ: Оценить соблюдение сроков

### ПСЕВДОКОД
```python
def compute_timeliness(actual_time: datetime, deadline: datetime) -> float:
    if actual_time <= deadline:
        return 1.0
    
    total_allowed = (deadline - task_start).total_seconds()
    actual_duration = (actual_time - task_start).total_seconds()
    
    lateness_ratio = (actual_duration - total_allowed) / total_allowed
    
    return max(0, 1 - min(1, lateness_ratio))
```

---

## Q_decomp = α·Completeness + β·Independence + γ·Granularity + δ·Feasibility

### Формула
$$\mathcal{Q}_{decomp} = \alpha \cdot \text{Completeness} + \beta \cdot \text{Independence} + \gamma \cdot \text{Granularity} + \delta \cdot \text{Feasibility}$$

### Входы
```
Completeness = |subtasks| / expected_subtasks
Independence = 1 - correlated_pairs / total_pairs
Granularity  = 1 - (avg_action_size / optimal_size)
Feasibility  = |executable| / |total|
```

### Выход
```
Q_decomp ∈ [0, 1]
```

### ДЕЙСТВИЕ: Оценить качество декомпозиции задачи

### ПРАВИЛО
```
if Q_decomp < 0.6:
    → Переделать декомпозицию
```

---

# ЧАСТЬ 4: РИСК (Ψ)

---

## Ψ = P_fail × (C_direct + C_reputation) — Risk Function

### Формула
$$\Psi = P_{fail} \cdot (C_{direct} + C_{reputation})$$

### Входы
```
P_fail         — вероятность отказа
C_direct       — прямые убытки при отказе ($)
C_reputation   — репутационные убытки
```

### Выход
```
Ψ = float ($) — ожидаемый ущерб от риска
```

### ДЕЙСТВИЕ: Оценить потенциальный ущерб от неудачи

### ПРАВИЛО
```
Ψ_max = task.price × 0.5  # Максимум 50% от цены

if Ψ > Ψ_max:
    → Риск слишком высок, требуется mitigation
```

---

## P_fail = P_base × (1 + αᵤ·U + αf·F + αₙ·N + αd·D) / (1 + αs·S)

### Формула
$$P_{fail} = P_{base} \cdot (1 + \alpha_u \cdot U + \alpha_f \cdot F + \alpha_n \cdot N + \alpha_d \cdot D) \cdot \frac{1}{1 + \alpha_s \cdot S}$$

### Входы
```
P_base = 0.1        (базовая вероятность отказа)
U      ∈ [0, 1]    (uncertainty задачи)
F      ∈ [0, 1]    (fatigue агента)
N      ∈ [0, 1]    (новизна задачи)
D      ∈ [0, 1]    (deadline pressure)
S      ∈ [0, 1]    (skill level агента)
```

### Выход
```
P_fail ∈ [0, 1]
```

### ДЕЙСТВИЕ: Рассчитать вероятность неудачи

### ПСЕВДОКОД
```python
def compute_failure_probability(
    task: Task,
    agent: AgentState
) -> float:
    # Измеряем параметры
    U = compute_task_uncertainty(task)
    F = compute_agent_fatigue(agent)
    N = compute_task_novelty(task, agent)
    D = compute_deadline_pressure(task)
    S = agent.skill_level
    
    # P_fail формула
    modifiers = 1 + U + F + N + D
    skill_reduction = 1 / (1 + S)
    
    return P_BASE * modifiers * skill_reduction
```

---

## P_cascade = 1 - ∏(1 - pᵢ) — Cascade probability

### Формула
$$P_{cascade} = 1 - \prod_{i=1}^{n} (1 - p_i)$$

### Входы
```
p₁, p₂, ..., pₙ — вероятности отдельных событий в цепочке
```

### Выход
```
P_cascade ∈ [0, 1] — вероятность что хотя бы одно событие произойдёт
```

### ДЕЙСТВИЕ: Оценить риск каскадного отказа в цепочке действий

### ПСЕВДОКОД
```python
def compute_cascade_probability(steps: List[Step]) -> float:
    """Для каждого шага в декомпозиции"""
    survival_prob = 1.0
    for step in steps:
        survival_prob *= (1 - step.failure_prob)
    
    return 1 - survival_prob
```

---

## P_risk_final = P_fail × ∏(1 - p_risk,i × (1 - Gᵢ)) — Risk reduction by guardrails

### Формула
$$P_{risk\_final} = P_{fail} \cdot \prod_{i} (1 - p_{risk,i} \cdot (1 - G_i))$$

### Входы
```
P_fail   — базовая вероятность
p_risk,i — вероятность i-го рискового события
Gᵢ       ∈ {0, 1} — активен ли i-й guardrail
```

### Выход
```
P_risk_final ∈ [0, P_fail]
```

### ДЕЙСТВИЕ: Рассчитать снижение риска от guardrails

### ПСЕВДОКОД
```python
def apply_guardrails(P_fail: float, guardrails: List[Guardrail]) -> float:
    reduction_factor = 1.0
    for guardrail in guardrails:
        risk_prob = guardrail.risk_event_probability
        is_active = guardrail.is_active()
        reduction_factor *= (1 - risk_prob * (1 - is_active))
    
    return P_fail * reduction_factor
```

---

# ЧАСТЬ 5: РЕПУТАЦИЯ (Υ)

---

## Υ = γ₁·R̄ + γ₂·τ_ret + γ₃·N⁺/N + γ₄·(1-δ) + γ₅·dΥ/dt — Reputation Function

### Формула
$$\Upsilon = \gamma_1 \cdot \bar{R} + \gamma_2 \cdot \tau_{ret} + \gamma_3 \cdot \frac{N^+}{N} + \gamma_4 \cdot (1 - \delta) + \gamma_5 \cdot \frac{d\Upsilon}{dt}$$

### Входы
```
R̄     — средний рейтинг (нормированный 0-1)
τ_ret — retention rate (вернувшиеся клиенты / всего)
N⁺/N  — доля положительных отзывов
δ     — среднее отклонение от SLA
dΥ/dt — momentum (скорость изменения репутации)
```

### Выход
```
Υ ∈ [0, 1] — 综合репутационный score
```

### ДЕЙСТВИЕ: Оценить репутацию агента

### ПСЕВДОКОД
```python
def compute_reputation(agent: AgentState) -> float:
    gamma = [0.30, 0.25, 0.20, 0.15, 0.10]  # Сумма = 1.0
    
    R_normalized = agent.avg_rating / 5.0
    tau_ret = agent.returning_clients / agent.total_clients
    pos_ratio = agent.positive_reviews / max(1, agent.total_reviews)
    sla_compliance = 1 - agent.avg_delay_ratio
    momentum = compute_reputation_momentum(agent.history)
    
    return (
        gamma[0] * R_normalized +
        gamma[1] * tau_ret +
        gamma[2] * pos_ratio +
        gamma[3] * sla_compliance +
        gamma[4] * momentum
    )
```

---

## R_bayesian = (m·μ₀ + Σrᵢ) / (m + n) — Bayesian rating

### Формула
$$R_{bayesian} = \frac{m \cdot \mu_0 + \sum_{i=1}^{n} r_i}{m + n}$$

### Входы
```
m = 7      (сила prior)
μ₀ = 4.2   (prior mean)
rᵢ         (отдельные оценки)
```

### Выход
```
R_bayesian ∈ [1, 5]
```

### ДЕЙСТВИЕ: Рассчитать сглаженный рейтинг (защита от выбросов)

### ПСЕВДОКОД
```python
def compute_bayesian_rating(reviews: List[int]) -> float:
    m = 7
    mu_0 = 4.2
    
    if len(reviews) == 0:
        return mu_0
    
    numerator = m * mu_0 + sum(reviews)
    denominator = m + len(reviews)
    
    return numerator / denominator
```

---

## Θ = 1 - (1/√N) × σR / (R_max - R_min) — Rating confidence

### Формула
$$\Theta = 1 - \frac{1}{\sqrt{N}} \cdot \frac{\sigma_R}{R_{max} - R_{min}}$$

### Входы
```
N      — количество оценок
σR     — стандартное отклонение оценок
R_max  = 5
R_min  = 1
```

### Выход
```
Θ ∈ [0, 1] — уверенность в рейтинге
```

### ДЕЙСТВИЕ: Оценить надёжность рейтинга

### ПРАВИЛО
```
if Θ < 0.5:
    → Рейтинг ненадёжен, нужно больше отзывов
```

---

## λ_orders = λ₀ × (R/R̄)^β_rep × Θ^γ_trust × (1 + SC)^δ — Order flow

### Формула
$$\lambda_{orders} = \lambda_0 \cdot \left(\frac{R}{\bar{R}}\right)^{\beta_{rep}} \cdot \Theta^{\gamma_{trust}} \cdot (1 + SC)^{\delta_{social}}$$

### Входы
```
λ₀      = 1.0    (базовый поток)
R/R̄    — отношение текущего рейтинга к среднему
Θ       — confidence в рейтинге
SC      — social capital (0-1)
```

### Выход
```
λ_orders — множитель потока заказов (>1 = больше заказов)
```

### ДЕЙСТВИЕ: Спрогнозировать ожидаемый поток заказов

### ПСЕВДОКОД
```python
def predict_order_flow(
    agent: AgentState,
    current_rating: float
) -> float:
    avg_market_rating = get_avg_platform_rating()
    
    lambda_0 = 1.0
    rating_factor = (current_rating / avg_market_rating) ** 0.5
    trust_factor = agent.rating_confidence ** 0.3
    social_factor = (1 + agent.social_capital) ** 0.2
    
    return lambda_0 * rating_factor * trust_factor * social_factor
```

---

## τ_recovery = τ_base / (ρ_resilience × (1 + β × N_good)) — Recovery time

### Формула
$$\tau_{recovery} = \frac{\tau_{base}}{\rho_{resilience} \cdot (1 + \beta \cdot N_{good})}$$

### Входы
```
τ_base = 24 часа      (базовое время восстановления)
ρ      — resilience агента
N_good — количество успешных задач подряд
```

### Выход
```
τ_recovery (часы) — время восстановления репутации
```

### ДЕЙСТВИЕ: Оценить время на восстановление после инцидента

---

## dR/dt = α·Q·(1 + β·V_resp) - γ·incidents·R — Reputation dynamics

### Формула
$$\frac{dR}{dt} = \alpha \cdot Q \cdot (1 + \beta \cdot V_{resp}) - \gamma \cdot \text{incidents} \cdot R$$

### Входы
```
Q       — качество результата
V_resp  — скорость реакции
incidents — количество инцидентов
R       — текущий рейтинг
```

### Выход
```
dR/dt — скорость изменения рейтинга
```

### ДЕЙСТВИЕ: Симулировать динамику репутации во времени

### ПСЕВДОКОД
```python
def simulate_reputation(
    current_rating: float,
    quality: float,
    response_velocity: float,
    incidents: int,
    dt: float = 1.0  # день
) -> float:
    alpha, beta, gamma = 0.1, 0.2, 0.05
    
    quality_term = alpha * quality * (1 + beta * response_velocity)
    incident_term = gamma * incidents * current_rating
    
    return current_rating + (quality_term - incident_term) * dt
```

---

# ЧАСТЬ 6: КОМПЛАЕНС (Γ)

---

## Γ(action) = 0 или -∞ — Veto Function

### Формула
$$\Gamma(action) = \begin{cases} 0, & \forall r \in Rules: r(action) = True \\ -\infty, & otherwise \end{cases}$$

### Входы
```
Rules = {r_legal, r_api, r_financial, r_security, ...}
```

### Выход
```
Γ = 0    → action PASSED compliance
Γ = -∞   → action VETOED
```

### ДЕЙСТВИЕ: Проверить легальность/безопасность действия

### ПРАВИЛО
```
if Γ(action) = 0:
    → Можно выполнять
else:
    → НЕ выполнять, заблокировать
```

### ПСЕВДОКОД
```python
def check_compliance(action: Action, context: Context) -> bool:
    """Biinary compliance check - VETO pattern"""
    
    rules = [
        check_legal(action),
        check_api_limits(action, context),
        check_financial_limits(action, context),
        check_security_rules(action, context),
        check_rate_limits(action, context),
    ]
    
    # ALL rules must pass
    return all(rules)


# Правила
def check_legal(action: Action) -> bool:
    """Действие не нарушает законы"""
    forbidden = ["illegal_request", "fraud", "copyright_violation"]
    return not any(word in action.description for word in forbidden)


def check_api_limits(action: Action, context: Context) -> bool:
    """API стоимость не превышает лимит"""
    return action.api_cost < context.max_api_cost_per_task


def check_financial_limits(action: Action, context: Context) -> bool:
    """Общая стоимость не превышает бюджет"""
    return context.total_cost + action.cost < context.max_budget


def check_security_rules(action: Action, context: Context) -> bool:
    """Нет угроз безопасности"""
    return not contains_malicious_pattern(action)


def check_rate_limits(action: Action, context: Context) -> bool:
    """Не превышен rate limit"""
    return context.calls_last_minute < context.max_calls_per_minute
```

---

## 𝕀[Γ(A) = 0] — Compliance indicator

### Формула
$$\mathbb{I}[\Gamma(A) = 0] = \begin{cases} 1, & \Gamma(A) = 0 \\ 0, & \Gamma(A) = -\infty \end{cases}$$

### ДЕЙСТВИЕ: Использовать как множитель в других формулах

### ПСЕВДОКОД
```python
def compliance_indicator(gamma_result: float) -> int:
    return 1 if gamma_result == 0 else 0
```

---

# ЧАСТЬ 7: ЭВОЛЮЦИЯ (Ω)

---

## L_s(t) = L_max × (1 - e^(-η·t^γ)) + L₀ — Learning Curve

### Формула
$$L_s(t) = L_{max} \cdot (1 - e^{-\eta \cdot t^{\gamma}}) + L_0$$

### Входы
```
L_max = 1.0      (максимальный skill level)
η = 0.01         (скорость обучения)
γ                 (форма кривой)
t                 (время в единицах задач или часов)
L₀ = 0.0         (начальный уровень)
```

### Выход
```
L_s(t) ∈ [0, L_max] — текущий skill level
```

### ДЕЙСТВИЕ: Рассчитать прогноз развития навыка

### ПСЕВДОКОД
```python
def predict_skill_level(
    current_level: float,
    time: float,
    learning_rate: float = 0.01
) -> float:
    import math
    
    L_max = 1.0
    gamma = 0.5  # форма кривой
    
    return L_max * (1 - math.exp(-learning_rate * time ** gamma)) + current_level * 0.1
```

---

## K(t) = K₀ + η_learn × Σ ΔK(τ) × (1 - K(τ)/K_max) — Knowledge Accumulation

### Формула
$$K(t) = K_0 + \eta_{learn} \cdot \sum_{\tau < t} \Delta K(\tau) \cdot \left(1 - \frac{K(\tau)}{K_{max}}\right)$$

### Входы
```
K₀      — начальное знание
η_learn — скорость обучения
ΔK(τ)   — прирост знаний в момент τ
K_max   = 1.0
```

### Выход
```
K(t) ∈ [0, 1] — текущий уровень знаний
```

### ДЕЙСТВИЕ: Рассчитать накопленные знания агента

### ПСЕВДОКОД
```python
def compute_knowledge(
    history: List[TaskResult],
    learning_rate: float = 0.01
) -> float:
    K = 0.0
    K_max = 1.0
    
    for result in history:
        delta_k = compute_learning_gain(result)
        K += learning_rate * delta_k * (1 - K / K_max)
    
    return min(K, K_max)
```

---

## ZPD = ZPD_base × (1 + α_M·M - α_CL·CL + α_η·η) — Zone of Proximal Development

### Формула
$$ZPD = ZPD_{base} \cdot (1 + \alpha_M \cdot M - \alpha_{CL} \cdot CL + \alpha_\eta \cdot \eta)$$

### Входы
```
ZPD_base — базовый ZPD
M         — мотивация
CL        — current load
η         — learning rate
```

### Выход
```
ZPD — зона ближайшего развития (сложность задач которые агент может освоить)
```

### ДЕЙСТВИЕ: Определить оптимальный уровень сложности для роста

### ПРАВИЛО
```
task_complexity > ZPD + threshold  → Задача слишком сложная
task_complexity < ZPD - threshold  → Задача слишком лёгкая
ZPD - threshold ≤ task_complexity ≤ ZPD + threshold → Optimal
```

---

## Φ_forget(t, n) = e^(-t / (S × (1 + κ·n)^ψ)) — Forgetting Factor

### Формула
$$\Phi_{forget}(t, n) = e^{-\frac{t}{S \cdot (1 + \kappa \cdot n)^\psi}}$$

### Входы
```
t    — время с момента последнего использования
S    — stability parameter
n    — количество повторений
κ, ψ — формы забывания
```

### Выход
```
Φ_forget ∈ [0, 1] — retention factor
```

### ДЕЙСТВИЕ: Рассчитать "забывание" навыка

### ПСЕВДОКОД
```python
def compute_retention(
    time_since_practice: float,
    stability: float,
    repetitions: int
) -> float:
    kappa, psi = 0.1, 0.5
    
    denominator = stability * (1 + kappa * repetitions) ** psi
    return math.exp(-time_since_practice / denominator)
```

---

# ЧАСТЬ 8: ГОМЕОСТАЗ (H)

---

## H = (F_reinforcing + ε) / (F_balancing + ε) — Homeostasis

### Формула
$$H = \frac{F_{reinforcing} + \epsilon}{F_{balancing} + \epsilon}$$

### Входы
```
F_reinforcing ≈ ν·VoI + γ·Υ + φ_ft·dN_tasks/dt
F_balancing  ≈ λ_Ψ·Ψ + ρ·E_error + δ_coord·N_agents²
ε = 10^-6     (защита от деления на ноль)
```

### Выход
```
H ∈ (0, ∞)
  H > 1 + ε  → Рост (expansion)
  H ≈ 1      → Гомеостаз
  H < 1 - ε  → Спад
```

### ДЕЙСТВИЕ: Определить состояние системы

### ПРАВИЛО
```
if H > 1 + eps_H:
    → Активировать EXPANSION mode (больше задач, риска)
elif H < 1 - eps_H:
    → Активировать CONSERVATION mode (меньше задач, больше безопасности)
else:
    → MAINTENANCE mode (стабильность)
```

### ПСЕВДОКОД
```python
def compute_homeostasis(agent: AgentState) -> HomeostasisResult:
    eps = 1e-6
    
    # Reinforcing forces
    F_rein = (
        NU * agent.voi +
        GAMMA * agent.reputation +
        PHI_FT * agent.task_growth_rate
    )
    
    # Balancing forces
    F_bal = (
        LAMBDA_PSI * agent.risk +
        RHO * agent.error_rate +
        DELTA_COORD * agent.num_agents ** 2
    )
    
    H = (F_rein + eps) / (F_bal + eps)
    
    if H > 1.1:
        mode = "EXPANSION"
    elif H < 0.9:
        mode = "CONSERVATION"
    else:
        mode = "MAINTENANCE"
    
    return HomeostasisResult(H=H, mode=mode)
```

---

## A = (ΔΦ_recovery + ε) / (ΔΦ_loss + ε) — Adaptability Index

### Формула
$$\mathcal{A} = \frac{\Delta \Phi_{recovery} + \epsilon}{\Delta \Phi_{loss} + \epsilon}$$

### Входы
```
ΔΦ_recovery — изменение прибыли при recovery
ΔΦ_loss     — изменение прибыли при потере
```

### Выход
```
A ∈ (0, ∞) — способность к адаптации
```

### ДЕЙСТВИЕ: Оценить resilience агента

---

# ЧАСТЬ 9: VALUE OF INFORMATION (VoI)

---

## VoI = E[Φ | with info] - E[Φ | without info] — Value of Information

### Формула
$$\text{VoI} = \mathbb{E}[\Phi | \text{with info}] - \mathbb{E}[\Phi | \text{without info}]$$

### Развёрнуто
```
E[Φ | with info] = Φ_yes × P(yes) + Φ_no × P(no)
E[Φ | without info] = Φ_attempt × S + Φ_refuse × (1-S)
```

### Входы
```
Φ_yes, Φ_no  — значения прибыли при ответе yes/no
P(yes), P(no) — вероятности
Φ_attempt     — прибыль при попытке выполнить
S             — вероятность успеха
```

### Выход
```
VoI ∈ (-∞, +∞) $
  VoI > 0  → Информация ценна, стоит запросить
  VoI < 0  → Информация не стоит затрат на получение
```

### ДЕЙСТВИЕ: Решить, стоит ли запрашивать дополнительную информацию

### ПСЕВДОКОД
```python
def compute_value_of_information(
    question: str,
    task: Task,
    agent: AgentState
) -> float:
    # До уточнения: ожидаемая прибыль
    S = compute_success_rate(task, agent)
    expected_without = task.price * S - task.expected_cost
    
    # После уточнения: вероятности + результаты
    # (упрощённо)
    P_yes = 0.7
    P_no = 0.3
    
    # Запрос информации имеет стоимость
    info_cost = estimate_info_cost(question)
    
    # Ожидаемая выгода от уточнения
    expected_with = P_yes * task.price - task.expected_cost + 100  # Улучшение от уточнения
    
    voi = expected_with - expected_without - info_cost
    
    return voi
```

---

# ЧАСТЬ 10: UTILITY (U)

---

## U = λ_Φ·Φ + λ_Υ·Υ + λ_Q·Q + λ_Ω·Ω - λ_Ψ·Ψ - λ_Γ·Γ — Utility Function

### Формула
$$U = \lambda_\Phi \cdot \Phi + \lambda_\Upsilon \cdot \Upsilon + \lambda_Q \cdot Q + \lambda_\Omega \cdot \Omega - \lambda_\Psi \cdot \Psi - \lambda_\Gamma \cdot \Gamma$$

### Входы
```
Φ, Υ, Q, Ω, Ψ, Γ — выходы соответствующих функций
λ_Φ, λ_Υ, ...    — веса (определяются Mission)
```

### Выход
```
U ∈ (-∞, +∞) — 综合utility score
```

### ДЕЙСТВИЕ: Финальное решение о выполнении задачи

### ПРАВИЛО
```
if U > U_threshold:
    → ACCEPT task
else:
    → REJECT task
```

### ПСЕВДОКОД
```python
def compute_utility(
    task: Task,
    agent: AgentState,
    mission: Mission  # Определяет веса
) -> float:
    # Вычисляем все компоненты
    phi = compute_profit(task, agent)
    upsilon = compute_reputation(agent)
    quality = estimate_quality(task, agent)
    omega = compute_evolution_score(agent)
    psi = compute_risk(task, agent)
    gamma = 0 if check_compliance(task) else float('-inf')
    
    # Веса из Mission
    weights = mission.get_weights()
    
    return (
        weights.lambda_phi * phi +
        weights.lambda_upsilon * upsilon +
        weights.lambda_quality * quality +
        weights.lambda_omega * omega -
        weights.lambda_psi * psi -
        weights.lambda_gamma * gamma
    )
```

---

## U_economic = Φ × (1 + α_rep × Υ) — Economic Utility

### Формула
$$U_{economic} = \Phi \cdot (1 + \alpha_{rep} \cdot \Upsilon)$$

### Входы
```
Φ      — прибыль
α_rep  — коэффициент репутационного бонуса
Υ      — репутация
```

### Выход
```
U_economic — прибыль с репутационным бонусом
```

### ДЕЙСТВИЕ: Быстрая оценка экономической целесообразности

---

## U_ext = Φ + λ_Υ·Υ + α_K·K + λ_VoI·VoI — Extended Utility

### Формула
$$U_{ext} = \Phi + \lambda_\Upsilon \cdot \Upsilon + \alpha_K \cdot K + \lambda_{VoI} \cdot \text{VoI}$$

### Входы
```
Φ    — прибыль
Υ    — репутация
K    — knowledge
VoI  — value of information
```

### Выход
```
U_ext ∈ (-∞, +∞)
```

### ДЕЙСТВИЕ: Utility с учётом долгосрочных факторов

---

## λ_cost(t) = λ₀ × (H(t)/H_target) × (1 + α_Ψ × Ψ(t)) — Lambda Cost

### Формула
$$\lambda_{cost}(t) = \lambda_0 \cdot \frac{H(t)}{H_{target}} \cdot (1 + \alpha_\Psi \cdot \Psi(t))$$

### Входы
```
H(t)       — homeostatic ratio
H_target   = 1.0
Ψ(t)       — текущий риск
```

### Выход
```
λ_cost ∈ (0, ∞) — динамический cost modifier
```

### ДЕЙСТВИЕ: Адаптивная модуляция стоимости

---

# ЧАСТЬ 11: ROUTING (Φ_R)

---

## Φ_R(D) = Φ(D) × 𝕀[Γ(D)=0] × (1 + α_rep × Υ) - λ_Ψ × Ψ(D)

### Формула
$$\Phi_R(D) = \Phi(D) \cdot \mathbb{I}[\Gamma(D) = 0] \cdot \left(1 + \alpha_{rep} \cdot \Upsilon \right) - \lambda_\Psi \cdot \Psi(D)$$

### Входы
```
Φ(D)       — прибыль декомпозиции
𝕀[Γ(D)=0] — индикатор прохождения compliance
Υ          — репутация
Ψ(D)       — риск декомпозиции
```

### Выход
```
Φ_R ∈ (-∞, +∞) — routing quality score
```

### ДЕЙСТВИЕ: Оценить план декомпозиции для принятия/отклонения

### ПРАВИЛО
```
if Φ_R > 0:
    → ACCEPT decomposition
else:
    → REJECT или REFINE
```

---

# ЧАСТЬ 12: EXECUTOR (Ξ)

---

## Ξ_task = α × Q_result - β × (O_time + O_cost) — Executor Function

### Формула
$$\Xi_{task} = \alpha \cdot Q_{result} - \beta \cdot (O_{time} + O_{cost})$$

### Входы
```
Q_result  — качество результата
O_time   — overrun времени vs план
O_cost   — overrun бюджета vs план
α, β     — коэффициенты (требуют калибровки)
```

### Выход
```
Ξ_task ∈ (-∞, +∞) — executor quality score
```

### ДЕЙСТВИЕ: Оценить качество работы исполнителя

### ПРАВИЛО
```
if Ξ_task > 0:
    → Executor performance ACCEPTABLE
else:
    → Executor performance NEEDS IMPROVEMENT
```

---

# ЧАСТЬ 13: ФАКТОРЫ СПОСОБНОСТЕЙ (x₁-x₁₇)

---

## x₁: LLM Capability

### Определение
$$C_{llm} = \alpha_Q \cdot Q_{bench} + \alpha_R \cdot R_{bench} + \alpha_C \cdot C_{bench} + \alpha_A \cdot A_{bench}$$

### Веса
```
α_Q = 0.25  (Quality benchmark)
α_R = 0.30  (Reasoning)
α_C = 0.25  (Coding)
α_A = 0.20  (Agentic)
```

### Влияние на S
$$S(m, t) = \frac{C_{llm}(m)}{1 + e^{-\lambda_t \cdot (C_{llm}(m) - \tau_t)}}$$

### Влияние на Q
$$Q(m) = Q_{max} \cdot \frac{C_{llm}(m)}{1 + \gamma \cdot (1 - C_{llm}(m))}$$

### ДЕЙСТВИЕ: Выбрать оптимальную LLM модель для задачи

### ПСЕВДОКОД
```python
LLM_MODELS = {
    "gpt-4":    {"Q": 0.9, "R": 0.95, "C": 0.9, "A": 0.9},
    "gpt-3.5":  {"Q": 0.7, "R": 0.8, "C": 0.75, "A": 0.7},
    "claude":   {"Q": 0.88, "R": 0.92, "C": 0.85, "A": 0.88},
    "ollama":   {"Q": 0.5, "R": 0.6, "C": 0.55, "A": 0.5},
}

def compute_llm_capability(model: str, task_type: str) -> float:
    weights = {"Q": 0.25, "R": 0.30, "C": 0.25, "A": 0.20}
    
    if task_type == "coding":
        weights = {"Q": 0.2, "R": 0.25, "C": 0.35, "A": 0.20}
    elif task_type == "reasoning":
        weights = {"Q": 0.2, "R": 0.40, "C": 0.2, "A": 0.20}
    
    caps = LLM_MODELS[model]
    return sum(weights[k] * caps[k] for k in weights)


def select_model(task: Task, agent: AgentState) -> str:
    """Выбрать модель максимизирующую utility"""
    
    candidates = []
    for model in LLM_MODELS:
        capability = compute_llm_capability(model, task.type)
        cost = get_model_cost(model)
        
        # S с учётом capability
        S = sigmoid_capability(capability)
        
        # Q (throughput)
        Q = compute_throughput(capability)
        
        # Прибыль
        phi = (task.price * S * Q - cost) / task.expected_time
        
        candidates.append((model, phi))
    
    # Выбрать с максимальной прибылью
    return max(candidates, key=lambda x: x[1])[0]
```

---

## x₂: Tool Calling

### Определение
```
x₂ ∈ {0, 1}
x₂ = 1 если agent использует tool calling
x₂ = 0 если agent работает только с raw LLM
```

### Влияние на S
```
ΔS = +0.20 при x₂ = 1
```

### Влияние на C
```
ΔC = стоимость tool вызова
```

### ДЕЙСТВИЕ: Решить использовать ли tool calling

### ПРАВИЛО
```
if task.requires_external_data OR task.requires_computation:
    → x₂ = 1 (использовать tools)
else:
    → Сравнить ΔS×P с ΔC
```

---

## x₃: MCP Integration

### Определение
```
x₃ ∈ {0, 1}
```

### Влияние на S
```
ΔS = +0.05 при x₃ = 1
```

### ДЕЙСТВИЕ: Использовать ли Model Context Protocol

---

## x₄: Memory

### Определение
```
M_p ∈ [0, 1] — качество памяти (precision)
```

### Влияние на S
$$\Delta S_{memory} = \beta_0 + \beta_1 \cdot M_p + \beta_2 \cdot M_p^2$$

### Влияние на Q
$$Q(M_p) = Q_0 \cdot (1 + \gamma \cdot M_p \cdot (1 - e^{-\delta \cdot M_p}))$$

### Влияние на C
$$C_{memory} = C_{storage} + C_{retrieval} + C_{maintenance}$$

### ДЕЙСТВИЕ: Определить оптимальный уровень memory для задачи

### ПСЕВДОКОД
```python
def compute_memory_benefit(memory_precision: float) -> dict:
    # S boost
    S_boost = 0.1 + 0.3 * memory_precision + 0.2 * memory_precision ** 2
    
    # Q multiplier
    Q_mult = 1 + 0.2 * memory_precision * (1 - math.exp(-0.5 * memory_precision))
    
    # Cost
    storage_cost = memory_precision * 0.01  # $/hour
    retrieval_cost = memory_precision * 0.001  # per query
    maintenance_cost = memory_precision * 0.005
    
    total_cost = storage_cost + retrieval_cost + maintenance_cost
    
    return {
        "S_boost": S_boost,
        "Q_mult": Q_mult,
        "cost": total_cost
    }
```

---

## x₅: Multi-Agent

### Определение
```
N ∈ {1, 2, 4, 8, 16} — количество агентов
```

### Влияние на S
$$\Delta S_{multi} = \alpha_0 + \alpha_1 \cdot \log(N_{agents}) + \alpha_2 \cdot \frac{N_{agents}}{N_{agents} + \beta}$$

### Влияние на C
$$C_{coordination} = \delta_1 \cdot N \cdot \log(N) + \delta_2 \cdot N^2$$

### ДЕЙСТВИЕ: Определить оптимальное количество агентов

### ПРАВИЛО
```
Оптимум N = 4-8 агентов
При N > 8 координационные затраты превышают выгоду
```

### ПСЕВДОКОД
```python
def compute_multi_agent_tradeoff(N: int, task: Task) -> float:
    # Benefit
    alpha_0, alpha_1, alpha_2 = 0.05, 0.1, 0.15
    beta_coord = 5
    
    S_benefit = alpha_0 + alpha_1 * math.log(N) + alpha_2 * N / (N + beta_coord)
    
    # Coordination cost
    delta_1, delta_2 = 0.01, 0.001
    coordination_cost = delta_1 * N * math.log(N) + delta_2 * N ** 2
    
    # Net benefit
    return S_benefit * task.price - coordination_cost


def select_agent_count(task: Task) -> int:
    best_N = 1
    best_value = compute_multi_agent_tradeoff(1, task)
    
    for N in [2, 4, 8, 16]:
        value = compute_multi_agent_tradeoff(N, task)
        if value > best_value:
            best_value = value
            best_N = N
    
    return best_N
```

---

## x₆: Self-Correction

### Определение
```
L_sc ∈ {0, 1, 2, 3, 4} — уровень self-correction
```

### Влияние на S
$$\Delta S_{sc} = \beta_1 \cdot L_{sc} + \beta_2 \cdot L_{sc}^2$$

### Влияние на T
```
~3 retries максимум
```

### ДЕЙСТВИЕ: Определить нужно ли self-correction

### ПРАВИЛО
```
if current_quality < quality_threshold:
    if remaining_retries > 0:
        → APPLY self-correction
```

---

## x₇: Prompt Engineering

### Определение
```
Q_p ∈ [0, 1] — качество промта
```

### Влияние на S
$$\Delta S_{prompt} = \beta_1 \cdot Q_p + \beta_2 \cdot Q_p^2$$

### ДЕЙСТВИЕ: Оптимизировать промт для задачи

### ПСЕВДОКОД
```python
def compute_prompt_benefit(prompt_quality: float) -> float:
    # Улучшение от 0 до 1 = 10x improvement в некоторых случаях
    beta_1 = 0.2
    beta_2 = 0.1
    
    return beta_1 * prompt_quality + beta_2 * prompt_quality ** 2


def optimize_prompt(task: Task) -> str:
    """Генерация оптимального промта"""
    
    components = [
        get_system_role(task.type),
        get_task_instructions(task.requirements),
        get_format_instructions(task.output_format),
        get_examples(task.type),
        get_constraints(task)
    ]
    
    return "\n\n".join(filter(None, components))
```

---

## x₈: Cost Tiering

### Определение
```
θ_tier ∈ [0, 1] — порог переключения на дорогую модель
```

### Влияние на C
```
local (ollama): cost ≈ 0, quality = 0.7 baseline
API (OpenAI): cost > 0, quality = 0.9 baseline
Экономия: до 77%
```

### ДЕЙСТВИЕ: Выбрать между дешёвой и дорогой моделью

### ПРАВИЛО
```
confidence_threshold > θ_tier:
    → Использовать дорогую модель (высокое качество)
confidence_threshold <= θ_tier:
    → Использовать дешёвую модель (быстро, дёшево)
```

### ПСЕВДОКОД
```python
def select_cost_tier(
    task: Task,
    confidence_threshold: float,
    theta_tier: float = 0.7
) -> str:
    if confidence_threshold > theta_tier:
        return "API"  # Дорогая модель
    else:
        return "LOCAL"  # Дешёвая модель (ollama)


def compute_tier_roi(
    task: Task,
    confidence: float
) -> dict:
    local_phi = compute_profit_with_model(task, "local")
    api_phi = compute_profit_with_model(task, "api")
    
    return {
        "local_phi": local_phi,
        "api_phi": api_phi,
        "break_even_confidence": find_break_even(confidence, local_phi, api_phi)
    }
```

---

## x₉: Grounding

### Определение
```
G ∈ {0, 1}
G = 1 если используется RAG/grounding
```

### Влияние на S
$$\Delta S_G = \beta_0 + \beta_1 \cdot G_{score} \cdot d$$

где:
```
G_score = α_ret·Q_ret + α_rerank·Q_rerank + α_gen·F_faith
d = retrieval depth
```

### ДЕЙСТВИЕ: Решить использовать ли grounding

### ПРАВИЛО
```
if task.requires_facts OR task.requires_code_context:
    → G = 1 (использовать grounding)
else:
    → G = 0
```

---

## x₁₀: Fine-tuning

### Определение
```
F_t ∈ {0, 1}
F_t = 1 если используется fine-tuned модель
```

### Влияние на S
$$\Delta S_{ft} = \beta \cdot (1 - e^{-\lambda \cdot N_{samples}})$$

где N_samples ≥ 500/месяц для эффективности

### ДЕЙСТВИЕ: Стоит ли fine-tunить модель

### ПРАВИЛО
```
if N_similar_tasks_per_month > 500 AND budget > fine_tuning_cost:
    → FINE_TUNE
```

---

## x₁₁: Browser

### Определение
```
B_a ∈ {0, 1, 2, 3} — уровень browser automation
```

### Влияние на S
$$\Delta S_{browser} = \beta \cdot B_{score} \cdot \sigma(d)$$

где B_score зависит от уровня автоматизации

### ДЕЙСТВИЕ: Нужна ли browser automation

---

## x₁₂: Guardrails

### Определение
```
G_eff = ∏(1 - p_risk,i × (1 - Gᵢ))
```

### Влияние на S
$$\Delta S_{guardrails} = \beta_g \cdot G_{eff}$$

### Влияние на Ψ
```
Ψ_reduced = Ψ × (1 - G_eff)
```

### ДЕЙСТВИЕ: Какие guardrails активировать

### ПСЕВДОКОД
```python
class Guardrail:
    def __init__(self, name, risk_prob, effectiveness, cost):
        self.name = name
        self.risk_prob = risk_prob  # p_risk,i
        self.effectiveness = effectiveness  # G_i (0 или 1)
        self.cost = cost


def compute_guardrails_roi(guardrails: List[Guardrail], task: Task) -> List[Guardrail]:
    """Какие guardrails стоит активировать"""
    
    # Базовый риск
    base_risk = compute_risk(task)
    
    selected = []
    for g in guardrails:
        # ΔS от guardrail
        delta_S = g.effectiveness * g.risk_prob * task.price
        
        # Cost guardrail
        if delta_S > g.cost:
            selected.append(g)
    
    return selected


def apply_guardrails(
    base_risk: float,
    active_guardrails: List[Guardrail]
) -> float:
    """Применить guardrails и получить reduced risk"""
    
    G_eff = 1.0
    for g in active_guardrails:
        G_eff *= (1 - g.risk_prob * g.effectiveness)
    
    return base_risk * G_eff
```

---

## x₁₃: Test-Time Compute

### Определение
```
T_think / T_base — ratio extra reasoning time
```

### Влияние на S
$$S_{reason} = S(x) + \beta_{reason} \cdot \log(1 + \frac{T_{think}}{T_{base}})$$

### Влияние на T
$$T_{reason} = T(x) \cdot (1 + 0.25 \cdot \frac{T_{think}}{T_{base}})$$

### ROI
$$\text{ROI}_{reasoning} = \frac{\Delta S \cdot P}{\Delta C_{api}}$$

### ДЕЙСТВИЕ: Сколько времени тратить на reasoning

### ПРАВИЛО
```
if ROI_reasoning > 1.0:
    → Использовать extended reasoning
else:
    → Минимальный reasoning
```

### ПСЕВДОКОД
```python
def compute_reasoning_tradeoff(
    base_success: float,
    base_time: float,
    base_cost: float,
    task_price: float,
    extra_reasoning_time: float
) -> dict:
    # ΔS от reasoning
    beta_reason = 0.18
    delta_S = beta_reason * math.log(1 + extra_reasoning_time)
    S_with_reasoning = min(1.0, base_success + delta_S)
    
    # T penalty
    T_with_reasoning = base_time * (1 + 0.25 * extra_reasoning_time)
    
    # ΔC
    extra_cost = extra_reasoning_time * API_COST_PER_SECOND
    
    # ΔΦ
    extra_revenue = (S_with_reasoning - base_success) * task_price
    delta_phi = (extra_revenue - extra_cost) / T_with_reasoning
    
    # ROI
    roi = extra_revenue / extra_cost if extra_cost > 0 else float('inf')
    
    return {
        "S_with": S_with_reasoning,
        "T_with": T_with_reasoning,
        "delta_phi": delta_phi,
        "roi": roi,
        "should_use": roi > 1.0
    }
```

---

## x₁₄: Design Patterns (Agentic)

### Определение
```
S_pattern(x) = S(x) + Σ α_p × P_p(x)
```

где паттерны:
| Паттерн | α_p |
|---------|-----|
| ReAct | +0.08 |
| Reflection | +0.12 |
| Planning | +0.15 |

### Влияние на Q
$$Q_{pattern} = Q(x) \cdot \prod_p (1 + \beta_p \cdot P_p)$$

### ДЕЙСТВИЕ: Выбрать паттерн для задачи

### ПСЕВДОКОД
```python
PATTERNS = {
    "react": {
        "alpha": 0.08,
        "use_when": ["exploration", "uncertain"],
        "overhead": 1.2
    },
    "reflection": {
        "alpha": 0.12,
        "use_when": ["quality_critical", "complex"],
        "overhead": 1.5
    },
    "planning": {
        "alpha": 0.15,
        "use_when": ["multi_step", "structured"],
        "overhead": 1.3
    }
}

def select_pattern(task: Task) -> str:
    for pattern_name, pattern in PATTERNS.items():
        if any(tag in task.tags for tag in pattern["use_when"]):
            return pattern_name
    
    return "simple"  # Без паттерна


def apply_pattern_bonus(
    base_success: float,
    pattern: str
) -> float:
    if pattern in PATTERNS:
        return base_success + PATTERNS[pattern]["alpha"]
    return base_success
```

---

## x₁₅: Evaluation & Benchmarking

### Определение
$$\hat{S}(x) = \alpha_{eval} \cdot S_{measured}(x) + (1 - \alpha_{eval}) \cdot S_{predicted}(x)$$

### Benchmarks
| Benchmark | Значение |
|-----------|---------|
| GAIA | 0.745 |
| SWE-bench | 0.15 |
| WebArena | 0.80 |
| RLI | 0.025 |
| ARC-AGI | 0.30 |

### ДЕЙСТВИЕ: Калибровать предсказания по бенчмаркам

---

## x₁₆: Continual Learning

### Определение
$$K_{cl}(t) = 1 - e^{-\lambda_{cl} \cdot N_{tasks}}$$

### Влияние на S
$$\Delta S_{cl} = \gamma_{cl} \cdot K_{cl} \cdot S(x)$$

### Forgetting
$$S_{cl}(x) = S(x) \cdot (1 - \rho \cdot e^{-\lambda \cdot t})$$

### Transfer
$$\Delta S_{transfer} = \gamma_{transfer} \cdot \text{TaskSimilarity}(t_{new}, t_{past}) \cdot K_{past}$$

### ДЕЙСТВИЕ: Определить переносимость навыков между задачами

### ПСЕВДОКОД
```python
def compute_continual_learning_benefit(
    agent: AgentState,
    new_task: Task
) -> float:
    # Knowledge level
    N_tasks = agent.total_completed_tasks
    lambda_cl = 0.01
    
    K_cl = 1 - math.exp(-lambda_cl * N_tasks)
    
    # Similarity с прошлыми задачами
    similar_tasks = find_similar_tasks(new_task, agent.history)
    
    transfer_benefit = 0
    for similar in similar_tasks:
        similarity = compute_task_similarity(new_task, similar)
        transfer_benefit += similarity * similar.outcome * K_cl
    
    return gamma_cl * transfer_benefit


def compute_forgetting(
    base_success: float,
    time_since_practice: float,
    repetitions: int
) -> float:
    rho = 0.1  # forgetting rate
    decay = math.exp(-time_since_practice / (1 + 0.1 * repetitions))
    
    return base_success * (1 - rho * decay)
```

---

## x₁₇: Inference Optimization

### Определение
$$T_{opt} = T_0 \cdot \prod_o (1 - \delta_o)$$

| Оптимизация | δ_o |
|------------|-----|
| Caching | 0.10 |
| Quantization INT8 | 0.20 |
| Flash Attention | 0.15 |
| Speculative Decoding | 0.30 |
| Batch Processing | 0.25 |

### Cost reduction
$$C_{opt}(x) = C(x) \cdot (1 - \sum_o \gamma_o \cdot O_o)$$

### Quality penalty
$$S_{opt}(x) = S(x) \cdot (1 - \epsilon_{quant} \cdot Q_{quantization})$$

### ДЕЙСТВИЕ: Какие оптимизации применить

### ПСЕВДОКОД
```python
OPTIMIZATIONS = {
    "caching": {"speedup": 0.10, "quality_penalty": 0.0},
    "quantization_int8": {"speedup": 0.20, "quality_penalty": 0.02},
    "flash_attention": {"speedup": 0.15, "quality_penalty": 0.0},
    "speculative_decoding": {"speedup": 0.30, "quality_penalty": 0.01},
    "batch_processing": {"speedup": 0.25, "quality_penalty": 0.0}
}

def select_optimizations(task: Task, agent: AgentState) -> List[str]:
    selected = []
    
    for opt_name, opt in OPTIMIZATIONS.items():
        # Speedup benefit
        time_savings = agent.expected_time * opt["speedup"]
        cost_savings = time_savings * agent.hourly_rate
        
        # Quality penalty cost
        quality_penalty = opt["quality_penalty"]
        quality_cost = quality_penalty * task.price
        
        # ROI
        if cost_savings > quality_cost:
            selected.append(opt_name)
    
    return selected


def apply_optimizations(
    base_time: float,
    base_cost: float,
    optimizations: List[str]
) -> dict:
    time_mult = 1.0
    cost_mult = 1.0
    quality_mult = 1.0
    
    for opt_name in optimizations:
        opt = OPTIMIZATIONS[opt_name]
        time_mult *= (1 - opt["speedup"])
        cost_mult *= (1 - opt["speedup"])  # same as time
        quality_mult *= (1 - opt["quality_penalty"])
    
    return {
        "optimized_time": base_time * time_mult,
        "optimized_cost": base_cost * cost_mult,
        "optimized_quality": quality_mult
    }
```

---

# ЧАСТЬ 14: АТОМАРНАЯ ДЕКОМПОЗИЦИЯ

---

## D*(T) = argmax U(A,θ) - λ·C(A,θ) — Optimal Decomposition

### Формула
$$D^*(T) = \underset{(A, \theta)}{\arg\max} \; \mathbb{I}_{pass}(\Gamma(A)) \cdot \left[ \mathcal{U}(A, \theta) - \lambda \cdot \mathcal{C}(A, \theta) \right]$$

### Входы
```
A     — набор атомарных действий
θ     — параметры декомпозиции
Γ(A)  — compliance для всех действий
U(A,θ) — utility декомпозиции
C(A,θ) — cost декомпозиции
λ     — trade-off coefficient
```

### Выход
```
D* — оптимальная декомпозиция задачи
```

### ДЕЙСТВИЕ: Разбить задачу на атомарные действия

### ПСЕВДОКОД
```python
def decompose_task(task: Task) -> Decomposition:
    # 1. Оценка complexity
    if should_decompose(task):
        # 2. Генерация candidate actions
        candidates = generate_candidate_actions(task)
        
        # 3. Оценка utility и cost для каждого
        evaluated = []
        for action in candidates:
            U = compute_action_utility(action)
            C = compute_action_cost(action)
            evaluated.append((action, U - lambda_tradeoff * C))
        
        # 4. Выбрать лучшую комбинацию
        selected = select_best_combination(evaluated)
        
        # 5. Проверить compliance
        if all(check_compliance(a) for a in selected):
            return Decomposition(actions=selected)
    
    # Не требуется декомпозиция
    return Decomposition(actions=[task])
```

---

## δ(T) = σ(w_δ^T · f(T) + b_δ) — Should Decompose?

### Формула
$$\delta(T) = \sigma(\mathbf{w}_\delta^T \cdot \mathbf{f}(T) + b_\delta)$$

### Признаки
$$\mathbf{f}(T) = [|T|_{words}, \text{complexity}(T), \text{uncertainty}(T), \text{depth}(T), \ldots]$$

### Выход
```
δ(T) ∈ [0, 1]
  δ > 0.7 → DECOMPOSE
  δ < 0.3 → NO DECOMPOSE
  0.3 ≤ δ ≤ 0.7 → SHALLOW DECOMPOSE
```

### ДЕЙСТВИЕ: Решить нужно ли декомпозировать задачу

### ПСЕВДОКОД
```python
def should_decompose(task: Task) -> bool:
    features = extract_features(task)
    # features = [size, complexity, uncertainty, depth, ...]
    
    weights = [0.2, 0.3, 0.2, 0.15, 0.15]  # w_δ
    bias = -0.5  # b_δ
    
    score = sum(w * f for w, f in zip(weights, features)) + bias
    probability = sigmoid(score)
    
    if probability > 0.7:
        return True
    elif probability < 0.3:
        return False
    else:
        return "shallow"  # partial decomposition
```

---

## u(a) = φ(a) × P(success | a, m) × quality(m) — Action Utility

### Формула
$$u(a) = \phi(a) \cdot P(\text{success} | a, m) \cdot \text{quality}(m)$$

### Входы
```
φ(a)           — confidence score действия
P(success|a,m) — вероятность успеха с моделью m
quality(m)     — качество модели
```

### Выход
```
u(a) ∈ [0, 1]
```

### ДЕЙСТВИЕ: Оценить utility отдельного действия

---

## ρ(a_i, a_j) = σ(w_dep^T · [e(a_i); e(a_j)] - b_dep) — Action Correlation

### Формула
$$\rho(a_i, a_j) = \sigma(\mathbf{w}_{dep}^T \cdot [\mathbf{e}(a_i); \mathbf{e}(a_j)] - b_{dep})$$

### Входы
```
e(a_i), e(a_j) — эмбеддинги действий
w_dep          — learned weights
```

### Выход
```
ρ ∈ [0, 1] — корреляция между действиями
```

### ДЕЙСТВИЕ: Определить зависимости между действиями

---

## U(A, θ) = ∏u(a_i) × ∏ρ(a_i, a_j) — Decomposition Utility

### Формула
$$\mathcal{U}(A, \theta) = \prod_{i=1}^{n} u(a_i) \cdot \prod_{(i,j) \in E} \rho(a_i, a_j)$$

### Входы
```
u(a_i)     — utilities отдельных действий
ρ(a_i, a_j) — корреляции (из E — множество зависимостей)
```

### Выход
```
U(A,θ) ∈ [0, 1]
```

### ДЕЙСТВИЕ: Оценить общую utility декомпозиции

---

## C(A, θ) = Σ [α·cost(m_i) + β·latency(m_i) + γ·|c_i|] — Decomposition Cost

### Формула
$$\mathcal{C}(A, \theta) = \sum_{i=1}^{n} \left[\alpha \cdot \text{cost}(m_i) + \beta \cdot \text{latency}(m_i) + \gamma \cdot |c_i|\right]$$

### Входы
```
cost(m_i)    — стоимость модели для действия i
latency(m_i) — latency модели для действия i
|c_i|        — размер контекста для действия i
α, β, γ      — веса
```

### Выход
```
C(A,θ) ∈ [0, ∞) — полная стоимость декомпозиции
```

### ДЕЙСТВИЕ: Рассчитать стоимость декомпозиции

---

## φ(a) = σ(w_φ^T · h(a) + b_φ) — Confidence Score

### Формула
$$\phi(a) = \sigma(\mathbf{w}_\phi^T \cdot \mathbf{h}(a) + b_\phi)$$

### Признаки
$$\mathbf{h}(a) = [\text{type}(a), \text{complexity}(a), \text{context\_relevance}(a), \ldots]$$

### Выход
```
φ(a) ∈ [0, 1] — уверенность в успехе действия
```

### ДЕЙСТВИЕ: Оценить confidence действия

### ПСЕВДОКОД
```python
def compute_confidence(action: Action) -> float:
    features = [
        action.type_score,
        action.complexity_score,
        action.context_relevance,
        action.history_success_rate,
        action.resource_availability
    ]
    
    weights = [0.25, 0.20, 0.25, 0.20, 0.10]
    
    score = sum(w * f for w, f in zip(weights, features))
    
    return sigmoid(score)
```

---

## f*(a) = argmax Softmax(w_f^T · g(a)) — Optimal Format

### Формула
$$f^*(a) = \underset{f \in \mathcal{F}}{\arg\max} \; \text{Softmax}(\mathbf{w}_f^T \cdot \mathbf{g}(a))_f$$

### Опции
```
f ∈ {json, text, markdown, code, binary, uri}
```

### ДЕЙСТВИЕ: Выбрать оптимальный формат вывода

### ПСЕВДОКОД
```python
def select_format(action: Action) -> str:
    features = extract_format_features(action)
    
    FORMAT_WEIGHTS = {
        "json":     [0.8, 0.2, 0.0, 0.0],  # structured data
        "text":     [0.2, 0.8, 0.0, 0.0],  # general text
        "code":     [0.0, 0.0, 0.9, 0.0], # code generation
        "markdown": [0.3, 0.5, 0.2, 0.0], # documentation
        "binary":   [0.0, 0.0, 0.0, 0.9], # file operations
    }
    
    scores = {}
    for fmt, weights in FORMAT_WEIGHTS.items():
        scores[fmt] = sum(w * f for w, f in zip(weights, features))
    
    return max(scores, key=scores.get)
```

---

## c*(a) = argmax [Relevance - λ_c × Cost] — Optimal Context

### Формула
$$c^*(a) = \underset{c \subseteq \mathcal{R}}{\arg\max} \; \text{Score}(a, c)$$

где:
$$\text{Score}(a, c) = \text{Relevance}(a, c) - \lambda_c \cdot \text{Cost}(c)$$

### Входы
```
Relevance = (1/|K|) × Σ BM25(a, c_k) × RRF(k)
Cost(c)   = α_t × tokens(c) + α_l × latency(c) + α_m × memory(c)
```

### Выход
```
c* — оптимальный контекст для действия
```

### ДЕЙСТВИЕ: Выбрать какой контекст включить

### ПРАВИЛО
```
Relevance > λ_c × Cost:
    → Включить контекст
Else:
    → Не включать
```

### ПСЕВДОКОД
```python
def select_context(
    action: Action,
    available_contexts: List[Context],
    lambda_cost: float = 0.1
) -> Context:
    best_context = None
    best_score = float('-inf')
    
    for ctx in available_contexts:
        relevance = compute_relevance(action, ctx)
        cost = compute_context_cost(ctx)
        
        score = relevance - lambda_cost * cost
        
        if score > best_score:
            best_score = score
            best_context = ctx
    
    return best_context


def compute_relevance(action: Action, context: Context) -> float:
    # BM25-style scoring
    return semantic_similarity(action.embedding, context.embedding)


def compute_context_cost(context: Context) -> float:
    alpha_t = 0.001  # per token
    alpha_l = 0.01   # latency
    alpha_m = 0.001  # memory
    
    return (alpha_t * context.token_count + 
            alpha_l * context.latency +
            alpha_m * context.memory_usage)
```

---

## m*(a) = argmax [P(success|a,m) × quality(m) - λ × cost(m)] — Optimal Model

### Формула
$$m^*(a) = \underset{m}{\arg\max} \; P(\text{success} | a, m) \cdot \text{quality}(m) - \lambda_m \cdot \text{API\_cost}(m)$$

### ДЕЙСТВИЕ: Выбрать модель для действия

### ПСЕВДОКОД
```python
def select_model_for_action(
    action: Action,
    available_models: List[Model],
    lambda_cost: float = 0.1
) -> Model:
    best_model = None
    best_score = float('-inf')
    
    for model in available_models:
        # P(success|a,m)
        P_success = model.success_rate * model.action_type_bonus[action.type]
        
        # Quality
        quality = model.quality
        
        # API cost
        cost = model.get_cost(action.token_count)
        
        score = P_success * quality - lambda_cost * cost
        
        if score > best_score:
            best_score = score
            best_model = model
    
    return best_model
```

---

# СВОДНАЯ ТАБЛИЦА: ФОРМУЛА → ДЕЙСТВИЕ

| ID | Формула | ДЕЙСТВИЕ | Правило |
|----|---------|----------|---------|
| 1 | Φ = (R-C)/T | Оценить profitability | Φ > 0 → profitable |
| 2 | R = P×S×Q | Рассчитать revenue | R > threshold |
| 3 | C = C₀+C_ops+C_risk | Рассчитать cost | C < task.price×0.8 |
| 4 | T = T₀×∏fᵢ | Рассчитать время | T < deadline |
| 5 | S(x) = S₀+Σβᵢxᵢ+Σγᵢⱼxᵢxⱼ | Success Rate с факторами | S > quality_threshold |
| 6 | Q = αQ_comp+βQ_acc+γQ_full+δQ_time | Quality score | Q > 0.7 |
| 7 | Q_comp = cov/total | Полнота | Q_comp > 0.8 |
| 8 | Q_acc = 1-KL | Accuracy | Q_acc > 0.85 |
| 9 | Q_time = 1-min(...) | Timeliness | Q_time > 0.9 |
| 10 | Ψ = P_fail×(C_direct+C_rep) | Risk assessment | Ψ < max_risk |
| 11 | P_fail = P_base×modifiers | Failure probability | P_fail < 0.3 |
| 12 | P_cascade = 1-∏(1-pᵢ) | Cascade risk | P_cascade < 0.5 |
| 13 | P_risk_final = P_fail×∏(1-...) | Risk after guardrails | P_risk_final < P_fail |
| 14 | Υ = Σγᵢ×componentᵢ | Reputation score | Υ > 0.7 |
| 15 | R_bayesian = (mμ₀+Σrᵢ)/(m+n) | Smoothed rating | R_bayesian > 4.0 |
| 16 | Θ = 1-(1/√N)×σ/(Rmax-Rmin) | Rating confidence | Θ > 0.5 |
| 17 | λ_orders = λ₀×(R/R̄)^β×Θ^γ×... | Order flow | λ_orders > 1.0 |
| 18 | τ_recovery = τ_base/(ρ×(1+βN)) | Recovery time | τ_recovery < acceptable |
| 19 | dR/dt = αQ(1+βV)-γincR | Reputation dynamics | dR/dt > 0 |
| 20 | Γ(action) = 0 or -∞ | Compliance check | Γ = 0 → allow |
| 21 | L_s(t) = L_max×(1-e^(-ηt^γ))+L₀ | Skill level prediction | L_s > task.difficulty |
| 22 | K(t) = K₀+ηΣΔK×(1-K/Kmax) | Knowledge accumulation | K(t) increasing |
| 23 | ZPD = ZPD_base×(...) | Zone of proximal dev | task.difficulty in ZPD |
| 24 | Φ_forget = e^(-t/(S×(1+κn)^ψ)) | Retention factor | Φ_forget > 0.5 |
| 25 | H = F_rein/F_bal | Homeostasis | H in [0.9, 1.1] |
| 26 | A = ΔΦ_recov/ΔΦ_loss | Adaptability | A > 1.0 |
| 27 | VoI = E[Φ\|info]-E[Φ] | Value of info | VoI > info_cost |
| 28 | U = Σλᵢ×componentᵢ | Total utility | U > threshold |
| 29 | U_economic = Φ×(1+αΥ) | Economic utility | U_economic > 0 |
| 30 | U_ext = Φ+λΥΥ+αKK+λVoIVoI | Extended utility | U_ext > baseline |
| 31 | λ_cost(t) = λ₀×H/Htarget×(1+αΨΨ) | Cost modulation | Adaptive |
| 32 | Φ_R = Φ×𝕀[Γ=0]×(1+αΥ)-λΨΨ | Routing quality | Φ_R > 0 |
| 33 | Ξ_task = αQ_result-β(O_t+O_c) | Executor assessment | Ξ_task > 0 |
| 34 | C_llm = αQQ+αRR+αCC+αAA | LLM capability | C_llm > threshold |
| 35 | S(m,t) = C_llm/(1+e^(-λ(C-τ))) | LLM Success Rate | S > 0.7 |
| 36 | Q(m) = Qmax×C_llm/(1+γ(1-C)) | LLM Throughput | Q > baseline |
| 37 | ΔS_memory = β₀+β₁M+β₂M² | Memory benefit | ΔS > memory_cost |
| 38 | ΔS_multi = α₀+α₁logN+α₂N/(N+β) | Multi-agent benefit | N=4-8 optimal |
| 39 | ΔS_prompt = β₁Q+β₂Q² | Prompt benefit | Q_p > 0.5 |
| 40 | G_eff = ∏(1-p_risk×(1-Gᵢ)) | Guardrails effectiveness | G_eff > 0.8 |
| 41 | S_reason = S+βlog(1+T_think/T_base) | Reasoning benefit | ROI > 1 |
| 42 | T_reason = T×(1+0.25×T_think/T_base) | Reasoning time cost | T within budget |
| 43 | S_pattern = S+ΣαₚPₚ | Pattern bonus | Apply best pattern |
| 44 | K_cl = 1-e^(-λN) | Knowledge from CL | K_cl increasing |
| 45 | S_cl = S×(1-ρe^(-λt)) | Forgetting penalty | S_cl acceptable |
| 46 | ΔS_transfer = γ×Similarity×K | Transfer learning | Similarity > 0.7 |
| 47 | T_opt = T₀×∏(1-δₒ) | Optimized time | T_opt < T |
| 48 | C_opt = C×(1-ΣγₒOₒ) | Optimized cost | C_opt < C |
| 49 | S_opt = S×(1-εQ) | Optimization penalty | Acceptable |
| 50 | D* = argmax U-λC | Optimal decomposition | Max U-λC |
| 51 | δ(T) = σ(w·f(T)+b) | Should decompose? | δ > 0.7 → yes |
| 52 | u(a) = φ×P(success|m)×quality | Action utility | u > threshold |
| 53 | ρ(aᵢ,aⱼ) = σ(w·[eᵢ;eⱼ]-b) | Action correlation | ρ > 0.5 → depends |
| 54 | U(A) = ∏u(aᵢ)×∏ρ(aᵢ,aⱼ) | Decomposition utility | U(A) > baseline |
| 55 | C(A) = Σ(αcost+βlat+γ|c|) | Decomposition cost | C(A) < budget |
| 56 | φ(a) = σ(w·h(a)+b) | Action confidence | φ > 0.5 |
| 57 | f*(a) = argmax Softmax(w·g(a)) | Optimal format | Based on action type |
| 58 | c*(a) = argmax [Rel-λCost] | Optimal context | Rel > λ×Cost |
| 59 | m*(a) = argmax [P×Q-λcost] | Optimal model | Max P×Q-λcost |

---

*Документ создан: 2026-07-08*
*Версия: 1.0*
*Статус: Готов для имплементации*
