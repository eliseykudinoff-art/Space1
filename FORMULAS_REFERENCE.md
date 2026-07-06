# 📐 FORMULAS_REFERENCE — Полный справочник формул

> **Дата:** 2026-07-06  
> **Источник:** capability_2.txt + существующие документы  
> **Статус:** 📋 ЧЕРНОВИК для унификации

---

## 🔢 Индекс формул

| # | Формула | Источник | Статус |
|---|---------|----------|--------|
| F001 | Ξ_task = α·Q_result - β·(O_time + O_cost) | capability_2 | 🆕 |
| F002 | Φ_opt = max_x Φ(x, M) | capability_2 | 🆕 |
| F003 | e_task = Embed(T) ∈ R^d | capability_2 | 🆕 |
| F004 | c_k = (1/N_k)·Σ e_i | capability_2 | 🆕 |
| F005 | sim(e_task, c_k) = dot/(norm) | capability_2 | 🆕 |
| F006 | d_hat = argmax_k sim(...) | capability_2 | 🆕 |
| F007 | C_router_fine = N_in·P_in + N_out·P_out | capability_2 | 🆕 |
| F008 | D(T) = {REJECT/CLARIFY/EXECUTE} | capability_2 | 🆕 |
| F009 | H(X) = -Σ p_i·log₂(p_i) | capability_2 | 🆕 |
| F010 | H_TZ = -Σ P(d|T)·log₂ P(d|T) | capability_2 | 🆕 |
| F011 | Ω = -Σ p_k·log₂(p_k) | capability_2 | 🆕 |
| F012 | IG = H_prior - H_posterior | capability_2 | 🆕 |
| F013 | VoI = E[Φ|with] - E[Φ|without] | capability_2 | 🆕 |
| F014 | Γ = Σ F_reinforcing / Σ F_balancing | capability_2 | 🆕 |
| F015 | E = Φ_team/Σ Φ_i - 1 | capability_2 | 🆕 |
| F016 | A = ΔΦ_recovery / ΔΦ_loss | capability_2 | 🆕 |
| F017 | K_maturity(t) = 1 - e^(-λ·(t-t₀)) | capability_2 | 🆕 |
| F018 | U(t) = K·U_exploit + (1-K)·U_explore | capability_2 | 🆕 |

---

## 🆕 Новые формулы из capability_2.txt

### F001: Функция Профессиональной Добросовестности (Ξ)

$$\Xi_{task} = \underbrace{\alpha \cdot Q_{result}}_{\text{Качество результата}} - \underbrace{\beta \cdot (O_{time} + O_{cost})}}_{\text{Штраф за перерасход ресурсов}}$$

**Контекст:** Для агентов-исполнителей, не для оркестратора.

**Где:**
- $Q_{result}$ — оценка качества (автотесты, LLM-судья)
- $O_{time}, O_{cost}$ — факт перерасхода vs выделенного

**Связь:** Αгент-исполнитель мыслит категориями Ξ, оркестратор — Φ.

---

### F002: Оптимизация Profit Function

$$\Phi_{opt} = \max_{\mathbf{x}} \Phi(\mathbf{x}, \mathcal{M})$$

**Контекст:** Meta-Learning в Калибровщике. Оптимизация по x₁-x₁₁.

---

### F003-F006: Embeddings и Task Routing

$$\mathbf{e}_{task} = \text{Embed}(T) \in \mathbb{R}^d$$

$$\mathbf{c}_k = \frac{1}{N_k} \sum_{i=1}^{N_k} \mathbf{e}_i \quad \text{(centroid)}$$

$$\text{sim}(\mathbf{e}_{task}, \mathbf{c}_k) = \frac{\mathbf{e}_{task} \cdot \mathbf{c}_k}{\|\mathbf{e}_{task}\| \|\mathbf{c}_k\|}$$

$$\hat{d} = \arg\max_k \text{sim}(\mathbf{e}_{task}, \mathbf{c}_k) \quad \text{при условии} \quad \max_k \text{sim}(\mathbf{e}_{task}, \mathbf{c}_k) \geq \tau_{fast}$$

**Контекст:** Fast-роутер для маршрутизации задач по доменам.

---

### F007: Стоимость Fine-Grained Router

$$C_{router\_fine} = N_{in} \cdot P_{in}^{small} + N_{out} \cdot P_{out}^{small}$$

**Контекст:** Стоимость вызова small LLM для детальной маршрутизации.

---

### F008: Функция маршрутизации задач

$$\mathcal{D}(T) = \begin{cases}
\textbf{REJECT} & \text{если } H_{TZ} > H_{max} \\
\textbf{CLARIFY} & \text{если } \tau_{auto} > \kappa_{conf} \geq \tau_{clarify} \land \Phi_{pred} \cdot \kappa_{conf} > \Phi_{min} \\
\textbf{EXECUTE} & \text{если } U(\Phi_{pred}) > 0
\end{cases}$$

**Контекст:** Полная функция маршрутизации с порогами.

---

### F009-F012: Энтропия и Информация

**Шенноновская энтропия:**
$$H(X) = -\sum_{i} p_i \cdot \log_2(p_i)$$

**Энтропия зон доверия:**
$$H_{TZ} = -\sum_{d \in D} P(d | T) \cdot \log_2 P(d | T)$$

**Распределение по доменам:**
$$\Omega = -\sum_{k=1}^{K} p_k \cdot \log_2(p_k)$$

**Information Gain:**
$$IG = H_{prior} - H_{posterior}$$

**Примеры:**
```
H(0.5, 0.5) = 1 бит (максимальная неопределённость)
H(0.9, 0.1) ≈ 0.47 бит (высокая определённость)
```

---

### F013: Value of Information

$$VoI = \mathbb{E}[\Phi | \text{with info}] - \mathbb{E}[\Phi | \text{without info}]$$

**Расшифровка:**
```
E[Φ | with info] = Φ_yes · P(yes) + Φ_no · P(no)
                 = 4450 · 0.3 + (-500) · 0.7 = 985

E[Φ | without info] = 3900 ( baseline )
                 = Φ_1 · S + Φ_2 · (1-S)
                 = 5000 · 0.8 + (-500) · 0.2 = 3900

VoI = 985 - 3900 = -2915 (отрицательная → не стоит спрашивать)
```

---

### F014: Homeostasis Index (Γ)

$$\Gamma = \frac{\sum \text{Reinforcing}}{\sum \text{Balancing}}$$

**Reinforcing forces (положительная обратная связь):**
$$F_{reinforcing} \approx \underbrace{\nu \cdot VoI}_{\text{Обучение}} + \underbrace{\gamma \cdot \Upsilon}_{\text{Репутация}} + \underbrace{\phi_{ft} \cdot \frac{d}{dt}(N_{tasks})}_{\text{Эффект масштаба}}$$

**Balancing forces (отрицательная обратная связь):**
$$F_{balancing} \approx \underbrace{\lambda \cdot \Psi}_{\text{Стоп-лосс}} + \underbrace{\rho \cdot E}_{\text{Штраф за ошибки}} + \underbrace{\delta_{coord} \cdot N_{agents}^2}_{\text{Затраты на координацию}}$$

**Итоговая:**
$$\Gamma = \frac{\nu \cdot VoI + \gamma \cdot \Upsilon + \phi_{ft} \cdot \frac{dN_{tasks}}{dt}}{\lambda \cdot \Psi + \rho \cdot E + \delta_{coord} \cdot N_{agents}^2}$$

**Интерпретация:**
- Γ > 1 → система в фазе роста
- Γ < 1 → система в фазе стабилизации/упадка
- Γ ≈ 1 → гомеостаз

---

### F015: Team Efficiency

$$\mathcal{E} = \frac{\Phi_{team}}{\sum_{i} \Phi_{individual}} - 1$$

**Interpretation:**
- E > 0 → синергия (1+1 > 2)
- E < 0 → координационные потери (1+1 < 2)

**Competitive pressure:**
$$P_{env} = -\frac{d\Phi}{dN_{comp}}$$

---

### F016: Adaptability Index

$$\mathcal{A} = \frac{\Delta \Phi_{recovery}}{\Delta \Phi_{loss}}$$

**Интерпретация:**
- A > 1 → система быстро восстанавливается
- A < 1 → система уязвима

---

### F017-F018: Maturity & Learning Curve

**Maturity Index:**
$$K_{maturity}(t) = 1 - e^{-\lambda \cdot (t - t_0)}$$

**Utility balancing exploitation vs exploration:**
$$U(t) = \underbrace{K_{maturity}(t) \cdot U_{exploit}}_{\text{Прибыль}} + \underbrace{(1 - K_{maturity}(t)) \cdot U_{explore}}_{\text{Обучение}}$$

**Dynamic complexity ceiling:**
$$H_{max}(t) = H_{min} + (H_{max}^{start} - H_{min}) \cdot (1 - K_{maturity}(t))$$

**Task complexity with maturity:**
$$D_{capable}(t) = D_{max} \cdot K_{maturity}(t)$$

---

## 📊 Дополнительные формулы (из существующих)

### Profit Function (из Manus)

$$\Phi(x) = \frac{R(x) - C(x)}{T(x)}$$

$$\Phi_{total} = \frac{P \cdot S_{total}(x) \cdot Q_{total}(x) - C_{total}(x) - C_{risk}(x_{12})}{T_{total}(x) \cdot T_{opt}(x_{17})}$$

**Компоненты:**
$$S_{total} = S_0 \cdot \prod_{i} f_{S,i}(x_i)$$
$$Q_{total} = Q_0 \cdot \prod_{i} f_{Q,i}(x_i)$$
$$C_{total} = C_0 + \sum_{i} \Delta C_i(x_i)$$
$$T_{total} = T_0 \cdot \prod_{i} f_{T,i}(x_i)$$

---

### Risk Function (Ψ)

$$\Psi(task) = P_{fail} \cdot (C_{direct} + C_{reputation})$$

**Стоимость риска:**
$$C_{risk} = \sum_{j} P_j \cdot L_j \cdot (1 - R_{guardrails,j})$$

---

### Reputation Function (Υ)

$$\Upsilon = \gamma_1 \cdot \bar{R} + \gamma_2 \cdot \tau_{ret} + \gamma_3 \cdot \frac{N^+}{N} + \gamma_4 \cdot (1 - \delta) + \gamma_5 \cdot \frac{d\Upsilon}{dt}$$

---

### Learning Function (ZPD)

$$ZPD = ZPD_{base} \cdot (1 + \alpha_M \cdot M - \alpha_{CL} \cdot CL + \alpha_\eta \cdot \eta)$$

**Forgetting:**
$$\Phi(t, n) = e^{-\frac{t}{S \cdot (1 + \kappa \cdot n)^\psi}}$$

**Knowledge accumulation:**
$$K(t) = K_0 + \int_0^t \eta_{learn} \cdot \Delta K(\tau) \cdot (1 - \frac{K(\tau)}{K_{max}}) d\tau$$

---

### Synergies

$$\gamma_{syn} = \sum_{(i,j) \in synergies} \Delta\gamma_{ij} \cdot x_i \cdot x_j$$

---

### Confidence & Reasoning

$$\phi(a) = \sigma(\mathbf{w}_\phi^T \cdot \mathbf{f}(a) + b_\phi)$$

$$\phi_{reason} = \alpha_{reason} \cdot \log(1 + \frac{T_{think}}{T_{base}})$$

$$S_{reason}(x) = S(x) + \beta_{reason} \cdot \phi_{reason} \cdot (1 - S(x))$$

---

## 🎯 Интеграционные связи

```
Ξ_task (F001) ───────────────────────────────→ Αгент-исполнитель
     │
     └── Q_result, O_time, O_cost

Γ (F014) ────────────────────────────────────→ Homeostat
     │
     ├── VoI (F013) ←── Information Theory
     ├── Υ (Reputation) ←── Υ function
     └── Ψ (Risk) ←── Risk function

K_maturity (F017) ─────────────────────────────→ Curriculum Learning
     │
     ├── U_exploit ←── Current tasks
     └── U_explore ←── ZPD tasks

D(T) (F008) ──────────────────────────────────→ Task Router
     │
     ├── H_TZ (F010) ←── Entropy
     ├── κ_conf ←── Confidence
     └── Φ_pred ←── Profit prediction
```

---

## ⚠️ Формулы требующие уточнения

| Формула | Проблема | Приоритет |
|---------|----------|-----------|
| Ξ_task | α, β не определены | 🟡 |
| Γ | ν, γ, φ_ft не определены | 🟡 |
| K_maturity | λ не определён | 🟡 |
| H_max | H_min, H_max^start не определены | 🟡 |
| sim() | τ_fast не определён | 🟢 Низкий |

---

*Создано: 2026-07-06*
*Источник: capability_2.txt*
