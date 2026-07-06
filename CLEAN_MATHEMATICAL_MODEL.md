# 🧮 ЧИСТАЯ МАТЕМАТИЧЕСКАЯ МОДЕЛЬ Manus

## Единая формализация AI-агента для фриланс-платформы

> **Версия:** 1.0  
> **Дата:** 2026-07-06  
> **Статус:** ✅ Финальная математическая модель

---

## 📋 СОДЕРЖАНИЕ

1. [Системные константы и параметры](#1-системные-константы-и-параметры)
2. [Базовые аксиомы](#2-базовые-аксиомы)
3. [Функция прибыли Φ](#3-функция-прибыли-φ)
4. [Функция качества Q](#4-функция-качества-q)
5. [Функция риска Ψ](#5-функция-риска-ψ)
6. [Функция репутации Υ](#6-функция-репутации-υ)
7. [Функция комплаенса Γ](#7-функция-комплаенса-γ)
8. [Функция эволюции Ω](#8-функция-эволюции-ω)
9. [Функция гомеостазиса H](#9-функция-гомеостазиса-h)
10. [Функция информации VoI](#10-функция-информации-voi)
11. [Атомарная декомпозиция](#11-атомарная-декомпозиция)
12. [Декомпозиция задач](#12-декомпозиция-задач)
13. [Классификация сложности](#13-классификация-сложности)
14. [Факторы способностей (x₁-x₁₇)](#14-факторы-способностей-x₁-x₁₇)
15. [Синергии факторов](#15-синергии-факторов)
16. [Функция полезности агента U](#16-функция-полезности-агента-u)
17. [Маршрутизация задач](#17-маршрутизация-задач)
18. [Сводная таблица всех функций](#18-сводная-таблица-всех-функций)

---

## 1. СИСТЕМНЫЕ КОНСТАНТЫ И ПАРАМЕТРЫ

### 1.1 Базовые константы (экзогенные переменные)

| Символ | Значение по умолчанию | Описание | Диапазон |
|--------|----------------------|----------|----------|
| $S_0$ | 0.30 | Базовый Success Rate (без факторов) | [0, 1] |
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
|--------|---------|----------|
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

## 3. ФУНКЦИЯ ПРИБЫЛИ Φ

### 3.1 Определение

$$\boxed{\Phi(\mathbf{x}) = \frac{P \cdot S(\mathbf{x}) \cdot Q(\mathbf{x}) - C(\mathbf{x})}{T(\mathbf{x})}}$$

где $\mathbf{x} = (x_1, x_2, \ldots, x_{17})$ — вектор факторов способностей.

### 3.2 Компоненты прибыли

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

### 3.3 Проверка размерности

| Компонент | Размерность | Проверка |
|----------|-------------|----------|
| $P$ | \$/задача | ✅ |
| $S$ | безразмерная [0,1] | ✅ |
| $Q$ | задач/час | ✅ |
| $C$ | \$/задача | ✅ |
| $T$ | час/задача | ✅ |
| $\Phi$ | \$/час | ✅ |

---

## 4. ФУНКЦИЯ КАЧЕСТВА Q

### 4.1 Определение

$$\boxed{Q = \alpha \cdot Q_{comp} + \beta \cdot Q_{acc} + \gamma \cdot Q_{full} + \delta \cdot Q_{time}}$$

где все веса нормированы: $\alpha + \beta + \gamma + \delta = 1$.

### 4.2 Компоненты качества

**Полнота (Completeness):**

$$Q_{comp} = \frac{|\text{CoveredAspects}|}{|\text{AllAspects}|}$$

**Точность (Accuracy):**

$$Q_{acc} = 1 - \frac{D_{KL}(P_{intent} \| P_{result})}{D_{max}}$$

или аппроксимация:

$$Q_{acc} \approx \text{cosine\_sim}(\text{embed}(intent), \text{embed}(result))$$

**Своевременность (Timeliness):**

$$Q_{time} = 1 - \min\left(1, \frac{t_{actual} - t_{deadline}}{t_{deadline}}\right)$$

### 4.3 Качество декомпозиции

$$\mathcal{Q}_{decomp} = \alpha \cdot \text{Completeness} + \beta \cdot \text{Independence} + \gamma \cdot \text{Granularity} + \delta \cdot \text{Feasibility}$$

### 4.4 Адаптивность к контексту

$$\mathcal{A}_c = \frac{\sum_{j=1}^{\max(N_{implicit}, 1)} \text{detected}(j) \cdot \text{satisfied}(j)}{\max(N_{implicit}, 1)}$$

---

## 5. ФУНКЦИЯ РИСКА Ψ

### 5.1 Определение

$$\boxed{\Psi = P_{fail} \cdot (C_{direct} + C_{reputation})}$$

### 5.2 Вероятность отказа

$$P_{fail} = P_{base} \cdot (1 + \alpha_u \cdot U + \alpha_f \cdot F + \alpha_n \cdot N + \alpha_d \cdot D) \cdot \frac{1}{1 + \alpha_s \cdot S}$$

где:
- $U$ — неопределённость задачи [0,1]
- $F$ — fatigue (усталость агента) [0,1]
- $N$ — новизна задачи [0,1]
- $D$ — deadline pressure [0,1]
- $S$ — skill level [0,1]

### 5.3 Каскадная вероятность

$$P_{cascade} = 1 - \prod_{i=1}^{n} (1 - p_i)$$

### 5.4 Guardrails Risk Reduction

$$P_{risk\_final} = P_{fail} \cdot \prod_{i} (1 - p_{risk,i} \cdot (1 - G_i))$$

где $G_i \in \{0, 1\}$ — эффективность i-го guardrail.

---

## 6. ФУНКЦИЯ РЕПУТАЦИИ Υ

### 6.1 Определение

$$\boxed{\Upsilon = \gamma_1 \cdot \bar{R} + \gamma_2 \cdot \tau_{ret} + \gamma_3 \cdot \frac{N^+}{N} + \gamma_4 \cdot (1 - \delta) + \gamma_5 \cdot \frac{d\Upsilon}{dt}}$$

где:
- $\bar{R}$ — средний рейтинг (нормированный в [0,1])
- $\tau_{ret}$ — retention rate (доля возвращающихся клиентов)
- $N^+/N$ — доля положительных отзывов
- $\delta$ — average delay ratio (задержка / SLA target)
- $\frac{d\Upsilon}{dt}$ — momentum (скорость изменения)

### 6.2 Байесовский рейтинг

$$R_{bayesian} = \frac{m \cdot \mu_0 + \sum_{i=1}^{n} r_i}{m + n}$$

где:
- $m = 7$ — сила prior
- $\mu_0 = 4.2$ — prior mean
- $r_i$ — отдельные оценки

### 6.3 Confidence в рейтинге

$$\Theta = 1 - \frac{1}{\sqrt{N}} \cdot \frac{\sigma_R}{R_{max} - R_{min}}$$

### 6.4 Order Flow (поток заказов)

$$\lambda_{orders} = \lambda_0 \cdot \left(\frac{R}{\bar{R}}\right)^{\beta_{rep}} \cdot \Theta^{\gamma_{trust}} \cdot (1 + SC)^{\delta_{social}}$$

### 6.5 Recovery Time (время восстановления)

$$\tau_{recovery} = \frac{\tau_{base}}{\rho_{resilience} \cdot (1 + \beta \cdot N_{good})}$$

### 6.6 Динамика репутации

$$\frac{dR}{dt} = \alpha \cdot Q \cdot (1 + \beta \cdot V_{resp}) - \gamma \cdot \text{incidents} \cdot R$$

где $V_{resp}$ — response velocity.

---

## 7. ФУНКЦИЯ КОМПЛАЕНСА Γ

### 7.1 Определение (Veto Function)

$$\boxed{\Gamma(action) = \begin{cases} 0, & \text{if } \forall r \in \text{Rules}: r(action) = \text{True} \\ -\infty, & \text{otherwise} \end{cases}}$$

> **Важно:** Γ не штрафует — Γ отвергает. $-\infty$ означает полный veto.

### 7.2 Примеры правил

| Правило | Условие | Описание |
|---------|---------|----------|
| $r_{legal}$ | не нарушает законы | Юридическая проверка |
| $r_{api}$ | $C_{api} \leq C_{max\_api}$ | Лимит API |
| $r_{budget}$ | $C_{total} \leq B_{remaining}$ | Бюджетное ограничение |
| $r_{security}$ | не модифицирует защищённые файлы | Безопасность |

### 7.3 Индикатор комплаенса

$$\mathbb{I}_{pass} = \begin{cases} 1, & \text{if } \Gamma = 0 \\ 0, & \text{if } \Gamma = -\infty \end{cases}$$

---

## 8. ФУНКЦИЯ ЭВОЛЮЦИИ Ω

### 8.1 Learning Curve

$$\boxed{L_s(t) = L_{max} \cdot (1 - e^{-\eta \cdot t^{\gamma}}) + L_0}$$

### 8.2 Knowledge Accumulation

$$\frac{dK}{dt} = \eta_{learn} \cdot \max(0, D_{task} - L_s) \cdot (1 - \frac{K}{K_{max}})$$

### 8.3 Forgetting Curve

$$\Phi_{memory}(t) = e^{-\frac{t}{\tau \cdot (1 + \kappa \cdot n)^{\psi}}}$$

где:
- $\tau$ — characteristic time
- $\kappa$ — benefit of repetitions
- $\psi$ — power law exponent
- $n$ — number of repetitions

### 8.4 Optimal Difficulty

$$D_{optimal}(t) = L_s(t) + \text{ZPD} \cdot \sigma_{skill}$$

### 8.5 Zone of Proximal Development

$$\text{ZPD} = \text{ZPD}_{base} \cdot (1 + \alpha_M \cdot M - \alpha_{CL} \cdot CL + \alpha_{\eta} \cdot \eta)$$

### 8.6 Transfer Learning

$$\Delta S_{transfer} = \gamma_{transfer} \cdot \text{TaskSimilarity}(t_{new}, t_{past}) \cdot K_{past}$$

### 8.7 Continual Learning Forgetting

$$S_{cl}(t) = S \cdot (1 - \rho_{forget} \cdot e^{-\lambda_{decay} \cdot t})$$

---

## 9. ФУНКЦИЯ ГОМЕОСТАЗИСА H

### 9.1 Определение (Homeostasis Index)

$$\boxed{H = \frac{F_{reinforcing} + \epsilon}{F_{balancing} + \epsilon}}$$

где $\epsilon = 10^{-6}$ защищает от деления на ноль.

### 9.2 Reinforcing Forces (усиливающие)

$$F_{reinforcing} = \nu \cdot \text{VoI} + \gamma_{\Upsilon} \cdot \Upsilon + \phi_{ft} \cdot \frac{dN_{tasks}}{dt}$$

### 9.3 Balancing Forces (уравновешивающие)

$$F_{balancing} = \lambda_{\Psi} \cdot \Psi + \rho_{E} \cdot E + \delta_{coord} \cdot N_{agents}^2$$

### 9.4 Интерпретация

| Диапазон H | Состояние | Описание |
|------------|----------|----------|
| $H > 1 + \epsilon_H$ | Рост | Система в фазе экспансии |
| $1 - \epsilon_H \leq H \leq 1 + \epsilon_H$ | Гомеостаз | Баланс |
| $H < 1 - \epsilon_H$ | Спад | Система в фазе стабилизации/упадка |

### 9.5 Maturity Index

$$K_{maturity}(t) = 1 - e^{-\lambda_{mat} \cdot (t - t_0)}$$

### 9.6 Adaptability Index

$$\mathcal{A} = \frac{\Delta \Phi_{recovery} + \epsilon}{\Delta \Phi_{loss} + \epsilon}$$

### 9.7 Utility Exploration-Exploitation

$$U(t) = K_{maturity}(t) \cdot U_{exploit} + (1 - K_{maturity}(t)) \cdot U_{explore}$$

### 9.8 Dynamic Complexity Ceiling

$$H_{max}(t) = H_{min} + (H_{max}^0 - H_{min}) \cdot (1 - K_{maturity}(t))$$

---

## 10. ФУНКЦИЯ ИНФОРМАЦИИ VoI

### 10.1 Определение

$$\boxed{\text{VoI} = \mathbb{E}[\Phi | \text{with info}] - \mathbb{E}[\Phi | \text{without info}]}$$

### 10.2 Shannon Entropy

$$H(X) = -\sum_{i} p_i \cdot \log_2(p_i)$$

### 10.3 Trust Zone Entropy

$$H_{TZ} = -\sum_{d \in D} P(d | T) \cdot \log_2 P(d | T)$$

### 10.4 Information Gain

$$\text{IG} = H_{prior} - H_{posterior}$$

### 10.5 Пример вычисления

```
E[Φ | ask] = Φ_yes · P(yes) + Φ_no · P(no)
            = 4450 · 0.3 + (-500) · 0.7 = 985

E[Φ | don't ask] = 3900 (baseline)

VoI = 985 - 3900 = -2915 (отрицательная → не стоит спрашивать)
```

---

## 11. АТОМАРНАЯ ДЕКОМПОЗИЦИЯ

### 11.1 Структура атомарного действия

$$\boxed{a = (p, f, c, m, o, \phi, r)}$$

где:
| Компонент | Тип | Описание |
|-----------|-----|----------|
| $p$ | $\mathcal{P}$ | Промт |
| $f$ | $\mathcal{F}$ | Формат вывода |
| $c$ | $\mathbb{R}^d$ | Контекст |
| $m$ | $\mathcal{M}$ | Модель |
| $o$ | $O$ | Выход |
| $\phi$ | $[0,1]$ | Confidence |
| $r$ | $\mathbb{R}^+$ | Ресурсы |

### 11.2 Utility одного действия

$$u(a) = \phi(a) \cdot P(\text{success} | a, m) \cdot \text{quality}(m)$$

### 11.3 Correlation между действиями

$$\rho(a_i, a_j) = \sigma(\mathbf{w}_{dep}^T \cdot [\mathbf{e}(a_i); \mathbf{e}(a_j)] - b_{dep})$$

### 11.4 Utility декомпозиции

$$\mathcal{U}(A, \theta) = \prod_{i=1}^{n} u(a_i) \cdot \prod_{(i,j) \in E} \rho(a_i, a_j)$$

### 11.5 Cost декомпозиции

$$\mathcal{C}(A, \theta) = \sum_{i=1}^{n} [\alpha \cdot \text{cost}(m_i) + \beta \cdot \text{latency}(m_i) + \gamma \cdot |c_i|]$$

### 11.6 Целевая функция декомпозиции

$$\boxed{D^*(T) = \underset{(A, \theta)}{\arg\max} \; \mathbb{I}_{pass}(\Gamma(A)) \cdot \left[ \mathcal{U}(A, \theta) - \lambda \cdot \mathcal{C}(A, \theta) \right]}$$

### 11.7 Решение о декомпозиции

$$\delta(T) = \sigma(\mathbf{w}_\delta^T \cdot \mathbf{f}(T) + b_\delta)$$

где $\mathbf{f}(T)$ — feature vector задачи.

### 11.8 Confidence Score

$$\phi(a) = \sigma(\mathbf{w}_\phi^T \cdot \mathbf{f}(a) + b_\phi)$$

### 11.9 Optimal Format

$$f^*(a) = \underset{f \in \mathcal{F}}{\arg\max} \; P(f | a, \theta_f)$$

### 11.10 Optimal Model

$$m^*(a) = \underset{m \in \mathcal{M}}{\arg\max} \; u(a, m) - \lambda_m \cdot \text{cost}(m)$$

где:
$$u(a, m) = P(\text{success} | a, m) \cdot \text{quality}(m)$$

### 11.11 Optimal Context

$$c^*(a) = \underset{c \subseteq \mathcal{R}}{\arg\max} \; [\text{Relevance}(a, c) - \lambda_c \cdot \text{Cost}(c)]$$

где:
$$\text{Relevance}(a, c) = \frac{1}{|\mathcal{K}|} \sum_{k \in \mathcal{K}} \text{BM25}(a, c_k) \cdot \text{RRF}(k)$$

---

## 12. ДЕКОМПОЗИЦИЯ ЗАДАЧ

### 12.1 Результат декомпозиции

$$D(T) = (\mathcal{S}, \mathcal{G})$$

где:
- $\mathcal{S} = \{s_1, s_2, \ldots, s_n\}$ — множество подзадач
- $\mathcal{G} = (\mathcal{S}, \mathcal{E})$ — DAG зависимостей

### 12.2 Optimal Depth

$$\text{depth}^* = \text{Round}\left(\log_2\left(\frac{|\text{affected\_files}| \cdot \text{complexity}}{\tau_{task}}\right)\right)$$

### 12.3 Dependency Function

$$\text{Dep}(s_i, s_j) = \mathbb{I}[\sigma(\mathbf{w}_{dep}^T \cdot [\mathbf{e}(s_i); \mathbf{e}(s_j)] - b_{dep}) > \tau_{dep}]$$

### 12.4 Feasibility

$$P(\text{feasible}(s)) = \sigma(\mathbf{w}_{feas}^T \cdot \mathbf{e}(s) + b_{feas})$$

### 12.5 Effort Estimation

$$\widehat{\text{effort}}(s) = \mathbf{w}_{eff}^T \cdot \mathbf{f}(s) + b_{eff}$$

### 12.6 Total Effort

$$\text{Effort}(T) = \sum_{s \in \mathcal{S}} \widehat{\text{effort}}(s) + \alpha \cdot \text{Overhead}(|\mathcal{S}|)$$

### 12.7 Parallelism Level

$$\text{Level}(l) = \{s \in \mathcal{S} : \text{longest\_path}(s) = l\}$$

$$\text{max\_parallelism} = \max_l |\text{Level}(l)|$$

### 12.8 Conflict Detection

$$\text{Conflict}(s_i, s_j) = \mathbb{I}(\text{ModifiesOverlap}(s_i, s_j) \land \neg \text{Ordered}(s_i, s_j))$$

---

## 13. КЛАССИФИКАЦИЯ СЛОЖНОСТИ

### 13.1 Классификация

$$\hat{c} = \underset{j \in \{1,\ldots,K\}}{\arg\max} \; P(c=j | \mathbf{x}, \theta)$$

### 13.2 Ordinal Classification

$$\hat{c} = 1 + \sum_{k=1}^{K-1} \mathbb{I}(\phi_k > 0)$$

где $\phi_k = \mathbf{w}_k^T \cdot \mathbf{e}_{fused} + b_k$.

### 13.3 Text Encoding

$$\mathbf{e}_{text} = \alpha \cdot \text{BERT}(\text{title}) + (1-\alpha) \cdot \text{Pool}(\text{BERT}(\text{description}))$$

### 13.4 Metadata Encoding

$$\mathbf{e}_{meta} = \text{ReLU}(\mathbf{W}_{meta} \cdot \mathbf{x}_{meta} + \mathbf{b}_{meta})$$

### 13.5 Fusion Layer

$$\mathbf{e}_{fused} = \text{gate} \odot \mathbf{e}_{text} + (1 - \text{gate}) \odot \mathbf{e}_{context}$$

где:
$$\text{gate} = \sigma(\mathbf{W}_{gate} \cdot [\mathbf{e}_{text}; \mathbf{e}_{context}] + \mathbf{b}_{gate})$$

### 13.6 Loss Function

$$\mathcal{L} = \mathcal{L}_{ordinal} + \beta \cdot (\mathcal{L}_{consistency} + \mathcal{L}_{ordinality})$$

---

## 14. ФАКТОРЫ СПОСОБНОСТЕЙ (x₁-x₁₇)

### 14.1 Полная таблица факторов

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
| $x_{12}$ | Guardrails | $G_{eff} = \prod_i (1 - p_i \cdot (1 - G_i))$ | $+\beta_g \cdot G_{eff}$ | +0.02 |
| $x_{13}$ | Reasoning | $T_{think}/T_{base}$ | $\beta \cdot \log(1 + T_{think}/T_{base})$ | +0.25 |
| $x_{14}$ | Design Patterns | $\sum_p \alpha_p \cdot P_p$ | $+\beta \cdot \sum \alpha_p P_p$ | -0.05 |
| $x_{15}$ | Evaluation | $\alpha_e \cdot B_{cov} + \beta_e \cdot A_{score}$ | +0.08 | +0.03 |
| $x_{16}$ | Continual Learning | $K_{cl}(t) = 1 - e^{-\lambda_{cl} N_{tasks}}$ | $+\gamma_{cl} \cdot K_{cl}$ | -0.10 |
| $x_{17}$ | Inference Opt | $\prod_o (1 - \delta_o)$ | 0 | -0.20 |

### 14.2 LLM Capability Definition (x₁)

$$C_{llm} = \alpha_Q \cdot Q_{bench} + \alpha_R \cdot R_{bench} + \alpha_C \cdot C_{bench} + \alpha_A \cdot A_{bench}$$

где:
| Компонент | Вес | Описание |
|-----------|-----|---------|
| $\alpha_Q$ | 0.25 | Quality (benchmarks) |
| $\alpha_R$ | 0.30 | Reasoning (логика) |
| $\alpha_C$ | 0.25 | Coding (agent tasks) |
| $\alpha_A$ | 0.20 | Agentic (tool use) |

### 14.3 Success Rate с учётом LLM

$$S(m, t) = \frac{C_{llm}(m)}{1 + e^{-\lambda_t \cdot (C_{llm}(m) - \tau_t)}}$$

### 14.4 Throughput с учётом LLM

$$Q(m) = Q_{max} \cdot \frac{C_{llm}(m)}{1 + \gamma \cdot (1 - C_{llm}(m))}$$

### 14.5 Cost Model

$$C_{api}(m, t) = I_t \cdot P^{in}_m + O_t \cdot P^{out}_m$$

### 14.6 Memory Factor (x₄)

$$\Delta S_{memory} = \beta_0 + \beta_1 \cdot M_p + \beta_2 \cdot M_p^2$$

$$Q(M_p) = Q_0 \cdot (1 + \gamma \cdot M_p \cdot (1 - e^{-\delta \cdot M_p}))$$

$$C_{memory} = C_{storage} + C_{retrieval} + C_{maintenance}$$

### 14.7 Multi-Agent (x₅)

$$\Delta S_{multi} = \alpha_0 + \alpha_1 \cdot \log(N_{agents}) + \alpha_2 \cdot \frac{N_{agents}}{N_{agents} + \beta}$$

$$C_{coordination} = \delta_1 \cdot N_{agents} \cdot \log(N_{agents}) + \delta_2 \cdot N_{agents}^2$$

### 14.8 Grounding (x₉)

$$G_{score} = \alpha_{ret} \cdot Q_{ret} + \alpha_{rerank} \cdot Q_{rerank} + \alpha_{gen} \cdot F_{faith}$$

$$\Delta S_G = \beta_0 + \beta_1 \cdot G_{score} \cdot d$$

### 14.9 Inference Optimization (x₁₇)

| Оптимизация | $\delta_o$ |
|------------|------------|
| Caching | 0.10 |
| Quantization INT8 | 0.20 |
| Flash Attention | 0.15 |
| Speculative Decoding | 0.30 |
| Batch Processing | 0.25 |

$$T_{opt} = T_0 \cdot \prod_{o} (1 - \delta_o)$$

---

## 15. СИНЕРГИИ ФАКТОРОВ

### 15.1 Определение

$$\gamma_{syn} = \sum_{(i,j) \in \text{synergies}} \Delta\gamma_{ij} \cdot x_i \cdot x_j$$

где $x_i \in \{0, 1\}$ для бинарных факторов.

### 15.2 Матрица синергий

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

## 16. ФУНКЦИЯ ПОЛЕЗНОСТИ АГЕНТА U

### 16.1 Определение

$$\boxed{U = \lambda_\Phi \cdot \Phi + \lambda_\Upsilon \cdot \Upsilon + \lambda_Q \cdot Q + \lambda_\Omega \cdot \Omega - \lambda_\Psi \cdot \Psi - \lambda_\Gamma \cdot \Gamma}$$

где веса определяются Mission:
$$\lambda_\Phi + \lambda_\Upsilon + \lambda_Q + \lambda_\Omega + \lambda_\Psi + \lambda_\Gamma = 1$$

### 16.2 Economic Utility

$$U_{economic} = \Phi \cdot (1 + \alpha_{rep} \cdot \Upsilon)$$

### 16.3 Extended Utility с Knowledge

$$U_{ext} = \Phi + \lambda_\Upsilon \cdot \Upsilon + \alpha_K \cdot K + \lambda_{VoI} \cdot \text{VoI}$$

### 16.4 Lambda Cost Function (Homeostasis Modulation)

$$\lambda_{cost}(t) = \lambda_0 \cdot \frac{H(t)}{H_{target}} \cdot (1 + \alpha_\Psi \cdot \Psi(t))$$

---

## 17. МАРШРУТИЗАЦИЯ ЗАДАЧ

### 17.1 Task Embedding

$$\mathbf{e}_{task} = \text{Embed}(T) \in \mathbb{R}^d$$

### 17.2 Domain Centroid

$$\mathbf{c}_k = \frac{1}{N_k} \sum_{i=1}^{N_k} \mathbf{e}_i$$

### 17.3 Cosine Similarity

$$\text{sim}(\mathbf{e}_{task}, \mathbf{c}_k) = \frac{\mathbf{e}_{task} \cdot \mathbf{c}_k}{\|\mathbf{e}_{task}\| \|\mathbf{c}_k\|}$$

### 17.4 Domain Prediction

$$\hat{d} = \arg\max_k \text{sim}(\mathbf{e}_{task}, \mathbf{c}_k) \quad \text{if} \quad \max_k \text{sim} \geq \tau_{fast}$$

### 17.5 Fine-Grained Routing

$$(d_{fine}, \rho_{diff}, \kappa_{conf}, \mathbf{b}, \mathbb{T}_{rec}) = \mathcal{L}(T, \text{system\_prompt})$$

### 17.6 Decision Function

$$\mathcal{D}(T) = \begin{cases} 
\textbf{REJECT}, & \text{if } H_{TZ} > H_{max} \\
\textbf{CLARIFY}, & \text{if } \tau_{auto} > \kappa_{conf} \geq \tau_{clarify} \land \Phi_{pred} \cdot \kappa_{conf} > \Phi_{min} \\
\textbf{EXECUTE}, & \text{if } U(\Phi_{pred}) > 0
\end{cases}$$

### 17.7 Full Semantic Router

$$\mathcal{R}(T) = \begin{cases} 
\mathcal{D}(\mathcal{L}(T)), & \text{if } \max_k \text{sim} < \tau_{fast} \\
\mathcal{D}(\hat{d}, 0.5, 1.0), & \text{otherwise}
\end{cases}$$

### 17.8 Router Cost

$$C_{\mathcal{R}} = C_{embed} + \begin{cases} C_{router\_fine}, & \text{if } \max_k \text{sim} < \tau_{fast} \\ 0, & \text{otherwise} \end{cases}$$

---

## 18. СВОДНАЯ ТАБЛИЦА ВСЕХ ФУНКЦИЙ

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
| S | Success Rate | $S_0 + \sum \beta_i x_i + \sum \gamma_{ij} x_i x_j$ | x | [0,1] |
| U | Utility | $\lambda \cdot \Phi + \lambda \cdot \Upsilon + \ldots$ | all functions | scalar |

---

## APPENDIX A: АКТИВАЦИОННЫЕ ФУНКЦИИ

### Сигмоида
$$\sigma(x) = \frac{1}{1 + e^{-x}}$$

### ReLU
$$\text{ReLU}(x) = \max(0, x)$$

### Softmax
$$\text{Softmax}(\mathbf{x})_i = \frac{e^{x_i}}{\sum_j e^{x_j}}$$

---

## APPENDIX B: РАЗМЕРНОСТИ

| Функция | Размерность | Единица |
|---------|------------|--------|
| Φ | [0, ∞) | \$/час |
| Q | [0, 1] | безразмерная |
| Ψ | [0, ∞) | \$ |
| Υ | [0, 1] | безразмерная |
| Γ | {0, -∞} | — |
| H | (0, ∞) | ratio |
| VoI | (-∞, ∞) | \$ |
| S | [0, 1] | безразмерная |

---

## APPENDIX C: ГРАНИЧНЫЕ УСЛОВИЯ

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

*Модель создана: 2026-07-06*  
*Версия: 1.0*  
*Статус: ✅ Финальная*
