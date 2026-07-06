# 🔧 РУКОВОДСТВО ПО ИСПРАВЛЕНИЮ ФОРМУЛ

## Содержание
1. [Немедленные исправления](#1-немедленные-исправления)
2. [Структурные исправления](#2-структурные-исправления)
3. [Перенумерация формул](#3-перенумерация-формул)
4. [Добавление недостающих определений](#4-добавление-недостающих-определений)
5. [Унификация нотации](#5-унификация-нотации)
6. [Патч-файлы](#6-патч-файлы)

---

## 1. НЕМЕДЛЕННЫЕ ИСПРАВЛЕНИЯ

### 1.1 F012 — Дублирующая скобка

**Файл:** ALL_FORMULAS.txt, строка ~107

```diff
## F012: Professional Conscientiousness Function

-$$\Xi_{task} = \underbrace{\alpha \cdot Q_{result}}_{\text{Качество результата}} - \underbrace{\beta \cdot (O_{time} + O_{cost})}}_{\text{Штраф за перерасход ресурсов}}}$$
+$$\Xi_{task} = \underbrace{\alpha \cdot Q_{result}}_{\text{Качество результата}} - \underbrace{\beta \cdot (O_{time} + O_{cost})}_{\text{Штраф за перерасход ресурсов}}$$
```

---

### 1.2 F062, F065, F450 — Защита от деления на ноль

**Файл:** ALL_FORMULAS.txt, строки ~535, ~564, ~2611

```diff
## F062: Homeostasis Index

-$$\Gamma = \frac{\sum \text{Reinforcing}}{\sum \text{Balancing}}$$
+$$\Gamma = \frac{\sum \text{Reinforcing}}{\sum \text{Balancing} + \epsilon_\Gamma}, \quad \text{где } \epsilon_\Gamma = 10^{-6}$$

**Комментарий:** $\epsilon_\Gamma$ предотвращает деление на ноль при отсутствии балансирующих сил.
```

```diff
## F065: Full Homeostasis

-$$\Gamma = \frac{\nu \cdot VoI + \gamma \cdot \Upsilon + \phi_{ft} \cdot \frac{dN_{tasks}}{dt}}{\lambda \cdot \Psi + \rho \cdot E + \delta_{coord} \cdot N_{agents}^2}$$
+$$\Gamma = \frac{\nu \cdot VoI + \gamma \cdot \Upsilon + \phi_{ft} \cdot \frac{dN_{tasks}}{dt}}{\lambda \cdot \Psi + \rho \cdot E + \delta_{coord} \cdot N_{agents}^2 + \epsilon_\Gamma}$$
```

---

### 1.3 F024 — Защита от N_implicit = 0

**Файл:** ALL_FORMULAS.txt, строка ~206

```diff
## F024: Адаптивность к контексту

-$$\mathcal{A}_c = \frac{1}{N_{implicit}} \sum_{j=1}^{N_{implicit}} \text{detected}(j) \cdot \text{satisfied}(j)$$
+$$\mathcal{A}_c = \frac{\sum_{j=1}^{\max(N_{implicit}, 1)} \text{detected}(j) \cdot \text{satisfied}(j)}{\max(N_{implicit}, 1)}$$

**Или альтернативно:**
+$$A_c = \begin{cases} 
+0 & \text{если } N_{implicit} = 0 \\
+\frac{1}{N_{implicit}} \sum_{j=1}^{N_{implicit}} \text{detected}(j) \cdot \text{satisfied}(j) & \text{иначе}
+\end{cases}$$
```

---

### 1.4 F066 — Защита от ΔΦ_loss = 0

**Файл:** ALL_FORMULAS.txt, строка ~572

```diff
## F066: Adaptability Index

-$$\mathcal{A} = \frac{\Delta \Phi_{recovery}}{\Delta \Phi_{loss}}$$
+$$\mathcal{A} = \frac{\Delta \Phi_{recovery}}{\Delta \Phi_{loss} + \epsilon_A}, \quad \epsilon_A = 10^{-6}$$
```

---

## 2. СТРУКТУРНЫЕ ИСПРАВЛЕНИЯ

### 2.1 Перенос определений u(a) и ρ перед F028

**ПРОБЛЕМА:** F028 использует `u(a_i)` и `ρ(a_i, a_j)`, которые определены в F221 и F222.

**РЕШЕНИЕ:** Создать новые ID для F221→F028a и F222→F028b, затем F028 становится F028c.

**Новый порядок:**

```
## F028a: Utility of Action (перенесено из F221)

$$u(a) = \phi(a) \cdot P(\text{success} | a, m) \cdot \text{quality}(m)$$

где:
- $\phi(a)$ — confidence из F090
- $P(\text{success}|a,m)$ — вероятность успеха (определена в F_NEW_1)
- $\text{quality}(m)$ — нормированная оценка модели (определена в F_NEW_2)

---

## F028b: Correlation of Actions (перенесено из F222)

$$\rho(a_i, a_j) = \sigma(\mathbf{w}_{dep}^T \cdot [\mathbf{e}(a_i); \mathbf{e}(a_j)] - b_{dep})$$

**Контекст:** Это вероятность того, что действия связаны.

---

## F028c: Atomic Decomposition Quality (было F028)

$$\mathcal{U}(A, \theta) = \prod_{i=1}^{n} u(a_i) \cdot \prod_{(i,j) \in E} \rho(a_i, a_j)$$
```

---

### 2.2 Добавление недостающих определений для F002

**ПРОБЛЕМА:** F002 использует P, T_opt, x_12, x_17 которые не определены.

**РЕШЕНИЕ:** Добавить определения перед F002.

```
## F001b: Price Definition (НОВОЕ)

$$P = P_{per\_task} \cdot N_{tasks}$$

где:
- $P_{per\_task}$ — цена за задачу (константа)
- $N_{tasks}$ — количество выполненных задач

**Источник:** Определено для полноты F002

---

## F001c: Inference Optimization Time (НОВОЕ)

$$T_{opt}(x_{17}) = T_0 \cdot \prod_{o \in \text{optimizations}} (1 - \delta_o)$$

где оптимизации включают:
- Caching: $\delta_{cache} = 0.10$
- Quantization: $\delta_{quant} = 0.20$
- Flash Attention: $\delta_{flash} = 0.15$
- Speculative Decoding: $\delta_{spec} = 0.30$
- Batch Processing: $\delta_{batch} = 0.25$

**Источник:** Определено для полноты F002
```

---

### 2.3 Определение Φ_R(D)

**ПРОБЛЕМА:** F014 использует Φ_R(D), но есть два определения (F223 и F224).

**РЕШЕНИЕ:** Унифицировать в одно определение.

```
## F014a: Routing Quality — Unified Definition (НОВОЕ)

$$\Phi_R(D) = \Phi(D) \cdot \mathbb{I}[\Gamma(D) = 0] \cdot \left(1 + \alpha_{rep} \cdot \Upsilon \right) - \lambda_\Psi \cdot \Psi(D)$$

где:
- $\Phi(D)$ — прибыль декомпозиции (F001)
- $\mathbb{I}[\Gamma(D) = 0]$ — индикатор прохождения комплаенс (F061)
- $\alpha_{rep}$ — коэффициент репутационного бонуса
- $\Upsilon$ — репутация (F040)
- $\lambda_\Psi$ — коэффициент штрафа за риск
- $\Psi(D)$ — риск декомпозиции (F031)

**Контекст:** План получает качество только если прошёл Compliance, 
умножается на репутационный бонус, и штрафуется за риск.
```

---

## 3. ПЕРЕНУМЕРАЦИЯ ФОРМУЛ

### 3.1 Рекомендуемый порядок формул

| Старый ID | Новый ID | Причина |
|-----------|----------|---------|
| F028 | F028c | Требует F028a, F028b |
| F221 | F028a | Utility of Action |
| F222 | F028b | Correlation of Actions |
| F223 | F014a | Унификация Φ_R |
| F224 | — | УДАЛИТЬ (дубликат F014a) |

### 3.2 Удаление дубликатов

| Удалить | Оставить | Формула |
|---------|----------|---------|
| F162 | F174 | Cosine Similarity |
| F070 | F430 | Shannon Entropy |
| F175 | F430 | Shannon Entropy |
| F062 | F450 | Homeostasis Index |
| F065 | F450 | Full Homeostasis |
| F012 | F220 | Ξ_task |
| F010 | F451 | Team Efficiency |
| F011 | F452 | Competitive Pressure |
| F229 | F470 | Υ_ext |

---

## 4. ДОБАВЛЕНИЕ НЕДОСТАЮЩИХ ОПРЕДЕЛЕНИЙ

### 4.1 Новые формулы для базовых функций

```
## NEW_F_BASICS: Базовые определения

### S(x) — Base Success Rate
$$S(x) = S_0 \cdot \prod_{i=1}^{11} f_{S,i}(x_i)$$

где $f_{S,i}$ определены в F302-F410.

### Q(x) — Base Quality Rate
$$Q(x) = Q_0 \cdot \prod_{i=1}^{11} f_{Q,i}(x_i)$$

где $f_{Q,i}$ аналогично S(x).

### C(x) — Base Cost Function
$$C(x) = C_0 + \sum_{i=1}^{11} \Delta C_i(x_i)$$

### T(x) — Base Time Function
$$T(x) = T_0 \cdot \prod_{i=1}^{11} f_{T,i}(x_i)$$

### R(x) — Revenue Function
$$R(x) = P \cdot S(x) \cdot Q(x)$$
```

### 4.2 Новые формулы для факторов x₁₂-x₁₇

```
## F512: Guardrails (x₁₂)

$$x_{12} = G_{eff} = \prod_{i} (1 - p_{risk,i} \cdot (1 - G_i))$$

где:
- $p_{risk,i}$ — вероятность i-го рискового события
- $G_i$ — эффективность i-го guardrail (0 или 1)

$$\Delta S_{guardrails} = \beta_g \cdot G_{eff}$$

---

## F513: Test-Time Compute (x₁₃)

$$x_{13} = T_{think} / T_{base}$$

$$\Delta S_{reasoning} = \beta_r \cdot \log(1 + T_{think}/T_{base})$$

$$\Delta T_{reasoning} = 1 + 0.25 \cdot T_{think}/T_{base}$$

---

## F514: Design Patterns (x₁₄)

$$x_{14} = \sum_{p \in \text{Patterns}} \alpha_p \cdot P_p(x)$$

где паттерны и их веса определены в F153.

---

## F515: Evaluation (x₁₅)

$$x_{15} = \alpha_e \cdot \text{BenchmarkCoverage} + \beta_e \cdot \text{AutoEvalScore}$$

---

## F516: Continual Learning (x₁₆)

$$x_{16} = K_{cl}(t) = 1 - e^{-\lambda_{cl} \cdot N_{tasks}}$$

$$\Delta S_{cl} = \gamma_{cl} \cdot K_{cl} \cdot S(x)$$

---

## F517: Inference Optimization (x₁₇)

$$x_{17} = \prod_{o} (1 - \delta_o)$$

$$\Delta T_{opt} = -x_{17} \cdot T_0$$

(определение аналогично F001c)
```

---

## 5. УНИФИКАЦИЯ НОТАЦИИ

### 5.1 Таблица замен

| Старая | Новая | Контекст |
|--------|-------|----------|
| `λ` (learning rate) | `η` | F050, F053, F059 |
| `λ` (orders) | `λ_orders` | F047 |
| `λ` (cost) | `λ_cost` | F471 |
| `λ` (decay) | `λ_decay` | F052, F055 |
| `K` (knowledge) | `K_knowledge` | F053 |
| `K` (maturity) | `K_maturity` | F067, F465 |
| `ρ` (forgetting) | `ρ_forget` | F055 |
| `ρ` (dependency) | `ρ_dep` | F105, F222 |
| `ρ` (resilience) | `ρ_resilience` | F048 |
| `ρ` (correlation) | `ρ_corr` | F407 |
| `E` (error) | `E_error` | F064 |
| `E` (energy) | `E_energy` | если используется |
| `φ` (phi) | `φ_conf` | F090 |
| `φ` (phi) | `φ_thresh` | F107 |
| `Φ_R` | `Φ_routing` | F223, F224 |
| `Γ` | оставить | F061, F062 |

### 5.2 Пример применения в F047

```diff
## F047: Order Flow

-$$\lambda_{orders}(R) = \lambda_0 \cdot \left(\frac{R}{R_{ref}}\right)^{\beta_{rep}} \cdot \Theta^{\gamma_{trust}} \cdot (1 + SC)^{\delta_{social}}$$
+$$\lambda_{orders}(R) = \lambda_0 \cdot \left(\frac{R}{R_{ref}}\right)^{\beta_{rep}} \cdot \Theta^{\gamma_{trust}} \cdot (1 + SC)^{\delta_{social}}$$

**Примечание:** $\lambda_0$ — базовая интенсивность заказов.
```

---

## 6. ПАТЧ-ФАЙЛЫ

### 6.1 Патч для критических ошибок (apply_critical.sh)

```bash
#!/bin/bash
# Патч для критических ошибок в ALL_FORMULAS.txt

FILE="ALL_FORMULAS.txt"

# 1. Исправить F012
sed -i 's/Ошибка в скобке заменить...//g' "$FILE"

# 2. Добавить epsilon в F062
sed -i '/\\Gamma = \\frac{\\sum \\text{Reinforcing}}{\\sum \\text{Balancing}}/s/$/ + \\epsilon_\\Gamma/' "$FILE"

# 3. Добавить epsilon в F065 и F450
sed -i '/\\Gamma = \\frac{\\nu \\cdot VoI/s/$/ + \\epsilon_\\Gamma/' "$FILE"

# 4. Исправить F024
sed -i 's/\\mathcal{A}_c = \\frac{1}{N_{implicit}}/\\mathcal{A}_c = \\frac{1}{\\max(N_{implicit}, 1)}/' "$FILE"

# 5. Исправить F066
sed -i '/\\mathcal{A} = \\frac{\\Delta \\Phi_{recovery}}{\\Delta \\Phi_{loss}}/s/$/ + \\epsilon_A/' "$FILE"

echo "Критические исправления применены"
```

---

## 7. ЧЕК-ЛИСТ ПЕРЕД РЕЛИЗОМ

- [ ] Исправлены все синтаксические ошибки (F012)
- [ ] Добавлены epsilon для защиты от деления на ноль
- [ ] Перенесены определения u(a) и ρ перед F028
- [ ] Определены P, T_opt для F002
- [ ] Удалены дубликаты (или помечены как deprecated)
- [ ] Унифицирована нотация λ, K, ρ
- [ ] Добавлены определения для x₁₂-x₁₇
- [ ] Проверены все циклические зависимости
- [ ] Обновлены ссылки между формулами
- [ ] Добавлен глоссарий переменных

---

*Руководство составлено: 2026-07-06*
