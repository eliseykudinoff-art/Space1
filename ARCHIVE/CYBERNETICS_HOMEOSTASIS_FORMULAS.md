---
author:
- Полное собрание с пояснениями
date: 2026-07-08
title: Формулы Гомеостаза и Кибернетики в Агентных Системах
---

# БАЗОВЫЕ УРАВНЕНИЯ КИБЕРНЕТИКИ (Wiener, 1948)

## Уравнение регулятора (Watt Governor)

$$\dot{x} = f(x, u, d)$$ **Что означает:** Состояние системы $x$
изменяется под влиянием управления $u$ и возмущений $d$.

## Уравнение отрицательной обратной связи

$$\begin{aligned}
e(t) &= r(t) - y(t) \\
u(t) &= K_p \cdot e(t)
\end{aligned}$$ **Что означает:** Ошибка $e$ = разница между уставкой
$r$ и выходом $y$.

## Энтропия информации (Shannon-Wiener)

$$H = -\sum_{i} p(x_i) \cdot \log_2 p(x_i)$$ **Что означает:** Мера
неопределённости в системе.

# ПИД-РЕГУЛЯТОР

## Основное уравнение ПИД

$$u(t) = K_p \cdot e(t) + K_i \int_0^{t} e(\tau)d\tau + K_d \frac{de(t)}{dt}$$
**Что означает:** Пропорциональное + интегральное + дифференциальное
управление.

## Пропорциональный регулятор

$$u(t) = K_p \cdot e(t)$$ **Что означает:** Чем больше ошибка, тем
сильнее управление.

## Интегральный регулятор

$$u(t) = K_i \int_0^{t} e(\tau)d\tau$$ **Что означает:** Накапливает
историю ошибок для устранения статической ошибки.

## Передаточная функция ПИД

$$G(s) = K_p + \frac{K_i}{s} + K_d \cdot s$$ **Что означает:**
Представление в частотной области.

# ГОМЕОСТАЗ (Golubitsky-Stewart)

## Определение гомеостаза

$$x_o(I) \approx \text{const} \quad \text{при} \Delta I$$ **Что
означает:** Выход остаётся постоянным при изменении входа.

## Бесконечно малый гомеостаз

$$x'_o(I_0) = 0$$ **Что означает:** Производная выхода по входу равна
нулю.

## Система ОДУ для гомеостаза

$$\begin{aligned}
\dot{x}_\iota &= f_\iota(x_\iota, I) \\
\dot{x}_\kappa &= f_\kappa(x_\iota, x_\kappa) \\
\dot{x}_o &= f_o(x_\iota, x_\kappa, x_o)
\end{aligned}$$ **Что означает:** Входной, скрытые и выходной узлы сети.

## Уравнение для инфнитезимального гомеостаза

$$h_x(x_0, z_0) = \frac{g'_1(x_0) \cdot g'_2(y_0)}{g'_2(y_0) + g'_5(y_0)}$$
**Что означает:** Условие гомеостатического поведения.

## Устойчивость равновесия

$$\begin{aligned}
V(x) &> 0 \quad \text{для } x \neq 0, \quad V(0) = 0 \\
\dot{V}(x) &= \frac{\partial V}{\partial x} \cdot f(x) \leq 0
\end{aligned}$$ **Что означает:** Функция Ляпунова для стабильности.

# МАРКОВСКИЕ ПРОЦЕССЫ ПРИНЯТИЯ РЕШЕНИЙ (MDP)

## MDP кортеж

$$\text{MDP} = (S, A, P, R, \gamma)$$ **Что означает:** S = состояния, A
= действия, P = вероятности, R = награды, $\gamma$ = дисконт.

## Функция ценности состояния (Беллман)

$$V^\pi(s) = \sum_{a \in A} \pi(a|s) \sum_{s' \in S} P(s'|s,a) \left[ R(s,a,s') + \gamma V^\pi(s') \right]$$
**Что означает:** Ожидаемая награда от состояния $s$ при политике $\pi$.

## Функция ценности действий (Q-function)

$$Q^\pi(s,a) = \sum_{s'} P(s'|s,a) \left[ R(s,a,s') + \gamma V^\pi(s') \right]$$
**Что означает:** Ценность конкретного действия $a$ в состоянии $s$.

## Оптимальные уравнения Беллмана

$$\begin{aligned}
V^*(s) &= \max_a \sum_{s'} P(s'|s,a) \left[ R(s,a,s') + \gamma V^*(s') \right] \\
Q^*(s,a) &= \sum_{s'} P(s'|s,a) \left[ R(s,a,s') + \gamma \max_{a'} Q^*(s',a') \right]
\end{aligned}$$ **Что означает:** Оптимальная политика = максимум по
всем действиям.

# ОБУЧЕНИЕ С ПОДКРЕПЛЕНИЕМ

## Q-learning обновление

$$Q(s,a) \leftarrow Q(s,a) + \alpha \left[ r + \gamma \max_{a'} Q(s',a') - Q(s,a) \right]$$
**Что означает:** Обновление через временную разность (TD-error).

## Уравнение Беллмана для Q

$$Q(s,a) = R(s,a) + \gamma \sum_{s'} P(s'|s,a) \max_{a'} Q(s',a')$$
**Что означает:** Q-value = immediate reward + discounted future.

## Градиент политики

$$\nabla_\theta J(\theta) = \mathbb{E}_{\tau \sim \pi_\theta} \left[ \sum_{t=0}^{T} \nabla_\theta \log \pi_\theta(a_t|s_t) G_t \right]$$
**Что означает:** Увеличение вероятности удачных действий.

# АКТИВНЫЙ ВЫВОД И СВОБОДНАЯ ЭНЕРГИЯ (Friston)

## Принцип свободной энергии

$$F = D_{KL}[q(z|x) \| p(z|x)] - \log p(x)$$ **Что означает:** Верхняя
граница логарифмического правдоподобия.

## Свободная энергия через сюрприз

$$F = U(x) - S[q] \approx -\log p(x)$$ **Что означает:** $U$ =
внутренняя энергия, $S$ = энтропия.

## Активный вывод

$$\pi^* = \arg\min_\pi F(\mu, \pi)$$ **Что означает:** Оптимальная
политика минимизирует свободную энергию.

## Обновление убеждений

$$\dot{\mu} = D_\mu \cdot \frac{\partial F}{\partial \mu}$$ **Что
означает:** Динамика скрытых состояний.

# УРАВНЕНИЯ УПРАВЛЕНИЯ АГЕНТАМИ

## Динамика контекста агента

$$\begin{aligned}
c_{t+1} &= f_\theta(c_t, a_t, o_t) \\
a_t &\sim \pi_\theta(\cdot | c_t)
\end{aligned}$$ **Что означает:** Контекст обновляется через действие и
наблюдение.

## Цикл агента

    while not done:
        response = LLM(messages)
        if has_tools(response):
            results = execute_tools(response.tools)
            messages.append(results)
        else:
            return response

## Целевая функция агента

$$J(\theta) = \mathbb{E} \left[ \sum_t \gamma^t \cdot R(s_t, a_t) \right]$$
**Что означает:** Максимизация ожидаемой награды.

# ЛЯПУНОВ И УСТОЙЧИВОСТЬ

## Устойчивость по Ляпунову

$$\|x(0) - x_e\| < \delta \implies \|x(t) - x_e\| < \epsilon \quad \forall t \geq 0$$
**Что означает:** Система остаётся в окрестности равновесия.

## Асимптотическая устойчивость

$$\|x(t) - x_e\| \to 0 \quad \text{при } t \to \infty$$ **Что
означает:** Система сходится к равновесию.

## Экспоненциальная устойчивость

$$\|x(t) - x_e\| \leq \alpha \|x(0) - x_e\| e^{-\beta t}$$ **Что
означает:** Экспоненциальная сходимость.

# СОГЛАСОВАНИЕ В МУЛЬТИ-АГЕНТНЫХ СИСТЕМАХ

## Динамика агента

$$\dot{x}_i = f\left(x_i, \sum_{j \in N_i} x_j, u_i \right)$$ **Что
означает:** Состояние зависит от соседей.

## Консенсус

$$\lim_{t \to \infty} \|x_i(t) - x_j(t)\| = 0$$ **Что означает:** Все
агенты сходятся к общему значению.

## Среднее консенсус

$$\dot{x}_i = \sum_{j \in N_i} a_{ij} (x_j - x_i)$$ **Что означает:**
Движение к среднему соседей.

# НЕЙРОННЫЕ СЕТИ И АТТРАКТОРЫ

## Уравнение аттрактора

$$\begin{aligned}
\tau \frac{du_i}{dt} &= -u_i + \sum_j w_{ij} \cdot r_j + I_i \\
r_i &= \sigma(u_i)
\end{aligned}$$ **Что означает:** Динамика нейронной активности.

## Правило Хебба

$$\dot{w}_{ij} = \eta \cdot x_i \cdot x_j - \lambda w_{ij}$$ **Что
означает:** "Нейроны вместе активируются -- вместе связываются".

## Гомеостатическая адаптация

$$\tau_a \frac{da_i}{dt} = -a_i + \gamma (u_i - \theta)^2$$ **Что
означает:** Замедление пластичности при высокой активности.

# ФУНКЦИОНАЛЬНЫЙ ГОМЕОСТАЗ

## Простая регуляция

$$\begin{aligned}
c'(t) &= \alpha (s - m(t)) \\
m'(t) &= \lambda c(t) - \mu m(t)
\end{aligned}$$ **Что означает:** Концентрация и сигнал регуляции.

## Уравнение Michaelis-Menten

$$v = \frac{V_{max} \cdot [S]}{K_m + [S]}$$ **Что означает:** Насыщающая
кинетика.

# ТЕОРИЯ УПРАВЛЕНИЯ

## Линейный квадратичный регулятор (LQR)

$$\begin{aligned}
J &= \int_0^T (x^T Q x + u^T R u) dt \\
u &= -K x
\end{aligned}$$ **Что означает:** Минимизация квадратичного cost.

## Уравнение Риккати

$$A^T P + P A - P B R^{-1} B^T P + Q = 0$$ **Что означает:** Решение для
бесконечного горизонта LQR.

# ВАРИАЦИОННЫЙ БАЙЕС

## Теорема Байеса

$$P(H|D) = \frac{P(D|H) \cdot P(H)}{P(D)}$$ **Что означает:** Обновление
убеждений.

## ELBO

$$\log p(x) \geq \mathbb{E}[\log p(x,z)] - \mathbb{E}[\log q(z)]$$ **Что
означает:** Нижняя граница правдоподобия.

# ИНТЕГРАЛЬНЫЕ УРАВНЕНИЯ

## Уравнение Вольтерра

$$x(t) = f(t) + \int_a^b K(t,s) \cdot x(s) ds$$ **Что означает:**
Системы с памятью.

# ПОИСК, ПЛАНИРОВАНИЕ И ПАМЯТЬ

## UCB1 для MCTS

$$P_{ucb} = \frac{V_i}{n_i} + c \sqrt{\frac{\ln N}{n_i}}$$ **Что
означает:** Exploration-exploitation баланс.

## Косинусное сходство

$$\text{Sim}(q, k) = \frac{q \cdot k}{\|q\| \cdot \|k\|} = \frac{\sum_i q_i k_i}{\sqrt{\sum_i q_i^2} \sqrt{\sum_i k_i^2}}$$
**Что означает:** Нормализованное скалярное произведение.

## Scaled Dot-Product Attention

$$\text{Attention}(Q, K, V) = \text{softmax}\left( \frac{Q K^T}{\sqrt{d_k}} \right) V$$
**Что означает:** Механизм attention в трансформерах.

## Reciprocal Rank Fusion

$$\text{RRF\_Score}(d) = \sum_{m \in M} \frac{1}{k + r_m(d)}$$ **Что
означает:** Объединение результатов поиска.

## BM25

$$\text{Score}(D, Q) = \sum_i \text{IDF}(q_i) \cdot \frac{f(q_i, D) \cdot (k_1 + 1)}{f(q_i, D) + k_1 \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}} \right)}$$
**Что означает:** TF-IDF с насыщением.

# ДИНАМИКА И ФИЛЬТРАЦИЯ ПАМЯТИ

## Экспоненциальное затухание

$$W(t) = W_0 \cdot e^{-\lambda t}$$ **Что означает:** Чем старше
воспоминание, тем меньше вес.

## Оценка приоритета памяти

$$I = w_1 \cdot \text{Recency}(t) + w_2 \cdot \text{Importance} + w_3 \cdot \text{Relevance}(q, k)$$
**Что означает:** Взвешенная сумма факторов.

## Forget Gate LSTM

$$f_t = \sigma(W_f \cdot [h_{t-1}, x_t] + b_f)$$ **Что означает:** Что
забыть из предыдущего состояния.

## InfoNCE

$$\mathcal{L}_{\text{InfoNCE}} = -\log \frac{\exp(\text{sim}(q, k_+) / \tau)}{\exp(\text{sim}(q, k_+) / \tau) + \sum_i \exp(\text{sim}(q, k_i^-) / \tau)}$$
**Что означает:** Contrastive loss для обучения представлений.

# ГОМЕОСТАЗ И АЛЛОСТАЗ

## Функция влечения (Drive Function)

$$D(H) = \sum_i |h_i^* - h_i|^p$$ **Что означает:** Расстояние до
оптимального гомеостатического состояния.

## Drive-Reduction Reward

$$R_t = D(H_t) - D(H_{t+1})$$ **Что означает:** Награда за снижение
потребности.

## Вариационная свободная энергия Фристона

$$F(q, y) = \mathbb{E}_{q(s)}[\ln q(s) - \ln p(y,s)] = D_{KL}(q(s) \| p(s|y)) - \ln p(y)$$
**Что означает:** Верхняя граница surprise.

## Фазовые аттракторы

$$\frac{dH}{dt} = f(H, A) + \eta(t)$$ **Что означает:** Эволюция с
шумом.

## Фильтр Калмана

$$\hat{H}_{t|t} = \hat{H}_{t|t-1} + K_t (z_t - C_t \hat{H}_{t|t-1})$$
**Что означает:** Апостериорная оценка состояния.

## EWC для защиты от забывания

$$\mathcal{L}(\theta) = \mathcal{L}_{\text{new}}(\theta) + \sum_i \frac{\lambda}{2} F_i (\theta_i - \theta_{i,\text{old}})^2$$
**Что означает:** Continual learning без катастрофического забывания.

# МАТЕМАТИКА СПЕЦИАЛИЗИРОВАННЫХ СИСТЕМ

## U-образная функция BioBlue

$$D(h_i) = \frac{1}{2} \cdot \left( \frac{h_i - h_i^*}{\sigma_i} \right)^2$$
**Что означает:** Квадратичное отклонение от оптимума.

## Метаболическое затухание Genesis

$$M_t = M_{t-1} - \left( w_1 \cdot \frac{\text{Tokens}_{\text{used}}}{\text{Context}_{\text{max}}} + w_2 \cdot \text{ExecutionTime}_{\text{sec}} \right)$$
**Что означает:** Budget уменьшается с использованием.

## Когнитивный бюджет Genesis

$$B_t = \max\left(0, \frac{\text{Budget}_{\text{remaining}}}{\text{Budget}_{\text{allocated}}} \right)$$
**Что означает:** Нормализованная мера ресурсов.

## Stability/Coherence Genesis

$$C_t = 1.0 - \frac{\text{Current\_KV\_Cache\_Size}}{\text{Max\_Allowed\_Context}}$$
**Что означает:** Чем больше контекст заполнен, тем ниже stability.

# ВНЕШНИЕ КИБЕРНЕТИЧЕСКИЕ ФИЛЬТРЫ

## Дельта-фильтрация

$$\Delta = \frac{|\text{Metric}_{\text{new}} - \text{Metric}_{\text{old}}|}{\text{Metric}_{\text{old}}}$$
**Что означает:** Относительное изменение метрики.

## Взвешенное евклидово расстояние

$$\text{Distance} = \sqrt{\sum_j w_j \cdot (\text{Current}_j - \text{State}_{i,j})^2}$$
**Что означает:** Расстояние до эталона с весами.

# ИСТОЧНИКИ

::: thebibliography
99

Wiener, N. (1948). *Cybernetics: Or Control and Communication in the
Animal and the Machine*

Golubitsky, M., Stewart, I. (2017). *Singularity Theory and Homeostasis*

Bellman, R. (1957). *Dynamic Programming*

Friston, K. (2010). *The Free Energy Principle*

Åström, K., Murray, R. (2008). *Feedback Systems*

Sutton, R., Barto, A. (2018). *Reinforcement Learning: An Introduction*

Vaswani, A. (2017). *Attention Is All You Need*

Hochreiter, S. (1997). *Long Short-Term Memory*

Kalman, R. (1960). *A New Approach to Linear Filtering and Prediction*
:::
