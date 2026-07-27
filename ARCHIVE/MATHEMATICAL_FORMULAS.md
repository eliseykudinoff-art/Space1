# 📐 MATHEMATICAL_FORMULAS — Полное собрание формул

> **Проект:** Space1 — AI-Agent Freelancer Model
> **Дата:** 2026-07-07
> **Статус:** ✅ Финальный
> **Источники:** CLEAN_MATHEMATICAL_MODEL.md, UNIFIED_MODEL.md, FORMULAS_REFERENCE.md

---

## 📋 СОДЕРЖАНИЕ

1. [Системные константы и параметры](#1-системные-константы-и-параметры)
2. [Базовые аксиомы](#2-базовые-аксиомы)
3. [Управляющие функции](#3-управляющие-функции)
   - [3.1 Φ — Profit Function](#31--profit-function)
   - [3.2 Q — Quality Function](#32-q--quality-function)
   - [3.3 Ψ — Risk Function](#33-ψ--risk-function)
   - [3.4 Υ — Reputation Function](#34-υ--reputation-function)
   - [3.5 Γ — Compliance Function](#35-γ--compliance-function)
   - [3.6 Ω — Evolution Function](#36-ω--evolution-function)
   - [3.7 H — Homeostasis Function](#37-h--homeostasis-function)
   - [3.8 VoI — Value of Information](#38-voi--value-of-information)
   - [3.9 U — Utility Function](#39-u--utility-function)
4. [Φ_R — Routing Quality](#4-φ_r--routing-quality)
5. [Ξ_task — Executor Function](#5-ξ_task--executor-function)
6. [Факторы способностей (x₁-x₁₁)](#6-факторы-способностей-x₁-x₁₁)
7. [Факторы способностей (x₁₂-x₁₇)](#7-факторы-способностей-x₁₂-x₁₇)
8. [Синергии факторов](#8-синергии-факторов)
9. [Атомарная декомпозиция](#9-атомарная-декомпозиция)
10. [Сводная таблица функций](#10-сводная-таблица-функций)
11. [Приложения](#11-приложения)

---

## 1. СИСТЕМНЫЕ КОНСТАНТЫ И ПАРАМЕТРЫ

### 1.1 Базовые константы (экзогенные переменные)

| Символ | Значение | Описание | Диапазон |
|--------|---------|---------|----------|
| $S_0$ | 0.30 | Базовый Success Rate | [0, 1] |
| $Q_0$ | 1.0 | Базовый Throughput (задач/час) | (0, ∞) |
| $C_0$ | 0.0 | Базовый Cost ($/задача) | [0, ∞) |
| $T_0$ | 1.0 | Базовое Time (час/задача) | (0, ∞) |
| $P$ | 50.0 | Цена за задачу ($) | (0, ∞) |
| $L_0$ | 0.0 | Начальный Skill Level | [0, 1] |
| $L_{max}$ | 1.0 | Максимальный Skill Level | [0, 1] |
| $K_0$ | 0.0 | Начальное Knowledge | [0, 1] |
| $K_{max}$ | 1.0 | Максимальное Knowledge | [0, 1] |
| $D_{max}$ | 1.0 | Максимальная сложность задач | [0, 1] |
| $H_{min}$ | 0.1 | Минимальный потолок сложности | [0, 1] |
| $H_{max}^0$ | 0.8 | Начальный максимальный потолок | [0, 1] |
| $R_{min}$ | 1.0 | Минимальный рейтинг | [1, 5] |
| $R_{max}$ | 5.0 | Максимальный рейтинг | [1, 5] |

### 1.2 Системные параметры

| Символ | Значение | Описание |
|--------|---------|---------|
| $\alpha$ | 0.25 | Вес качества в Q |
| $\beta$ | 0.25 | Вес точности в Q |
| $\gamma$ | 0.25 | Вес полноты в Q |
| $\delta$ | 0.25 | Вес своевременности в Q |
| $\eta$ | 0.01 | Базовая скорость обучения |
| $\lambda_0$ | 1.0 | Базовый λ (order flow) |
| $\tau_{base}$ | 24.0 | Базовое время восстановления (часы) |
| $\rho_0$ | 1.0 | Базовый resilience |
| $\Gamma_{target}$ | 1.0 | Целевой гомеостазис |
| $\epsilon$ | $10^{-6}$ | Малая константа для защиты от деления на ноль |

---

## 2. БАЗОВЫЕ АКСИОМЫ

### Аксиома A1: Прибыль = (Доход - Затраты) / Время

$$\Phi = \frac{R - C}{T}$$

где:
- $R$ — Revenue (доход)
- $C$ — Cost (затраты)
- $T$ — Time (время)

### Аксиома A2: Доход = Цена × Качество × Пропускная способность

$$R = P \cdot S \cdot Q$$

### Аксиома A3: Затраты = Базовые + Накладные + Рисковые

$$C = C_0 + C_{ops} + C_{risk}$$

### Аксиома A4: Время = Базовое × Модификаторы

$$T = T_0 \cdot \prod_i f_i$$

### Аксиома A5: Success Rate ∈ [0, 1]

$$S \in [0, 1]$$

### Аксиома A6: Throughput ∈ (0, ∞)

$$Q > 0$$

### Аксиома A7: Cost ≥ 0

$$C \geq 0$$

---

## 3. УПРАВЛЯЮЩИЕ ФУНКЦИИ

---

### 3.1 Φ — Profit Function

#### 3.1.1 Определение

$$\boxed{\Phi(\mathbf{x}) = \frac{P \cdot S(\mathbf{x}) \cdot Q(\mathbf{x}) - C(\mathbf{x})}{T(\mathbf{x})}}$$

где $\mathbf{x} = (x_1, x_2, \ldots, x_{17})$ — вектор факторов способностей.

#### 3.1.2 Компоненты прибыли

**Success Rate с факторами:**

$$S(\mathbf{x}) = S_0 + \sum_{i=1}^{17} \beta_i \cdot x_i + \sum_{i<j} \gamma_{ij} \cdot x_i \cdot x_j$$

где:
- $\beta_i$ — коэффициент влияния i-го фактора
- $\gamma_{ij}$ — коэффициент синергии между факторами i и j

**Throughput с факторами:**

$$Q(\mathbf{x}) = Q_0 \cdot \prod_{i=1}^{17} f_{Q,i}(x_i)$$

**Cost с факторами:**

$$C(\mathbf{x}) = C_0 + \sum_{i=1}^{17} \Delta C_i(x_i)$$

**Time с факторами:**

$$T(\mathbf{x}) = T_0 \cdot \prod_{i=1}^{17} f_{T,i}(x_i)$$

#### 3.1.3 Проверка размерности

| Компонент | Размерность | Проверка |
|-----------|-------------|-----------|
| $P$ | \$/задача | ✅ |
| $S$ | безразмерная [0,1] | ✅ |
| $Q$ | задач/час | ✅ |
| $C$ | \$/задача | ✅ |
| $T$ | час/задача | ✅ |
| $\Phi$ | \$/час | ✅ |

---

### 3.2 Q — Quality Function

#### 3.2.1 Определение

$$\boxed{Q = \alpha \cdot Q_{comp} + \beta \cdot Q_{acc} + \gamma \cdot Q_{full} + \delta \cdot Q_{time}}$$

где все веса нормированы: $\alpha + \beta + \gamma + \delta = 1$.

#### 3.2.2 Компоненты качества

**Полнота (Completeness):**

$$Q_{comp} = \frac{|\text{CoveredAspects}|}{|\text{AllAspects}|}$$

**Точность (Accuracy):**

$$Q_{acc} = 1 - \frac{D_{KL}(P_{intent} \| P_{result})}{D_{max}}$$

или аппроксимация:

$$Q_{acc} \approx \text{cosine\_sim}(\text{embed}(intent), \text{embed}(result))$$

**Своевременность (Timeliness):**

$$Q_{time} = 1 - \min\left(1, \frac{t_{actual} - t_{deadline}}{t_{deadline}}\right)$$

#### 3.2.3 Качество декомпозиции

$$\mathcal{Q}_{decomp} = \alpha \cdot \text{Completeness} + \beta \cdot \text{Independence} + \gamma \cdot \text{Granularity} + \delta \cdot \text{Feasibility}$$

#### 3.2.4 Адаптивность к контексту

$$\mathcal{A}_c = \frac{\sum_{j=1}^{\max(N_{implicit}, 1)} \text{detected}(j) \cdot \text{satisfied}(j)}{\max(N_{implicit}, 1)}$$

> **Примечание:** $\max(N_{implicit}, 1)$ защищает от деления на ноль при отсутствии неявных требований.

---

### 3.3 Ψ — Risk Function

#### 3.3.1 Определение

$$\boxed{\Psi = P_{fail} \cdot (C_{direct} + C_{reputation})}$$

#### 3.3.2 Вероятность отказа

$$P_{fail} = P_{base} \cdot (1 + \alpha_u \cdot U + \alpha_f \cdot F + \alpha_n \cdot N + \alpha_d \cdot D) \cdot \frac{1}{1 + \alpha_s \cdot S}$$

где:
- $U$ — неопределённость задачи [0,1]
- $F$ — fatigue (усталость агента) [0,1]
- $N$ — новизна задачи [0,1]
- $D$ — deadline pressure [0,1]
- $S$ — skill level [0,1]

#### 3.3.3 Каскадная вероятность

$$P_{cascade} = 1 - \prod_{i=1}^{n} (1 - p_i)$$

#### 3.3.4 Guardrails Risk Reduction

$$P_{risk\_final} = P_{fail} \cdot \prod_{i} (1 - p_{risk,i} \cdot (1 - G_i))$$

где $G_i \in \{0, 1\}$ — эффективность i-го guardrail.

---

### 3.4 Υ — Reputation Function

#### 3.4.1 Определение

$$\boxed{\Upsilon = \gamma_1 \cdot \bar{R} + \gamma_2 \cdot \tau_{ret} + \gamma_3 \cdot \frac{N^+}{N} + \gamma_4 \cdot (1 - \delta) + \gamma_5 \cdot \frac{d\Upsilon}{dt}}$$

где:
- $\bar{R}$ — средний рейтинг (нормированный в [0,1])
- $\tau_{ret}$ — retention rate (доля возвращающихся клиентов)
- $N^+/N$ — доля положительных отзывов
- $\delta$ — average delay ratio (задержка / SLA target)
- $\frac{d\Upsilon}{dt}$ — momentum (скорость изменения)

#### 3.4.2 Байесовский рейтинг

$$R_{bayesian} = \frac{m \cdot \mu_0 + \sum_{i=1}^{n} r_i}{m + n}$$

где:
- $m = 7$ — сила prior
- $\mu_0 = 4.2$ — prior mean
- $r_i$ — отдельные оценки

#### 3.4.3 Confidence в рейтинге

$$\Theta = 1 - \frac{1}{\sqrt{N}} \cdot \frac{\sigma_R}{R_{max} - R_{min}}$$

#### 3.4.4 Order Flow (поток заказов)

$$\lambda_{orders} = \lambda_0 \cdot \left(\frac{R}{\bar{R}}\right)^{\beta_{rep}} \cdot \Theta^{\gamma_{trust}} \cdot (1 + SC)^{\delta_{social}}$$

#### 3.4.5 Recovery Time (время восстановления)

$$\tau_{recovery} = \frac{\tau_{base}}{\rho_{resilience} \cdot (1 + \beta \cdot N_{good})}$$

#### 3.4.6 Динамика репутации

$$\frac{dR}{dt} = \alpha \cdot Q \cdot (1 + \beta \cdot V_{resp}) - \gamma \cdot \text{incidents} \cdot R$$

где $V_{resp}$ — response velocity.

---

### 3.5 Γ — Compliance Function

#### 3.5.1 Определение (Veto Function)

$$\boxed{\Gamma(action) = \begin{cases} 0, & \text{if } \forall r \in \text{Rules}: r(action) = \text{True} \\ -\infty, & \text{otherwise} \end{cases}}$$

> **Важно:** Γ не штрафует — Γ отвергает. $-\infty$ означает полный veto.

#### 3.5.2 Примеры правил

| Правило | Условие | Описание |
|---------|---------|---------|
| $r_{legal}$ | не нарушает законы | Юридическая проверка |
| $r_{api}$ | $C_{api} < C_{limit}$ | Лимиты API |
| $r_{financial}$ | $C_{total} < B_{max}$ | Финансовые ограничения |
| $r_{security}$ | нет угроз | Безопасность |

#### 3.5.3 Индикатор прохождения

$$\mathbb{I}_{pass}(\Gamma(A)) = \begin{cases} 1, & \Gamma(A) = 0 \\ 0, & \Gamma(A) = -\infty \end{cases}$$

> ⚠️ **Вопрос к уточнению:** Требуется ли порог veto? Что если Γ(action) находится между 0 и -∞ (например, -1000)? Как принимается решение ACCEPT/REJECT в этом случае? Это указано в CRITICAL_MATHEMATICAL_REVIEW.md как открытый вопрос.

---

### 3.6 Ω — Evolution Function

#### 3.6.1 Learning Curve

$$L_s(t) = L_{max} \cdot (1 - e^{-\eta \cdot t^{\gamma}}) + L_0$$

где:
- $\eta$ — скорость обучения
- $\gamma$ — форма кривой
- $L_0$ — начальный уровень навыка

#### 3.6.2 Knowledge Accumulation

$$K(t) = K_0 + \eta_{learn} \cdot \sum_{\tau < t} \Delta K(\tau) \cdot \left(1 - \frac{K(\tau)}{K_{max}}\right)$$

#### 3.6.3 ZPD (Zone of Proximal Development)

$$ZPD = ZPD_{base} \cdot (1 + \alpha_M \cdot M - \alpha_{CL} \cdot CL + \alpha_\eta \cdot \eta)$$

#### 3.6.4 Forgetting Factor

$$\Phi_{forget}(t, n) = e^{-\frac{t}{S \cdot (1 + \kappa \cdot n)^\psi}}$$

---

### 3.7 H — Homeostasis Function

#### 3.7.1 Определение

$$\boxed{H = \frac{F_{reinforcing} + \epsilon}{F_{balancing} + \epsilon}}$$

где $\epsilon = 10^{-6}$ защищает от деления на ноль.

#### 3.7.2 Reinforcing Forces (усиливающие)

$$F_{reinforcing} \approx \nu \cdot \text{VoI} + \gamma \cdot \Upsilon + \phi_{ft} \cdot \frac{dN_{tasks}}{dt}$$

#### 3.7.3 Balancing Forces (уравновешивающие)

$$F_{balancing} \approx \lambda_\Psi \cdot \Psi + \rho \cdot E_{error} + \delta_{coord} \cdot N_{agents}^2$$

#### 3.7.4 Интерпретация

| Диапазон H | Состояние | Описание |
|------------|-----------|---------|
| $H > 1 + \epsilon_H$ | Рост | Система в фазе экспансии |
| $1 - \epsilon_H \leq H \leq 1 + \epsilon_H$ | Гомеостаз | Баланс |
| $H < 1 - \epsilon_H$ | Спад | Система в фазе стабилизации/упадка |

#### 3.7.5 Adaptability Index

$$\mathcal{A} = \frac{\Delta \Phi_{recovery} + \epsilon}{\Delta \Phi_{loss} + \epsilon}$$

---

### 3.8 VoI — Value of Information

$$\text{VoI} = \mathbb{E}[\Phi | \text{with info}] - \mathbb{E}[\Phi | \text{without info}]$$

**Расшифровка:**
```
E[Φ | with info] = Φ_yes · P(yes) + Φ_no · P(no)
                 = 4450 · 0.3 + (-500) · 0.7 = 985

E[Φ | without info] = Φ_1 · S + Φ_2 · (1-S)
                 = 5000 · 0.8 + (-500) · 0.2 = 3900

VoI = 985 - 3900 = -2915 (отрицательная → не стоит спрашивать)
```

---

### 3.9 U — Utility Function

#### 3.9.1 Определение

$$\boxed{U = \lambda_\Phi \cdot \Phi + \lambda_\Upsilon \cdot \Upsilon + \lambda_Q \cdot Q + \lambda_\Omega \cdot \Omega - \lambda_\Psi \cdot \Psi - \lambda_\Gamma \cdot \Gamma}$$

где веса определяются Mission:
$$\lambda_\Phi + \lambda_\Upsilon + \lambda_Q + \lambda_\Omega + \lambda_\Psi + \lambda_\Gamma = 1$$

#### 3.9.2 Economic Utility

$$U_{economic} = \Phi \cdot (1 + \alpha_{rep} \cdot \Upsilon)$$

#### 3.9.3 Extended Utility с Knowledge

$$U_{ext} = \Phi + \lambda_\Upsilon \cdot \Upsilon + \alpha_K \cdot K + \lambda_{VoI} \cdot \text{VoI}$$

#### 3.9.4 Lambda Cost Function (Homeostasis Modulation)

$$\lambda_{cost}(t) = \lambda_0 \cdot \frac{H(t)}{H_{target}} \cdot (1 + \alpha_\Psi \cdot \Psi(t))$$

---

## 4. Φ_R — ROUTING QUALITY

### 4.1 Определение

> ⚠️ **Вопрос к уточнению:** Φ_R используется в UNIFIED_MODEL, но определение добавлено из FORMULAS_REFERENCE. Требуется проверка согласованности с другими функциями.

$$\Phi_R(D) = \Phi(D) \cdot \mathbb{I}[\Gamma(D) = 0] \cdot \left(1 + \alpha_{rep} \cdot \Upsilon \right) - \lambda_\Psi \cdot \Psi(D)$$

где:
- $\Phi(D)$ — прибыль декомпозиции
- $\mathbb{I}[\Gamma(D) = 0]$ — индикатор прохождения compliance
- $\alpha_{rep}$ — коэффициент репутационного бонуса
- $\Upsilon$ — репутация
- $\lambda_\Psi$ — коэффициент штрафа за риск
- $\Psi(D)$ — риск декомпозиции

**Интерпретация:** План получает качество только если прошёл Compliance, умножается на репутационный бонус, и штрафуется за риск.

---

## 5. Ξ_task — EXECUTOR FUNCTION

### 5.1 Определение

> ⚠️ **Вопрос к уточнению:** Ξ_task определена для агента-исполнителя (не для оркестратора). Требуется уточнение коэффициентов α, β.

$$\Xi_{task} = \alpha \cdot Q_{result} - \beta \cdot (O_{time} + O_{cost})$$

где:
- $Q_{result}$ — оценка качества (автотесты, LLM-судья)
- $O_{time}$ — фактический перерасход времени vs выделенного
- $O_{cost}$ — фактический перерасход бюджета vs выделенного

### 5.2 Контекст

> Αгент-исполнитель мыслит категориями Ξ, оркестратор — Φ.

**Двухуровневая архитектура:**
```
Оркестратор: U(Φ) = w₁·Φ + w₂·Υ + w₃·Ω - w₄·Ψ
Исполнитель: Ξ_task = α·Q - β·(O_time + O_cost)
```

---

## 6. ФАКТОРЫ СПОСОБНОСТЕЙ (x₁-x₁₁)

### 6.1 Таблица факторов

| ID | Фактор | Определение | Влияние на S | Влияние на T |
|----|--------|------------|--------------|--------------|
| $x_1$ | LLM Capability | $C_{llm} = \alpha_Q \cdot Q + \alpha_R \cdot R + \alpha_C \cdot C + \alpha_A \cdot A$ | сигмоида | зависит от модели |
| $x_2$ | Tool Calling | $x_2 \in \{0, 1\}$ | +0.20 | — |
| $x_3$ | MCP Integration | $x_3 \in \{0, 1\}$ | +0.05 | — |
| $x_4$ | Memory | $M_p \in [0, 1]$ | $\beta_1 M_p + \beta_2 M_p^2$ | максимум |
| $x_5$ | Multi-Agent | $N \in \{1,2,4,8,16\}$ | $\alpha_1 \log N + \alpha_2 \frac{N}{N+\beta}$ | оптимум 4-8 |
| $x_6$ | Self-Correction | $L_{sc} \in \{0,1,2,3,4\}$ | $\beta_1 L_{sc} + \beta_2 L_{sc}^2$ | ~3 retries |
| $x_7$ | Prompt Engineering | $Q_p \in [0, 1]$ | $\beta_1 Q_p + \beta_2 Q_p^2$ | 10x improvement |
| $x_8$ | Cost Tiering | $\theta_{tier} \in [0, 1]$ | зависит от модели | экономия 77% |
| $x_9$ | Grounding | $G \in \{0, 1\}$ | $\beta \cdot d \cdot \log(1 + Q_{ret})$ | задержка |
| $x_{10}$ | Fine-tuning | $F_t \in \{0, 1\}$ | $\beta \cdot (1 - e^{-\lambda N})$ | N > 500/mo |
| $x_{11}$ | Browser | $B_a \in \{0,1,2,3\}$ | $\beta \cdot B_{score} \cdot \sigma(d)$ | задержка |

### 6.2 LLM Capability Definition (x₁)

$$C_{llm} = \alpha_Q \cdot Q_{bench} + \alpha_R \cdot R_{bench} + \alpha_C \cdot C_{bench} + \alpha_A \cdot A_{bench}$$

где:
| Компонент | Вес | Описание |
|-----------|-----|---------|
| $\alpha_Q$ | 0.25 | Quality (benchmarks) |
| $\alpha_R$ | 0.30 | Reasoning (логика) |
| $\alpha_C$ | 0.25 | Coding (agent tasks) |
| $\alpha_A$ | 0.20 | Agentic (tool use) |

### 6.3 Success Rate с учётом LLM

$$S(m, t) = \frac{C_{llm}(m)}{1 + e^{-\lambda_t \cdot (C_{llm}(m) - \tau_t)}}$$

### 6.4 Throughput с учётом LLM

$$Q(m) = Q_{max} \cdot \frac{C_{llm}(m)}{1 + \gamma \cdot (1 - C_{llm}(m))}$$

### 6.5 Cost Model

$$C_{api}(m, t) = I_t \cdot P^{in}_m + O_t \cdot P^{out}_m$$

### 6.6 Memory Factor (x₄)

$$\Delta S_{memory} = \beta_0 + \beta_1 \cdot M_p + \beta_2 \cdot M_p^2$$

$$Q(M_p) = Q_0 \cdot (1 + \gamma \cdot M_p \cdot (1 - e^{-\delta \cdot M_p}))$$

$$C_{memory} = C_{storage} + C_{retrieval} + C_{maintenance}$$

### 6.7 Multi-Agent (x₅)

$$\Delta S_{multi} = \alpha_0 + \alpha_1 \cdot \log(N_{agents}) + \alpha_2 \cdot \frac{N_{agents}}{N_{agents} + \beta}$$

$$C_{coordination} = \delta_1 \cdot N_{agents} \cdot \log(N_{agents}) + \delta_2 \cdot N_{agents}^2$$

### 6.8 Grounding (x₉)

$$G_{score} = \alpha_{ret} \cdot Q_{ret} + \alpha_{rerank} \cdot Q_{rerank} + \alpha_{gen} \cdot F_{faith}$$

$$\Delta S_G = \beta_0 + \beta_1 \cdot G_{score} \cdot d$$

---

## 7. ФАКТОРЫ СПОСОБНОСТЕЙ (x₁₂-x₁₇)

### 7.1 Таблица факторов

| ID | Фактор | Определение | β (на S) | δ (на T) | Приоритет |
|----|--------|------------|----------|----------|----------|
| $x_{12}$ | Guardrails | $G_{eff} = \prod_i (1 - p_i \cdot (1 - G_i))$ | +0.05 | +0.02 | HIGH |
| $x_{13}$ | Test-Time Compute | $T_{think}/T_{base}$ | +0.18 | +0.25 | Medium |
| $x_{14}$ | Design Patterns | $\sum_p \alpha_p \cdot P_p$ | +0.10 | -0.05 | Medium |
| $x_{15}$ | Evaluation | $\alpha_e \cdot B_{cov} + \beta_e \cdot A_{score}$ | +0.08 | +0.03 | Low |
| $x_{16}$ | Continual Learning | $K_{cl}(t) = 1 - e^{-\lambda_{cl} N_{tasks}}$ | +0.12 | -0.10 | Medium |
| $x_{17}$ | Inference Opt | $\prod_o (1 - \delta_o)$ | 0 | -0.20 | HIGH |

### 7.2 Guardrails & Safety (x₁₂)

**Формула снижения риска:**

$$C_{risk}(x) = \sum_{j} P_j \cdot L_j \cdot (1 - R_{guardrails,j})$$

**Effectiveness:**

$$G_{eff} = \prod_{i} (1 - p_{risk,i} \cdot (1 - G_i))$$

где:
- $p_{risk,i}$ — вероятность i-го рискового события
- $G_i$ — эффективность i-го guardrail (0 или 1)

**ΔS от Guardrails:**

$$\Delta S_{guardrails} = \beta_g \cdot G_{eff}$$

**Синергия:** $x_{12} + x_2$ (Guardrails усиливают безопасность tool calls)

### 7.3 Test-Time Compute / Reasoning (x₁₃)

**Influence on Success Rate:**

$$S_{reason} = S(x) + \beta_{reason} \cdot \log(1 + \frac{T_{think}}{T_{base}})$$

**Time penalty:**

$$T_{reason} = T(x) \cdot (1 + 0.25 \cdot \frac{T_{think}}{T_{base}})$$

**ROI:**

$$\text{ROI}_{reasoning} = \frac{\Delta S \cdot P}{\Delta C_{api}}$$

**Синергия:** $x_1 + x_{13}$ (LLM + Reasoning)

### 7.4 Agentic Design Patterns (x₁₄)

**Success Rate с паттернами:**

$$S_{pattern}(x) = S(x) + \sum_{p \in \text{Patterns}} \alpha_p \cdot P_p(x)$$

где $P_p(x)$ — probability of applying pattern $p$.

| Паттерн | $\alpha_p$ | Применение |
|---------|------------|------------|
| ReAct | +0.08 | Exploration tasks |
| Reflection | +0.12 | Quality-critical |
| Planning | +0.15 | Complex multi-step |

**Throughput multiplier:**

$$Q_{pattern} = Q(x) \cdot \prod_p (1 + \beta_p \cdot P_p)$$

**Синергия:** $x_{14} + x_6$ (Patterns + Self-correction)

### 7.5 Evaluation & Benchmarking (x₁₅)

**Calibration:**

$$\hat{S}(x) = \alpha_{eval} \cdot S_{measured}(x) + (1 - \alpha_{eval}) \cdot S_{predicted}(x)$$

**Benchmarks:**

| Benchmark | Значение | Описание |
|----------|---------|---------|
| GAIA | 0.745 | General AI assistant |
| SWE-bench | 0.15 | Software engineering |
| WebArena | 0.80 | Web interaction |
| RLI | 0.025 | Real freelance tasks |
| ARC-AGI | 0.30 | Generalization |

### 7.6 Continual Learning (x₁₆)

**Knowledge accumulation:**

$$K(t) = K_0 + \eta_{learn} \cdot \sum_{\tau < t} \Delta K(\tau) \cdot \left(1 - \frac{K(\tau)}{K_{max}}\right)$$

**Transfer learning benefit:**

$$\Delta S_{transfer} = \gamma_{transfer} \cdot \text{TaskSimilarity}(t_{new}, t_{past}) \cdot K_{past}$$

**Forgetting factor:**

$$S_{cl}(x) = S(x) \cdot (1 - \rho \cdot e^{-\lambda \cdot t})$$

где $\rho$ — скорость забывания.

**Knowledge growth:**

$$K_{cl}(t) = 1 - e^{-\lambda_{cl} \cdot N_{tasks}}$$

$$\Delta S_{cl} = \gamma_{cl} \cdot K_{cl} \cdot S(x)$$

**Синергия:** $x_4 + x_{16}$ (Memory + Continual Learning)

### 7.7 Inference Optimization (x₁₇)

**Speedup factors:**

| Оптимизация | $\delta_o$ | Примечание |
|------------|------------|-----------|
| Caching | 0.10 | 10% latency reduction |
| Quantization INT8 | 0.20 | 50% cost reduction |
| Flash Attention | 0.15 | Memory bandwidth |
| Speculative Decoding | 0.30 | Draft tokens |
| Batch Processing | 0.25 | Parallelism |

**Combined speedup:**

$$T_{opt} = T_0 \cdot \prod_{o} (1 - \delta_o)$$

**Cost reduction:**

$$C_{opt}(x) = C(x) \cdot (1 - \sum_o \gamma_o \cdot O_o)$$

**Quality penalty (if any):**

$$S_{opt}(x) = S(x) \cdot (1 - \epsilon_{quant} \cdot Q_{quantization})$$

**Синергия:** $x_{17} + x_8$ (Inference Opt + Cost tiering)

---

## 8. СИНЕРГИИ ФАКТОРОВ

### 8.1 Определение

$$\gamma_{syn} = \sum_{(i,j) \in \text{synergies}} \Delta\gamma_{ij} \cdot x_i \cdot x_j$$

где $x_i \in \{0, 1\}$ для бинарных факторов.

### 8.2 Матрица синергий

| Пара факторов | $\Delta\gamma$ | Механизм |
|--------------|---------------|----------|
| $x_1 + x_7$ | +0.08 | Улучшенный промт компенсирует слабую модель |
| $x_2 + x_9$ | +0.12 | Grounding делает tool calls точнее |
| $x_5 + x_6$ | +0.15 | Multi-agent + Self-correction |
| $x_1 + x_{10}$ | +0.05 | Fine-tuning усиливает базовую модель |
| $x_6 + x_{14}$ | +0.15 | Self-correction + Reflection |
| $x_4 + x_{16}$ | +0.10 | Memory + Continual Learning |
| $x_2 + x_{12}$ | +0.08 | Tool Calling + Guardrails |
| $x_1 + x_{13}$ | +0.12 | LLM + Reasoning (test-time) |
| $x_{17} + x_8$ | +0.06 | Inference Opt + Cost tiering |

---

## 9. АТОМАРНАЯ ДЕКОМПОЗИЦИЯ

### 9.1 Целевая функция

$$\boxed{D^*(T) = \underset{(A, \theta)}{\arg\max} \; \mathbb{I}_{pass}(\Gamma(A)) \cdot \left[ \mathcal{U}(A, \theta) - \lambda \cdot \mathcal{C}(A, \theta) \right]}$$

### 9.2 Структура атомарного действия

$$a = (p, f, c, m, o, \phi, r)$$

где:
- $p$ — промт
- $f$ — формат вывода
- $c$ — контекст
- $m$ — модель
- $o$ — выход
- $\phi$ — confidence score
- $r$ — ресурсы

### 9.3 Utility атомарного действия

$$u(a) = \phi(a) \cdot P(\text{success} | a, m) \cdot \text{quality}(m)$$

### 9.4 Correlation между действиями

$$\rho(a_i, a_j) = \sigma(\mathbf{w}_{dep}^T \cdot [\mathbf{e}(a_i); \mathbf{e}(a_j)] - b_{dep})$$

### 9.5 Полезность декомпозиции

$$\mathcal{U}(A, \theta) = \prod_{i=1}^{n} u(a_i) \cdot \prod_{(i,j) \in E} \rho(a_i, a_j)$$

### 9.6 Стоимость декомпозиции

$$\mathcal{C}(A, \theta) = \sum_{i=1}^{n} \left[\alpha \cdot \text{cost}(m_i) + \beta \cdot \text{latency}(m_i) + \gamma \cdot |c_i|\right]$$

### 9.7 Решение о декомпозиции

$$\delta(T) = \sigma(\mathbf{w}_\delta^T \cdot \mathbf{f}(T) + b_\delta)$$

где $\mathbf{f}(T)$ — вектор признаков задачи.

### 9.8 Confidence Score

$$\phi(a) = \sigma(\mathbf{w}_\phi^T \cdot \mathbf{f}(a) + b_\phi)$$

---

## 10. СВОДНАЯ ТАБЛИЦА ФУНКЦИЙ

| ID | Функция | Определение | Входы | Выходы |
|----|---------|-----------|-------|--------|
| Φ | Profit | $(R - C) / T$ | P, S, Q, C, T | \$/час |
| Q | Quality | $\alpha Q_{comp} + \beta Q_{acc} + \gamma Q_{full} + \delta Q_{time}$ | task, result | [0,1] |
| Ψ | Risk | $P_{fail} \cdot (C_{direct} + C_{rep})$ | task, state | cost |
| Υ | Reputation | $\sum \gamma_i \cdot component_i$ | history | [0,1] |
| Γ | Compliance | 0 или -∞ | action | binary |
| Ω | Evolution | $L_s(t), K(t)$ | time, tasks | skill, knowledge |
| H | Homeostasis | $F_{rein} / F_{bal}$ | VoI, Υ, Ψ, E | ratio |
| VoI | Value of Info | $\mathbb{E}[\Phi | info] - \mathbb{E}[\Phi]$ | info, baseline | delta |
| U | Utility | $\lambda \cdot \Phi + \lambda \cdot \Upsilon + \ldots$ | all functions | scalar |
| Φ_R | Routing Quality | $\Phi \cdot \mathbb{I}[\Gamma=0] \cdot (1+\alpha_{rep}\cdot\Upsilon) - \lambda_\Psi \cdot \Psi$ | Φ, Γ, Υ, Ψ | scalar |
| Ξ | Executor | $\alpha \cdot Q - \beta \cdot (O_{time} + O_{cost})$ | Q, O | scalar |
| S | Success Rate | $S_0 + \sum \beta_i x_i + \sum \gamma_{ij} x_i x_j$ | x | [0,1] |

---

## 11. ПРИЛОЖЕНИЯ

### 11.1 Активационные функции

**Сигмоида:**
$$\sigma(x) = \frac{1}{1 + e^{-x}}$$

**ReLU:**
$$\text{ReLU}(x) = \max(0, x)$$

**Softmax:**
$$\text{Softmax}(\mathbf{x})_i = \frac{e^{x_i}}{\sum_j e^{x_j}}$$

### 11.2 Размерности

| Функция | Размерность | Единица |
|---------|------------|---------|
| Φ | [0, ∞) | \$/час |
| Q | [0, 1] | безразмерная |
| Ψ | [0, ∞) | \$ |
| Υ | [0, 1] | безразмерная |
| Γ | {0, -∞} | — |
| H | (0, ∞) | ratio |
| VoI | (-∞, ∞) | \$ |
| S | [0, 1] | безразмерная |

### 11.3 Граничные условия

| Переменная | Min | Max | Ограничение |
|-----------|-----|-----|------------|
| S | 0 | 1 | ✅ hard constraint |
| Q | 0 | 1 | ✅ hard constraint |
| Φ | -∞ | +∞ | мягкое |
| Υ | 0 | 1 | ✅ hard constraint |
| H | 0 | +∞ | ✅ > 0 (epsilon protection) |
| C | 0 | +∞ | ✅ hard constraint |
| T | $\epsilon$ | +∞ | ✅ > 0 (epsilon protection) |

---

## ❓ ОТКРЫТЫЕ ВОПРОСЫ (для отдельного документа)

1. **Γ threshold:** Что если Γ(action) находится между 0 и -∞? Как принимается решение ACCEPT/REJECT?

2. **Ξ_task coefficients:** Коэффициенты α, β не определены. Требуется калибровка.

3. **Φ_R consistency:** Требуется проверка согласованности с другими функциями.

4. **Impulse → Chain:** Механизм трансформации импульса в цепочку действий не формализован.

5. **Внешняя среда:** Модель рынка, конкурентов, клиентов отсутствует.

6. **Feedback loop:** Формула для обновления метрик после действия отсутствует.

---

*Документ создан: 2026-07-07*
*Версия: 1.0*
*Источники: CLEAN_MATHEMATICAL_MODEL.md, UNIFIED_MODEL.md, FORMULAS_REFERENCE.md*
