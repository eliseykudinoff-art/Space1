# 🏗️ Архитектура системы управления AI-агента

## Логическая модель: Функции, потоки, иерархия решений

---

## 1. Философия архитектуры

### 1.1 Принцип разделения concerns

Согласно вашим наблюдениям, текущая модель смешивает разнородные функции:
- **Экономические** (прибыль, стоимость) — одно domain
- **Операционные** (успешность, время) — другое domain  
- **Комплаенс** (правила, риски) — третье domain
- **Эволюционные** (обучение, рост) — четвёртое domain

**Предложение:** Каждый domain получает **собственную функцию** с чёткой зоной ответственности. Они взаимодействуют через интерфейсы, но не смешиваются в одной формуле.

### 1.2 Иерархия уровней управления

```
┌─────────────────────────────────────────────────────────────┐
│                    МЕТА-УРОВЕНЬ (Mission)                   │
│         Идентичность, Принципы, Граничные условия           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              СТРАТЕГИЧЕСКИЙ УРОВЕНЬ (Orchestrator)          │
│     Планирование, Распределение ресурсов, Диверсификация    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 ТАКТИЧЕСКИЙ УРОВЕНЬ (Agent)                 │
│        Выбор задач, Декомпозиция, Выполнение, Коррекция      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   ОПЕРАЦИОННЫЙ УРОВЕНЬ (API)                │
│              Атомарные действия, Вызовы, Метрики             │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Карта функций по доменам

### 2.1 Таксономия функций

| Уровень | Домен | Функция | Ключевая? | Тип |
|---------|-------|---------|-----------|-----|
| **Meta** | Identity | `M(·)` — Миссия | ✅ Ключевая | Набор правил |
| **Meta** | Compliance | `Γ(·)` — Граничные условия | ✅ Ключевая | Hard constraints |
| **Strategic** | Economy | `Φ(·)` — Прибыль | ✅ Ключевая | Objective |
| **Strategic** | Reputation | `Υ(·)` — Репутация | ✅ Ключевая | Objective |
| **Strategic** | Evolution | `Ω(·)` — Обучение/Рост | 📋 Вторичная | Objective |
| **Tactical** | Quality | `Q(·)` — Качество результата | ✅ Ключевая | Constraint |
| **Tactical** | Risk | `Ψ(·)` — Оценка риска | ✅ Ключевая | Objective |
| **Tactical** | Error | `E(·)` — Минимизация ошибок | ❓ Под вопросом | Objective |
| **Operational** | Information | `VoI(·)` — Ценность информации | ✅ Ключевая | Heuristic |
| **Operational** | Uncertainty | `H(·)` — Энтропия/Любопытство | 📋 Вторичная | Heuristic |
| **Hidden** | Calibration | `B(·)` — Байесовская оптимизация | 🔧 Скрытая | Meta-learning |

---

## 3. Детальная спецификация функций

### 3.1 МЕТА-УРОВЕНЬ (Непосредственно не управляет, но ограничивает)

#### M(·): Функция Миссии (Identity)

```python
class MissionFunction:
    """
    Не вычисляет значение — определяет принципы агента.
    Это immutable на уровне сессии.
    """
    
    PRINCIPLES = {
        "survival": True,           # Агент должен выживать
        "autonomy": True,           # Стремление к автономии  
        "truth": True,              # Приоритет истины
        "efficiency": True,        # Оптимизация ресурсов
    }
    
    def get_weights(self) -> Dict[str, float]:
        """
        Возвращает веса λ, μ, ν для функции U
        Эти веса определяются миссией, а не оптимизируются
        """
        return {
            "profit_weight": 0.3,
            "reputation_weight": 0.25,
            "evolution_weight": 0.2,
            "quality_weight": 0.25,
        }
```

#### Γ(·): Функция Граничных Условий (Compliance)

> **Ваше предложение:** Выделить в отдельную модель — **ПРИНЯТО**

```python
class ComplianceFunction:
    """
    Описывает hard constraints — нарушение = смерть агента.
    Эта функция НЕ оптимизируется, а проверяется.
    """
    
    def evaluate(self, action: Action, context: Context) -> ComplianceResult:
        checks = {
            "legal": self.check_legal_compliance(action),      # Законы
            "api_provider": self.check_api_limits(action),     # Лимиты API
            "cloud_resources": self.check_cloud_quota(action), # Квоты облака
            "financial": self.check_financial_limits(action),  # Бюджет
            "security": self.check_security_rules(action),      # Безопасность
        }
        
        failed = [k for k, v in checks.items() if not v]
        
        if failed:
            return ComplianceResult(
                status="REJECT",
                reason=f"Compliance failure: {failed}",
                severity="CRITICAL"
            )
        
        return ComplianceResult(status="PASS", severity="OK")
    
    # Примеры правил:
    RULES = {
        "max_api_cost_per_task": 5.0,      # $
        "max_file_writes": 10,             # шт
        "blocked_domains": ["evil.com"],    # чёрный список
        "data_retention_days": 30,         # GDPR
        "rate_limit_per_minute": 60,       # API
    }
```

**Математическая формализация:**

$$\Gamma(action) = \begin{cases} 0, & \text{if } \forall r \in Rules: r(action) = \text{True} \\ -\infty, & \text{otherwise} \end{cases}$$

> ⚠️ **Ключевое отличие:** Это не штраф, а **absolutny veto**. Если Γ = 0, действие не рассматривается вообще.

---

### 3.2 СТРАТЕГИЧЕСКИЙ УРОВЕНЬ (Оркестратор)

#### Φ(·): Функция Прибыли (Economy)

```python
class ProfitFunction:
    """
    Основная экономическая функция — максимизация (R - C) / T
    """
    
    def compute(self, x: Vector, params: ModelParams) -> float:
        S = self.compute_success_rate(x, params)
        Q = self.compute_throughput(x, params)
        C = self.compute_cost(x, params)
        T = self.compute_time(x, params)
        P = params.price_per_task
        
        R = P * Q * S
        return (R - C) / T
```

#### Υ(·): Функция Репутации

> **Ваше предложение:** Выделить отдельно — **ПРИНЯТО с уточнениями**

```python
class ReputationFunction:
    """
    Репутация = долгосрочный капитал агента.
    Влияет на: частоту заказов, допустимую цену, доступ к премиум-задачам.
    """
    
    def compute(self, history: TaskHistory) -> float:
        components = {
            # Средний рейтинг (0-5 → 0-1)
            "rating": self.avg_rating / 5,
            
            # Retention rate (возвратные клиенты)
            "retention": self.return_client_rate,
            
            # Положительные отзывы / всего
            "positive_ratio": self.positive_feedbacks / self.total_tasks,
            
            # Скорость реакции
            "response_speed": 1 - self.avg_delay / self.SLA_target,
            
            # Долгосрочный тренд
            "momentum": self.compute_momentum(),
        }
        
        weights = {
            "rating": 0.30,
            "retention": 0.25,
            "positive_ratio": 0.20,
            "response_speed": 0.15,
            "momentum": 0.10,
        }
        
        return sum(w * components[k] for k, w in weights.items())
```

**Формула:**

$$\Upsilon = \gamma_1 \cdot \bar{R} + \gamma_2 \cdot \tau_{ret} + \gamma_3 \cdot \frac{N^+}{N} + \gamma_4 \cdot (1 - \delta) + \gamma_5 \cdot \frac{d\Upsilon}{dt}$$

**Синергия с Φ:**

$$U_{economic} = \Phi + \alpha_{rep} \cdot \Upsilon \cdot \Phi$$

---

#### Ω(·): Функция Эволюции/Обучения

> **Ваше предложение:** Выделить отдельно — **ПРИНЯТО**

```python
class EvolutionFunction:
    """
    Функция долгосрочного роста агента.
    Влияет на: сложность задач, скорость обучения, навыки.
    """
    
    def compute(self, agent_state: AgentState, time: float) -> float:
        # Компоненты роста:
        components = {
            # Накопленные знания (K)
            "knowledge": self.knowledge_accumulation(),
            
            # Сложность выполненных задач (растёт или падает)
            "complexity_gradient": self.task_complexity_trend(),
            
            # Transfer learning (перенос навыков)
            "transfer_benefit": self.transfer_learning_gains(),
            
            # Автономия (способность работать без помощи)
            "autonomy_level": self.autonomy_metric(),
            
            # Эмерджентность (новые способности)
            "emergence_score": self.emergence_detection(),
        }
        
        return sum(components.values()) / len(components)
    
    def knowledge_accumulation(self) -> float:
        """
        K(t) = K₀ + η·Σ(ΔK·(1 - K/K_max))
        """
        K_0 = self.initial_knowledge
        K_max = self.max_knowledge
        eta = self.learning_rate
        
        accumulated = sum(
            delta_k * (1 - k / K_max)
            for delta_k, k in self.learning_events
        )
        
        return K_0 + eta * accumulated
```

**Связь с Compliance:** Чем сложнее задачи, тем жёстче требования → Γ становится важнее.

---

### 3.3 ТАКТИЧЕСКИЙ УРОВЕНЬ (Агент-Исполнитель)

#### Q(·): Функция Качества

```python
class QualityFunction:
    """
    Оценивает качество результата.
    Используется агентом для self-correction.
    """
    
    def compute(self, result: Result, task: Task) -> float:
        dimensions = {
            # Полнота (все ли требования выполнены)
            "completeness": self.check_completeness(result, task.requirements),
            
            # Точность (нет ли фактических ошибок)
            "accuracy": self.check_accuracy(result, task.facts),
            
            # Формат (соответствие требованиям)
            "format": self.check_format(result, task.format_spec),
            
            # Своевременность (в рамках SLA)
            "timeliness": 1 - self.delay_hours / task.sla_hours,
        }
        
        weights = {"completeness": 0.35, "accuracy": 0.35, "format": 0.15, "timeliness": 0.15}
        
        return sum(w * dimensions[k] for k, w in weights.items())
```

#### Ψ(·): Функция Риска

> **Уже определена в модели, сохраняем**

```python
class RiskFunction:
    """
    Ψ(task) = P_fail · (C_direct + C_reputation)
    
    Оценивает взвешенные потери от провала.
    """
    
    def compute(self, task: Task, agent_state: AgentState) -> float:
        p_fail = self.estimate_failure_probability(task, agent_state)
        
        c_direct = (
            task.cost_budget +                    # Прямые затраты
            self.estimate_retry_cost(task)        # Стоимость переделки
        )
        
        c_reputation = (
            self.reputation_sensitivity *          # Насколько риск репутации
            self.reputation_damage_if_fail(task)  # Урон репутации
        )
        
        return p_fail * (c_direct + c_reputation)
```

#### E(·): Функция Минимизации Ошибок

> **Ваше предложение:** Под вопросом — **ПРЕДЛОЖЕНИЕ**

```python
class ErrorMinimizationFunction:
    """
    ⚠️ ЭТО ПОД ВОПРОСОМ
    
    Альтернативные интерпретации:
    
    1. E — это часть Q (quality) и Ψ (risk)
       E(δ) = Q(1 - error_rate) - Ψ(error_rate)
       
    2. E — это meta-функция для self-correction
       E определяет когда агент должен остановиться и переделать
       
    3. E — redundant, убираем
       Q и Ψ уже покрывают ошибки
    """
    
    def should_retry(self, attempt: Attempt, task: Task) -> bool:
        """
        Функция решения: делать retry или нет.
        Это bridge между Quality и Risk.
        """
        quality = self.quality.compute(attempt.result, task)
        risk = self.risk.compute(task, attempt)
        
        # Retry если: качество ниже порога И риск ретрая приемлем
        return quality < self.quality_threshold and risk < self.max_risk
        
    # Моё предложение: E — это НЕ отдельная функция
    # E = f(Q, Ψ) — уже учтено в других функциях
    # Но E полезна как diagnostic для аналитики
```

**Рекомендация:** E(·) — **diagnostic function**, не управляющая. Убираем из списка ключевых функций, оставляем как метрику.

---

### 3.4 ОПЕРАЦИОННЫЙ УРОВЕНЬ (Атомарные действия)

#### VoI(·): Функция Ценности Информации

```python
class ValueOfInformationFunction:
    """
    VoI = E[Φ | with info] - E[Φ | without info]
    
    Решает: нужно ли запрашивать дополнительную информацию?
    """
    
    def compute(self, candidate_info: Info, task: Task, current_phi: float) -> float:
        # Симулируем: что будет если получим информацию?
        with_info = self.simulate_execution(task, additional_info=candidate_info)
        
        # Симулируем: что будет без информации?
        without_info = self.simulate_execution(task, additional_info=None)
        
        voi = with_info.expected_phi - without_info.expected_phi
        
        return voi
    
    def should_acquire(self, voi: float, acquisition_cost: float) -> bool:
        """
        Решение: покупать информацию или нет.
        """
        return voi > acquisition_cost
```

#### H(·): Функция Энтропии/Любопытства

```python
class CuriosityFunction:
    """
    H(T) = -Σ P(d|T) · log₂ P(d|T)
    
    Измеряет неопределённость задачи.
    Высокая энтропия = задача непонятна.
    
    ⚠️ "Любопытство" — это метафора для:
    - Exploration vs Exploitation
    - Should I try something new?
    - Risk of novel approaches
    """
    
    def compute_entropy(self, task: Task) -> float:
        """
        Энтропия по распределению возможных декомпозиций
        """
        decompositions = self.get_possible_decompositions(task)
        
        probs = [d.probability for d in decompositions]
        entropy = -sum(p * log2(p) for p in probs if p > 0)
        
        return entropy
    
    def compute_curiosity(self, task: Task, agent_state: AgentState) -> float:
        """
        Любопытство = энтропия - знакомость
        
        Если задача непонятна (высокая H) И мы её ещё не видели
        (низкая familiarity) = высокое любопытство
        """
        h_task = self.compute_entropy(task)
        familiarity = agent_state.get_familiarity(task)
        
        curiosity = h_task * (1 - familiarity)
        
        return curiosity
    
    def should_explore(self, curiosity: float, exploitation_threshold: float) -> bool:
        """
        Exploration vs Exploitation decision
        """
        return curiosity > exploitation_threshold
```

---

### 3.5 СКРЫТЫЙ УРОВЕНЬ (Meta-learning, не управляет напрямую)

#### B(·): Байесовская Оптимизация Весов

> **Ваше уточнение:** Скрытая функция, не влияет на решения напрямую

```python
class BayesianWeightOptimizer:
    """
    B(·) — обновляет параметры модели на основе наблюдений.
    Работает в фоне, не блокирует основной flow.
    
    Используется для:
    - Калибровки коэффициентов β, γ, δ
    - Адаптации весов под конкретного клиента
    - Обнаружения concept drift
    """
    
    def update_weights(self, observed_outcomes: List[Outcome], params: Params):
        """
        Байесовское обновление: P(θ|observations) ∝ P(observations|θ) · P(θ)
        """
        for param_name, param_dist in params.items():
            # Likelihood
            likelihood = self.compute_likelihood(observed_outcomes, param_name)
            
            # Prior
            prior = param_dist.prior
            
            # Posterior
            posterior = likelihood * prior
            param_dist.update(posterior)
    
    def suggest_next_optimization(self, params: Params) -> str:
        """
        Рекомендует: какой фактор оптимизировать дальше?
        Returns: "x4 (memory)", "x7 (prompt)", etc.
        """
        # Marginal improvement per unit of effort
        candidates = self.estimate_roi_per_factor(params)
        return max(candidates, key=lambda x: x[1])[0]
```

---

## 4. Интегрированная Скаляризованная Функция

### 4.1 Иерархия принятия решений

```python
def make_decision(task: Task, agent_state: AgentState) -> Decision:
    """
    Иерархия:
    1. Проверь Γ (Compliance) — если FAIL, REJECT без обсуждений
    2. Проверь M (Mission alignment) — если misaligned, REJECT
    3. Вычисли все функции: Φ, Υ, Q, Ψ, VoI, H
    4. Скомбинируй в U
    5. Реши: REJECT / CLARIFY / EXECUTE
    """
    
    # === STEP 1: HARD CONSTRAINTS ===
    compliance = ComplianceFunction().evaluate(task, agent_state)
    if not compliance.passed:
        return Decision.REJECT(reason=compliance.reason, level="HARD")
    
    # === STEP 2: MISSION ALIGNMENT ===
    if not MissionFunction().is_aligned(task):
        return Decision.REJECT(reason="Mission misalignment", level="HARD")
    
    # === STEP 3: COMPUTE ALL FUNCTIONS ===
    phi = ProfitFunction().compute(task, agent_state)
    upsilon = ReputationFunction().compute(agent_state.history)
    omega = EvolutionFunction().compute(agent_state, time_now)
    quality = QualityFunction().compute(task)
    psi = RiskFunction().compute(task, agent_state)
    voi = ValueOfInformationFunction().compute(task)
    h = CuriosityFunction().compute_entropy(task)
    
    # === STEP 4: COMBINE INTO U ===
    weights = MissionFunction().get_weights()
    
    U = (
        weights["profit"] * phi +
        weights["reputation"] * upsilon +
        weights["evolution"] * omega
    )
    
    # Quality and Risk as constraints/bounded terms
    U = apply_quality_constraint(U, quality, threshold=0.7)
    U = apply_risk_penalty(U, psi, max_psi=5.0)
    
    # VoI decision
    if voi > 0 and h > h_max:
        return Decision.CLARIFY(task, info_needed=voi)
    
    # === STEP 5: FINAL DECISION ===
    if U > 0:
        return Decision.EXECUTE(task, utility=U)
    else:
        return Decision.REJECT(reason=f"U={U:.2f} < 0", level="SOFT")
```

### 4.2 Математическая запись

$$\boxed{U = \underbrace{\lambda_\phi \cdot \Phi}_{\text{Прибыль}} + \underbrace{\lambda_\upsilon \cdot \Upsilon}_{\text{Репутация}} + \underbrace{\lambda_\omega \cdot \Omega}_{\text{Эволюция}}}$$

subject to:
$$\Gamma(action) = 0 \quad \text{(hard constraint)}$$
$$Q(result) \geq q_{min} \quad \text{(soft constraint)}$$
$$\Psi(task) \leq \psi_{max} \quad \text{(risk budget)}$$

---

## 5. Граф взаимодействия функций

```
╔══════════════════════════════════════════════════════════════════════════╗
║                           МЕТА-УРОВЕНЬ                                    ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║    ┌─────────────────┐         ┌─────────────────┐                       ║
║    │   M(·) Mission  │         │  Γ(·) Complianc│                       ║
║    │  ─────────────  │         │  ─────────────  │                       ║
║    │ Определяет:     │         │ VETO на любые  │                       ║
║    │  • λ_φ, λ_υ, λ_ω│         │  действий      │                       ║
║    │  • q_min, ψ_max │         │  если FAIL     │                       ║
║    │  • приоритеты   │         │                │                       ║
║    └────────┬────────┘         └───────┬─────────┘                       ║
║             │                         │                                  ║
║             │ weights                 │ hard constraint                  ║
║             ▼                         ▼                                  ║
╠══════════════════════════════════════════════════════════════════════════╣
║                         СТРАТЕГИЧЕСКИЙ УРОВЕНЬ                            ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐               ║
║    │ Φ(·) Прибыль │    │ Υ(·) Репут. │    │ Ω(·) Эвол.  │               ║
║    │ ────────────│    │ ────────────│    │ ────────────│               ║
║    │ (R-C)/T     │    │ rating+     │    │ K(t)+       │               ║
║    │             │    │ retention+  │    │ complexity+ │               ║
║    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘               ║
║           │                   │                   │                       ║
║           └───────────────────┼───────────────────┘                       ║
║                               │                                           ║
║                               ▼                                           ║
║                    ┌──────────────────┐                                   ║
║                    │   U = Σ λ·F      │                                   ║
║                    │  Скаляризованная  │                                   ║
║                    │    полезность     │                                   ║
║                    └────────┬─────────┘                                   ║
║                             │                                             ║
╠══════════════════════════════════════════════════════════════════════════╣
║                          ТАКТИЧЕСКИЙ УРОВЕНЬ                               ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐               ║
║    │ Q(·) Качество│    │ Ψ(·) Риск    │    │ B(·) Bayesian│               ║
║    │ ────────────│    │ ────────────│    │ ────────────│               ║
║    │ completeness │    │ P_fail·    │    │ Обновление   │               ║
║    │ accuracy     │    │   (Cdir+   │    │ весов        │               ║
║    │              │    │    Crep)   │    │ (скрытый)    │               ║
║    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘               ║
║           │                   │                   │                       ║
║           │ constraint       │ penalty           │ feedback              ║
║           └──────────────────┼───────────────────┘                       ║
║                              │                                             ║
╠══════════════════════════════════════════════════════════════════════════╣
║                        ОПЕРАЦИОННЫЙ УРОВЕНЬ                                ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║    ┌──────────────┐    ┌──────────────┐                                  ║
║    │VoI(·) Ценность│    │ H(·) Энтропия│                                  ║
║    │ ────────────│    │ ────────────│                                  ║
║    │ E[Φ|w] -    │    │ Неопределён- │                                  ║
║    │   E[Φ|wo]   │    │ ность задачи │                                  ║
║    └──────┬───────┘    └──────┬───────┘                                  ║
║           │                   │                                           ║
║           │ CLARIFY decision │ Curiosity                                 ║
║           └──────────────────┴──────────────────────────────────────────  ║
║                              │                                             ║
║                              ▼                                             ║
║                    ┌──────────────────┐                                   ║
║                    │   D(T) = ?       │                                   ║
║                    │ REJECT/EXECUTE/ │                                   ║
║                    │ CLARIFY         │                                   ║
║                    └──────────────────┘                                   ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
```

---

## 6. Ключевые vs Вторичные функции

### 6.1 Ключевые функции (управляющие)

| Функция | Роль | Влияет на |
|---------|------|----------|
| **Γ(·)** | Veto | Любое решение |
| **M(·)** | Принципы | Веса всех λ |
| **Φ(·)** | Прибыль | REJECT/EXECUTE |
| **Υ(·)** | Репутация | Долгосрочный U |
| **Q(·)** | Качество | Self-correction |
| **Ψ(·)** | Риск | REJECT/EXECUTE |

### 6.2 Вторичные функции ( advisory)

| Функция | Роль | Влияет на |
|---------|------|----------|
| **Ω(·)** | Эволюция | Стратегию, λ_ω |
| **VoI(·)** | Информация | CLARIFY |
| **H(·)** | Неопределённость | Curiosity |
| **B(·)** | Калибровка | Все коэффициенты |

### 6.3 Диагностические (не управляют)

| Функция | Роль | Использование |
|---------|------|---------------|
| **E(·)** | Ошибки | Аналитика |
| **Autonomy** | Автономия | Метрика зрелости |

---

## 7. Что определяет поведение агента

### 7.1 Иерархия влияния

```
1. Γ(·) Compliance — ОПРЕДЕЛЯЕТ (hard constraint)
   └─ Никакая оптимизация не важна, если Γ = 0
   
2. M(·) Mission — ОПРЕДЕЛЯЕТ (soft constraints, веса)
   └─ Mission определяет ЧТО агент считает важным
   
3. Φ(·), Υ(·), Ω(·) — ОПРЕДЕЛЯЮТ (utility decomposition)
   └─ Взвешенная сумма даёт итоговое решение
   
4. Q(·), Ψ(·) — МОДИФИЦИРУЮТ (soft constraints)
   └─ Q ниже порога → penalty
   └─ Ψ выше порога → REJECT
   
5. VoI(·), H(·) — КОНДИЦИОНИРУЮТ (when-to-act)
   └─ Высокая VoI + неопределённость → CLARIFY
```

### 7.2 Что агент контролирует напрямую

| Что | Как | Функция |
|-----|-----|---------|
| Выбор задачи | REJECT/EXECUTE | D(T) |
| Декомпозиция | Как разбить | δ*() |
| Ресурсы | Сколько потратить | c*() |
| Модель | Какую LLM | m*() |
| Retry | Делать ли заново | E() |

### 7.3 Что агент НЕ контролирует

| Что | Кто | Как |
|-----|-----|-----|
| Рыночная цена | Клиент | P |
| Правила | Провайдеры | Γ() |
| Репутация | Клиенты | Υ() |
| Результат | LLM | Stochastic |

---

## 8. Решения по открытым вопросам

### 8.1 Ваши вопросы → Мои рекомендации

| Вопрос | Рекомендация | Обоснование |
|--------|--------------|-------------|
| **Γ(·) отдельно?** | ✅ ДА | Compliance — это не optimization, это VETO. Смешивание с Φ语义чески некорректно |
| **Υ(·) отдельно?** | ✅ ДА | Репутация — долгосрочный asset. Имеет свою динамику, отличную от Φ |
| **Ω(·) отдельно?** | ✅ ДА | Эволюция — на другой timescales. Не должна "конкурировать" с Φ за веса |
| **E(·) отдельно?** | ❌ НЕТ | E = f(Q, Ψ). Диагностическая, не управляющая |
| **B(·) скрытая?** | ✅ ДА | B(·) обновляет параметры других функций. Не управляет напрямую |
| **H(·) и любопытство?** | ✅ ДА, в VoI | Информационная теория = хорошая основа для CLARIFY решения |

### 8.2 Новые предложения

| Предложение | Статус | Комментарий |
|-------------|--------|-------------|
| **Self-Assessment** | 📋 Добавить | Метрика зрелости агента: A(t) |
| **Maturity Index** | 📋 Добавить | M = f(Φ, Ω, autonomy) |
| **Entropy penalty** | ❓ Под вопросом | Может быть частью VoI |

---

## 9. Финальная архитектура: 7 управляющих функций

```
┌─────────────────────────────────────────────────────────────────┐
│                    7 КЛЮЧЕВЫХ ФУНКЦИЙ                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   1. Γ(·) — COMPLIANCE        [VETO, Hard constraint]          │
│      └─ Legal, API limits, Security, Financial                  │
│                                                                 │
│   2. M(·) — MISSION           [Principles, веса λ]               │
│      └─ Identity, survival, autonomy, truth                      │
│                                                                 │
│   3. Φ(·) — PROFIT            [Economic objective]              │
│      └─ (R - C) / T, Core utility                               │
│                                                                 │
│   4. Υ(·) — REPUTATION        [Long-term asset]                │
│      └─ Rating, retention, feedback                             │
│                                                                 │
│   5. Ω(·) — EVOLUTION         [Growth, learning]                │
│      └─ Knowledge, complexity, emergence                        │
│                                                                 │
│   6. Q(·) — QUALITY           [Result assessment]               │
│      └─ Completeness, accuracy, format                          │
│                                                                 │
│   7. Ψ(·) — RISK              [Loss prevention]                 │
│      └─ P_fail · (C_direct + C_rep)                             │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                      ВТОРИЧНЫЕ ФУНКЦИИ                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   8. VoI(·) — VALUE OF INFO    [CLARIFY decision]               │
│   9. H(·) — ENTROPY           [Uncertainty measure]             │
│  10. B(·) — BAYESIAN OPT      [Hidden, weight calibration]     │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                       ДИАГНОСТИКА                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  11. E(·) — ERROR RATE        [Analytics, not control]         │
│  12. A(·) — AUTONOMY          [Maturity metric]                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 10. Интеграция с существующими документами

### Что сохраняется

| Документ | Что остаётся | Изменения |
|----------|-------------|-----------|
| `capability.txt` | 17 факторов, β, δ коэффициенты | Γ(·) выделен отдельно |
| `atomic_decomposition_model.md` | δ*, f*, c*, m*, p*, φ* | Интеграция с новыми функциями |
| `UNIFIED_MODEL.md` | Синергии x₁+x₇ | Добавлены Γ, Υ, Ω, VoI |

### Что добавляется

| Новый элемент | Описание |
|--------------|----------|
| `ComplianceLayer` | Γ(·), правила, VETO логика |
| `ReputationModule` | Υ(·), рейтинг, retention |
| `EvolutionTracker` | Ω(·), knowledge accumulation |
| `CuriosityEngine` | H(·), VoI, exploration |

---

## 11. Следующие шаги

```
□ Реализовать Γ(·) — Compliance Layer (priority: CRITICAL)
□ Интегрировать Υ(·) в существующую архитектуру
□ Формализовать Ω(·) — функцию эволюции
□ Проверить: как Γ влияет на существующие тесты?
□ Реализовать VoI + H(·) для CLARIFY решения
□ Добавить Bayesian weight optimization (B)
□ Написать unit-тесты для каждой функции
□ Валидировать на синтетических данных
```

---

*Документ подготовлен: 2026-07-05*
*Автор: OpenHands Agent*
*Версия: 1.0 — Полная архитектура управляющих функций*