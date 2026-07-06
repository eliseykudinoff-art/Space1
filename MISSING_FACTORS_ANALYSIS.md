# 📋 Анализ пропущенных факторов в математической модели

## ⚠️ Обнаруженное расхождение

| Часть документа | Количество факторов | Статус |
|-----------------|---------------------|--------|
| Практический Guide (строки 1-598) | **17 факторов** | ✅ Полный |
| Математическая модель (строки 623+) | **11 факторов** (x₁-x₁₁) | ❌ Неполный |

---

## 🔍 Детальный анализ

### Практический Guide — все 17 факторов:

| # | Фактор | Включён в мат. модель? | Обозначение |
|---|--------|------------------------|-------------|
| 1 | LLM модель | ✅ Да | $x_1$ |
| 2 | Tool Calling | ✅ Да | $x_2$ |
| 3 | MCP | ✅ Да | $x_3$ |
| 4 | Memory | ✅ Да | $x_4$ |
| 5 | Multi-Agent | ✅ Да | $x_5$ |
| 6 | Self-Correction | ✅ Да | $x_6$ |
| 7 | Prompts | ✅ Да | $x_7$ |
| 8 | Cost Tiering | ✅ Да | $x_8$ |
| 9 | Guardrails & Safety | ❌ **ПРОПУЩЕН** | **$x_{12}$** |
| 10 | Test-Time Compute | ❌ **ПРОПУЩЕН** | **$x_{13}$** |
| 11 | Fine-tuning | ✅ Да | $x_{10}$ |
| 12 | Design Patterns | ❌ **ПРОПУЩЕН** | **$x_{14}$** |
| 13 | Browser Automation | ✅ Да | $x_{11}$ |
| 14 | Evaluation | ❌ **ПРОПУЩЕН** | **$x_{15}$** |
| 15 | Continual Learning | ❌ **ПРОПУЩЕН** | **$x_{16}$** |
| 16 | Grounding | ✅ Да | $x_9$ |
| 17 | Inference Optimization | ❌ **ПРОПУЩЕН** | **$x_{17}$** |

---

## ❌ Пропущенные факторы (6 штук)

### 1. $x_{12}$: Guardrails & Safety

**Из документа:**
```
Без этого агент может "уйти в sandbox" или потерять деньги.
```

**Математическая формализация:**

$$S_{safe}(x) = S(x) \cdot \prod_{i} (1 - p_{risk,i} \cdot (1 - G_i))$$

где:
- $p_{risk,i}$ — вероятность рискового события для фактора $i$
- $G_i$ — эффективность guardrails (0 или 1)

**Влияние на целевую функцию:**

$$C_{risk} = \sum_{j} P_j \cdot L_j \cdot (1 - R_{guardrails,j})$$

где:
- $P_j$ — вероятность события $j$
- $L_j$ — потенциальный убыток
- $R_{guardrails,j}$ — снижение риска guardrails

**Синергия:** $x_{12} + x_2$ (Guardrails усиливают Tool Calling)

---

### 2. $x_{13}$: Test-Time Compute (Reasoning)

**Из документа:**
```
o1-preview превосходит Claude 5 Sonnet на сложных задачах 
за счёт "рассуждающего" режима.
```

**Математическая формализация:**

$$\phi_{reason} = \alpha_{reason} \cdot \log(1 + \frac{T_{think}}{T_{base}})$$

**Success Rate с reasoning:**

$$S_{reason}(x) = S(x) + \beta_{reason} \cdot \phi_{reason} \cdot (1 - S(x))$$

**Time penalty:**

$$T_{reason} = T(x) \cdot (1 + \gamma_{think} \cdot \frac{T_{think}}{T_{base}})$$

**ROI:**

$$\text{ROI}_{reasoning} = \frac{\Delta S \cdot P}{\Delta C_{api}}$$

---

### 3. $x_{14}$: Agentic Design Patterns

**Из документа:**
```
Pattern 1: ReAct (Reasoning + Acting)
Pattern 2: Reflection
Pattern 3: Planning
```

**Математическая формализация:**

$$S_{pattern}(x) = S(x) + \sum_{p \in \text{Patterns}} \alpha_p \cdot P_p(x)$$

где $P_p(x)$ — probability of applying pattern $p$.

| Паттерн | $\alpha_p$ | Применение |
|---------|------------|------------|
| ReAct | +0.08 | Exploration tasks |
| Reflection | +0.12 | Quality-critical |
| Planning | +0.15 | Complex multi-step |

**Множитель throughput:**

$$Q_{pattern} = Q(x) \cdot \prod_p (1 + \beta_p \cdot P_p)$$

---

### 4. $x_{15}$: Evaluation & Benchmarking

**Из документа:**
```
Benchmarks: GAIA (74.5%), SWE-bench, WebArena, RLI (2.5%), ARC-AGI
```

**Математическая формализация:**

**Calibration function:**

$$\hat{S}(x) = \alpha_{eval} \cdot S_{measured}(x) + (1 - \alpha_{eval}) \cdot S_{predicted}(x)$$

**Improvement rate:**

$$\frac{dS}{dt} = \eta_{eval} \cdot \text{BenchmarkCoverage}(x) \cdot S(x)$$

**Decision utility:**

$$\text{VoI}_{eval} = \mathbb{E}[\max_a U(a | \text{eval results})] - \max_a U(a | \text{no eval})$$

---

### 5. $x_{16}$: Continual Learning

**Из документа:**
```
Агент учится на своих ошибках.
failed_patterns, successful_patterns
```

**Математическая формализация:**

**Knowledge accumulation:**

$$K(t) = K_0 + \int_0^t \eta_{learn} \cdot \Delta K(\tau) \cdot (1 - \frac{K(\tau)}{K_{max}}) d\tau$$

**Transfer learning benefit:**

$$\Delta S_{transfer} = \gamma_{transfer} \cdot \text{TaskSimilarity}(t_{new}, t_{past}) \cdot K_{past}$$

**Forgetting factor:**

$$S_{cl}(x) = S(x) \cdot (1 - \rho \cdot e^{-\lambda \cdot t})$$

где $\rho$ — скорость забывания.

---

### 6. $x_{17}$: Inference Optimization

**Из документа:**
```
Speculative decoding, Flash Attention, Квантизация, Кэширование
Кэширование: 75% входных токенов за 10% цены
```

**Математическая формализация:**

**Speedup factors:**

$$T_{opt}(x) = T(x) \cdot \prod_{o \in \text{Optimizations}} (1 - \delta_o \cdot O_o)$$

| Оптимизация | $\delta_o$ | Примечание |
|-------------|-----------|------------|
| Caching | 0.10 | 10% latency reduction |
| Quantization INT8 | 0.20 | |
| Flash Attention | 0.15 | |
| Speculative Decoding | 0.30 | |
| Batch Processing | 0.25 | |

**Cost reduction:**

$$C_{opt}(x) = C(x) \cdot (1 - \sum_o \gamma_o \cdot O_o)$$

**Quality penalty (if any):**

$$S_{opt}(x) = S(x) \cdot (1 - \epsilon_{quant} \cdot Q_{quantization})$$

---

## 📐 Расширенная целевая функция

### Текущая (11 факторов):

$$\Phi_{11}(x) = \frac{P \cdot Q_0 \cdot S_{11}(x) - C_{11}(x)}{T_{11}(x)}$$

### Расширенная (17 факторов):

$$\boxed{\Phi_{17}(x) = \frac{P \cdot Q_0 \cdot S_{17}(x) - C_{17}(x) - C_{risk}(x)}{T_{17}(x)}}$$

где:

$$S_{17}(x) = S_0 + \sum_{i=1}^{17} \beta_i x_i + \sum_{i<j} \gamma_{ij} x_i x_j$$

$$C_{17}(x) = C_{base} + C_{api}(x) + C_{compute}(x) + C_{failure}(x) - C_{opt}(x)$$

$$T_{17}(x) = T_{base} \cdot \prod_i d_i(x_i) \cdot (1 - \delta_{reasoning} \cdot x_{13})$$

---

## 📋 План реализации недостающих частей

### Этап 1: Guardrails ($x_{12}$)
```
Задачи:
□ Определить типы рисков {financial, security, reputational}
□ Формализовать P_j (вероятности событий)
□ Определить L_j (потенциальные убытки)
□ Реализовать функцию C_risk(x)
□ Добавить синергию с x₂ (Tool Calling)
□ Написать unit-тесты
□ Добавить в unified_model.md
```

### Этап 2: Test-Time Compute ($x_{13}$)
```
Задачи:
□ Определить T_think / T_base ratio
□ Формализовать φ_reason
□ Реализовать S_reason(x)
□ Добавить time penalty
□ Рассчитать ROI_threshold
□ Интегрировать в pipeline
□ Написать unit-тесты
```

### Этап 3: Design Patterns ($x_{14}$)
```
Задачи:
□ Определить паттерны {ReAct, Reflection, Planning}
□ Формализовать α_p для каждого паттерна
□ Реализовать P_p(x) — probability of pattern
□ Интегрировать с Self-Correction (x₆)
□ Добавить в unified_model.md
```

### Этап 4: Evaluation ($x_{15}$)
```
Задачи:
□ Определить набор benchmarks
□ Формализовать calibration function
□ Реализовать measurement pipeline
□ Интегрировать VoI calculation
□ Написать unit-тесты
```

### Этап 5: Continual Learning ($x_{16}$)
```
Задачи:
□ Определить knowledge representation
□ Формализовать K(t) accumulation
□ Реализовать forgetting factor
□ Интегрировать с Memory (x₄)
□ Добавить transfer learning benefit
□ Написать unit-тесты
```

### Этап 6: Inference Optimization ($x_{17}$)
```
Задачи:
□ Определить optimizations {cache, quant, flash, spec, batch}
□ Формализовать δ_o для каждой оптимизации
□ Реализовать T_opt(x) и C_opt(x)
□ Учесть quality penalty от квантизации
□ Написать unit-тесты
□ Добавить benchmarks
```

---

## 📊 Сводная таблица новых факторов

| ID | Фактор | $\beta_i$ (влияние на S) | $\delta_i$ (влияние на T) | Приоритет |
|----|--------|---------------------------|--------------------------|-----------|
| $x_{12}$ | Guardrails | +0.05 | +0.02 | Высокий |
| $x_{13}$ | Test-Time Compute | +0.18 | +0.25 | Средний |
| $x_{14}$ | Design Patterns | +0.10 | -0.05 | Средний |
| $x_{15}$ | Evaluation | +0.08 | +0.03 | Низкий |
| $x_{16}$ | Continual Learning | +0.12 | -0.10 | Средний |
| $x_{17}$ | Inference Opt | 0 | -0.20 | Высокий |

---

## 🔄 Новые синергии

| Пара | $\Delta\gamma$ | Механизм |
|------|---------------|----------|
| $x_6 + x_{14}$ | +0.15 | Self-correction + Reflection |
| $x_4 + x_{16}$ | +0.10 | Memory + Continual Learning |
| $x_2 + x_{12}$ | +0.08 | Tools + Safety |
| $x_1 + x_{13}$ | +0.12 | LLM + Reasoning |
| $x_{17} + x_8$ | +0.06 | Optimization + Cost tiering |

---

*Анализ подготовлен: 2026-07-05*
*Автор: OpenHands Agent*