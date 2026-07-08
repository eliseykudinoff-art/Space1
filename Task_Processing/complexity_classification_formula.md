# Математическая модель классификации сложности задач

## Формула

$$\boxed{\hat{c}(\mathbf{x}) = \underset{j \in \{1,\ldots,K\}}{\arg\max} \; P(c=j | \mathbf{x}, \theta)}$$

---

## 1. Постановка задачи

**Дано:**
- Множество задач $\mathcal{T} = \{t_1, t_2, \ldots, t_n\}$
- Множество классов сложности $\mathcal{C} = \{1, 2, \ldots, K\}$ с естественным порядком $1 < 2 < \ldots < K$

**Цель:** найти функцию $\hat{c}(\mathbf{x})$ которая:
1. Минимизирует ошибку классификации
2. Учитывает семантику задачи
3. Принимает обоснованные решения с оценкой неопределённости

---

## 2. Входные данные (Input Features)

Каждая задача $\mathbf{x}$ характеризуется:

| Тип | Признаки | Обозначение |
|-----|----------|-------------|
| Текстовые | Заголовок, описание, комментарии | $\mathbf{x}_{text}$ |
| Метаданные | Labels, timestamps | $\mathbf{x}_{meta}$ |
| Репозиторий | Stars, language, contributors | $\mathbf{x}_{repo}$ |
| Исторические | Similar issues avg, author performance | $\mathbf{x}_{hist}$ |

---

## 3. Семантическое кодирование (Semantic Encoding)

### 3.1 Text Encoder (Transformer)

$$\mathbf{e}_{text} = \alpha \cdot \text{BERT}(\text{title}) + (1-\alpha) \cdot \text{Pool}(\text{BERT}(\text{description}))$$

где:
- $\alpha \in [0, 1]$ — обучаемый вес важности заголовка
- $\text{Pool}$ — attention-based pooling

### 3.2 Metadata Encoder (MLP)

$$\mathbf{e}_{meta} = \text{MLP}(\mathbf{x}_{meta}) = \text{ReLU}(\mathbf{W}_{meta} \cdot \mathbf{x}_{meta} + \mathbf{b}_{meta})$$

### 3.3 Repository Encoder

$$\mathbf{e}_{repo} = \text{MLP}(\mathbf{x}_{repo})$$

### 3.4 Historical Features

$$\mathbf{e}_{hist} = \begin{bmatrix} \sigma(\text{similar\_avg}) \\ \sigma(\text{author\_perf}) \end{bmatrix}$$

где $\sigma(x) = \frac{1}{1 + e^{-x}}$ — сигмоида для нормализации.

---

## 4. Fusion Layer (Объединение признаков)

$$\mathbf{e}_{fused} = \underbrace{\text{gate}}_{\sigma(\mathbf{W}_{gate} \cdot [\mathbf{e}_{text}; \mathbf{e}_{context}] + \mathbf{b}_{gate})} \odot \mathbf{e}_{text} + (1 - \text{gate}) \odot \mathbf{e}_{context}$$

где $\mathbf{e}_{context} = [\mathbf{e}_{meta}; \mathbf{e}_{repo}; \mathbf{e}_{hist}]$

**Гейтинговый механизм** позволяет модели автоматически определять, какие признаки важнее для конкретной задачи.

---

## 5. Ordinal Classification (Классификация с учётом порядка)

### 5.1 Вычисление порогов

$$\phi_k = \mathbf{w}_k^T \cdot \mathbf{e}_{fused} + b_k, \quad k = 1, 2, \ldots, K-1$$

### 5.2 Вероятности классов

$$P(c=j | \mathbf{e}) = \sigma(\phi_j - \phi_{j-1})$$

где $\phi_0 = -\infty$, $\phi_K = +\infty$, и $\sigma$ — сигмоида.

### 5.3 Предсказание класса

$$\hat{c} = 1 + \sum_{k=1}^{K-1} \mathbb{I}(\phi_k > 0)$$

где $\mathbb{I}$ — индикаторная функция.

### Пример для K=5 (Trivial → Complex):

```
ĉ = 1  если φ₁ < 0, φ₂ < 0, φ₃ < 0, φ₄ < 0  [Trivial]
ĉ = 2  если φ₁ ≥ 0, φ₂ < 0, φ₃ < 0, φ₄ < 0  [Easy]
ĉ = 3  если φ₁ ≥ 0, φ₂ ≥ 0, φ₃ < 0, φ₄ < 0  [Medium]
ĉ = 4  если φ₁ ≥ 0, φ₂ ≥ 0, φ₃ ≥ 0, φ₄ < 0  [Hard]
ĉ = 5  если φ₁ ≥ 0, φ₂ ≥ 0, φ₃ ≥ 0, φ₄ ≥ 0  [Complex]
```

---

## 6. Функция потерь (Loss Function)

### 6.1 Ordinal Cross-Entropy

$$\mathcal{L}_{ordinal} = -\sum_{j=1}^{K} y_j \log P(c=j | \mathbf{x})$$

где $y_j = \mathbb{I}(c^* = j)$ — one-hot кодирование истинного класса.

### 6.2 Semantic Consistency Regularizer

$$\mathcal{L}_{consistency} = \frac{1}{|\mathcal{P}|} \sum_{(i,j) \in \mathcal{P}} \max\left(0, (c_j - c_i) - \epsilon \cdot \|\mathbf{e}_i - \mathbf{e}_j\|\right)$$

**Смысл:** если две задачи семантически похожи ($\|\mathbf{e}_i - \mathbf{e}_j\|$ мало), их сложность должна быть близка.

### 6.3 Ordinality Regularizer

$$\mathcal{L}_{ordinality} = \sum_{k=1}^{K-2} \max(0, \phi_{k+1} - \phi_k + \delta)$$

**Смысл:** пороги должны быть строго возрастающими: $\phi_1 < \phi_2 < \ldots < \phi_{K-1}$

### 6.4 Полная функция потерь

$$\boxed{\mathcal{L}(\theta) = \mathcal{L}_{ordinal} + \beta \cdot \left(\mathcal{L}_{consistency} + \mathcal{L}_{ordinality}\right)}$$

где $\theta = \{\mathbf{W}_*, \mathbf{b}_*, \alpha, \epsilon, \delta\}$ — все обучаемые параметры.

---

## 7. Функция принятия решений (Decision Function)

### 7.1 Энтропия (мера неопределённости)

$$H(\hat{c}) = -\sum_{j=1}^{K} P(c=j) \log P(c=j)$$

### 7.2 Правило решения

$$
\text{Decision}(\mathbf{x}) = 
\begin{cases}
\text{AUTO\_ASSIGN}(\hat{c}) & \text{если } H < \tau_{auto} \\
\text{HUMAN\_REVIEW}(\hat{c}, \text{top-2}) & \text{если } \tau_{auto} \leq H < \tau_{review} \\
\text{ESCALATE}(\hat{c}) & \text{если } H \geq \tau_{review}
\end{cases}
$$

где $\tau_{auto} = 0.5$, $\tau_{review} = 1.0$ — адаптируемые пороги.

---

## 8. Итоговая компактная форма

### Формула предсказания:

$$\boxed{\hat{c} = \underset{j}{\arg\max} \; \sigma\left(\mathbf{w}_j^T \cdot \left[\text{gate} \odot \mathbf{e}_{text} + (1-\text{gate}) \odot \mathbf{e}_{context}\right] + b_j\right)}$$

### Полная архитектура:

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│    x_text ──► BERT ──► e_text ──┐                                          │
│                                  │                                          │
│    x_meta ──► MLP ──► e_meta ──┤                                          │
│                                  ├──► CONCAT ──► e_fused ──► φ ──► ĉ      │
│    x_repo ──► MLP ──► e_repo ──┤                                          │
│                                  │                                          │
│    x_hist ──► σ ───► e_hist ───┘                                          │
│                                                                            │
│                              Gate = σ(W · [e_text; e_context])            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Свойства модели

| Свойство | Описание |
|----------|---------|
| **Дифференцируемость** | Все операции дифференцируемы → можно обучать градиентным спуском |
| **Ordinal awareness** | Учитывает порядок классов, а неTreats их как независимые |
| **Мультимодальность** | Комбинирует текст, метаданные, историю |
| **Uncertainty estimation** | Энтропия для оценки уверенности |
| **Интерпретируемость** | Gate-механизм показывает важность признаков |
| **Scalability** | Можно квантизировать для production |

---

## 10. Обучение

### Градиентный спуск:

$$\theta_{t+1} = \theta_t - \eta \cdot \nabla_\theta \mathcal{L}(\theta_t)$$

### regularization:

$$\text{Reg}(\theta) = \|\mathbf{W}\|_2^2 + \lambda_{drop} \cdot \text{Dropout}(\mathbf{e}_{fused})$$

---

## 11. Пример вычисления

**Задача:** "Fix memory leak in data processing pipeline"

**Шаг 1: Кодирование**
```
e_text = [0.2, -0.1, 0.8, ..., 0.3]    # BERT embedding (768-dim)
e_meta = [0.5, 0.2, 0.9]               # [labels, timestamp]
e_repo = [0.7, 0.4]                    # [stars_norm, lang]
e_hist = [0.6, 0.8]                    # [similar, performance]
```

**Шаг 2: Fusion**
```
gate = σ(W · [e_text; e_context]) = 0.7
e_fused = 0.7·e_text + 0.3·e_context
```

**Шаг 3: Пороги**
```
φ₁ = -0.5  (trivial | easy)
φ₂ = 0.2   (easy | medium)
φ₃ = 0.8   (medium | hard)
φ₄ = 1.5   (hard | complex)
```

**Результат:** $\hat{c} = 3$ (Medium) с вероятностью $P(3) = 0.45$

**Решение:** $H = 0.8 < 1.0$ → HUMAN_REVIEW
