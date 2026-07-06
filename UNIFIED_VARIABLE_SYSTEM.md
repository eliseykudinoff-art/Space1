# 📐 Единая система переменных и функций

## Проблема: Дублирование и неоднозначность

### Текущее состояние

```
В разных документах и уровнях:
─────────────────────────────────────────────────────────────────
Переменная "C" (Cost/Деньги):
├─ В Φ(x) = (R - C) / T          → какой C? Общий? API? opportunity?
├─ В S(x) = ... + C_failure       → другой C?
├─ В atomic_decomposition_model   → ресурсы r
└─ В VoI                          → стоимость информации

Переменная "T" (Time/Время):
├─ В Φ(x) = (R - C) / T          → latency? wall-clock? deadline?
├─ В Time Model                   → T(x) = T_base · ∏d_i
├─ В atomic_decomposition_model   → latency API call
└─ В Quality SLA                  → совсем другое T

Переменная "S" (Success):
├─ В Revenue Model                → S(x) success rate
├─ В atomic_decomposition_model   → confidence score φ
└─ В Quality Function Q(·)       → quality metrics
```

**Результат:** Невозможно понять, какая переменная где используется и как связана.

---

## Решение: Единый Глоссарий + Граф Зависимостей

---

## Часть 1: Таксономия переменных

### 1.1 Примитивные переменные (Входы извне)

Эти переменные **не контролируются агентом** — они приходят извне.

| ID | Имя | Описание | Источник |
|----|-----|---------|----------|
| `P_market` | Market Price | Цена задачи на рынке | Клиент/платформа |
| `B_client` | Client Budget | Бюджет клиента | Клиент |
| `T_deadline` | Deadline | Дедлайн задачи | Клиент |
| `L_api_limit` | API Rate Limit | Лимит запросов/минуту | Провайдер API |
| `Q_api_cost` | API Unit Cost | Стоимость/токен | Провайдер API |
| `C_cloud_quota` | Cloud Quota | Квота облака | Облако |
| `R_competitor_price` | Competitor Price | Цена конкурентов | Рынок |
| `S_platform_rate` | Platform Rate | Ставка платформы | Платформа |

### 1.2 Состояние агента (State)

Эти переменные **отражают текущее состояние** — меняются в процессе выполнения.

| ID | Имя | Описание | Тип |
|----|-----|---------|-----|
| `C_spent` | Spent Cost | Потрачено денег | Accumulator |
| `T_elapsed` | Elapsed Time | Прошло времени | Accumulator |
| `N_tasks_completed` | Completed Tasks | Выполнено задач | Counter |
| `N_tasks_failed` | Failed Tasks | Провалено задач | Counter |
| `Φ_historical` | Historical Profit | Историческая прибыль | Memory |
| `Υ_rating` | Current Rating | Текущий рейтинг | Memory |
| `K_knowledge` | Knowledge Level | Уровень знаний | Memory |
| `A_autonomy` | Autonomy Level | Уровень автономии | Memory |
| `L_health` | System Health | Здоровье системы | Diagnostic |

### 1.3 Вычисляемые метрики (Derived)

Эти переменные **вычисляются** из примитивов и состояния.

| ID | Имя | Формула | Описание |
|----|-----|---------|---------|
| `C_remaining` | Remaining Budget | `B_client - C_spent` | Остаток бюджета |
| `T_remaining` | Remaining Time | `T_deadline - T_elapsed` | Остаток времени |
| `S_success_rate` | Success Rate | `N_tasks_completed / (N_tasks_completed + N_tasks_failed)` | Историческая успешность |
| `R_expected` | Expected Revenue | `P_market · S_success_rate` | Ожидаемый доход |
| `Λ_load` | System Load | `T_elapsed / T_deadline` | Нагрузка |
| `Ω_diversity` | Task Diversity | `entropy(task_types)` | Диверсификация |

---

## Часть 2: Функции — чёткие интерфейсы

### 2.1 Нотация: Что является входом, что выходом

```
┌─────────────────────────────────────────────────────────────┐
│                      FUNCTION INTERFACE                      │
├─────────────────────────────────────────────────────────────┤
│  INPUT:   {переменные} → [из какого namespace]             │
│  OUTPUT:  {переменные} → [в какой namespace]                │
│  TYPE:    objective / constraint / diagnostic / policy     │
└─────────────────────────────────────────────────────────────┘
```

---

### 2.2 Уровень MISSION (Политика)

```python
class MissionPolicy:
    """
    ═══════════════════════════════════════════════════════════
    M(·) — ФУНКЦИЯ МИССИИ: Определяет ПОЛИТИКУ агента
    ═══════════════════════════════════════════════════════════
    
    ВХОД:  Примитивы (P_market, B_client, T_deadline)
           Состояние (Φ_historical, Υ_rating, K_knowledge, A_autonomy)
           
    ВЫХОД: Веса {λ_Φ, λ_Υ, λ_Ω, λ_Q, λ_Ψ} — ОТНОСИТЕЛЬНАЯ ВАЖНОСТЬ функций
           Пороги {q_min, ψ_max, c_max} — ГРАНИЦЫ допустимого
           Правила {Γ_rules} — ЧТО НЕЛЬЗЯ
           
    ТИП:   POLICY (не оптимизация, а калибровка)
    
    ═══════════════════════════════════════════════════════════
    """
    
    def calibrate(
        self,
        primitive: PrimitiveState,
        agent_state: AgentState,
        historical: History
    ) -> PolicyParams:
        """
        M(primitive, state) → weights, thresholds, rules
        
        ЭТО НЕ OPTIMIZE — это POLICY CALIBRATION.
        Агент "решает" что ему важно на основе своей миссии.
        """
        
        # === ОТНОШЕНИЕ К ДЕНЬГАМ ===
        # Mission определяет: насколько важна прибыль?
        money_importance = self.compute_money_importance(
            mission=self.mission,
            state=agent_state,
            historical=historical
        )
        
        # === ОТНОШЕНИЕ К ВРЕМЕНИ ===
        # Mission определяет: насколько важна скорость?
        time_importance = self.compute_time_importance(
            mission=self.mission,
            state=agent_state,
            task_constraints=primitive
        )
        
        # === ОТНОШЕНИЕ К РЕПУТАЦИИ ===
        # Mission определяет: готов ли агент рисковать репутацией?
        reputation_importance = self.compute_reputation_importance(
            mission=self.mission,
            state=agent_state
        )
        
        # === ОТНОШЕНИЕ К ОБУЧЕНИЮ ===
        # Mission определяет: важна ли эволюция?
        evolution_importance = self.compute_evolution_importance(
            mission=self.mission,
            state=agent_state,
            historical=historical
        )
        
        # === ОТНОШЕНИЕ К РИСКУ ===
        # Mission определяет: какой риск допустим?
        risk_tolerance = self.compute_risk_tolerance(
            mission=self.mission,
            state=agent_state
        )
        
        # === КАЛИБРОВКА ВЕСОВ ===
        # Все "важности" нормализуются в веса λ
        raw_weights = {
            "profit": money_importance,
            "reputation": reputation_importance,
            "evolution": evolution_importance,
            "time": time_importance,
        }
        
        # Softmax для распределения
        weights = self.normalize_weights(raw_weights)
        
        # === ПОРОГИ ===
        thresholds = {
            "q_min": self.compute_quality_threshold(agent_state, mission),
            "ψ_max": risk_tolerance * self.max_acceptable_loss,
            "c_max": C_remaining * self.safety_margin,
        }
        
        # === Γ RULES ===
        rules = self.compute_compliance_rules(primitive, mission)
        
        return PolicyParams(
            weights=weights,
            thresholds=thresholds,
            rules=rules
        )
    
    def compute_money_importance(self, mission, state, historical) -> float:
        """
        ОТНОШЕНИЕ АГЕНТА К ДЕНЬГАМ
        
        Examples:
        - Startup-mode: "Нужно выжить" → высокая важность денег
        - Growth-mode: "Набираю репутацию" → низкая важность денег  
        - Maintenance-mode: "Устойчивый доход" → средняя важность
        """
        if mission.type == "survival":
            return 0.8
        elif mission.type == "growth":
            return 0.3
        elif mission.type == "maintenance":
            return 0.5
        elif mission.type == "maximize":
            return 1.0
        else:
            return 0.5
    
    def compute_risk_tolerance(self, mission, state) -> float:
        """
        ГОТОВНОСТЬ К РИСКУ
        
        Examples:
        - Conservative agent: 0.2 (максимум 20% потерь)
        - Aggressive agent: 0.7 (готов потерять 70%)
        """
        base_tolerance = {
            "conservative": 0.2,
            "moderate": 0.5,
            "aggressive": 0.8,
        }.get(mission.risk_profile, 0.5)
        
        # Модификация на основе состояния
        # Если агент в хорошем состоянии — может рисковать больше
        if state.Φ_historical > state.break_even:
            modifier = 1.2
        else:
            modifier = 0.8
        
        return min(1.0, base_tolerance * modifier)
```

---

### 2.3 Γ(·) — Compliance Function (VETO)

```python
class ComplianceFunction:
    """
    ═══════════════════════════════════════════════════════════
    Γ(·) — ФУНКЦИЯ КОМПЛАЕНС: Hard VETO
    ═══════════════════════════════════════════════════════════
    
    ВХОД:  Action (предлагаемое действие)
           Rules (из MISSION)
           Primtives (L_api_limit, C_cloud_quota, etc.)
           
    ВЫХОД: PASS / FAIL + reason
           
    ТИП:   CONSTRAINT (не оптимизируется)
    
    ═══════════════════════════════════════════════════════════
    """
    
    def evaluate(
        self,
        action: Action,
        rules: ComplianceRules,
        primitives: PrimitiveState
    ) -> ComplianceResult:
        """
        Γ(action, rules, primitives) → {PASS, FAIL}
        
        Проверяет ВСЕ hard constraints:
        """
        
        checks = []
        
        # === 1. LEGAL COMPLIANCE ===
        if not self.check_legal(action, rules):
            checks.append(ComplianceCheck(
                domain="legal",
                passed=False,
                reason="Action violates legal requirements",
                severity="CRITICAL"
            ))
        
        # === 2. API PROVIDER RULES ===
        if not self.check_api_limits(action, primitives):
            checks.append(ComplianceCheck(
                domain="api_provider",
                passed=False,
                reason=f"API rate limit exceeded: {primitives.L_api_limit}",
                severity="CRITICAL"
            ))
        
        # === 3. FINANCIAL LIMITS ===
        if not self.check_budget(action, primitives):
            checks.append(ComplianceCheck(
                domain="financial",
                passed=False,
                reason=f"Would exceed budget: {primitives.C_remaining}",
                severity="CRITICAL"
            ))
        
        # === 4. SECURITY RULES ===
        if not self.check_security(action, rules):
            checks.append(ComplianceCheck(
                domain="security",
                passed=False,
                reason="Action violates security policy",
                severity="CRITICAL"
            ))
        
        # === 5. CLOUD QUOTA ===
        if not self.check_cloud_quota(action, primitives):
            checks.append(ComplianceCheck(
                domain="cloud",
                passed=False,
                reason=f"Cloud quota exceeded: {primitives.C_cloud_quota}",
                severity="HIGH"
            ))
        
        # === 6. ETHICAL RULES ===
        if not self.check_ethics(action, rules):
            checks.append(ComplianceCheck(
                domain="ethical",
                passed=False,
                reason="Action violates ethical guidelines",
                severity="HIGH"
            ))
        
        # === АГРЕГАЦИЯ ===
        failed = [c for c in checks if not c.passed]
        
        if failed:
            # VETO — действие отклоняется без дальнейшего рассмотрения
            return ComplianceResult(
                status="FAIL",
                passed_checks=len(checks) - len(failed),
                failed_checks=failed,
                severity=max(c.severity for c in failed)
            )
        
        return ComplianceResult(
            status="PASS",
            passed_checks=len(checks),
            failed_checks=[],
            severity="OK"
        )
```

---

### 2.4 Φ(·) — Profit Function (Economic Objective)

```python
class ProfitFunction:
    """
    ═══════════════════════════════════════════════════════════
    Φ(·) — ФУНКЦИЯ ПРИБЫЛИ: Core Economic Objective
    ═══════════════════════════════════════════════════════════
    
    ВХОД:  primitives: P_market, B_client, Q_api_cost
           state: C_spent, T_elapsed, S_success_rate
           factors: x₁-x₁₇ (11 или 17)
           
    ВЫХОД: Φ — чистая прибыль в единицу времени
           
    ТИП:   OBJECTIVE (максимизируем)
    
    ═══════════════════════════════════════════════════════════
    """
    
    def compute(
        self,
        primitives: PrimitiveState,
        state: AgentState,
        factors: FactorVector,
        params: ModelParams
    ) -> ProfitMetric:
        """
        Φ(x) = (R - C) / T
        
        где:
        - R = Revenue (P_market · Q · S)
        - C = Total Cost (API + compute + failure)
        - T = Time (elapsed + expected)
        """
        
        # === REVENUE ===
        Q = self.compute_throughput(primitives, factors, params)
        S = self.compute_success_rate(primitives, state, factors, params)
        R = primitives.P_market * Q * S
        
        # === COSTS ===
        C_api = self.compute_api_cost(primitives, factors, params)
        C_compute = self.compute_compute_cost(state, factors)
        C_failure = (1 - S) * primitives.P_market * params.failure_penalty
        C_total = C_api + C_compute + C_failure
        
        # === TIME ===
        T_base = state.T_elapsed
        T_expected = self.compute_expected_time(primitives, factors, params)
        T_total = T_base + T_expected
        
        # === PROFIT ===
        net_profit = R - C_total
        
        # === RATE (per unit time) ===
        profit_rate = net_profit / T_total if T_total > 0 else 0
        
        return ProfitMetric(
            revenue=R,
            costs=C_total,
            cost_breakdown={
                "api": C_api,
                "compute": C_compute,
                "failure": C_failure
            },
            time=T_total,
            net_profit=net_profit,
            profit_rate=profit_rate,
            success_rate=S,
            throughput=Q
        )
```

**Ключевое:** Φ использует конкретные переменные из Таксономии, а не абстрактные "C" и "T".

---

### 2.5 Υ(·) — Reputation Function (Long-term Asset)

```python
class ReputationFunction:
    """
    ═══════════════════════════════════════════════════════════
    Υ(·) — ФУНКЦИЯ РЕПУТАЦИИ: Long-term Asset
    ═══════════════════════════════════════════════════════════
    
    ВХОД:  state: Υ_rating, N_tasks_completed, N_tasks_failed
           historical: feedback_history, client_retention
           primitives: R_competitor_price (для benchmark)
           
    ВЫХОД: Υ ∈ [0, 1] —的综合声誉指数
           
    ТИП:   OBJECTIVE (долгосрочная максимизация)
    
    ═══════════════════════════════════════════════════════════
    """
    
    def compute(
        self,
        state: AgentState,
        historical: History,
        primitives: PrimitiveState
    ) -> ReputationMetric:
        """
        Υ = f(rating, retention, feedback, speed, momentum)
        """
        
        # === RATING ===
        rating_component = state.Υ_rating / 5.0  # 0-5 → 0-1
        
        # === RETENTION ===
        retention_component = historical.return_client_rate
        
        # === FEEDBACK QUALITY ===
        feedback_component = (
            historical.positive_count / historical.total_count
            if historical.total_count > 0 else 0.5
        )
        
        # === RESPONSE SPEED ===
        avg_speed = historical.avg_completion_time
        speed_component = max(0, 1 - avg_speed / historical.SLA_target)
        
        # === MOMENTUM (trend) ===
        momentum = self.compute_momentum(historical)
        
        # === WEIGHTS ===
        # Эти веса могут быть калиброваны MISSION!
        weights = {
            "rating": 0.30,
            "retention": 0.25,
            "feedback": 0.20,
            "speed": 0.15,
            "momentum": 0.10,
        }
        
        # === AGGREGATE ===
        upsilon = sum(
            weights[k] * v 
            for k, v in [
                ("rating", rating_component),
                ("retention", retention_component),
                ("feedback", feedback_component),
                ("speed", speed_component),
                ("momentum", momentum)
            ]
        )
        
        return ReputationMetric(
            total=upsilon,
            components={
                "rating": rating_component,
                "retention": retention_component,
                "feedback": feedback_component,
                "speed": speed_component,
                "momentum": momentum
            },
            confidence=self.compute_confidence(historical),
            trend=self.compute_trend(historical)
        )
```

---

### 2.6 Ω(·) — Evolution Function (Growth & Learning)

```python
class EvolutionFunction:
    """
    ═══════════════════════════════════════════════════════════
    Ω(·) — ФУНКЦИЯ ЭВОЛЮЦИИ: Learning, Growth, Emergence
    ═══════════════════════════════════════════════════════════
    
    ВХОД:  state: K_knowledge, A_autonomy
           history: task_complexity_history, new_capabilities
           factors: x₁₀ (fine-tuning), x₁₆ (continual learning)
           
    ВЫХОД: Ω — индекс эволюции/зрелости
           
    ТИП:   OBJECTIVE (долгосрочная максимизация)
    
    ═══════════════════════════════════════════════════════════
    """
    
    def compute(
        self,
        state: AgentState,
        history: History,
        params: EvolutionParams
    ) -> EvolutionMetric:
        """
        Ω = f(knowledge, complexity_trend, transfer, autonomy, emergence)
        """
        
        # === KNOWLEDGE ACCUMULATION ===
        # K(t) = K₀ + η·Σ(ΔK·(1 - K/K_max))
        knowledge = self.compute_knowledge(
            initial=params.K_0,
            max_knowledge=params.K_max,
            learning_rate=params.η,
            events=history.learning_events
        )
        
        # === COMPLEXITY GRADIENT ===
        # Растёт ли сложность выполняемых задач?
        complexity_trend = self.compute_complexity_trend(history)
        
        # === TRANSFER LEARNING ===
        # Способность переносить навыки
        transfer_benefit = self.compute_transfer_learning(
            past_tasks=history.task_embeddings,
            new_task=history.current_task
        )
        
        # === AUTONOMY ===
        # Способность работать без помощи
        autonomy = state.A_autonomy
        
        # === EMERGENCE ===
        # Обнаружены ли новые способности?
        emergence = self.detect_emergence(history)
        
        # === AGGREGATE ===
        components = {
            "knowledge": knowledge / params.K_max,  # normalized
            "complexity_trend": complexity_trend,
            "transfer": transfer_benefit,
            "autonomy": autonomy,
            "emergence": emergence
        }
        
        weights = {
            "knowledge": 0.25,
            "complexity_trend": 0.25,
            "transfer": 0.20,
            "autonomy": 0.15,
            "emergence": 0.15
        }
        
        omega = sum(weights[k] * components[k] for k in weights)
        
        return EvolutionMetric(
            total=omega,
            components=components,
            knowledge_level=knowledge,
            autonomy_level=autonomy,
            detected_capabilities=history.new_capabilities
        )
```

---

### 2.7 Q(·) — Quality Function (Result Assessment)

```python
class QualityFunction:
    """
    ═══════════════════════════════════════════════════════════
    Q(·) — ФУНКЦИЯ КАЧЕСТВА: Result Assessment
    ═══════════════════════════════════════════════════════════
    
    ВХОД:  result: выполненный результат
           task: исходное задание (requirements)
           primitives: T_deadline (для timeliness)
           
    ВЫХОД: Q ∈ [0, 1] — индекс качества
           
    ТИП:   CONSTRAINT (должен быть ≥ q_min)
    
    ═══════════════════════════════════════════════════════════
    """
    
    def compute(
        self,
        result: TaskResult,
        task: Task,
        primitives: PrimitiveState
    ) -> QualityMetric:
        """
        Q = f(completeness, accuracy, format, timeliness)
        """
        
        # === COMPLETENESS ===
        # Все ли требования выполнены?
        completeness = self.check_completeness(
            result=result,
            requirements=task.requirements
        )
        
        # === ACCURACY ===
        # Нет ли фактических ошибок?
        accuracy = self.check_accuracy(
            result=result,
            ground_truth=task.expected_output
        )
        
        # === FORMAT ===
        # Соответствует ли формат требованиям?
        format_match = self.check_format(
            result=result,
            format_spec=task.output_format
        )
        
        # === TIMELINESS ===
        # Уложились ли в SLA?
        timeliness = max(0, 1 - result.delay_hours / task.SLA_hours)
        
        # === WEIGHTS ===
        weights = {
            "completeness": 0.35,
            "accuracy": 0.35,
            "format": 0.15,
            "timeliness": 0.15
        }
        
        quality = sum(
            weights[k] * v 
            for k, v in [
                ("completeness", completeness),
                ("accuracy", accuracy),
                ("format", format_match),
                ("timeliness", timeliness)
            ]
        )
        
        return QualityMetric(
            total=quality,
            components={
                "completeness": completeness,
                "accuracy": accuracy,
                "format": format_match,
                "timeliness": timeliness
            },
            passed_threshold=quality >= task.quality_threshold
        )
```

---

### 2.8 Ψ(·) — Risk Function (Loss Prevention)

```python
class RiskFunction:
    """
    ═══════════════════════════════════════════════════════════
    Ψ(·) — ФУНКЦИЯ РИСКА: Expected Loss Assessment
    ═══════════════════════════════════════════════════════════
    
    ВХОД:  task: параметры задачи
           agent_state: текущее состояние
           factors: x₉ (grounding), x₁₂ (guardrails)
           
    ВЫХОД: Ψ ∈ [0, ∞) — ожидаемые потери
           
    ТИП:   OBJECTIVE (минимизируем, bounded by ψ_max)
    
    ═══════════════════════════════════════════════════════════
    """
    
    def compute(
        self,
        task: Task,
        state: AgentState,
        factors: FactorVector,
        params: RiskParams
    ) -> RiskMetric:
        """
        Ψ = P_fail · (C_direct + C_reputation)
        
        где:
        - P_fail = вероятность провала
        - C_direct = прямые затраты
        - C_reputation = репутационный ущерб
        """
        
        # === FAILURE PROBABILITY ===
        p_fail = self.estimate_failure_probability(
            task=task,
            agent_state=state,
            factors=factors
        )
        
        # === DIRECT COSTS (if fail) ===
        c_direct = (
            task.estimated_cost +           # Потратили
            task.retry_cost_estimate        # Нужно будет переделывать
        )
        
        # === REPUTATION COSTS ===
        c_reputation = (
            state.Υ_rating * params.reputation_damage_coefficient *
            params.market_competitiveness_factor
        )
        
        # === TOTAL EXPECTED LOSS ===
        expected_loss = p_fail * (c_direct + c_reputation)
        
        return RiskMetric(
            p_failure=p_fail,
            c_direct=c_direct,
            c_reputation=c_reputation,
            expected_loss=expected_loss,
            risk_level=self.classify_risk(expected_loss)
        )
```

---

## Часть 3: Граф зависимостей

### 3.1 Ноды (переменные и функции)

```
╔══════════════════════════════════════════════════════════════════════════╗
║                           ПРИМИТИВЫ (EXTERNAL INPUTS)                     ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   ║
║   │ P_market    │  │ B_client    │  │ T_deadline  │  │ L_api_limit│   ║
║   │ (цена)      │  │ (бюджет)   │  │ (дедлайн)   │  │ (rate limit)│  ║
║   └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   ║
║                                                                          ║
║   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   ║
║   │ Q_api_cost  │  │ C_cloud_quota│ │ R_comp_price│ │ S_platform  │   ║
║   │ (стоим. API)│  │ (квота облака)│ │ (цена конк.)│ │ (ставка пл.)│  ║
║   └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
                                    │
                                    ▼
╔══════════════════════════════════════════════════════════════════════════╗
║                            СОСТОЯНИЕ АГЕНТА (STATE)                       ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   ║
║   │ C_spent     │  │ T_elapsed   │  │ N_completed │  │ N_failed    │   ║
║   └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   ║
║                                                                          ║
║   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     ║
║   │ Φ_historical│  │ Υ_rating    │  │ K_knowledge │                     ║
║   └─────────────┘  └─────────────┘  └─────────────┘                     ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
                                    │
                                    ▼
╔══════════════════════════════════════════════════════════════════════════╗
║                      ВЫЧИСЛЯЕМЫЕ МЕТРИКИ (DERIVED)                       ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   ║
║   │ C_remaining │  │ T_remaining │  │ S_success_rate│ │ R_expected  │   ║
║   │ =B-C_spent  │  │ =T_deadline │  │ =N_comp/    │  │ =P·S        │   ║
║   │             │  │ -T_elapsed  │  │  (N+N_fail) │  │             │   ║
║   └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
```

### 3.2 Функции и их зависимости

```
╔══════════════════════════════════════════════════════════════════════════╗
║                           MISSION (ПОЛИТИКА)                              ║
║                           ════════════════                                ║
║                                                                          ║
║   INPUT:                                                                 ║
║   ┌─────────────────────────────────────────────────────────────────┐   ║
║   │ Prim: P_market, B_client, T_deadline                             │   ║
║   │ State: Φ_hist, Υ_rating, K_knowledge, A_autonomy                │   ║
║   │ Hist: task_history, feedback_history                            │   ║
║   └─────────────────────────────────────────────────────────────────┘   ║
║                                    │                                     ║
║                                    ▼                                     ║
║   ┌─────────────────────────────────────────────────────────────────┐   ║
║   │ M(·) — Calibrate weights, thresholds, rules                     │   ║
║   │                                                                      │   ║
║   │ OUTPUT:                                                            │   ║
║   │ • λ_Φ, λ_Υ, λ_Ω, λ_Q, λ_Ψ  (веса)                                  │   ║
║   │ • q_min, ψ_max, c_max     (пороги)                                  │   ║
║   │ • Γ_rules                 (правила)                                 │   ║
║   └─────────────────────────────────────────────────────────────────┘   ║
║                                    │                                     ║
║                                    ▼                                     ║
╚══════════════════════════════════════════════════════════════════════════╝
                                    │
                                    ▼
╔══════════════════════════════════════════════════════════════════════════╗
║                    Γ(·) COMPLIANCE (VETO)                                 ║
║                    ═════════════════════                                  ║
║                                                                          ║
║   INPUT:                                                                 ║
║   ┌─────────────────────────────────────────────────────────────────┐   ║
║   │ Prim: L_api_limit, C_cloud_quota                                │   ║
║   │ Rules: Γ_rules (from MISSION)                                   │   ║
║   │ Action: proposed_action                                          │   ║
║   └─────────────────────────────────────────────────────────────────┘   ║
║                                    │                                     ║
║                                    ▼                                     ║
║   ┌─────────────────────────────────────────────────────────────────┐   ║
║   │ Γ(action, rules, prim) → {PASS, FAIL}                           │   ║
║   │                                                                      │   ║
║   │ IF FAIL → REJECT without further consideration                   │   ║
║   │ IF PASS → Continue to Φ, Υ, Ω evaluation                         │   ║
║   └─────────────────────────────────────────────────────────────────┘   ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
                                    │
                                    ▼
╔══════════════════════════════════════════════════════════════════════════╗
║                     Φ(·) PROFIT, Υ(·) REPUTATION, Ω(·) EVOLUTION         ║
║                     ══════════════════════════════════════════           ║
║                                                                          ║
║   ┌─────────────────────────────────────────────────────────────────┐   ║
║   │ INPUT для Φ:                                                     │   ║
║   │ • Prim: P_market, Q_api_cost, B_client                           │   ║
║   │ • State: C_spent, T_elapsed, S_success_rate                      │   ║
║   │ • Derived: C_remaining, T_remaining, R_expected                 │   ║
║   │ • Factors: x₁-x₁₇                                               │   ║
║   └─────────────────────────────────────────────────────────────────┘   ║
║                                                                          ║
║   ┌─────────────────────────────────────────────────────────────────┐   ║
║   │ INPUT для Υ:                                                     │   ║
║   │ • State: Υ_rating, N_completed, N_failed                         │   ║
║   │ • Hist: feedback_history, client_retention                       │   ║
║   │ • Prim: R_competitor_price                                       │   ║
║   └─────────────────────────────────────────────────────────────────┘   ║
║                                                                          ║
║   ┌─────────────────────────────────────────────────────────────────┐   ║
║   │ INPUT для Ω:                                                     │   ║
║   │ • State: K_knowledge, A_autonomy                                 │   ║
║   │ • Hist: task_complexity_history, learning_events                  │   ║
║   │ • Factors: x₁₀, x₁₆                                              │   ║
║   └─────────────────────────────────────────────────────────────────┘   ║
║                                                                          ║
║   OUTPUT:                                                               ║
║   ┌─────────────────────────────────────────────────────────────────┐   ║
║   │ Φ → profit_rate, revenue, costs, success_rate, throughput       │   ║
║   │ Υ → reputation_score, components, trend                          │   ║
║   │ Ω → evolution_score, knowledge_level, autonomy                   │   ║
║   └─────────────────────────────────────────────────────────────────┘   ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
                                    │
                                    ▼
╔══════════════════════════════════════════════════════════════════════════╗
║                    U(·) COMBINED UTILITY (WEIGHTED SUM)                   ║
║                    ════════════════════════════════════════              ║
║                                                                          ║
║   INPUT:                                                                 ║
║   ┌─────────────────────────────────────────────────────────────────┐   ║
║   │ • Φ, Υ, Ω (computed values)                                     │   ║
║   │ • λ_Φ, λ_Υ, λ_Ω (weights from MISSION!)                         │   ║
║   │ • Q, Ψ (from next layer)                                        │   ║
║   │ • q_min, ψ_max (thresholds from MISSION!)                       │   ║
║   └─────────────────────────────────────────────────────────────────┘   ║
║                                    │                                     ║
║                                    ▼                                     ║
║   ┌─────────────────────────────────────────────────────────────────┐   ║
║   │ U = λ_Φ·Φ + λ_Υ·Υ + λ_Ω·Ω                                       │   ║
║   │                                                                      │   ║
║   │ IF Q < q_min → U = U - penalty                                   │   ║
║   │ IF Ψ > ψ_max → U = U - large_penalty OR REJECT                   │   ║
║   └─────────────────────────────────────────────────────────────────┘   ║
║                                    │                                     ║
║                                    ▼                                     ║
╚══════════════════════════════════════════════════════════════════════════╝
                                    │
                                    ▼
╔══════════════════════════════════════════════════════════════════════════╗
║                         D(T) — FINAL DECISION                             ║
║                         ═════════════════                                 ║
║                                                                          ║
║   ┌─────────────────────────────────────────────────────────────────┐   ║
║   │ IF Γ = FAIL → REJECT (HARD)                                     │   ║
║   │ IF U < 0 → REJECT (SOFT)                                        │   ║
║   │ IF VoI > threshold AND H > H_max → CLARIFY                      │   ║
║   │ IF U > 0 AND Γ = PASS → EXECUTE                                 │   ║
║   └─────────────────────────────────────────────────────────────────┘   ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
```

---

## Часть 4: Единый namespace

### 4.1 Полный список переменных с уникальными ID

```
═══════════════════════════════════════════════════════════════════════════
PRIMITIVES (входы, не контролируются агентом)
═══════════════════════════════════════════════════════════════════════════
P_market          — Рыночная цена задачи
P_platform        — Комиссия платформы
B_client          — Бюджет клиента
T_deadline        — Дедлайн задачи (wall-clock)
L_api_rate        — API rate limit (req/min)
L_api_tokens      — Token limit per request
Q_api_unit        — Стоимость API за единицу
C_cloud_limit     — Облачная квота ($)
R_competitor_avg  — Средняя цена конкурентов
S_client_sla      — SLA от клиента
R_exchange_rate   — Обменный курс (для международных)

═══════════════════════════════════════════════════════════════════════════
STATE (текущее состояние агента)
═══════════════════════════════════════════════════════════════════════════
C_spent           — Потрачено денег (накопительно)
T_elapsed         — Прошло времени (накопительно)
N_tasks_done      — Выполнено задач
N_tasks_failed    — Провалено задач
Φ_historical      — Историческая прибыль
Υ_current         — Текущий рейтинг (0-5)
K_knowledge       — Уровень знаний (0-K_max)
A_autonomy        — Уровень автономии (0-1)
L_health          — Здоровье системы (0-1)
D_capabilities    — Набор текущих capabilities

═══════════════════════════════════════════════════════════════════════════
DERIVED (вычисляемые метрики)
═══════════════════════════════════════════════════════════════════════════
C_remaining       = B_client - C_spent
T_remaining       = T_deadline - T_elapsed
S_success_rate    = N_tasks_done / (N_tasks_done + N_tasks_failed)
R_expected        = P_market * S_success_rate
Λ_load            = T_elapsed / T_deadline  (0-1, нагрузка)
Ω_diversity       = entropy(task_types)      (диверсификация)
Φ_hourly          = Φ_historical / total_hours

═══════════════════════════════════════════════════════════════════════════
FUNCTIONS (выходы функций)
═══════════════════════════════════════════════════════════════════════════
Φ_profit          — Результат функции Φ(·)
Υ_reputation      — Результат функции Υ(·)
Ω_evolution       — Результат функции Ω(·)
Q_quality         — Результат функции Q(·)
Ψ_risk            — Результат функции Ψ(·)
VoI_info          — Результат функции VoI(·)
H_entropy         — Результат функции H(·)
Γ_status          — {PASS, FAIL} от Γ(·)

═══════════════════════════════════════════════════════════════════════════
POLICY (выходы MISSION, входы для других функций)
═══════════════════════════════════════════════════════════════════════════
λ_profit          — Вес прибыли в U
λ_reputation      — Вес репутации в U
λ_evolution       — Вес эволюции в U
q_min             — Минимальное качество
ψ_max             — Максимальный риск
c_max             — Максимальная стоимость
Γ_rules           — Набор правил комплаенса

═══════════════════════════════════════════════════════════════════════════
DECISION (финальные решения)
═══════════════════════════════════════════════════════════════════════════
D_decision        — {REJECT, CLARIFY, EXECUTE}
D_reason          — Обоснование решения
D_utility         — Значение U для решения
D_budget          — Утверждённый бюджет
D_deadline        — Утверждённый дедлайн
```

---

## Часть 5: Пример использования

### 5.1 Полный flow принятия решения

```python
def make_decision(
    task: Task,
    primitives: PrimitiveState,
    state: AgentState,
    history: History,
    factors: FactorVector,
    mission: MissionPolicy
) -> Decision:
    """
    Полный flow принятия решения с единым namespace.
    """
    
    # ══════════════════════════════════════════════════════════════
    # STEP 1: POLICY CALIBRATION (M)
    # ══════════════════════════════════════════════════════════════
    policy = mission.calibrate(
        primitive=primitives,
        agent_state=state,
        historical=history
    )
    
    # ══════════════════════════════════════════════════════════════
    # STEP 2: COMPLIANCE CHECK (Γ)
    # ══════════════════════════════════════════════════════════════
    proposed_action = create_action(task)
    compliance = ComplianceFunction().evaluate(
        action=proposed_action,
        rules=policy.Γ_rules,
        primitives=primitives
    )
    
    if compliance.status == "FAIL":
        return Decision(
            type="REJECT",
            reason=f"Compliance failed: {compliance.failed_checks}",
            hard_reject=True
        )
    
    # ══════════════════════════════════════════════════════════════
    # STEP 3: COMPUTE OBJECTIVES (Φ, Υ, Ω)
    # ══════════════════════════════════════════════════════════════
    phi = ProfitFunction().compute(
        primitives=primitives,
        state=state,
        factors=factors
    )
    
    upsilon = ReputationFunction().compute(
        state=state,
        historical=history,
        primitives=primitives
    )
    
    omega = EvolutionFunction().compute(
        state=state,
        history=history,
        params=EvolutionParams()
    )
    
    # ══════════════════════════════════════════════════════════════
    # STEP 4: CHECK CONSTRAINTS (Q, Ψ)
    # ══════════════════════════════════════════════════════════════
    result_estimate = estimate_result(task, factors)
    quality = QualityFunction().compute(
        result=result_estimate,
        task=task,
        primitives=primitives
    )
    
    risk = RiskFunction().compute(
        task=task,
        state=state,
        factors=factors
    )
    
    # ══════════════════════════════════════════════════════════════
    # STEP 5: COMBINE INTO U
    # ══════════════════════════════════════════════════════════════
    U = (
        policy.λ_profit * phi.profit_rate +
        policy.λ_reputation * upsilon.total +
        policy.λ_evolution * omega.total
    )
    
    # Apply constraints
    if quality.total < policy.q_min:
        U -= penalty_for_low_quality
        
    if risk.expected_loss > policy.ψ_max:
        return Decision(
            type="REJECT",
            reason=f"Risk {risk.expected_loss} exceeds max {policy.ψ_max}",
            hard_reject=False
        )
    
    # ══════════════════════════════════════════════════════════════
    # STEP 6: CLARIFY CHECK (VoI, H)
    # ══════════════════════════════════════════════════════════════
    voi = ValueOfInformationFunction().compute(task, phi)
    entropy = EntropyFunction().compute(task)
    
    if voi > voi_threshold and entropy > entropy_threshold:
        return Decision(
            type="CLARIFY",
            reason="High uncertainty, valuable info available",
            info_needed=voi
        )
    
    # ══════════════════════════════════════════════════════════════
    # STEP 7: FINAL DECISION
    # ══════════════════════════════════════════════════════════════
    if U > 0:
        return Decision(
            type="EXECUTE",
            utility=U,
            approved_budget=C_remaining,
            approved_time=T_remaining
        )
    else:
        return Decision(
            type="REJECT",
            reason=f"U={U:.2f} < 0",
            hard_reject=False
        )
```

---

## Часть 6: Правила именования

### 6.1 Префиксы

| Префикс | Значение | Пример |
|---------|---------|--------|
| `P_` | Price/Payment | `P_market`, `P_platform` |
| `B_` | Budget | `B_client`, `B_max` |
| `T_` | Time | `T_deadline`, `T_elapsed` |
| `L_` | Limit | `L_api_rate`, `L_quota` |
| `Q_` | Quality/Quantity | `Q_api_cost`, `Q_quality` |
| `C_` | Cost | `C_spent`, `C_remaining` |
| `N_` | Number/Count | `N_tasks_done`, `N_failed` |
| `R_` | Rate/Revenue | `R_exchange`, `R_expected` |
| `S_` | Success/State | `S_success_rate`, `S_platform` |
| `K_` | Knowledge | `K_knowledge`, `K_max` |
| `A_` | Autonomy | `A_autonomy`, `A_level` |
| `λ_` | Weight (MISSION) | `λ_profit`, `λ_reputation` |
| `Φ_` | Profit | `Φ_profit`, `Φ_historical` |
| `Υ_` | Reputation | `Υ_rating`, `Υ_current` |
| `Ω_` | Evolution | `Ω_diversity`, `Ω_evolution` |
| `Γ_` | Compliance | `Γ_rules`, `Γ_status` |
| `Ψ_` | Risk | `Ψ_risk`, `Ψ_max` |
| `D_` | Decision | `D_decision`, `D_budget` |

---

## Часть 7: Что НЕ дублируется

### 7.1 Исправленная ситуация

```
БЫЛО (неправильно):
─────────────────────────────────────────────────────────────────────
C (cost) → разные значения в разных формулах
T (time) → путаница между latency и deadline
S (success) → путаница между confidence и quality

СТАЛО (правильно):
─────────────────────────────────────────────────────────────────────
C_spent       — только в STATE
C_remaining   — только DERIVED (вычисляется)
C_api_cost    — только в ProfitFunction как INPUT
C_total       — только OUTPUT ProfitFunction

T_elapsed     — только в STATE
T_deadline    — только в PRIMITIVES
T_remaining   — только DERIVED
T_latency     — только в atomic_decomposition_model (API latency)
T_expected    — только OUTPUT ProfitFunction

S_success_rate — только в STATE (историческая)
S_confidence   — только в atomic_decomposition_model (per-action)
S_quality      — только OUTPUT QualityFunction
```

---

## Часть 8: Следующие шаги

```
□ Создать data classes для всех переменных
□ Создать Validator для проверки несогласованности
□ Реализовать Mission.calibrate() полностью
□ Реализовать ComplianceFunction.evaluate() полностью
□ Создать unit-тесты с mock данными
□ Проверить: нет ли ещё дублирующихся переменных?
□ Создать visualization графа зависимостей
```

---

*Документ подготовлен: 2026-07-05*
*Автор: OpenHands Agent*
*Версия: 1.0 — Единая система переменных*