# Критический разбор математического ядра Space1

## Резюме

| Аспект | Оценка | Почему |
|---|---|---|
| **Концепция** | 6/10 | Сильная идея, но фундаментальный раскол «личный ассистент vs автономный агент» не решён |
| **Математика** | 4.5/10 | Отдельные формулы корректны, но как единая система — не существует |
| **Код** | 2/10 | Ядровая математика реализована на ~15%, с серьёзными багами |
| **Согласованность** | 3/10 | 4–5 несведённых черновиков модели живут параллельно |

---

## 1. Фундаментальное противоречие: для кого строится система?

**Версия А — «Автономный экономический агент»**: Φ/Υ/Γ/Mission, репутация на бирже, конкуренция за заказы.

**Версия Б — «Личный цифровой помощник»**: Telegram-бот, ищущий вакансии *для владельца*, пишущий отклики *от его имени*, хранящий факты о владельце («живёт в Петербурге», «рисует»).

**Почему это критично, а не терминологическая мелочь:**

- Зачем личному ассистенту «функция репутации на бирже фриланса» или «Mission = SURVIVAL с λ_profit = 0.8»?
- Зачем автономному агенту-фрилансеру «парадигмальная линза для смены мировоззрения» и «трекер навыков рисования владельца»?

**В коде это уже физически слито:** `Digital Garden` (личный ассистент) назначен «оркестратором» всей экономической архитектуры. Это как если бы Excel вдруг стал торговым роботом на бирже.

> **Вердикт:** Пока этот вопрос не решён явно, любая доработка математики рискует чинить не тот продукт.

---

## 2. Гомеостаз H — одно понятие, четыре несовместимые формализации

| # | Источник | Формула | Диапазон |
|---|---|---|---|
| 1 | `MATHEMATICAL_FORMULAS.md` §3.7 | `H = (F_reinforcing + ε) / (F_balancing + ε)` | `(0, ∞)` |
| 2 | `homeostatic_state.py` (реальный код) | `H = 1 − stress`, где `stress = 0.3(1−balance) + 0.3(1−rating) + 0.2·workload + 0.2(1−quality)` | `(-∞, 1]` |
| 3 | `FREELANCER_AGENT_ARCHITECTURE.md` | Вектор `h_i` по Йерксу-Додсону, **нет единого скаляра H** | — |
| 4 | `CYBERNETICS_HOMEOSTASIS_FORMULAS.md` | ОДУ-система `ẋ_ι, ẋ_κ, ẋ_o` | Динамика по времени |

**Проблема глубже, чем «разные формулы»:**

- В варианте 2 (`H = 1 − stress`) порог `H > 1.2` означает LOW stress. Но по конструкции `stress ≥ 0`, значит `H ≤ 1`. **Порог 1.2 математически недостижим.** Это баг, обнаруженный только при формальной проверке.
- В варианте 1 `H` — отношение сил, может быть любым положительным. В варианте 2 — линейная свёртка. В варианте 3 — вектор. В варианте 4 — дифференциальные уравнения. Это не «разные реализации одного понятия» — это **четыре разных математических объекта**.

> **Вердикт:** Канон `02_MATHEMATICAL_CORE.md` §IV.7 исправляет это (убирает верхний срез `min(1.0, ...)`), но код (`srs/utility/__init__.py`) уже реализует исправленную версию — **код опережает документацию**, что само по себе проблема управления версиями.

---

## 3. Utility U — минимум четыре несовместимые «итоговые» функции

| # | Источник | Формула | Ключевое отличие |
|---|---|---|---|
| 1 | `MATHEMATICAL_FORMULAS.md` §3.9 | `U = λ_Φ·Φ + λ_Υ·Υ + λ_Q·Q + λ_Ω·Ω − λ_Ψ·Ψ − λ_Γ·Γ` | Γ входит аддитивно |
| 2 | `MATHEMATICAL_FORMULAS.md` §4 | `Φ_R = Φ·𝟙[Γ=0]·(1+α_rep·Υ) − λ_Ψ·Ψ` | Отдельная «решающая» функция |
| 3 | `FREELANCER_AGENT_ARCHITECTURE.md` §7.2.1 | `U = Σ w_i·u_i`, цели g1..g5 | Другие переменные, другие цели |
| 4 | Манускрипт §5.1 | `U_agent = w_P·P_profit + w_Q·Q_total + w_L·ΔL_s − w_R·R_total + w_Rep·λ_orders` | ΔL_s — прирост навыка, нет нигде больше |

**Критический баг в варианте 1:** `Γ = −∞` (hard veto) даёт `U → +∞` — результат прямо противоположный ожидаемому. Это было замечено в `MATHEMATICAL_REVIEW.md` §4.1, но «патч» (`Φ_R` с индикатором) ввёл новую функцию вместо исправления U.

**Канон `02_MATHEMATICAL_CORE.md` §IV.11 исправляет это:**
- `Γ_hard` выведена из тела U, работает как предикат-гейт **до** вычисления U
- `Γ_soft` входит мультипликативно: `U = U_raw · (1 − min(1, Γ_soft))`

**Но в коде (`srs/utility/__init__.py`, `score_action`):**
```python
score = _clamp(u_raw * (1.0 - min(1.0, gamma_soft)), -1.0, 1.0)
```
— реализовано канонически. Но `u_raw` вычисляется как:
```python
u_raw = w.profit_weight * phi_norm + w.reputation_weight * upsilon + w.evolution_weight * aggregate["omega"] + w.quality_weight * quality
```
— без нормировки `phi_norm` (деление на `price_per_task` — произвольный якорь, не связанный с реальным масштабом Φ).

> **Вердикт:** Формула U в коде технически соответствует канону, но масштабирование Φ — подмена. `phi_norm = phi / price_per_task` не делает Φ «сопоставимым» с Υ∈[0,1] — если `price_per_task = 100`, а реальная Φ = 500, получаем `phi_norm = 5`, что ломает всю свёртку.

---

## 4. Profit Φ — размерностная нестыковка и логические дыры

**Аксиома A1 (канон):** `Φ_task = (R_task − C_task) / T_task` [$/час]

**Проблема 1 — размерность в старой версии:**
- `R = P·S·Q` где `P` [$/задача], `Q` [задач/час] → `R` [$/час]
- `C` [$/задача] (по таблице размерностей)
- `R − C` смешивает `$/час` и `$/задача` — **операция размерностно некорректна**

**Исправление в каноне:** Всё считается на уровне одной задачи в долларах, деление на `T` — только один раз, на последнем шаге.

**Проблема 2 — в коде (`compute_phi`):**
```python
# Новая сигнатура: compute_phi(price, quality, cost, time_hours)
modulated_price = price * (1.0 + b_Q)
modulated_price = modulated_price * (1.0 - C_platform - C_processing)
duration = max(t_val, 0.1)
return (modulated_price - c_val) / duration
```
— корректно по размерности. **Но:**
- `C_platform` и `C_processing` вычитаются как **множители** `(1 − C_platform − C_processing)`, а не как абсолютные величины. Если `C_platform = 0.2` (20%) и `C_processing = 0.029` (2.9%), получаем `price * 0.771` — это процентные комиссии, корректно.
- **Но** `C_tokens` (стоимость токенов) вообще не передаётся в новую сигнатуру! Она есть только в legacy-ветке:
```python
if token_tracker is not None:
    cost += token_tracker.get_total_cost()
```
— и эта ветка вызывается **только** при использовании старой сигнатуры `compute_phi(task, agent, ...)`.

> **Вердикт:** Новая «каноническая» сигнатура **не учитывает стоимость токенов** — один из главных пунктов критики старой версии. Это регресс, не улучшение.

**Проблема 3 — риск-корректировка дохода:**
Канон: `R_adj = P·(1+b_Q(Q))·ρ_risk`, где `ρ_risk = ∏(1 − P_k·w_k)`

В коде:
```python
modulated_price = price * (1.0 + b_Q)
modulated_price = modulated_price * (1.0 - C_platform - C_processing)
```
— `ρ_risk` **отсутствует полностью**. Риск не корректирует доход.

> **Вердикт:** Код реализует ~60% канонической формулы Φ. Риск-корректировка, одна из ключевых инноваций канона, — не реализована.

---

## 5. Quality Q — две конкурирующие версии, ни одна не работает как заявлено

**Канон (4 компоненты):** `Q = α·Q_comp + β·Q_acc + γ·Q_full + δ·Q_time`

**В коде (`compute_quality`):**
```python
# Новая сигнатура
value = _clamp(
    weights_tuple[0] * c +
    weights_tuple[1] * a +
    weights_tuple[2] * f +
    weights_tuple[3] * t
)
```
— корректно. **Но:**

**Проблема 1 — `Q_time` вычисляется неверно в legacy-ветке:**
```python
if t_actual is not None and t_deadline is not None:
    deadline = max(t_deadline, 1e-9)
    timeliness = 1.0 - min(1.0, max(0.0, t_actual - t_deadline) / deadline)
```
— это **не** каноническая формула `Q_time = 1 − min(1, max(0, t_actual − t_deadline) / t_deadline)`. В каноне делитель — `t_deadline`, в коде — тоже `t_deadline` (переменная `deadline = max(t_deadline, 1e-9)`). Ок, совпадает.

**Но** в каноне `max(0, t_actual − t_deadline)` — защита от досрочной сдачи. В коде:
```python
max(0.0, t_actual - t_deadline) / deadline
```
— та же защита. Ок.

**Проблема 2 — `Q_acc` (accuracy) через cosine similarity:**
Канон: `Q_acc ≈ cosine_sim(embed(intent), embed(result))`

В коде: `accuracy` — **входной параметр**, не вычисляется. Нигде в проекте нет реализации `embed(intent)` vs `embed(result)`.

> **Вердикт:** `Q` в коде — заглушка, принимающая внешние значения. Внутренняя логика качества не реализована.

---

## 6. Risk Ψ — абстрактные коэффициенты без калибровки

**Канон:** `Ψ = P_fail·(C_direct + C_reputation)`

`P_fail = P_base·(1 + α_u·U + α_f·F + α_n·N + α_d·D)·(1 / (1 + α_s·S_skill))`

**В коде (`compute_psi`):**
```python
if arg_canonical:
    p_fail = P_base * (
        1.0 + alpha_u * uncertainty + alpha_f * fatigue +
        alpha_n * novelty + alpha_d * deadline
    ) * (1.0 / (1.0 + alpha_s * skill))
    return p_fail * (C_direct + C_reputation)
```
— каноническая ветка **есть**, но `arg_canonical` — параметр, который **никто не вызывает с True**. В `score_action`:
```python
psi = compute_psi(task, agent_context)
```
— без `canonical=True`, значит выполняется **legacy-ветка**:
```python
raw = (
    weights.uncertainty_coef * uncertainty +
    weights.fatigue_coef * fatigue +
    weights.novelty_coef * novelty +
    weights.deadline_coef * deadline +
    weights.skill_coef * skill
)
normalizer = max(sum_of_weights, 1e-9)
return _clamp(raw / normalizer)
```
— это **не** Ψ по канону! Это нормированная свёртка факторов, а не `P_fail·(C_direct + C_reputation)`.

**Проблема глубже:** Даже в канонической ветке коэффициенты `α_u, α_f, α_n, α_d, α_s` — статус [О] (экспертная оценка, не откалибрована). В реестре параметров Часть V: «самый неопределённый узел ядра».

> **Вердикт:** Ψ — самый слабый узел системы. Формула есть, но коэффициенты — догадки. Legacy-реализация вообще другая формула.

---

## 7. Решающее правило 𝒟(T) — логические дыры в каскаде

**Канон (5 уровней):**
1. REJECT — `Γ_hard = −∞`
2. DECLINE — `Ψ > ψ_max` или `C_t < C_min`
3. CLARIFY — `H_TZ > H_TZ,max` или `VoI > C_info` или `H < H_clarify`
4. EXECUTE — `U > 0` и `Q_predicted ≥ q_min`
5. DECLINE — иначе (`U ≤ 0`)

**В коде (`evaluate_decision_rule`):**
```python
# Level 1
if veto_type == VetoType.HARD or gamma_hard == float('-inf') or gamma_hard < -1e9:
    return "REJECT"

# Level 2
if psi > psi_max or C_t < C_min:
    return "DECLINE"

# Level 3
if H_TZ > H_TZ_max or VoI > C_info or H_val < H_clarify:
    return "CLARIFY"

# Level 4
if U_val > 0.0 and Q_predicted >= q_min:
    return "EXECUTE"

# Level 5
return "DECLINE"
```
— структурно совпадает. **Но:**

**Проблема 1 — `C_t` (вычислительный бюджет) в коде:**
```python
C_t = self.core_agent.metrics.balance  # в orchestrator/core.py
```
— **это баланс в долларах, не вычислительный бюджет!** Канон §IV.15 определяет `C_t = 1 − KV_Cache_used / Context_max` — это доля свободного контекста, не деньги.

> **Вердикт:** В коде `C_t` — деньги, в документации — контекст. Это разные вещи, и проверка `C_t < C_min` имеет совершенно другой смысл.

**Проблема 2 — `VoI` (Value of Information):**
Канон: `VoI = E[Φ|with info] − E[Φ|without info]`

В коде (`orchestrator/core.py`):
```python
voi_val = max(0.0, phi_hat * h_tz_val * 0.2)
```
— это **не** VoI. Это произведение прогнозной прибыли на энтропию с произвольным коэффициентом 0.2. Никакого сравнения «с информацией / без информации».

> **Вердикт:** VoI в коде — фикция. Формула не реализована.

**Проблема 3 — `Q_predicted` vs `q_min`:**
В `orchestrator/core.py`:
```python
q_min = task.metadata.get("quality_requirement", 0.5)
```
— `q_min` берётся из метаданных задачи, а не из Mission.calibrate(). Канон §IV.12: `q_min = base_quality(mission_type) · quality_boost(personality)`.

> **Вердикт:** Гейт по качеству не связан с Mission-профилем. Ещё одна развязка.

---

## 8. Kalman-фильтр — красивая формула, фиктивное использование

**Канон §IV.2:**
```python
Φ_historical(t) = Φ_historical(t−1) + K_t·(Φ_task(t) − Φ_historical(t−1))
K_t = σ²_prior / (σ²_prior + σ²_obs)
```

**В коде:**
```python
class KalmanFilter:
    def __init__(self, initial_state=0.0, Q=0.01, R=0.1, P=1.0):
        self.x = initial_state
        self.Q = Q  # process noise
        self.R = R  # measurement noise
        self.P = P  # estimate covariance

    def update(self, observed):
        K = self.P / (self.P + self.R)
        self.x = self.x + K * (observed - self.x)
        self.P = (1 - K) * self.P
        return self.x
```
— реализация корректна. **Но:**

**Где используется?**
```python
def update_phi_historical(prev, observed, kalman_gain):
    k = _clamp(kalman_gain)
    return prev + k * (observed - prev)
```
— есть wrapper, но **нигде в orchestrator не вызывается**. В `orchestrator/core.py`, Stage XI:
```python
# Operational recording
self.op_mem.set("task_id", task.id)
self.op_mem.update_metric("revenue", ...)
```
— нет обновления `Φ_historical`. Kalman-фильтр создан, но **не интегрирован в пайплайн**.

> **Вердикт:** Мёртвый код. Красивый, математически корректный, но не используемый.

---

## 9. Многомерная репутация Υ — скалярная свёртка с магическими числами

**Канон §IV.5:**
```python
Υ = (Υ_tech, Υ_econ, Υ_comm, Υ_rel, Υ_sec, Υ_domain)
Υ_scalar = Σ w_k · Υ_k, Σ w_k = 1
```

**В коде (`MultidimensionalReputation`):**
```python
def scalar_reputation(self):
    return _clamp(
        0.2 * self.tech + 0.2 * self.econ +
        0.15 * self.comm + 0.15 * self.rel +
        0.15 * self.sec + 0.15 * self.domain
    )
```
— веса **не суммируются в 1.0**: `0.2+0.2+0.15+0.15+0.15+0.15 = 1.0`. Ок, совпадает.

**Но** в `compute_upsilon_scalar`:
```python
weights.get("tech", 0.2) * rep.get("tech", 0.8) + ...
```
— дефолтные веса `0.2/0.2/0.15...`, но дефолтные значения репутации `0.8`. Если репутация не инициализирована, получаем `Υ_scalar ≈ 0.8` — **высокая репутация по умолчанию** для нового агента. Это контринтуитивно: новый агент должен иметь нейтральную или неопределённую репутацию, не высокую.

> **Вердикт:** Логика «новый агент = репутация 0.8» — нарушение здравого смысла. Должно быть 0.5 (нейтрально) или Bayesian prior с `m=7, μ_0=4.2` (из канона), что даёт ~0.6 при первой оценке.

---

## 10. Порядок обновления состояния — нарушен в коде

**Канон §XI.1:**
```python
Υ_k(t+1) → Φ_historical(t+1) → H(t+1)
```
— порядок важен, потому что H зависит от Υ и Φ.

**В коде (`orchestrator/core.py`, Stage XI):**
```python
# Operational recording
self.op_mem.set("task_id", task.id)
self.op_mem.update_metric("revenue", ...)
self.op_mem.update_metric("cost", ...)
self.op_mem.update_metric("risk", psi_hat)
self.op_mem.update_metric("quality", q_value)

# Consolidation
exp = self.consolidation_gate.consolidate(self.op_mem)
self.storage_mgr.persist(...)

# Stage XII
pressures = self.homeo.update_all(metrics_dict)
calibrated_weights = self.weights_calibrator.calibrate(pressures)
```
— `Υ` (через `consolidation_gate`) обновляется **после** записи в `op_mem`, но **H вычисляется в Stage II** (до обновления Υ!), а в Stage XII — `pressures = self.homeo.update_all(metrics_dict)` использует **старые** `metrics_dict`, не обновлённые Υ.

> **Вердикт:** Порядок нарушен. H вычисляется из устаревших данных. Канон явно предупреждал об этом, но код игнорирует.

---

## 11. Математические дефекты, не пойманные существующей самокритикой

### 11.1. `T(x) = T_0 · Π f_i(x_i)` без нижней границы

Если несколько `f_i < 1`, при достаточном числе факторов `T → 0`, а `Φ → ∞`. В каноне добавлена `ε_T`, но в коде:
```python
multiplier = max(0.1, min(10.0, 1.0 + delta_time))
duration = max(T_base * multiplier, 0.1 * T_base, 0.1)
```
— `0.1 * T_base` защищает от нуля, но **не от бесконечности Φ**. Если `T_base = 1`, `multiplier = 0.1`, получаем `duration = 0.1`, `Φ = (R−C)/0.1 = 10·(R−C)` — десятикратное завышение.

> **Вердикт:** Защита есть, но она не предотвращает экстремальные значения Φ. Нужен также верхний порог на Φ.

### 11.2. `Θ = 1 − (1/√N)·(σ_R/(R_max−R_min))` не определена при `N=0`

Канон исправляет: `√(N+1)`. В коде:
```python
# Не используется напрямую — bayesian_rating вычисляется отдельно
bayes_rating = (w.prior_strength * w.prior_mean + n_reviews_val * rating_val) / max(w.prior_strength + n_reviews_val, 1)
```
— `Θ` вообще **не реализована**. Используется только Bayesian rating.

> **Вердикт:** `Θ` (доверие к рейтингу) — пропущена. Код использует упрощённую версию.

### 11.3. Коллизии обозначений внутри одного документа

`α, β, γ, δ` используются в четырёх несовместимых ролях:
- Веса компонентов Q (§3.2)
- Коэффициенты в `S(x)` (§3.1.2)
- Веса benchmark-компонентов LLM (§6.2)
- Синергетические коэффициенты (§8)

В коде это частично разрешено через префиксы (`kappa_bonus`, `alpha_u` и т.д.), но не системно.

---

## 12. Оркестратор — «12-стадийный пайплайн» как театр теней

### 12.1. Stage I–V: Решение принимается на основе **прогнозных** значений

```python
phi_hat, q_predicted_hat, psi_hat = predict_estimates(...)
decision = evaluate_decision_rule(..., U_val=u_val, Q_predicted=q_predicted_hat, ...)
```
— ок, по канону.

### 12.2. Stage VI–VIII: Исполнение через **mock/SimulatedResponse**

```python
response_obj = self.ai_super_router.route_prompt_detailed(
    system_prompt="Execute specialized subroutine",
    user_prompt=f"You are {spec_name} executing Action: {action.name}..."
)
```
— LLM получает **просьбу «выполни действие»**, а не структурированный запрос с конкретным API/инструментом. Это prompt-based execution, not programmatic.

**Проверка «успеха»:**
```python
success = (
    bool(result_text) and
    len(result_text) > 10 and
    not result_text.startswith("Error") and
    not result_text.startswith("Exception")
)
```
— **это не проверка качества**. Это проверка «ответ не пустой и не начинается со слова Error». Формально агент может вернуть бессвязный набор слов длиной > 10 — и это засчитается как `success = True`.

### 12.3. Stage IX: Quality вычисляется из **флага success**, не из реального качества

```python
q_value = compute_quality(
    completeness=0.9 if execution_successful else 0.4,
    accuracy=0.85 if execution_successful else 0.5,
    fullness=0.9 if execution_successful else 0.3
)
```
— **жёстко зашитые константы**. Если `execution_successful = True` (по критерию «ответ > 10 символов»), получаем `Q = 0.9·0.25 + 0.85·0.25 + 0.9·0.25 + 0.7·0.25 ≈ 0.84` — **всегда**, независимо от реального содержания.

### 12.4. Stage X: Reflection — **не reflection, а повторная попытка с тем же кодом**

```python
if q_value < required_q:
    # ... remedial retry ...
    result_text = str(all_responses[-1].text)  # ТОТ ЖЕ ОТВЕТ!
    success = (bool(result_text) and len(result_text) > 10 ...)
```
— «исправление» использует **тот же ответ**, что и до reflection. Просто перепроверяется длина строки.

### 12.5. Stage XI: Запись в память — **не обновляет Υ, Φ_historical, H**

```python
self.op_mem.set("task_id", task.id)
self.op_mem.update_metric("revenue", ...)
# Нет update_upsilon!
# Нет update_phi_historical!
# Нет compute_h!
```

> **Вердикт:** Пайплайн — театр. Формы соблюдены, содержания нет. 12 стадий имитируют работу, но ключевые математические функции (обновление репутации, исторической прибыли, гомеостаза) — не вызываются.

---

## 13. Системные паттерны «анти-разработки»

### 13.1. «Документация как код»

В `orchestrator/core.py` ~50% строк — **docstrings и комментарии на русском**, описывающие, что «должно» происходить. Сам код делает что-то другое или заглушку.

### 13.2. «Двойная сигнатура» — легаси vs новая

Каждая функция в `utility/__init__.py` имеет 2+ сигнатуры:
```python
def compute_phi(task_or_price: Task | float | None = None, agent_or_quality: Agent | float | None = None, ...)
```
— это **не перегрузка**, это `if isinstance(...)` внутри. Код в 3 раза длиннее, чем нужно, и в 3 раза хрупче.

### 13.3. «Магические числа» вместо конфигурации

```python
c_exploration = 1.414  # sqrt(2)
tau = 0.1  # 10%
k_max = 3  # попытки
delay_max = 60  # секунд
```
— канон §IV.12 и §VII.1 требуют чтения из конфигурации. В коде — хардкод.

### 13.4. `get_config()` — глобальное состояние, не DI

```python
cfg = get_config()
w = cfg.weights.quality
```
— конфигурация читается глобально, не передаётся явно. Тестирование невозможно без мокирования глобального состояния.

---

## 14. Итоговый вердикт

| Проблема | Серьёзность | Где |
|---|---|---|
| Фундаментальный раскол продукта | 🔴 Критическая | Концепция |
| 4 несовместимые версии H | 🔴 Критическая | Документация + код |
| Γ=−∞ даёт U=+∞ (в старой версии) | 🔴 Критическая | `MATHEMATICAL_FORMULAS.md` |
| `C_t` — деньги вместо контекста | 🔴 Критическая | `orchestrator/core.py` |
| VoI — фикция | 🟠 Высокая | `orchestrator/core.py` |
| Φ без риск-корректировки | 🟠 Высокая | `utility/__init__.py` |
| Q — заглушка | 🟠 Высокая | `utility/__init__.py` |
| Ψ — legacy-формула по умолчанию | 🟠 Высокая | `utility/__init__.py` |
| Kalman — мёртвый код | 🟡 Средняя | `utility/__init__.py` |
| Порядок обновления Υ→Φ→H нарушен | 🟡 Средняя | `orchestrator/core.py` |
| Пайплайн — театр теней | 🟡 Средняя | `orchestrator/core.py` |
| Магические числа | 🟡 Средняя | Везде |
| Двойные сигнатуры | 🟡 Средняя | `utility/__init__.py` |
| Глобальный `get_config()` | 🟡 Средняя | Везде |

---

## 15. Что делать (приоритеты)

1. **Фаза 0 (1 неделя):** Решить — личный ассистент или автономный агент. Это меняет всё.
2. **Фаза 1 (2–3 недели):** Выбрать **одну** версию каждой функции, архивировать остальные. Не пытаться примирить 4 версии H — выбрать одну.
3. **Фаза 2 (3–4 недели):** Реализовать **минимальный замкнутый цикл**: `Task → Γ → Φ → Ψ → U → 𝒟(T) → Execute → Q_actual → Update(Υ, Φ_hist, H) → Test`. Без 17 факторов, без multi-agent, без 10-компонентного Q. Одна задача, один агент, 4 компоненты качества.
4. **Фаза 3 (2–3 недели):** Симулятор рынка. Без него все коэффициенты — догадки.
5. **Фаза 4+:** Только после проверки на симуляторе — расширение.

> **Главное правило:** Остановить генерацию новых документов. 15 архитектур в одном репозитории — это не богатство, это паралич.


# Дополнительный критический разбор Space1

## 16. TaskComplexityClassifier — «MLP» без нейросети, keyword-matching как наука

**Документация (03_PIPELINE_MATH.md):** «Ordinal MLP для классификации сложности задач».

**Реальность (`srs/models/task.py`):**
```python
self.complexity_keywords = {
    "critical": 1.0,
    "error": 0.8,
    "leak": 0.8,
    "refactor": 0.75,
    "database": 0.7,
    "api": 0.5,
    "fix": 0.4,
    "typo": 0.15,
    "update": 0.2,
}

def predict_complexity(self, title, description):
    text = (title + " " + description).lower()
    score_sum = 0.0
    matches = 0
    for kw, val in self.complexity_keywords.items():
        if kw in text:
            score_sum += val
            matches += 1
    if matches > 0:
        complexity_score = score_sum / matches
    else:
        # Эвристика: длинные задачи обычно сложнее
        word_count = len(text.split())
        if word_count < 5: complexity_score = 0.2
        elif word_count < 15: complexity_score = 0.4
        elif word_count < 30: complexity_score = 0.6
        else: complexity_score = 0.8
```

**Проблемы:**
- Это **не MLP**. Это словарь из 9 ключевых слов. Никаких слоёв, весов, обучения.
- «Энтропия» вычисляется через softmax от расстояний до 5 фиксированных центров — это **не энтропия предсказательной неопределённости**, это математический театр.
- «Self-consistency» (`m_runs=5`) добавляет гауссов шум к тому же keyword-matching — это **не self-consistency в смысле CoT-голосования**, это просто 5 раз запускается одна и та же функция с шумом.
- **Routing Decision:** если `complexity_score < 0.4` → AUTO_ASSIGN, иначе HUMAN_REVIEW. Но complexity_score определяется по наличию слова «typo» (0.15) или «critical» (1.0). Задача «Fix critical typo in API» получит score = (1.0 + 0.15)/2 = 0.575 → HUMAN_REVIEW. Задача «Deploy production database with critical security leak» = (0.7 + 1.0 + 0.8)/3 = 0.83 → ESCALATE. Это **не классификация сложности**, это keyword-counting.

> **Вердикт:** Название «MLP» — обман. Это простейший keyword matcher. Не работает для реальных задач, где сложность определяется не ключевыми словами, а архитектурой, зависимостями, масштабом.

---

## 17. Platt Scale — применена неверно

```python
def platt_scale(conf_raw: float, alpha: float = 1.0, beta: float = 0.0) -> float:
    return 1.0 / (1.0 + math.exp(-(alpha * conf_raw + beta)))
```

**Проблема:** Platt scaling — это **калибровка выходов классификатора** (обычно SVM) путём обучения логистической регрессии на валидационной выборке. Здесь же:
- `conf_raw = 1.0 - entropy` — это не выход классификора, это произвольная комбинация.
- `alpha=1.5, beta=0.2` — жёстко зашитые, не обученные.
- Функция нигде не используется для калибровки — она просто squashes значение через сигмоид.

> **Вердикт:** Это не Platt scaling. Это просто сигмоид с магическими коэффициентами. Название вводит в заблуждение.

---

## 18. Task.__post_init__ — side effects при создании объекта

```python
def __post_init__(self):
    if self.deadline is not None and self.deadline < datetime.now():
        raise ValueError(f"deadline не может быть в прошлом: {self.deadline}")
    self._update_deadline_fields()

    # Auto-classify complexity if not already present
    if "complexity" not in self.metadata:
        classifier = TaskComplexityClassifier()
        comp, entropy, routing, std_dev = classifier.predict_complexity_self_consistency(...)
        self.metadata["complexity"] = comp
        ...

    # Set priority critical if classifier recommends escalate
    if routing == "ESCALATE":
        self.priority = TaskPriority.CRITICAL
```

**Проблемы:**
1. **Валидация deadline в прошлом при десериализации:** Если загрузить задачу из БД, которая была создана вчера с deadline сегодня — `__post_init__` выбросит `ValueError`. Датакласс не должен валидировать бизнес-логику при создании.
2. **Мутация priority:** Пользователь явно передал `priority=MEDIUM`, но классификатор переопределил его в `CRITICAL` без предупреждения. Это **нарушение принципа наименьшего удивления**.
3. **Self-consistency при каждом создании:** `predict_complexity_self_consistency` делает 5 запусков с `random.gauss` — результат **недетерминированный**. Два одинаковых вызова `create_task("Fix bug")` дадут разные `complexity` и `priority`.

> **Вердикт:** `__post_init__` делает слишком много: валидация, вычисление, мутация. Нарушает SRP и делает поведение недетерминированным.

---

## 19. Urgency score — нелинейная логика с логическим разрывом

```python
if self.slack_time <= 0:
    self.urgency_score = 1.0
elif self.slack_time >= 24:
    # При slack > 24h urgency ниже среднего
    self.urgency_score = 0.5 * (1.0 - (self.slack_time - 24) / 100)
    self.urgency_score = max(0.1, self.urgency_score)
else:
    # Линейная интерполяция для 0-24h
    self.urgency_score = 1.0 - (self.slack_time / 48.0)
    self.urgency_score = max(0.1, min(0.95, self.urgency_score))
```

**Проблемы:**
- При `slack_time = 0` → `urgency = 1.0`
- При `slack_time = 1` → `urgency = 1.0 - 1/48 = 0.979`
- При `slack_time = 24` → `urgency = 1.0 - 24/48 = 0.5` (ветка else)
- При `slack_time = 25` → `urgency = 0.5 * (1.0 - 1/100) = 0.495` (ветка >=24)

**Разрыв:** В точке `slack_time = 24` переход из 0.5 (else) в 0.495 (>=24) — **скачок 0.005**. Не критичен, но показывает отсутствие единой формулы.

**Более серьёзно:** При `slack_time = 100` → `urgency = 0.5 * (1.0 - 76/100) = 0.12`. При `slack_time = 124` → `urgency = 0.5 * (1.0 - 100/100) = 0`. Но `max(0.1, ...)` → `0.1`. При `slack_time = 200` → `0.5 * (1.0 - 176/100) = -0.38` → `max(0.1, -0.38) = 0.1`. То есть задача с deadline через 200 часов имеет ту же urgency (0.1), что и задача через 124 часа. **Плато без различения**.

> **Вердикт:** Формула ad-hoc, без теоретического обоснования. Лучше использовать единую сигмоиду или экспоненту.

---

## 20. AgentCapabilities — 17 факторов, 4 из них «LLM-специфичные»

```python
# Core LLM (x₁-x₄)
llm_quality: float = 0.7
code_gen: float = 0.7
data_analysis: float = 0.7
llm_reasoning: float = 0.7

# Tools & Execution (x₅-x₇)
browser: float = 0.0
code_exec: float = 0.0
multimodal: float = 0.0

# Soft skills (x₈-x₁₀)
negotiation: float = 0.5
legal: float = 0.5
design: float = 0.5

# Domain expertise (x₁₁-x₁₃)
research: float = 0.5
testing: float = 0.5
devops: float = 0.5

# Specialized (x₁₄-x₁₇)
i18n: float = 0.5
accessibility: float = 0.5
performance: float = 0.5
security_audit: float = 0.5
```

**Проблема:** В каноне (02_MATHEMATICAL_CORE.md Приложение A) 17 факторов — это **возможности агента как фрилансера**: код, анализ данных, браузер, переговоры, юриспруденция, дизайн, исследования, тестирование, devops, i18n, accessibility, performance, security audit, data privacy.

Но в коде 4 из 17 — это **характеристики LLM** (`llm_quality`, `code_gen`, `data_analysis`, `llm_reasoning`), а не возможности агента. `code_gen` и `data_analysis` — это и есть навыки агента, но они дублируются с `llm_quality`/`llm_reasoning`. Нет чёткого разделения «что умеет LLM» vs «что умеет агент».

**Ещё:** `browser`, `code_exec`, `multimodal` — булевы возможности (0.0 или 1.0), но тип `float`. Это не continuous capability, это binary feature.

> **Вердикт:** Модель capabilities смешивает уровни абстракции. LLM-метрики и агент-навыки в одном списке без различения.

---

## 21. AgentMetrics.rating — веса репутации отличаются от канона

```python
@property
def rating(self) -> float:
    weights = {"tech": 0.20, "econ": 0.25, "comm": 0.15, "rel": 0.15, "sec": 0.15, "domain": 0.10}
    return sum(self.reputation_vector.get(k, 0.5) * w for k, w in weights.items())
```

**Канон (02_MATHEMATICAL_CORE.md §IV.5):**
```python
Υ_scalar = 0.20·Υ_tech + 0.20·Υ_econ + 0.15·Υ_comm + 0.15·Υ_rel + 0.15·Υ_sec + 0.15·Υ_domain
```

**Различие:**
- Канон: `tech=0.20, econ=0.20, comm=0.15, rel=0.15, sec=0.15, domain=0.15` → сумма = 1.0
- Код: `tech=0.20, econ=0.25, comm=0.15, rel=0.15, sec=0.15, domain=0.10` → сумма = 1.0

`econ` завышен на 0.05, `domain` занижен на 0.05. Это не случайность — это **разные веса в разных местах одного проекта**.

> **Вердикт:** Ещё одно расхождение документации и кода. Веса репутации не консистентны.

---

## 22. MetricRegistry.get() — создаёт метрику, если не найдена

```python
def get(self, metric: str, default: Optional[float] = 0.0) -> float:
    value = self._tracker.get(metric, default)
    if metric not in self._tracker.get_all():
        # Создаём метрику, чтобы она появилась в get_all()
        self._tracker._metrics[metric] = value
        self._tracker._history[metric] = []
        self._tracker._timestamps[metric] = __import__('time').time()
    return value
```

**Проблема:** `get()` — операция чтения — **мутирует состояние**, создавая метрику. Это нарушение контракта getter. Если вызвать `get("nonexistent")` → метрика создаётся со значением `default`. Последующий `get_all()` будет включать эту «метрику».

**Ещё хуже:** `__import__('time').time()` — динамический импорт внутри метода вместо `import time` в начале файла.

> **Вердикт:** Getter, который создаёт. Side effect при чтении. Антипаттерн.

---

## 23. MetricTracker — EMA без временных меток

```python
def update(self, metric: str, new_value: float, alpha: Optional[float] = None) -> float:
    alpha = alpha if alpha is not None else self._default_alpha
    if metric not in self._metrics:
        self._metrics[metric] = new_value
    else:
        current = self._metrics[metric]
        self._metrics[metric] = current + alpha * (new_value - current)
    return self._metrics[metric]
```

**Проблема:** EMA (Exponential Moving Average) обычно учитывает **временные интервалы** между обновлениями. Здесь `alpha` — фиксированный, не зависит от `dt`. Два обновления с интервалом 1 секунда и 1 час имеют одинаковый вес — это **не EMA по времени**, это просто экспоненциальное сглаживание по счётчику обновлений.

**Сравнение с каноном:** В `02_MATHEMATICAL_CORE.md` §IV.6 формула Φ_forget использует `e^(-λ·Δt)` — зависимость от времени явная. В MetricTracker — нет.

> **Вердикт:** «EMA» в названии — неточность. Это просто экспоненциальное сглаживание без временной компоненты.

---

## 24. PIDController — derivative term вычисляется неверно

```python
d_error = (error - self._state.last_error) / dt
d_term = self.kd * d_error
```

**Проблема:** Классическая формула PID:
- `de/dt = (e(t) - e(t-Δt)) / Δt` — это **конечная разность первого порядка** (backward difference).
- Но при первом вызове `last_error = 0`, `error = setpoint - measured`. Если `setpoint = 1.0, measured = 0.8` → `error = 0.2`, `last_error = 0` → `d_error = 0.2 / dt` — **огромный derivative spike** при старте.

**Отсутствует:**
- Derivative kick protection (setpoint weighting)
- Derivative filtering (low-pass на D-term)
- Anti-windup для integral (есть clamping, но не conditional integration)

> **Вердикт:** Базовая реализация PID, подходящая для демо, но не для production. Derivative spike при старте — известная проблема, не решённая.

---

## 25. HomeostaticRegulator.calculate_homeostasis — rating_ratio может быть > 1, но это не значит хорошо

```python
# 2. Rating ratio (no upper min(1.0, ...) cap to allow rating_ratio > 1.0 and H > 1.2)
rating_ratio = rating / max(rating_target, 1e-9)

# 3. Quality ratio (no upper min(1.0, ...) cap to allow quality_ratio > 1.0 and H > 1.2)
quality_ratio = quality / max(quality_target, 1e-9)
```

**Комментарий в коде:** «no upper min(1.0, ...) cap to allow rating_ratio > 1.0 and H > 1.2».

**Проблема:** Это **осознанное решение** (исправление бага из `homeostatic_state.py`, где H > 1.2 был недостижим). Но логика странная:
- `rating_ratio > 1.0` означает `rating > rating_target` — агент **превосходит цель**.
- В формуле stress: `w_R * (1.0 - rating_ratio)` — если `rating_ratio = 1.5`, то `(1.0 - 1.5) = -0.5`, stress **уменьшается** (отрицательный вклад).
- `H = 1.0 - stress` → H > 1.0 означает «лучше, чем целевое состояние».

Это **не гомеостаз** в классическом смысле. Гомеостаз — поддержание в пределах нормы, не максимизация. H > 1.0 означает «система в сверхоптимальном состоянии» — концептуально это не гомеостаз, это **эвтрофикация**.

> **Вердикт:** Исправление одного бага (H > 1.2 недостижим) создало другое: H > 1.0 — не гомеостаз. Нужна пересмотренная модель.

---

## 26. StateModifier — пороги «асимметричные», но логика симметричная

```python
class StateModifier:
    # Modifier thresholds (asymmetric)
    balance_high: float = 0.9  # Above this -> profit bonus
    balance_low: float = 0.3  # Below this -> profit penalty
    stress_high: float = 1.3   # Above this -> conservative
    reputation_low: float = 0.5  # Below this -> reputation bonus
    workload_high: float = 3.0   # Tasks in queue
    workload_low: float = 0.5      # Below this -> growth mode
```

**Проблема:** Пороги названы «асимметричными», но `balance_high=0.9` и `balance_low=0.3` — **не асимметрия**, это просто разные пороги. Асимметрия в гомеостазе означает разную скорость реакции на отклонение вверх/вниз (например, гипогликемия опаснее гипергликемии). Здесь — просто два порога с разными модификаторами.

**Ещё:** `stress_high = 1.3` — но stress в `calculate_homeostasis` вычисляется как взвешенная сумма, и при нормальных значениях rarely превышает 1.0. Порог 1.3 — **практически недостижим**.

> **Вердикт:** «Асимметричные» пороги — не асимметрия. Порог stress_high=1.3 — недостижим.

---

## 27. MissionPolicy.calibrate — нормализация после модификации, но модификации могут быть конфликтующими

```python
# Apply pressure adjustments
calibrated = dict(weights)
if "balance" in pressures and pressures["balance"] < 100:
    calibrated["profit_weight"] = min(1.0, calibrated["profit_weight"] * 1.2)
    calibrated["quality_weight"] = max(0.0, calibrated["quality_weight"] * 0.8)
if "stress" in pressures and pressures["stress"] > 0.7:
    calibrated["risk_weight"] = max(0.0, calibrated["risk_weight"] * 0.5)

# Normalize to sum = 1.0
total = sum(calibrated.values())
if total > 0:
    calibrated = {k: v / total for k, v in calibrated.items()}
```

**Проблема:** Если давление по балансу и стрессу активны одновременно:
- `profit_weight *= 1.2`, `quality_weight *= 0.8`, `risk_weight *= 0.5`
- Нормализация «исправит» сумму до 1.0, но **относительные пропорции изменятся непредсказуемо**.
- Например, SURVIVAL: `(0.40, 0.10, 0.30, 0.20)` → profit=0.48, risk=0.05, speed=0.30, quality=0.16 → нормализовано: `(0.44, 0.05, 0.28, 0.15)`. Risk weight стал 0.05 — **ниже, чем в CHARITY** (0.05). Это не «консервативный» режим, это **параноидальный**.

> **Вердикт:** Нормализация после независимых модификаций даёт непредсказуемые результаты. Нужна совместная оптимизация, а не последовательные правки.

---

## 28. ConsolidationGate._elevate_patterns — паттерны «высокого качества» с порогом 0.8, но quality_actual — заглушка

```python
# Pattern 1: High quality consistency
recent_quality = [e.quality_actual for e in all_eps[-5:] if e.status == "completed"]
if len(recent_quality) >= 3 and all(q > 0.8 for q in recent_quality[-3:]):
    self.semantic.add_fact(
        key="pattern_high_quality_consistency",
        value="Recent tasks consistently achieve high quality (Q > 0.8)",
        confidence=sum(recent_quality[-3:]) / 3,
        ...
    )
```

**Проблема:** `quality_actual` в Episode заполняется из `op_mem.get_metric("quality", 0.7)`. А в `orchestrator/core.py` Stage IX:
```python
q_value = compute_quality(
    completeness=0.9 if execution_successful else 0.4,
    accuracy=0.85 if execution_successful else 0.5,
    fullness=0.9 if execution_successful else 0.3
)
```
— `execution_successful` определяется как `len(result_text) > 10`. Так что `quality_actual` для успешных задач **всегда ≈ 0.84**. Паттерн «high quality consistency» сработает после 3 успешных задач подряд — то есть после 3 задач с ответом длиной > 10 символов.

> **Вердикт:** Pattern elevation работает с фиктивными данными. Выявленные «паттерны» — артефакты заглушек.

---

## 29. EpisodicMemory._build_tfidf_index — O(N²) при каждом добавлении эпизода

```python
def add_episode(self, episode: Episode) -> None:
    self._episodes.append(episode)
    self._tfidf_dirty = True  # Mark index for rebuild

def _build_tfidf_index(self) -> None:
    if not self._tfidf_dirty or not self._episodes:
        return
    # Rebuild TF-IDF from ALL episodes
    corpus = []
    for ep in self._episodes:
        text = f"{ep.title} {ep.strategy} {' '.join(ep.category_probs.keys())}"
        corpus.append(self._tokenize(text))
    # ... build full index ...
    self._tfidf_dirty = False
```

**Проблема:** При каждом добавлении эпизода индекс помечается «грязным» и **перестраивается полностью** при следующем запросе. Для N эпизодов — O(N²) суммарно. Для 1000 эпизодов — приемлемо. Для 100000 — катастрофа.

**Нет:**
- Инкрементального обновления индекса
- Отдельного потока для переиндексации
- Ограничения размера корпуса

> **Вердикт:** TF-IDF индекс — proof-of-concept, не production-ready. O(N²) перестроение не масштабируется.

---

## 30. SemanticMemory.confirm/contradict — формулы с фиксированными коэффициентами, не доказательные

```python
def confirm(self, key: str) -> bool:
    fact.confidence = 0.9 * fact.confidence + 0.1
    fact.confidence = min(1.0, fact.confidence)

def contradict(self, key: str) -> bool:
    fact.confidence = 0.7 * fact.confidence
    fact.contradictions += 1
```

**Проблема:** Коэффициенты 0.9/0.1 и 0.7 — **не выведены из теории вероятностей**. Это не Bayesian update с proper prior. Это ad-hoc эвристика.

**Сравнение с каноном:** В `02_MATHEMATICAL_CORE.md` §IV.6 формула Φ_forget: `Φ_forget(t) = Φ_historical · e^(-λ·Δt)` — экспоненциальное затухание с обоснованием из теории надежности. В SemanticMemory — нет такого обоснования.

**Ещё:** `contradictions` увеличивается, но `confidence` просто умножается на 0.7. После 3 contradictions: `confidence * 0.7^3 = confidence * 0.343`. После 10: `confidence * 0.028`. Это **экспоненциальное затухание без нижней границы** — факт может иметь confidence ~0, но всё ещё существовать в памяти.

> **Вердикт:** Update rules — эвристики без теоретического обоснования. Нижняя граница confidence отсутствует.

---

## 31. TriggerSystem — обработка событий без гарантий доставки

```python
def handle_event(self, event_name: str, payload: Optional[Dict[str, Any]] = None) -> List[str]:
    fired = []
    for trigger in self._event_triggers:
        if trigger.check(event_name, payload):
            trigger.fire(event_name, payload)
            fired.append(trigger.name)
    return fired
```

**Проблема:**
- Если callback выбрасывает исключение — **все последующие триггеры не обрабатываются**.
- Нет persistence: при перезапуске агента все триггеры теряются.
- Нет приоритизации: критический триггер «баланс < 0» и информационный триггер «новое сообщение» обрабатываются в одной очереди.

> **Вердикт:** Триггерная система — in-memory proof-of-concept. Не fault-tolerant, не persistent.

---

## 32. TaskDecomposer — бюджет распределяется пропорционально, но не проверяется

```python
Action(name=f"security_audit{suffix}", resource_cost=0.15 * budget, params={...})
Action(name=f"implement_auth{suffix}", resource_cost=0.35 * budget, params={...})
Action(name=f"verify_encryption{suffix}", resource_cost=0.10 * budget, params={...})
```

**Проблема:** `resource_cost` — это **доля от budget**, не абсолютная стоимость. Если `budget = 10.0`, то costs = 1.5, 3.5, 1.0. Сумма = 6.0 < 10.0. Но нигде не проверяется, что сумма costs ≤ budget. Для категории «deploy» сумма = 0.20 + 0.40 + 0.15 = 0.75. Для «finance» = 0.10 + 0.30 + 0.10 = 0.50. **Никогда не превышает 100%**, но и не использует бюджет полностью.

**Ещё:** `budget` передаётся как параметр, но `Task` имеет поле `price` — нет связи между `task.price` и `budget`.

> **Вердикт:** Декомпозиция — keyword-based template matching. Бюджет — декоративный параметр.

---

## 33. CircuitBreaker — theta_fail=0.99 означает почти невозможный переход в OPEN

```python
cb = CircuitBreaker(failure_threshold=2, cooldown_seconds=0.1, theta_fail=0.99)
```

**Проблема:** `theta_fail` — порог вероятности ошибки для перехода в OPEN. 0.99 означает, что нужна **99% уверенность** в ошибке. С `failure_threshold=2` (2 ошибки подряд) это невозможно достичь статистически при малом числе наблюдений. Circuit breaker **никогда не перейдёт в OPEN** при реальных данных.

**В тесте:**
```python
cb.record_failure()
cb.record_failure()  # 2 failures -> state == "OPEN"?
```
— тест проверяет `assert cb.state == "OPEN"`, но это работает только потому, что `record_failure()` инкрементит счётчик напрямую, не через вероятностную модель.

> **Вердикт:** theta_fail=0.99 делает CircuitBreaker бесполезным. Либо порог должен быть ~0.5, либо нужна Bayesian оценка с достаточным числом наблюдений.

---

## 34. Memory/core.py — dataclass_from_dict хрупкая

```python
def dataclass_from_dict(cls, d):
    return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})
```

**Проблема:**
- Не обрабатывает nested dataclasses
- Не обрабатывает `field(default_factory=...)` — если в dict нет ключа, который имеет `default_factory`, будет ошибка
- Не валидирует типы
- Используется в `get_fact`, `get_all_facts` — при десериализации из хранилища может сломаться

> **Вердикт:** Сериализация/десериализация — ad-hoc, не robust. Для production нужен `dacite` или `pydantic`.

---

## 35. Orchestrator Stage XII — HomeostaticUtilityModulator не используется

В `orchestrator/core.py` Stage XII:
```python
pressures = self.homeo.update_all(metrics_dict)
calibrated_weights = self.weights_calibrator.calibrate(pressures)
```

Но `HomeostaticUtilityModulator` (из `test_orchestrator.py`) — отдельный класс, который:
```python
def modulate(self, base_utility, pressures):
    # Zone 1: Complacency (total sum of positive pressures = 0.1)
    # f = 0.5 + 1.0 * total = 0.6
    ...
```

— **не вызывается в orchestrator**. Есть `update_all` (вычисляет давления) и `calibrate` (калибрует веса), но нет `modulate` (модулирует utility). Модуль `HomeostaticUtilityModulator` — мёртвый код, как и KalmanFilter.

> **Вердикт:** Ещё один мёртвый модуль. Создан для тестов, не интегрирован в пайплайн.

---

## 36. Глобальное состояние через get_config() — проблема тестируемости

```python
# В utility/__init__.py, control.py, и десятках других файлов
cfg = get_config()
w = cfg.weights.quality
```

**Проблема:** `get_config()` — глобальная функция, возвращающая singleton-конфигурацию. Это означает:
- Невозможно запустить два агента с разными конфигурациями в одном процессе
- Тесты мутируют глобальное состояние → order-dependent failures
- Невозможно сделать dependency injection

**Веса в YAML (`config/weights.yaml`):**
```yaml
utility:
  profit_weight: 0.30
  reputation_weight: 0.25
  evolution_weight: 0.20
  quality_weight: 0.25
```

— но в `MissionPolicy._PRESETS`:
```python
MissionProfile.SURVIVAL: {"profit": 0.40, "risk": 0.10, "speed": 0.30, "quality": 0.20}
```

— разные имена (`profit_weight` vs `profit`), разные структуры. Нет единого источника истины.

> **Вердикт:** Глобальная конфигурация + дублирование весов в коде = невозможность управлять поведением централизованно.

---

## 37. Test suite — тесты проверяют форму, не содержание

**test_utility.py:**
```python
def test_compute_phi_public_api():
    assert space1.compute_phi(revenue=50.0, cost=10.0, time_hours=2.0) == 20.0
    # (50-10)/2 = 20. Correct.

def test_compute_phi_from_task_like_object():
    assert compute_phi(TaskLike()) == 45.0
    # TaskLike: revenue=100, estimated_hours=2.0, cost=10.0
    # (100-10)/2 = 45. Correct.

def test_compute_phi_includes_token_tracker_cost():
    tracker = TokenCostTracker()
    tracker.record("gpt-4o-mini", 1000, 500)
    result = compute_phi(revenue=1.0, cost=0.0, time_hours=1.0, token_tracker=tracker)
    assert abs(result - 0.99955) < 0.00001
    # Token cost for 1500 tokens at $0.00055/1K = $0.000825
    # (1.0 - 0.000825)/1.0 = 0.999175
    # But test expects 0.99955 — mismatch!
```

**Проблема:** Последний тест — **неверный**. Стоимость 1500 токенов gpt-4o-mini:
- Input: 1000 tokens @ $0.00015/1K = $0.00015
- Output: 500 tokens @ $0.00060/1K = $0.00030
- Total: $0.00045
- Φ = (1.0 - 0.00045) / 1.0 = 0.99955

Тест ожидает 0.99955, но если `TokenCostTracker` считает по-другому — тест может падать или проходить по случайности. **Тест проверяет магическое число, не логику.**

**test_orchestrator.py:**
```python
def test_signal_to_context_synthesizer_survival(self):
    memory = StrategicMemory()
    memory.add_experience(StrategicExperience(...))
    synthesizer = SignalToContextSynthesizer(memory=memory)
    metrics = {"balance": 2.0, "success_rate": 0.8, ...}
    context = synthesizer.synthesize(metrics, task=task)
    assert "Mode: SURVIVAL" in context.situation
    assert context.recommended_tone == "CONSERVATIVE / SURVIVAL ONLY"
```

— тест проверяет **строки в выводе**, не математическую корректность. Если `synthesize` вернёт «Mode: SURVIVAL (simulated)» — тест упадёт.

> **Вердикт:** Тесты — smoke tests, не unit tests. Проверяют наличие строк, не корректность вычислений.

---

## 38. Финансовая модель — нет учёта валюты, инфляции, налогов

Вся система работает с «долларами» как безразмерными числами:
- `balance: float = 0.0`
- `price_per_task: float = 50.0`
- `Φ = (R - C) / T` [$/час]

**Нет:**
- Валюты (USD, EUR, RUB)
- Налогов (self-employment tax, VAT)
- Комиссий платформы (Upwork 20%, Fiverr 20%)
- Инфляции
- Курсов валют
- Платёжных циклов (NET-30, escrow)

Для «автономного экономического агента» это критично. Агент, не учитывающий налоги и комиссии, **банкротится в реальности**.

> **Вердикт:** Финансовая модель — игрушечная. Не применима к реальному фрилансу.

---

## 39. Нет механизма обучения на реальных данных

Вся система построена на:
- Экспертных оценках (коэффициенты [О])
- Симулированных данных (mock responses)
- Keyword matching (decomposer, classifier)

**Нет:**
- Сбора данных с реальных платформ (Upwork, Freelancer)
- A/B тестирования стратегий
- Онлайн-обучения (bandit algorithms)
- Feedback loop с реальными клиентами

> **Вердикт:** Система — «simulator in a vacuum». Без реальных данных все коэффициенты — догадки.

---

## 40. Дублирование MissionType и MissionProfile

```python
# srs/mission/core.py
class MissionType(Enum):
    SURVIVAL = "survival"
    GROWTH = "growth"
    MAINTENANCE = "maintenance"
    MAXIMIZE = "maximize"
    PREMIUM = "premium"
    CHARITY = "charity"

class MissionProfile(Enum):
    SURVIVAL = "survival"
    GROWTH = "growth"
    MAINTENANCE = "maintenance"
    MAXIMIZE = "maximize"
    PREMIUM = "premium"
    CHARITY = "charity"
```

— **два идентичных enum** в одном файле. `MissionType` используется в `Mission`, `MissionProfile` — в `MissionPolicy`. Это не разные концепции, это **дублирование**.

> **Вердикт:** Два enum для одного понятия. Технический долг сразу при создании.


# Дополнительный критический разбор Space1 — Часть 2

## 41. AIOSSToolManager — UCB1 с бинарными rewards, но reward = 1.0/0.0 не отражает качество

```python
def record_outcome(self, name: str, success: bool) -> None:
    if name in self._stats:
        self._stats[name]["selections"] += 1
        self._stats[name]["rewards_sum"] += 1.0 if success else 0.0
        self._total_selections += 1

def select_best_specialist(self, candidates: List[str]) -> str:
    for name in candidates:
        if name in self._stats and self._stats[name]["selections"] == 0:
            return name  # Cold start

    for name in candidates:
        stats = self._stats.get(name, {"selections": 0, "rewards_sum": 0.0})
        n_i = stats["selections"]
        if n_i == 0:
            continue
        mean_reward = stats["rewards_sum"] / n_i
        ucb_score = mean_reward + self.c * math.sqrt(math.log(max(1, self._total_selections)) / n_i)
```

**Проблема:** UCB1 — алгоритм для **multi-armed bandit с непрерывными rewards**. Здесь reward бинарный (1.0/0.0), что технически работает, но:
- `success` определяется как `len(result_text) > 10` — reward 1.0 за бессвязный набор слов
- Нет градации качества: задача выполненная на 90% и на 10% получают одинаковый reward
- UCB1 exploration term (`c * sqrt(log(N)/n_i)`) с `c=1.414` — для бинарных rewards лучше использовать **Thompson Sampling** или **Bayesian UCB**

**Ещё:** Cold start выбирает **первого** кандидата с нулевыми попытками, не случайного. Это детерминированный bias к порядку в списке.

> **Вердикт:** UCB1 применён формально, но reward model — фикция. Exploration/exploitation trade-off работает с мусорными данными.

---

## 42. TaskDecomposer — категории определены жёстко, без расширяемости

```python
categories = {
    "security": ["security", "auth", "encrypt", "vulnerability", "penetration", "firewall", "oauth", "jwt", "ssl", "tls"],
    "performance": ["performance", "optimize", "speed", "latency", "cache", "memory", "cpu", "bottleneck", "profiling"],
    "database": ["database", "sql", "query", "schema", "migration", "index", "postgres", "mysql", "mongodb", "redis"],
    "api": ["api", "endpoint", "rest", "graphql", "swagger", "openapi", "http", "request", "response"],
    "frontend": ["frontend", "ui", "ux", "react", "vue", "angular", "css", "html", "component", "responsive"],
    "devops": ["devops", "deploy", "ci/cd", "docker", "kubernetes", "terraform", "aws", "azure", "gcp", "pipeline"],
    "testing": ["testing", "test", "unit", "integration", "e2e", "jest", "pytest", "coverage", "mock", "fixture"],
    "documentation": ["documentation", "docs", "readme", "wiki", "guide", "tutorial", "manual", "api-doc"],
    "refactoring": ["refactoring", "refactor", "clean", "legacy", "technical-debt", "code-quality", "maintainability"],
    "feature": ["feature", "implement", "add", "new", "enhancement", "capability", "functionality"],
    "bugfix": ["bugfix", "bug", "fix", "error", "crash", "issue", "defect", "regression", "hotfix"],
    "research": ["research", "investigate", "analyze", "study", "explore", "prototype", "spike", "feasibility"],
    "integration": ["integration", "integrate", "connect", "sync", "webhook", "third-party", "external", "adapter"],
    "compliance": ["compliance", "gdpr", "hipaa", "soc2", "audit", "regulation", "privacy", "security-standard"],
    "finance": ["finance", "payment", "billing", "invoice", "subscription", "pricing", "revenue", "cost"],
}
```

**Проблема:**
- 15 категорий, 10+ ключевых слов каждая — **ручная курируемая таксономия**
- Нет механизма добавления новых категорий без правки кода
- Пересечения: «security» есть и в `security`, и в `compliance`. Задача «GDPR security audit» попадёт в обе категории, но выбирается только одна (первая по порядку проверки)
- «jwt» — это security, но задача «Implement JWT refresh token» — это скорее feature

> **Вердикт:** Декомпозиция — keyword matching с жёсткой таксономией. Не масштабируется, не адаптируется к новым доменам.

---

## 43. TaskDecomposer — бюджет делится фиксированными долями, не зависит от реальной сложности

```python
"security": {
    "actions": [
        Action(name=f"security_audit{suffix}", resource_cost=0.15 * budget, ...),
        Action(name=f"implement_auth{suffix}", resource_cost=0.35 * budget, ...),
        Action(name=f"verify_encryption{suffix}", resource_cost=0.10 * budget, ...),
    ],
    "total_cost": 0.60 * budget,
}
```

**Проблема:**
- `resource_cost` — это **доля от budget**, не реальная оценка в часах/долларах
- Для категории «security» сумма = 0.15 + 0.35 + 0.10 = 0.60. Но нигде не проверяется, что сумма ≤ 1.0
- Для «finance» сумма = 0.10 + 0.30 + 0.10 = 0.50 — **половина бюджета не используется**
- Нет связи с `task.estimated_hours` — бюджет и время — ортогональные величины

> **Вердикт:** Бюджет — декоративный параметр. Распределение фиксировано и не адаптируется под задачу.

---

## 44. AgentState — критерий `is_critical` с жёсткими порогами, не калибруется

```python
def is_critical(self) -> bool:
    return (
        self.balance < 10.0 or
        self.reputation < 0.2 or
        self.stress_level > 0.9 or
        self.health_score < 0.3
    )
```

**Проблема:**
- `balance < 10.0` — 10 долларов? 10 тысяч? Нет валюты, нет масштаба
- `reputation < 0.2` — при дефолтном значении 0.5 новый агент **не критичен**, но при первой неудаче (reputation падает) — сразу критичен
- `stress_level > 0.9` — stress вычисляется как `1.0 - H`, где H может быть > 1.0. При H = 1.5, stress = -0.5 — **никогда не превысит 0.9**
- Пороги жёстко зашиты, не зависят от Mission

> **Вердикт:** Критерий критичности — ad-hoc, не связан с математической моделью. Пороги не калиброваны.

---

## 45. MissionExecutionContext — поля `phi`, `psi`, `upsilon`, `quality` дублируют AgentMetrics

```python
@dataclass
class MissionExecutionContext:
    mission_id: str
    mission_name: str
    mission_type: str = "MAINTENANCE"

    # Metrics
    phi: float = 0.0     # Profit component
    psi: float = 0.0     # Risk component  
    upsilon: float = 0.5 # Reputation component
    quality: float = 0.7 # Quality score
```

**Проблема:**
- `AgentMetrics` уже имеет `balance`, `reputation`, `stress_level`
- `MissionExecutionContext` дублирует логически связанные метрики под другими именами
- Нет единого источника: `phi` в контексте vs `balance` в метриках — это разные вещи или одно и то же?
- `quality` здесь — оценка задачи, но в `AgentMetrics` нет поля для качества выполненных задач

> **Вердикт:** Дублирование метрик в разных dataclass'ах без чёткой семантики. Риск рассинхронизации.

---

## 46. TransformationContext — `actor` как строка, не типизированная ссылка

```python
@dataclass
class TransformationContext:
    state: AgentState
    actor: str  # Agent name
    timestamp: datetime = field(default_factory=datetime.now)
    source_module: str = ""
    source_operation: str = ""
```

**Проблема:**
- `actor` — строка с именем агента, не ссылка на объект `Agent`
- Нет валидации: можно передать несуществующее имя
- Нет связи с реальным агентом: трансформация записывает «actor="Alice"», но Alice может быть удалена

> **Вердикт:** Слабая типизация. Строковые идентификаторы вместо ссылок — источник ошибок.

---

## 47. EventRecord — синтаксическая ошибка в `to_dict`

```python
def to_dict(self) -> Dict[str, Any]:
    return {
        "event_id": self.event_id,
        "event_type": self.event_type,
        "sequence_number": self.sequence_number,
        "caused_by": self.caused_by
        "affects": self.affects,
        ...
    }
```

**Проблема:** После `"caused_by": self.caused_by` **нет запятой**. Это `SyntaxError` — код не запустится.

> **Вердикт:** Синтаксическая ошибка в production-коде. Линтер/CI должен был поймать.

---

## 48. EventRecord — `state_snapshot` хранит полный AgentState, но без версионирования

```python
state_snapshot: Optional[AgentState] = None
```

**Проблема:**
- Каждый EventRecord хранит **полную копию** AgentState
- При 1000 событиях — 1000 копий состояния
- Нет дедупликации: если состояние не изменилось между событиями — всё равно копируется
- Нет версионирования схемы: если AgentState изменится — старые snapshot'ы сломаются при десериализации

> **Вердикт:** Хранение полного состояния в каждом событии — избыточно. Нужны дельты или версионирование.

---

## 49. HomeostaticRegulator — `update_all` вызывает `calculate_homeostasis`, но тут же перезаписывает `stress_level`

```python
def update_all(self, metrics: Dict[str, float]) -> Dict[str, float]:
    # Inject newly calculated canonical stress_level into metrics if not already present
    if "stress_level" not in metrics:
        _, stress = self.calculate_homeostasis(metrics)
        metrics["stress_level"] = max(0.0, stress)

    for level, thresholds in self.THRESHOLDS.items():
        for metric, threshold in thresholds.items():
            if metric in metrics:
                if metric in ["stress_level"]:
                    setpoint = threshold * 0.5
                else:
                    setpoint = threshold * 1.2

                self.update_metric(metric, setpoint, metrics[metric])

    return self._pressures.copy()
```

**Проблема:**
- `calculate_homeostasis` вычисляет `stress` из метрик
- Затем `stress_level` добавляется в `metrics`
- Затем для `stress_level` вызывается `update_metric` с `setpoint = threshold * 0.5`
- Но `threshold` для `stress_level` = 0.8, значит `setpoint = 0.4`
- PID получает `setpoint=0.4, measured=stress` — **регулирует stress к 0.4**, а не к минимуму

**Логика:** Хотим минимизировать stress (цель = 0), но setpoint = 0.4 означает «stress = 0.4 — это норма». Это **не минимизация**, это стабилизация вокруг 0.4.

> **Вердикт:** PID для stress настроен на стабилизацию, не минимизацию. Конфликт с каноном, где цель — минимизировать stress.

---

## 50. HomeostaticRegulator — `get_mode` hysteresis логика нарушает инварианты

```python
def get_mode(self) -> str:
    survival_pressure = max(
        (self._pressures.get(m, 0) for m in self.THRESHOLDS["survival"]),
        default=0
    )

    if self._mode == "survival":
        if survival_pressure > 0.15:
            self._mode = "survival"
            return "survival"
    else:
        if survival_pressure > 0.3:
            self._mode = "survival"
            return "survival"

    growth_pressure = max(...)

    if self._mode == "growth":
        if growth_pressure < -0.05:
            self._mode = "growth"
            return "growth"
    else:
        if growth_pressure < -0.1:
            self._mode = "growth"
            return "growth"

    self._mode = "normal"
    return "normal"
```

**Проблема:**
- Если `_mode == "survival"` и `survival_pressure = 0.2` (> 0.15) — остаёмся в survival
- Если `_mode == "normal"` и `survival_pressure = 0.2` — проверяем `> 0.3`? Нет, 0.2 < 0.3 — переходим к growth
- Но `survival_pressure = 0.2` — это высокое давление! Почему normal не переключается в survival?

**Hysteresis работает только для выхода из режима, не для входа.** Входной порог (0.3) выше выходного (0.15), но если система в normal — она **не видит** survival_pressure = 0.2 как угрозу.

> **Вердикт:** Hysteresis защищает от быстрого переключения, но создаёт «слепую зону» между 0.15 и 0.3, где система не реагирует на survival pressure.

---

## 51. HomeostaticRegulator — `get_weight_adjustment` нормализует веса, но не сохраняет zero-weights

```python
def get_weight_adjustment(self, base_weights: Dict[str, float]) -> Dict[str, float]:
    mode = self.get_mode()
    adjusted = dict(base_weights)

    if mode == "survival":
        adjusted["profit_weight"] = min(1.0, adjusted.get("profit_weight", 0.3) * 1.5)
        adjusted["evolution_weight"] = max(0.0, adjusted.get("evolution_weight", 0.2) * 0.5)
    elif mode == "growth":
        adjusted["evolution_weight"] = min(1.0, adjusted.get("evolution_weight", 0.2) * 1.3)
        adjusted["profit_weight"] = max(0.0, adjusted.get("profit_weight", 0.3) * 0.9)

    total = sum(adjusted.values())
    if total > 0:
        adjusted = {k: v / total for k, v in adjusted.items()}

    return adjusted
```

**Проблема:**
- Если `base_weights = {"profit": 0.4, "risk": 0.1, "speed": 0.3, "quality": 0.2}` (SURVIVAL preset)
- В survival mode: profit = 0.4 * 1.5 = 0.6, evolution (не существует в preset!) = 0.2 * 0.5 = 0.1
- Но в preset нет ключа "evolution_weight"! `adjusted.get("evolution_weight", 0.2)` возвращает 0.2 — **вводит новый вес, которого не было в preset**
- Нормализация: `(0.6 + 0.1 + 0.3 + 0.2) = 1.2` → `(0.5, 0.083, 0.25, 0.167)`
- Risk weight (0.1) стал 0.083 — **уменьшился без явной команды**

> **Вердикт:** Нормализация после независимых модификаций — непредсказуема. Веса, не упомянутые в логике mode, тоже изменяются.

---

## 52. PIDController — `dt <= 0` защита создаёт искусственный шаг

```python
now = time.time()
dt = now - self._state.last_time

if dt <= 0:
    dt = 1e-6  # Prevent division by zero
```

**Проблема:**
- Если два вызова подряд в одну и ту же миллисекунду — `dt = 1e-6`
- Derivative term: `d_error = (error - last_error) / 1e-6` — **огромное значение**
- Integral term: `integral += error * 1e-6` — **практически ноль**
- PID выдаёт spike на derivative, ничего не интегрирует

**Реальное решение:** Если `dt` слишком мал — **не обновлять**, вернуть предыдущий output.

> **Вердикт:** Защита от dt=0 хуже, чем сама проблема. Создаёт нефизичные сигналы.

---

## 53. PIDController — `output_limit` clamps сумму, но не отдельные terms

```python
output = p_term + i_term + d_term
output = max(-self.output_limit, min(self.output_limit, output))
```

**Проблема:**
- Если `p_term = 0.8, i_term = 0.5, d_term = 0.3` — сумма = 1.6, clamp to 1.0
- Но integral продолжает расти: `integral += error * dt` — **anti-windup не работает**
- Clamping output не предотвращает windup integral

**Канон §IV.13:** «Integral windup: если u(t) насыщен, интеграл не должен накапливаться». В коде — нет conditional integration.

> **Вердикт:** Anti-windup — декларативный (clamping), не функциональный. Integral накапливается даже при saturation.

---

## 54. HomeostaticRegulator.THRESHOLDS — метрики разных масштабов в одном max()

```python
"survival": {
    "balance": 10.0,      # $ — абсолютная величина
    "success_rate": 0.2,  # [0, 1] — относительная
    "stress_level": 0.8,  # [0, 1] — относительная
}
```

**Проблема:**
- `survival_pressure = max(pressures.get("balance", 0), pressures.get("success_rate", 0), pressures.get("stress_level", 0))`
- Pressure для balance: PID output, масштаб ~[-1, 1] (из-за output_limit=1.0)
- Pressure для success_rate: тоже ~[-1, 1]
- Pressure для stress_level: тоже ~[-1, 1]
- **Но** исходные метрики — разных масштабов: balance в долларах, success_rate в долях
- PID «нормализует» через setpoint/measured, но масштабирование не явное

> **Вердикт:** Разные метрики приводятся к одному масштабу через PID неявно. Нет явной нормализации перед сравнением.

---

## 55. AIOSSToolManager — `c_exploration = 1.414` (sqrt(2)) без обоснования

```python
def __init__(self, c_exploration: float = 1.414):
    self.c = c_exploration
```

**Проблема:**
- `sqrt(2)` — популярный выбор для UCB1, но **теоретически обоснован только для bounded rewards in [0,1]**
- Здесь rewards бинарные {0, 1}, но «успех» определяется произвольно
- Для реальных задач лучше использовать `c = sqrt(2 * ln(...))` или адаптивный `c`

> **Вердикт:** Магическое число без адаптации к домену. sqrt(2) — default из учебников, не калибровано.

---

## 56. TaskComplexityClassifier — `self_consistency` добавляет гауссов шум к детерминированной функции

```python
def predict_complexity_self_consistency(self, title, description, m_runs=5):
    scores = []
    for _ in range(m_runs):
        noise = random.gauss(0, 0.05)
        score, entropy, routing = self.predict_complexity(title, description)
        scores.append(max(0.0, min(1.0, score + noise)))

    mean_score = sum(scores) / len(scores)
    std_dev = (sum((s - mean_score) ** 2 for s in scores) / len(scores)) ** 0.5
    return mean_score, std_dev, routing, std_dev
```

**Проблема:**
- `predict_complexity` — детерминированная функция (keyword matching)
- Добавление шума и усреднение — **не self-consistency** в смысле CoT
- Self-consistency (Wang et al.) — агрегация **разных рассуждений** к одному ответу
- Здесь — агрегация **одного рассуждения с шумом** — это просто сглаживание
- `std_dev` возвращается дважды: как 2-й и 4-й элемент tuple

> **Вердикт:** Не self-consistency. Это Monte Carlo smoothing детерминированной функции. Название вводит в заблуждение.

---

## 57. TokenCostTracker — цены в `$ per 1M tokens`, но деление на `1_000_000`

```python
def _calc_cost(self, usage: TokenUsage) -> float:
    in_price, out_price = self._config.get_price(usage.model)
    return (usage.input_tokens / 1_000_000) * in_price +            (usage.output_tokens / 1_000_000) * out_price
```

**Проблема:**
- Цены в конфиге: `"gpt-4o-mini": (0.15, 0.60)` — это **$ per 1M tokens**
- Деление на 1_000_000 — корректно
- Но `get_total_cost()` возвращает `base + tokens + tools`, где `base` — не определён по умолчанию
- `set_base_cost()` — отдельный метод, легко забыть вызвать

> **Вердикт:** Формула корректна, но API позволяет забыть base cost. Не fail-safe.

---

## 58. TokenCostConfig — цены захардкожены, не обновляются

```python
prices_per_million: Dict[str, tuple] = field(default_factory=lambda: {
    "gpt-4o": (5.0, 15.0),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4-turbo": (10.0, 30.0),
    "gpt-3.5-turbo": (0.5, 1.5),
    "claude-3-5-sonnet": (3.0, 15.0),
    ...
})
```

**Проблема:**
- Цены OpenAI/Anthropic меняются. Хардкод — устареет
- Нет fallback для новых моделей — только "unknown": (1.0, 3.0)
- Нет валидации: можно передать `model="gpt-5"` — получить цену "unknown"

> **Вердикт:** Цены — статичные данные, не сервис. Нужен API для получения актуальных цен.

---

## 59. Scheduler — `deserialize_task` создаёт Task, затем мутирует приватные поля

```python
def deserialize_task(d: dict) -> Task:
    task = Task(
        id=d["id"],
        title=d["title"],
        ...
    )
    task.created_at = created_at  # Мутация после создания!
    task.started_at = started_at
    task.completed_at = completed_at
    task.urgency_score = d.get("urgency_score", 0.5)
    task.slack_time = d.get("slack_time", 24.0)
    return task
```

**Проблема:**
- `Task` — dataclass с `frozen=False` (по умолчанию)
- Мутация после `__post_init__` — `urgency_score` и `slack_time` вычисляются в `__post_init__`, но здесь перезаписываются
- Если `deadline` в прошлом — `__post_init__` выбросит `ValueError` до мутации
- Нет единого метода `from_dict` в самом Task

> **Вердикт:** Десериализация — ad-hoc, нарушает инкапсуляцию Task. Должна быть методом класса.

---

## 60. Scheduler — `pop_next_task` сортирует всю очередь при каждом вызове

```python
def pop_next_task(self) -> Optional[Task]:
    if not self._queue:
        return None

    self._queue.sort(key=lambda t: (
        t.metadata.get("source", "MARKETPLACE") != "OWNER_DIRECT",
        -(t.priority.value if hasattr(t.priority, "value") else float(t.priority))
    ))

    res_task = self._queue.pop(0)
    self._save_queue()
    return res_task
```

**Проблема:**
- Сортировка при каждом `pop` — O(N log N)
- Для очереди из 1000 задач — приемлемо. Для 100000 — нет
- `heapq` или `PriorityQueue` — правильная структура данных
- `t.priority.value` — обращение к `.value` enum, но `float(t.priority)` — fallback, если priority — строка. Не типобезопасно

> **Вердикт:** Неправильная структура данных для priority queue. Сортировка при каждом извлечении — неэффективно.

---

## 61. Scheduler — `_save_queue` использует атомарную запись, но без блокировок

```python
def _save_queue(self) -> None:
    temp_filepath = self.filepath + ".tmp"
    try:
        with open(temp_filepath, "w", encoding="utf-8") as f:
            json.dump([item.to_dict() for item in self._queue], f, indent=2)
        os.replace(temp_filepath, self.filepath)
    except Exception:
        if os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Suppressed error: {e}")
```

**Проблема:**
- `os.replace` атомарна на POSIX, но **не гарантирует fsync**
- Если процесс упадёт между `json.dump` и `os.replace` — останется `.tmp` файл
- Нет блокировок: два процесса могут одновременно писать в один файл
- `logging.getLogger(__name__)` — создаёт логгер при каждой ошибке, не reuse

> **Вердикт:** Атомарность — best effort, не гарантированная. Нет concurrency control.

---

## 62. Orchestrator — `predict_estimates` возвращает фиктивные прогнозы

```python
def predict_estimates(self, task, agent_context):
    # Simplified prediction
    phi_hat = task.price * 0.8  # Предполагаем 80% от цены — прибыль?
    q_predicted_hat = 0.7  # Фиксированное качество
    psi_hat = 0.3  # Фиксированный риск
    return phi_hat, q_predicted_hat, psi_hat
```

**Проблема:**
- `phi_hat = task.price * 0.8` — это **доход**, не прибыль. Прибыль = доход - затраты
- `q_predicted_hat = 0.7` — константа, не зависит от агента, задачи, истории
- `psi_hat = 0.3` — константа
- Прогнозы не используют ни историю, ни capabilities агента, ни сложность задачи

> **Вердикт:** Прогнозная модель — заглушка. Не прогнозирует, а возвращает константы.

---

## 63. Orchestrator — `execute_action` через LLM-prompt, не через API/tools

```python
response_obj = self.ai_super_router.route_prompt_detailed(
    system_prompt="Execute specialized subroutine",
    user_prompt=f"You are {spec_name} executing Action: {action.name}..."
)
```

**Проблема:**
- Действие «выполняется» просьбой к LLM «сделай что-то»
- Нет структурированного вызова функций (OpenAI functions, tool use)
- Нет валидации результата — только `len(result_text) > 10`
- Нет retry с exponential backoff
- Нет circuit breaker для LLM-вызовов (хотя CircuitBreaker существует, он не используется здесь)

> **Вердикт:** Execution layer — prompt-based, not programmatic. Ненадёжно, не воспроизводимо, не тестируемо.

---

## 64. Orchestrator — `reflection` использует тот же ответ, не генерирует новый

```python
if q_value < required_q:
    # Remedial retry
    result_text = str(all_responses[-1].text)  # ТОТ ЖЕ ОТВЕТ!
    success = (bool(result_text) and len(result_text) > 10 ...)
```

**Проблема:**
- Reflection должен **пересмотреть** подход, запросить уточнение, попробовать другую стратегию
- Здесь — просто повторная проверка того же ответа
- Если ответ плохой — он останется плохим, сколько раз ни проверяй

> **Вердикт:** Reflection — имитация. Нет реального пересмотра.

---

## 65. Orchestrator — Stage XI не обновляет репутацию, хотя канон требует

```python
# Operational recording
self.op_mem.set("task_id", task.id)
self.op_mem.update_metric("revenue", task.price if success else 0.0)
self.op_mem.update_metric("cost", sum(c.resource_cost for c in task.actions))
self.op_mem.update_metric("risk", psi_hat)
self.op_mem.update_metric("quality", q_value)
```

**Проблема:**
- Канон §XI.1: `Υ_k(t+1) = Υ_k(t) + ΔΥ_k` — репутация должна обновляться
- Канон §XI.1: `Φ_historical(t+1)` — историческая прибыль должна обновляться
- Канон §XI.1: `H(t+1)` — гомеостаз должен пересчитываться
- В коде — только запись в `op_mem`, нет вызовов `update_upsilon`, `update_phi_historical`, `compute_h`

> **Вердикт:** Пайплайн замыкается на себя — данные записываются, но состояние не обновляется. Следующая итерация использует старые значения.

---

## 66. Orchestrator — `required_q` из метаданных задачи, не из Mission

```python
q_min = task.metadata.get("quality_requirement", 0.5)
```

**Проблема:**
- Канон §IV.12: `q_min = base_quality(mission_type) * quality_boost(personality)`
- Здесь — `q_min` приходит извне (заказчик? случайное число?)
- Нет связи между Mission-профилем и требованиями к качеству
- Задача с `mission_type="SURVIVAL"` может иметь `q_min=0.9` — конфликт

> **Вердикт:** Гейт качества не интегрирован с Mission-системой. Внешние требования игнорируют внутренние ограничения.

---

## 67. Orchestrator — `metrics_dict` для homeo.update_all собирается вручную, не из состояния

```python
metrics_dict = {
    "balance": self.core_agent.metrics.balance,
    "reputation": self.core_agent.metrics.rating,
    "quality": q_value,
    "active_tasks": len(self.core_agent.active_tasks),
}
pressures = self.homeo.update_all(metrics_dict)
```

**Проблема:**
- `metrics_dict` — ad-hoc сборка, не полный набор метрик
- Нет `stress_level` — хотя он вычисляется в `calculate_homeostasis`
- Нет `success_rate` — важная метрика для survival mode
- Нет `workload` — используется `active_tasks`, но это не то же самое

> **Вердикт:** Метрики для гомеостаза собираются ad-hoc, неполно. Риск неучёта важных факторов.

---

## 68. Orchestrator — `consolidation_gate.consolidate` возвращает `Experience`, но он не используется

```python
exp = self.consolidation_gate.consolidate(self.op_mem)
self.storage_mgr.persist(exp, self.core_agent)
```

**Проблема:**
- `consolidate` возвращает `Experience` — но что с ним происходит?
- `storage_mgr.persist` — сохраняет, но **не обновляет** репутацию, навыки, состояние
- Experience попадает в хранилище, но не влияет на будущие решения

> **Вердикт:** Консолидация — архивирование, не обучение. Данные копятся, но не используются.

---

## 69. Orchestrator — `all_responses` список, но обрабатывается только последний

```python
all_responses = []
for attempt in range(max_attempts):
    response_obj = self.ai_super_router.route_prompt_detailed(...)
    all_responses.append(response_obj)
    result_text = str(response_obj.text)
    if len(result_text) > 10 and not result_text.startswith("Error"):
        break
```

**Проблема:**
- Если первый ответ — ошибка, второй — успех — в `all_responses` оба
- Но при reflection используется `all_responses[-1]` — последний
- Если последний — успешный, reflection не срабатывает
- Если последний — ошибка (после max_attempts), reflection тоже не сработает (q_value вычисляется из success флага)

> **Вердикт:** Логика retry + reflection перепутана. Список all_responses — артефакт, не используется полностью.

---

## 70. Orchestrator — `task.actions` заполняется декомпозитором, но `resource_cost` не проверяется

```python
self.op_mem.update_metric("cost", sum(c.resource_cost for c in task.actions))
```

**Проблема:**
- `resource_cost` — доля от budget (например, 0.15 * 50.0 = 7.5)
- Сумма может превысить `task.price` — агент потратит больше, чем получит
- Нет проверки `sum(resource_cost) <= task.price`
- Нет проверки `sum(resource_cost) <= agent.metrics.balance`

> **Вердикт:** Финансовый контроль отсутствует. Агент может «потратить» больше, чем имеет.

---

## 71. Orchestrator — `C_t = self.core_agent.metrics.balance` — деньги вместо контекста

```python
C_t = self.core_agent.metrics.balance  # В коде
# Канон: C_t = 1 - KV_Cache_used / Context_max  # В документации
```

**Проблема:**
- В каноне `C_t` — вычислительный бюджет (доля свободного контекста)
- В коде `C_t` — баланс в долларах
- Проверка `C_t < C_min` в `evaluate_decision_rule`:
  - Канон: «не хватает контекста для задачи» → DECLINE
  - Код: «не хватает денег» → DECLINE
- Это **разные решения**: отказ из-за денег — финансовый, отказ из-за контекста — технический

> **Вердикт:** Фундаментальное несоответствие. Код реализует одну логику, документация описывает другую.

---

## 72. Orchestrator — `SimulatedResponse` вместо реальных вызовов LLM

```python
class SimulatedResponse:
    def __init__(self, text: str, model: str = "gpt-4o-mini", tokens: int = 100):
        self.text = text
        self.model = model
        self.tokens = tokens
```

**Проблема:**
- В `orchestrator/core.py` используется `SimulatedResponse` для «имитации» ответа LLM
- Нет реальной интеграции с OpenAI, Anthropic, или другими провайдерами
- `ai_super_router` — маршрутизатор, но куда? В `SimulatedResponse`?
- Токены не считаются реально — `tokens=100` — захардкожено

> **Вердикт:** Execution layer — полностью simulated. Нет интеграции с реальными LLM.

---

## 73. Orchestrator — `system_prompt` и `user_prompt` на русском и английском вперемешку

```python
system_prompt="Execute specialized subroutine",
user_prompt=f"You are {spec_name} executing Action: {action.name}. Task: {task.title}. Description: {task.description}. Please provide a detailed implementation."
```

**Проблема:**
- Комментарии и docstrings — на русском
- Prompts — на английском
- Переменные — смешанные (`spec_name`, `action.name` — английские, но `task.title` может быть на русском)
- LLM получает контекст на двух языках — качество страдает

> **Вердикт:** Локализация — хаос. Два языка в одном проекте без стратегии.

---

## 74. Orchestrator — `max_attempts = 3` и `delay_max = 60` — магические числа

```python
max_attempts = 3
delay_max = 60  # seconds
```

**Проблема:**
- Нет exponential backoff
- Нет jitter
- Нет circuit breaker между попытками
- `delay_max = 60` — фиксированная задержка, не адаптивная

> **Вердикт:** Retry policy — минимальная. Нет production-grade retry.

---

## 75. Orchestrator — `op_mem` (OperationalMemory) не очищается между задачами

```python
self.op_mem = OperationalMemory()  # Создаётся один раз в __init__
```

**Проблема:**
- `op_mem` накапливает метрики от всех задач
- Между задачами не вызывается `op_mem.clear()`
- Метрики «revenue», «cost» — суммарные, не per-task
- Нельзя отследить прибыльность конкретной задачи

> **Вердикт:** OperationalMemory — глобальное состояние, не изолированное по задачам. Метрики смешиваются.

---

## 76. Orchestrator — `storage_mgr.persist` вызывается с `exp` и `agent`, но сигнатура неизвестна

```python
self.storage_mgr.persist(exp, self.core_agent)
```

**Проблема:**
- Нет определения `StorageManager` в предоставленном коде
- Неизвестно, что делает `persist` — сохраняет в файл? БД? Облако?
- Нет обработки ошибок сохранения
- Нет транзакционности

> **Вердикт:** Интеграция с хранилищем — чёрный ящик. Невозможно проверить корректность.

---

## 77. Orchestrator — `core_agent` передаётся в конструктор, но не валидируется

```python
def __init__(self, core_agent, ...):
    self.core_agent = core_agent
```

**Проблема:**
- Нет проверки типа: можно передать `None`, строку, число
- Нет проверки обязательных атрибутов: `metrics`, `active_tasks`, `capabilities`
- Ошибки будут в runtime, не при создании

> **Вердикт:** Конструктор не защищён. Fail-fast principle нарушен.

---

## 78. Orchestrator — `weights_calibrator.calibrate` возвращает веса, но они не применяются к `core_agent`

```python
calibrated_weights = self.weights_calibrator.calibrate(pressures)
# calibrated_weights — не используется дальше!
```

**Проблема:**
- `calibrate` возвращает скорректированные веса
- Но они **не применяются** к агенту, не сохраняются, не передаются в `score_action`
- Следующая задача использует старые веса
- Калибровка — мёртвый код

> **Вердикт:** Ещё один мёртвый модуль. Вычисляется, но не применяется.

---

## 79. Orchestrator — `homeo.update_all` вызывается в Stage XII, но H уже использовался в Stage II

```python
# Stage II
H_val = self.homeo.calculate_homeostasis(metrics_dict)[0]  # H для решения

# ... pipeline ...

# Stage XII
pressures = self.homeo.update_all(metrics_dict)  # Обновление ПОСЛЕ решения
```

**Проблема:**
- H для принятия решения (Stage II) вычисляется **до** выполнения задачи
- H после задачи (Stage XII) — **не используется** для принятия решения
- Решение принимается на основе **устаревшего** H
- Канон §XI.1 требует обновления Υ→Φ→H **перед** следующим циклом, но в рамках того же цикла H должен быть актуальным

> **Вердикт:** H устаревает между циклами. Следующее решение основано на данных до предыдущей задачи.

---

## 80. Глобальная проблема: 15+ архитектурных документов, но ни один не является source of truth

**Документы в репозитории:**
- `00_MASTER.md` — обзор
- `01_PRODUCT_VISION.md` — продукт
- `02_MATHEMATICAL_CORE.md` — математика (канон)
- `03_PIPELINE_MATH.md` — пайплайн
- `04_ARCHITECTURE.md` — архитектура
- `05_TECHNICAL_SPECIFICATION.md` — техническая спецификация
- `06_IMPLEMENTATION_GUIDE.md` — руководство
- `07_TESTING_STRATEGY.md` — тестирование
- `08_DEPLOYMENT_GUIDE.md` — деплой
- `09_MAINTENANCE.md` — поддержка
- `10_SECURITY.md` — безопасность
- `11_COMPLIANCE.md` — compliance
- `12_PERFORMANCE.md` — производительность
- `13_API_REFERENCE.md` — API
- `14_USER_GUIDE.md` — пользователь
- `15_TROUBLESHOOTING.md` — troubleshooting

**Проблема:**
- Каждый документ — «канон» для своей области
- Но они **противоречат друг другу**
- `02_MATHEMATICAL_CORE.md` говорит одно, `03_PIPELINE_MATH.md` — другое
- `04_ARCHITECTURE.md` описывает компоненты, которых нет в коде
- `07_TESTING_STRATEGY.md` требует 80% coverage, но реальное покрытие — дымовые тесты

> **Вердикт:** Документация — не описание системы, а спецификация желаемого. Система не соответствует ни одному документу полностью.
