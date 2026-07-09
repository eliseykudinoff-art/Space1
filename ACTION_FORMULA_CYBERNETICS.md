# ACTION → FORMULA: Кибернетика и Гомеостаз

## Маппинг для имплементации

> **Цель:** Каждая кибернетическая формула → конкретное управляющее действие
> **Контекст:** Биологические аналогии, теория управления, MDP, гомеостаз

---

## СТРУКТУРА ЗАПИСИ

```
ФОРМУЛА
  └─ Область (Кибернетика/MDP/RL/Нейросети/etc)
  └─ Код (LaTeX)
  └─ Входы
  └─ Выход
  └─ ДЕЙСТВИЕ: Что делаем
  └─ ПРАВИЛО: if/else логика
  └─ ПСЕВДОКОД
```

---

# ЧАСТЬ 1: БАЗОВАЯ КИБЕРНЕТИКА

---

## 1.1 State Dynamics — Динамика состояния

### Область: Wiener (1948)

### Формула
$$\dot{x} = f(x, u, d)$$

### Входы
```
x  — текущее состояние
u  — управление (control signal)
d  — возмущение (disturbance)
```

### Выход
```
ẋ — производная состояния (скорость изменения)
```

### ДЕЙСТВИЕ: Обновить состояние системы

### ПСЕВДОКОД
```python
def update_state(
    current_state: State,
    control_signal: float,
    disturbance: float
) -> State:
    """
    ẋ = f(x, u, d)
    """
    # Простейшая модель: линейная система
    derivative = (
        A * current_state +      # собственная динамика
        B * control_signal +    # управление
        D * disturbance          # возмущение
    )
    
    # Интегрирование (Эйлер)
    new_state = current_state + derivative * dt
    
    return new_state
```

---

## 1.2 Error Computation — Вычисление ошибки

### Область: Feedback Control

### Формула
$$e(t) = r(t) - y(t)$$

### Входы
```
r(t) — уставка (setpoint, target)
y(t) — текущий выход (actual output)
```

### Выход
```
e(t) ∈ (-∞, +∞) — ошибка регулирования
```

### ДЕЙСТВИЕ: Вычислить отклонение от цели

### ПСЕВДОКОД
```python
def compute_error(
    setpoint: float,
    current_output: float
) -> float:
    """
    e(t) = r(t) - y(t)
    """
    return setpoint - current_output


# Пример: ошибка для разных метрик агента
def compute_all_errors(agent_state: AgentState) -> dict:
    return {
        "profit_error": TARGET_PROFIT - agent_state.current_profit,
        "reputation_error": TARGET_REPUTATION - agent_state.current_reputation,
        "load_error": TARGET_LOAD - agent_state.current_load,
        "risk_error": TARGET_RISK - agent_state.current_risk,
    }
```

---

## 1.3 Proportional Control — П-регулятор

### Область: Classical Control

### Формула
$$u(t) = K_p \cdot e(t)$$

### Входы
```
K_p  — коэффициент усиления
e(t) — ошибка
```

### Выход
```
u(t) ∈ (-∞, +∞) — управляющее воздействие
```

### ДЕЙСТВИЕ: Генерировать корректирующее воздействие

### ПСЕВДОКОД
```python
def proportional_control(
    error: float,
    Kp: float
) -> float:
    """
    u(t) = Kp × e(t)
    """
    return Kp * error


# Пример: коррекция рабочей нагрузки
def adjust_workload(
    current_load: float,
    target_load: float
) -> Adjustment:
    error = target_load - current_load
    Kp_load = 0.5
    
    adjustment = Kp_load * error
    
    if adjustment > 0:
        return Adjustment(type="ACCEPT_MORE_TASKS", magnitude=adjustment)
    else:
        return Adjustment(type="REDUCE_LOAD", magnitude=-adjustment)
```

---

## 1.4 PID Control — ПИД регулятор

### Область: Classical Control

### Формула
$$u(t) = K_p \cdot e(t) + K_i \int_0^{t} e(\tau)d\tau + K_d \frac{de(t)}{dt}$$

### Входы
```
K_p  — пропорциональный коэффициент
K_i  — интегральный коэффициент
K_d  — дифференциальный коэффициент
e(τ) — история ошибок
```

### Выход
```
u(t) — композитное управление
```

### ДЕЙСТВИЕ: Полное управление с учётом истории и тренда

### ПСЕВДОКОД
```python
class PIDController:
    def __init__(self, Kp: float, Ki: float, Kd: float):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.integral = 0.0
        self.prev_error = 0.0
    
    def compute(
        self,
        error: float,
        dt: float
    ) -> float:
        """
        u(t) = Kp×e(t) + Ki×∫e(τ)dτ + Kd×de(t)/dt
        """
        # Пропорциональная часть
        P = self.Kp * error
        
        # Интегральная часть
        self.integral += error * dt
        I = self.Ki * self.integral
        
        # Дифференциальная часть
        derivative = (error - self.prev_error) / dt
        D = self.Kd * derivative
        self.prev_error = error
        
        return P + I + D


# Пример: PID для управления потоком заказов
def adjust_order_flow(
    current_flow: float,
    target_flow: float,
    history: List[float]
) -> float:
    pid = PIDController(Kp=0.5, Ki=0.1, Kd=0.2)
    
    error = target_flow - current_flow
    control = pid.compute(error, dt=1.0)
    
    return current_flow + control
```

---

## 1.5 Entropy — Энтропия Шеннона

### Область: Information Theory

### Формула
$$H = -\sum_{i} p(x_i) \cdot \log_2 p(x_i)$$

### Входы
```
p(xᵢ) — вероятности исходов
```

### Выход
```
H ∈ [0, log₂(n)] — неопределённость (биты)
```

### ДЕЙСТВИЕ: Измерить неопределённость системы

### ПСЕВДОКОД
```python
import numpy as np

def compute_entropy(probabilities: List[float]) -> float:
    """
    H = -Σ p(xᵢ) × log₂ p(xᵢ)
    """
    probs = np.array(probabilities)
    # Убираем нулевые вероятности
    probs = probs[probs > 0]
    
    return -np.sum(probs * np.log2(probs))


# Пример: энтропия неопределённости задачи
def compute_task_uncertainty(task: Task) -> float:
    outcomes = estimate_probable_outcomes(task)
    probabilities = [o.probability for o in outcomes]
    
    return compute_entropy(probabilities)


# Пример: неопределённость выбора между действиями
def compute_action_entropy(actions: List[Action]) -> float:
    utilities = np.array([a.expected_utility for a in actions])
    # Softmax для получения вероятностей
    probs = softmax(utilities)
    
    return compute_entropy(probs)
```

---

# ЧАСТЬ 2: ГОМЕОСТАЗ

---

## 2.1 Homeostatic Setpoint — Точка гомеостаза

### Область: Golubitsky-Stewart

### Формула
$$x_o(I) \approx \text{const} \quad \text{при} \quad \Delta I$$

### Входы
```
I  — входной сигнал
ΔI — изменение входа
```

### Выход
```
xₒ ≈ const — выход остаётся постоянным
```

### ДЕЙСТВИЕ: Поддерживать постоянство критических переменных

### ПСЕВДОКОД
```python
class HomeostaticVariable:
    def __init__(self, name: str, target: float, tolerance: float):
        self.name = name
        self.target = target
        self.tolerance = tolerance  # ± допуск
    
    def is_in_range(self, value: float) -> bool:
        return abs(value - self.target) <= self.tolerance
    
    def deviation(self, value: float) -> float:
        return (value - self.target) / self.target


# Критические переменные агента
HOMEOSTATIC_VARIABLES = {
    "profit_rate": HomeostaticVariable("profit_rate", target=10.0, tolerance=2.0),
    "reputation": HomeostaticVariable("reputation", target=4.5, tolerance=0.3),
    "workload": HomeostaticVariable("workload", target=0.7, tolerance=0.1),
    "risk_level": HomeostaticVariable("risk_level", target=0.3, tolerance=0.1),
    "queue_depth": HomeostaticVariable("queue_depth", target=5.0, tolerance=2.0),
}


def check_homeostasis(agent_state: AgentState) -> HomeostasisResult:
    deviations = {}
    for name, variable in HOMEOSTATIC_VARIABLES.items():
        current = getattr(agent_state, name)
        deviations[name] = variable.deviation(current)
    
    # Проверяем все ли в допуске
    all_stable = all(
        variable.is_in_range(getattr(agent_state, name))
        for name, variable in HOMEOSTATIC_VARIABLES.items()
    )
    
    return HomeostasisResult(
        stable=all_stable,
        deviations=deviations,
        most_deviated=max(deviations, key=lambda k: abs(deviations[k]))
    )
```

---

## 2.2 Lyapunov Stability — Устойчивость по Ляпунову

### Область: Stability Theory

### Формулы
$$V(x) > 0 \quad \text{for} \quad x \neq 0, \quad V(0) = 0$$
$$\dot{V}(x) = \frac{\partial V}{\partial x} \cdot f(x) \leq 0$$

### Входы
```
V(x)  — функция Ляпунова
ẋ = f(x) — динамика системы
```

### Выход
```
V̇(x) ≤ 0 → УСТОЙЧИВО
V̇(x) > 0 → НЕУСТОЙЧИВО
```

### ДЕЙСТВИЕ: Проверить устойчивость системы

### ПСЕВДОКОД
```python
def lyapunov_function(state: np.array) -> float:
    """
    Простейшая функция Ляпунова: квадратичная форма
    V(x) = x^T P x
    """
    P = np.eye(len(state))  # Единичная матрица для простоты
    return state @ P @ state


def check_lyapunov_stability(
    trajectory: List[np.array],
    epsilon: float = 0.01
) -> StabilityResult:
    """
    Проверка: V(x) > 0 и V̇(x) ≤ 0
    """
    for i, state in enumerate(trajectory):
        V = lyapunov_function(state)
        V_dot = compute_V_dot(state, trajectory, epsilon)
        
        if V <= 0 and i > 0:
            return StabilityResult(
                stable=False,
                reason=f"V({i}) = {V} ≤ 0"
            )
        
        if V_dot > 0:
            return StabilityResult(
                stable=False,
                reason=f"V̇({i}) = {V_dot} > 0"
            )
    
    return StabilityResult(stable=True)


def compute_V_dot(
    state: np.array,
    trajectory: List[np.array],
    dt: float
) -> float:
    """Численное вычисление производной V"""
    idx = trajectory.index(state)
    if idx == 0:
        return 0
    
    V_curr = lyapunov_function(state)
    V_prev = lyapunov_function(trajectory[idx - 1])
    
    return (V_curr - V_prev) / dt
```

---

## 2.3 Homeostatic Dynamics — Динамика гомеостаза

### Область: Golubitsky-Stewart

### Формула
$$\begin{aligned}
\dot{x}_\iota &= f_\iota(x_\iota, I) \\
\dot{x}_\kappa &= f_\kappa(x_\iota, x_\kappa) \\
\dot{x}_o &= f_o(x_\iota, x_\kappa, x_o)
\end{aligned}$$

### Входы
```
x_ι — входные узлы
x_κ — скрытые узлы  
xₒ — выходные узлы
I  — внешний вход
```

### Выход
```
ẋ_ι, ẋ_κ, ẋₒ — изменения всех узлов
```

### ДЕЙСТВИЕ: Симулировать динамику гомеостатической сети

### ПСЕВДОКОД
```python
class HomeostaticNetwork:
    def __init__(self):
        self.input_nodes = {}    # x_ι
        self.hidden_nodes = {}   # x_κ  
        self.output_nodes = {}   # xₒ
    
    def step(self, external_input: dict, dt: float) -> dict:
        """
        dx/dt = f(x, inputs)
        """
        # Обновляем входные узлы
        new_inputs = {}
        for name, node in self.input_nodes.items():
            input_val = external_input.get(name, 0)
            new_inputs[name] = node.value + node.derivative(node.value, input_val) * dt
        
        # Обновляем скрытые узлы
        new_hidden = {}
        for name, node in self.hidden_nodes.items():
            deps = node.get_dependencies(self.input_nodes, self.hidden_nodes)
            new_hidden[name] = node.value + node.derivative(node.value, deps) * dt
        
        # Обновляем выходные узлы
        new_outputs = {}
        for name, node in self.output_nodes.items():
            deps = node.get_dependencies(self.hidden_nodes, self.output_nodes)
            new_outputs[name] = node.value + node.derivative(node.value, deps) * dt
        
        return {"inputs": new_inputs, "hidden": new_hidden, "outputs": new_outputs}


# Пример: Гомеостатическая регуляция потока задач
def regulate_task_flow(
    queue_depth: int,
    processing_rate: float,
    incoming_rate: float
) -> RegulationSignal:
    """
    ẋ_ι = f_ι(x_ι, I) — вход: incoming rate
    ẋ_κ = f_κ(x_ι, x_κ) — скрытый: буфер
    ẋₒ = fₒ(x_κ) — выход: processing adjustment
    """
    target_queue = 5
    
    # Входной узел: входящие задачи
    input_change = incoming_rate - target_queue
    
    # Скрытый узел: размер очереди
    queue_deviation = queue_depth - target_queue
    hidden_state = -0.5 * queue_deviation  # Отрицательная обратная связь
    
    # Выходной узел: регулировка
    adjustment = -0.3 * hidden_state  # Если много в очереди — замедляем
    
    return RegulationSignal(
        adjust_processing_rate=adjustment,
        adjust_incoming=0,  # Не можем контролировать входящие
        alert_if_needed=abs(queue_deviation) > 3
    )
```

---

## 2.4 Infinitesimal Homeostasis Index — Индекс гомеостаза

### Область: Golubitsky-Stewart

### Формула
$$h_x(x_0, z_0) = \frac{g'_1(x_0) \cdot g'_2(y_0)}{g'_2(y_0) + g'_5(y_0)}$$

### Входы
```
g'₁, g'₂, g'₅ — производные функций активации
x₀, y₀, z₀    — рабочие точки
```

### Выход
```
hₓ — индекс гомеостатичности (близость к гомеостазу)
```

### ДЕЙСТВИЕ: Измерить близость к гомеостатическому состоянию

### ПСЕВДОКОД
```python
def compute_homeostasis_index(
    g1_derivative: float,  #чувствительность входа
    g2_derivative: float,  #чувствительность выхода 1
    g5_derivative: float,  #чувствительность выхода 2
) -> float:
    """
    hₓ = g'₁(x₀) × g'₂(y₀) / (g'₂(y₀) + g'₅(y₀))
    """
    if g2_derivative + g5_derivative == 0:
        return 0
    
    return (g1_derivative * g2_derivative) / (g2_derivative + g5_derivative)


# Аппроксимация через отклонения
def approximate_homeostasis_index(
    current_state: dict,
    target_state: dict
) -> float:
    """
    Индекс гомеостаза: чем ближе к 1, тем лучше
    """
    deviations = []
    for key in target_state:
        if key in current_state:
            deviation = 1 - abs(current_state[key] - target_state[key]) / target_state[key]
            deviations.append(max(0, deviation))
    
    if not deviations:
        return 0
    
    # Среднее гармоническое (штраф за любой низкий компонент)
    n = len(deviations)
    return n / sum(1 / (d + 1e-6) for d in deviations)
```

---

## 2.5 Drive Function — Функция влечения

### Область: Allostasis

### Формула
$$D(H) = \sum_i |h_i^* - h_i|^p$$

### Входы
```
h*ᵢ — оптимальное значение i-й переменной
hᵢ  — текущее значение
p    — степень (обычно p=2)
```

### Выход
```
D(H) ∈ [0, ∞) — совокупное отклонение от оптимума
```

### ДЕЙСТВИЕ: Измерить "потребность" системы

### ПСЕВДОКОД
```python
def compute_drive(
    current_state: dict,
    target_state: dict,
    p: float = 2.0
) -> float:
    """
    D(H) = Σ |h*ᵢ - hᵢ|^p
    """
    total = 0.0
    for key in target_state:
        if key in current_state:
            deviation = abs(target_state[key] - current_state[key])
            total += deviation ** p
    
    return total


def compute_drive_per_variable(
    current_state: dict,
    target_state: dict
) -> dict:
    """Вклад каждой переменной в drive"""
    drives = {}
    for key in target_state:
        if key in current_state:
            drives[key] = abs(target_state[key] - current_state[key])
    
    # Нормализуем
    total = sum(drives.values())
    if total > 0:
        for key in drives:
            drives[key] /= total
    
    return drives


# Определение приоритетности действий по drive
def prioritize_by_drive(
    current_state: dict,
    target_state: dict,
    possible_actions: List[Action]
) -> List[Action]:
    """
    Чем выше drive, тем приоритетнее действие
    """
    drive_per_var = compute_drive_per_variable(current_state, target_state)
    
    scored_actions = []
    for action in possible_actions:
        # Какое отклонение компенсирует это действие?
        affected_vars = action.affects_variables
        
        total_drive = sum(
            drive_per_var.get(var, 0) 
            for var in affected_vars
        )
        
        scored_actions.append((action, total_drive))
    
    # Сортируем по убыванию drive
    scored_actions.sort(key=lambda x: x[1], reverse=True)
    
    return [action for action, _ in scored_actions]
```

---

## 2.6 Drive Reduction Reward — Награда за снижение потребности

### Область: Reinforcement Learning / Allostasis

### Формула
$$R_t = D(H_t) - D(H_{t+1})$$

### Входы
```
D(Hₜ) — drive в момент t
D(Hₜ₊₁) — drive в момент t+1
```

### Выход
```
Rₜ ∈ (-∞, +∞)
  > 0 → положительная награда (снизили потребность)
  < 0 → отрицательная награда (увеличили потребность)
```

### ДЕЙСТВИЕ: Оценить награду за действие через снижение влечения

### ПСЕВДОКОД
```python
def compute_drive_reduction_reward(
    previous_state: dict,
    current_state: dict,
    target_state: dict
) -> float:
    """
    Rₜ = D(Hₜ) - D(Hₜ₊₁)
    """
    drive_before = compute_drive(previous_state, target_state)
    drive_after = compute_drive(current_state, target_state)
    
    return drive_before - drive_after


def update_agent_with_drive_reward(
    agent: Agent,
    action: Action,
    previous_state: dict,
    new_state: dict
):
    """
    Агент получает награду = снижение drive
    """
    reward = compute_drive_reduction_reward(
        previous_state, new_state, agent.target_state
    )
    
    # Обновляем Q-values или policy
    agent.remember(
        state=previous_state,
        action=action,
        reward=reward,
        next_state=new_state
    )
    
    return reward
```

---

# ЧАСТЬ 3: MDP И RL

---

## 3.1 MDP Tuple — Кортеж MDP

### Область: Dynamic Programming

### Формула
$$\text{MDP} = (S, A, P, R, \gamma)$$

### Компоненты
```
S  — пространство состояний
A  — пространство действий
P  — функция переходов P(s'|s,a)
R  — функция награды R(s,a,s')
γ  — коэффициент дисконтирования
```

### ДЕЙСТВИЕ: Определить структуру задачи RL

### ПСЕВДОКОД
```python
@dataclass
class MDP:
    states: Set[State]
    actions: Set[Action]
    transition_probs: Dict[Tuple[State, Action], Dict[State, float]]
    reward_fn: Callable[[State, Action, State], float]
    gamma: float  # discount factor
    
    def get_transition_probs(
        self, 
        state: State, 
        action: Action
    ) -> Dict[State, float]:
        key = (state, action)
        return self.transition_probs.get(key, {})
    
    def get_reward(
        self,
        state: State,
        action: Action,
        next_state: State
    ) -> float:
        return self.reward_fn(state, action, next_state)


# Пример: MDP для агента-фрилансера
freelancer_mdp = MDP(
    states={
        "LOW_FUNDS", "MEDIUM_FUNDS", "HIGH_FUNDS",
        "LOW_REPUTATION", "HIGH_REPUTATION",
        "IDLE", "BUSY", "OVERLOADED"
    },
    actions={
        "TAKE_TASK", "DECLINE_TASK", "REFINE_SKILLS",
        "WAIT", "BID", "NEGOTIATE"
    },
    transition_probs=...,  # P(s'|s,a)
    reward_fn=lambda s, a, s': compute_reward(s, a, s'),
    gamma=0.95
)
```

---

## 3.2 State Value Function — Функция ценности состояния

### Область: Bellman

### Формула
$$V^\pi(s) = \sum_{a \in A} \pi(a|s) \sum_{s' \in S} P(s'|s,a) \left[ R(s,a,s') + \gamma V^\pi(s') \right]$$

### Входы
```
π(a|s)  — политика (вероятность действия a в состоянии s)
P(s'|s,a) — вероятность перехода
R(s,a,s') — награда
γ         — дисконт
```

### Выход
```
V^π(s) — ожидаемая дисконтированная награда от состояния s
```

### ДЕЙСТВИЕ: Оценить "ценность" состояния

### ПСЕВДОКОД
```python
def compute_state_value(
    state: State,
    policy: Policy,
    mdp: MDP,
    V: Dict[State, float],  # Текущие значения
    gamma: float
) -> float:
    """
    V^π(s) = Σₐ π(a|s) Σₛ' P(s'|s,a) × [R(s,a,s') + γV(s')]
    """
    value = 0.0
    
    for action in mdp.actions:
        action_prob = policy.get_probability(state, action)
        if action_prob == 0:
            continue
        
        action_value = 0.0
        transitions = mdp.get_transition_probs(state, action)
        
        for next_state, prob in transitions.items():
            reward = mdp.get_reward(state, action, next_state)
            action_value += prob * (reward + gamma * V.get(next_state, 0.0))
        
        value += action_prob * action_value
    
    return value


def policy_evaluation(
    mdp: MDP,
    policy: Policy,
    theta: float = 1e-6,
    max_iterations: int = 1000
) -> Dict[State, float]:
    """
    Итеративная оценка политики до сходимости
    """
    V = {s: 0.0 for s in mdp.states}
    
    for _ in range(max_iterations):
        delta = 0
        
        for state in mdp.states:
            v = V[state]
            V[state] = compute_state_value(state, policy, mdp, V, mdp.gamma)
            delta = max(delta, abs(v - V[state]))
        
        if delta < theta:
            break
    
    return V
```

---

## 3.3 Q-Function — Функция ценности действия

### Область: Bellman

### Формула
$$Q^\pi(s,a) = \sum_{s'} P(s'|s,a) \left[ R(s,a,s') + \gamma V^\pi(s') \right]$$

### Входы
```
s, a  — состояние и действие
P, R, γ — компоненты MDP
V^π    — функция ценности состояния
```

### Выход
```
Q^π(s,a) — ожидаемая награда за действие a в состоянии s
```

### ДЕЙСТВИЕ: Оценить качество конкретного действия

### ПСЕВДОКОД
```python
def compute_q_value(
    state: State,
    action: Action,
    mdp: MDP,
    V: Dict[State, float]
) -> float:
    """
    Q^π(s,a) = Σₛ' P(s'|s,a) × [R(s,a,s') + γV(s')]
    """
    q_value = 0.0
    transitions = mdp.get_transition_probs(state, action)
    
    for next_state, prob in transitions.items():
        reward = mdp.get_reward(state, action, next_state)
        future_value = V.get(next_state, 0.0)
        q_value += prob * (reward + mdp.gamma * future_value)
    
    return q_value


def compute_all_q_values(
    state: State,
    mdp: MDP,
    V: Dict[State, float]
) -> Dict[Action, float]:
    """Вычислить Q-values для всех действий в состоянии"""
    return {
        action: compute_q_value(state, action, mdp, V)
        for action in mdp.actions
    }
```

---

## 3.4 Optimal Value Function — Оптимальная функция ценности

### Область: Dynamic Programming

### Формула
$$V^*(s) = \max_a \sum_{s'} P(s'|s,a) \left[ R(s,a,s') + \gamma V^*(s') \right]$$

### Входы
```
Те же что и для V^π, но max по действиям
```

### Выход
```
V*(s) — максимально возможная ожидаемая награда
```

### ДЕЙСТВИЕ: Найти оптимальную стратегию

### ПСЕВДОКОД
```python
def compute_optimal_value(
    state: State,
    mdp: MDP,
    V: Dict[State, float]
) -> Tuple[float, Action]:
    """
    V*(s) = maxₐ Σₛ' P(s'|s,a) × [R(s,a,s') + γV(s')]
    """
    best_value = float('-inf')
    best_action = None
    
    for action in mdp.actions:
        q_value = compute_q_value(state, action, mdp, V)
        if q_value > best_value:
            best_value = q_value
            best_action = action
    
    return best_value, best_action


def value_iteration(
    mdp: MDP,
    theta: float = 1e-6,
    max_iterations: int = 1000
) -> Tuple[Dict[State, float], Policy]:
    """
    Алгоритм Value Iteration для нахождения оптимальной политики
    """
    V = {s: 0.0 for s in mdp.states}
    policy = {}
    
    for _ in range(max_iterations):
        delta = 0
        
        for state in mdp.states:
            v = V[state]
            best_value, best_action = compute_optimal_value(state, mdp, V)
            V[state] = best_value
            policy[state] = best_action
            delta = max(delta, abs(v - best_value))
        
        if delta < theta:
            break
    
    return V, GreedyPolicy(policy)
```

---

## 3.5 Q-Learning Update — Обновление Q-значения

### Область: Reinforcement Learning

### Формула
$$Q(s,a) \leftarrow Q(s,a) + \alpha \left[ r + \gamma \max_{a'} Q(s',a') - Q(s,a) \right]$$

### Входы
```
α  — learning rate
r  — полученая награда
γ  — discount factor
Q(s',a') — текущая оценка следующего состояния
```

### Выход
```
Обновлённое Q(s,a)
```

### ДЕЙСТВИЕ: Обучить агента на основе опыта

### ПСЕВДОКОД
```python
class QLearningAgent:
    def __init__(self, alpha: float, gamma: float, epsilon: float):
        self.alpha = alpha      # Learning rate
        self.gamma = gamma      # Discount factor
        self.epsilon = epsilon  # Exploration rate
        self.Q = {}            # Q-table: (state, action) -> value
    
    def get_q_value(self, state: State, action: Action) -> float:
        return self.Q.get((state, action), 0.0)
    
    def update(
        self,
        state: State,
        action: Action,
        reward: float,
        next_state: State
    ):
        """
        Q(s,a) ← Q(s,a) + α × [r + γ maxₐ' Q(s',a') - Q(s,a)]
        """
        current_q = self.get_q_value(state, action)
        
        # Max Q-value для следующего состояния
        max_next_q = max(
            self.get_q_value(next_state, a)
            for a in self.get_possible_actions(next_state)
        ) if self.get_possible_actions(next_state) else 0
        
        # TD-target
        td_target = reward + self.gamma * max_next_q
        
        # TD-error
        td_error = td_target - current_q
        
        # Обновление
        self.Q[(state, action)] = current_q + self.alpha * td_error
    
    def choose_action(self, state: State) -> Action:
        """
        ε-greedy policy
        """
        if random.random() < self.epsilon:
            return random.choice(self.get_possible_actions(state))
        else:
            # Greedy: выбираем действие с max Q-value
            q_values = [
                (action, self.get_q_value(state, action))
                for action in self.get_possible_actions(state)
            ]
            return max(q_values, key=lambda x: x[1])[0]
```

---

## 3.6 Policy Gradient — Градиент политики

### Область: Reinforcement Learning

### Формула
$$\nabla_\theta J(\theta) = \mathbb{E}_{\tau \sim \pi_\theta} \left[ \sum_{t=0}^{T} \nabla_\theta \log \pi_\theta(a_t|s_t) G_t \right]$$

### Входы
```
π_θ(aₜ|sₜ) — политика параметризованная θ
Gₜ         — discounted return от времени t
```

### Выход
```
∇_θ J(θ) — градиент для обновления политики
```

### ДЕЙСТВИЕ: Обновить параметры политики

### ПСЕВДОКОД
```python
def compute_policy_gradient(
    trajectories: List[Trajectory],
    policy: ParametricPolicy,
    gamma: float = 0.99
) -> np.array:
    """
    ∇_θ J(θ) = E[Σ ∇_θ log π_θ(aₜ|sₜ) × Gₜ]
    """
    gradients = []
    
    for traj in trajectories:
        traj_gradient = np.zeros_like(policy.parameters)
        
        G = 0  # Discounted return
        for t in reversed(range(len(traj))):
            state, action, reward = traj[t]
            G = reward + gamma * G
            
            # ∇_θ log π_θ(aₜ|sₜ)
            log_prob_grad = policy.log_prob_gradient(state, action)
            traj_gradient += log_prob_grad * G
        
        gradients.append(traj_gradient)
    
    # Матожидание по траекториям
    return np.mean(gradients, axis=0)


def update_policy(
    policy: ParametricPolicy,
    gradient: np.array,
    learning_rate: float = 0.001
):
    """
    θ ← θ + α × ∇_θ J(θ)
    """
    policy.parameters += learning_rate * gradient
```

---

# ЧАСТЬ 4: АКТИВНЫЙ ВЫВОД И СВОБОДНАЯ ЭНЕРГИЯ

---

## 4.1 Free Energy Principle — Принцип свободной энергии

### Область: Friston (2010)

### Формула
$$F = D_{KL}[q(z|x) \| p(z|x)] - \log p(x)$$

### Входы
```
q(z|x) — вариационное приближение posterior
p(z|x) — истинный posterior (неизвестен)
p(x)   — маргинальное правдоподобие
```

### Выход
```
F ∈ (-∞, +∞) — свободная энергия (нижняя = лучше)
```

### ДЕЙСТВИЕ: Оценить "удивление" модели

### ПСЕВДОКОД
```python
def compute_free_energy(
    posterior_approx: Distribution,  # q(z|x)
    prior: Distribution,          # p(z)
    observation: np.array          # x
) -> float:
    """
    F = D_KL[q(z|x) || p(z|x)] - log p(x)
    
    Для вариационного вывода:
    F ≈ D_KL[q(z) || p(z)] - E_q[log p(x|z)]
    """
    # KL(q || p) = Σ q(z) × log(q(z)/p(z))
    kl_divergence = kl_divergence(posterior_approx, prior)
    
    # Ожидаемый log-likelihood
    expected_log_likelihood = expected_log_likelihood(
        posterior_approx, observation
    )
    
    return kl_divergence - expected_log_likelihood


def surprise(observation: np.array, model: GenerativeModel) -> float:
    """
    F ≈ -log p(x) — сюрприз
    """
    return -model.log_probability(observation)
```

---

## 4.2 Active Inference — Активный вывод

### Область: Friston

### Формула
$$\pi^* = \arg\min_\pi F(\mu, \pi)$$

### Входы
```
F(μ, π) — свободная энергия
μ        — скрытые состояния
π        — политика
```

### Выход
```
π* — оптимальная политика
```

### ДЕЙСТВИЕ: Найти политику минимизирующую free energy

### ПСЕВДОКОД
```python
def active_inference(
    current_beliefs: dict,
    desired_outcome: dict,
    possible_policies: List[Policy]
) -> Policy:
    """
    π* = argmin_π F(μ, π)
    """
    best_policy = None
    best_free_energy = float('inf')
    
    for policy in possible_policies:
        expected_fe = simulate_policy_free_energy(
            current_beliefs, policy, desired_outcome
        )
        
        if expected_fe < best_free_energy:
            best_free_energy = expected_fe
            best_policy = policy
    
    return best_policy


def simulate_policy_free_energy(
    beliefs: dict,
    policy: Policy,
    target: dict,
    n_samples: int = 100
) -> float:
    """Симуляция свободной энергии для политики"""
    free_energies = []
    
    for _ in range(n_samples):
        # Симулируем исход
        simulated_outcome = simulate_trajectory(beliefs, policy)
        
        # Free energy для исхода
        fe = compute_free_energy_for_outcome(simulated_outcome, target)
        free_energies.append(fe)
    
    return np.mean(free_energies)
```

---

## 4.3 Belief Update — Обновление убеждений

### Область: Friston

### Формула
$$\dot{\mu} = D_\mu \cdot \frac{\partial F}{\partial \mu}$$

### Входы
```
D_μ — матрица точности
∂F/∂μ — градиент свободной энергии по убеждениям
```

### Выход
```
μ̇ — изменение убеждений
```

### ДЕЙСТВИЕ: Обновить внутренние убеждения агента

### ПСЕВДОКОД
```python
def update_beliefs(
    current_beliefs: np.array,
    free_energy_gradient: np.array,
    precision_matrix: np.array,
    dt: float = 0.1
) -> np.array:
    """
    μ̇ = D_μ × ∂F/∂μ
    """
    # Градиент свободной энергии
    gradient = precision_matrix @ free_energy_gradient
    
    # Обновление
    return current_beliefs + gradient * dt


def compute_free_energy_gradient(
    beliefs: np.array,
    observation: np.array,
    model: GenerativeModel
) -> np.array:
    """
    ∂F/∂μ — численное вычисление градиента
    """
    eps = 1e-5
    gradient = np.zeros_like(beliefs)
    
    for i in range(len(beliefs)):
        beliefs_plus = beliefs.copy()
        beliefs_plus[i] += eps
        beliefs_minus = beliefs.copy()
        beliefs_minus[i] -= eps
        
        fe_plus = compute_free_energy(
            beliefs_plus, observation, model
        )
        fe_minus = compute_free_energy(
            beliefs_minus, observation, model
        )
        
        gradient[i] = (fe_plus - fe_minus) / (2 * eps)
    
    return gradient
```

---

# ЧАСТЬ 5: УПРАВЛЕНИЕ АГЕНТАМИ

---

## 5.1 Context Dynamics — Динамика контекста

### Область: Agent Control

### Формула
$$c_{t+1} = f_\theta(c_t, a_t, o_t)$$

### Входы
```
cₜ  — текущий контекст
aₜ  — выполненное действие
oₜ  — наблюдение (feedback)
f_θ — learned transition function
```

### Выход
```
c_{t+1} — обновлённый контекст
```

### ДЕЙСТВИЕ: Обновить контекст агента

### ПСЕВДОКОД
```python
class ContextManager:
    def __init__(self, model):
        self.model = model  # f_θ
    
    def update(
        self,
        current_context: np.array,
        action: Action,
        observation: np.array
    ) -> np.array:
        """
        c_{t+1} = f_θ(cₜ, aₜ, oₜ)
        """
        # Кодируем действие и наблюдение
        action_encoded = self.encode_action(action)
        obs_encoded = self.encode_observation(observation)
        
        # Конкатенируем с контекстом
        combined = np.concatenate([
            current_context,
            action_encoded,
            obs_encoded
        ])
        
        # Применяем модель
        new_context = self.model(combined)
        
        return new_context


# GRU-based context update (упрощённо)
class GRUContextUpdate:
    def forward(self, c_prev, action, observation):
        combined = np.concatenate([c_prev, action, observation])
        # GRU equations (упрощённо)
        z = sigmoid(W_z @ combined + b_z)  # Update gate
        r = sigmoid(W_r @ combined + b_r)  # Reset gate
        h_tilde = tanh(W_h @ np.concatenate([r * c_prev, combined]) + b_h)
        c_new = (1 - z) * c_prev + z * h_tilde
        return c_new
```

---

## 5.2 Action Selection — Выбор действия

### Область: Agent Control

### Формула
$$a_t \sim \pi_\theta(\cdot | c_t)$$

### Входы
```
π_θ — политика (нейросеть)
cₜ  — текущий контекст
```

### Выход
```
aₜ — выбранное действие
```

### ДЕЙСТВИЕ: Выбрать действие на основе контекста

### ПСЕВДОКОД
```python
class PolicyNetwork:
    def __init__(self, context_dim, action_dim):
        self.network = build_mlp(context_dim, action_dim)
    
    def sample_action(
        self,
        context: np.array,
        temperature: float = 1.0
    ) -> Action:
        """
        aₜ ~ π_θ(·|cₜ)
        """
        logits = self.network(context)
        
        # Temperature sampling
        probs = softmax(logits / temperature)
        
        # Сэмплируем
        action_idx = np.random.choice(len(probs), p=probs)
        
        return Action(index=action_idx)
    
    def greedy_action(self, context: np.array) -> Action:
        """Greedy выбор — для exploitation"""
        logits = self.network(context)
        action_idx = np.argmax(logits)
        return Action(index=action_idx)
    
    def probability(self, context: np.array, action: Action) -> float:
        """P(a|c)"""
        logits = self.network(context)
        probs = softmax(logits)
        return probs[action.index]
```

---

## 5.3 Agent Objective — Целевая функция агента

### Область: Agent Control

### Формула
$$J(\theta) = \mathbb{E} \left[ \sum_t \gamma^t \cdot R(s_t, a_t) \right]$$

### Входы
```
θ    — параметры агента
R(sₜ, aₜ) — награда
γ    — discount
```

### Выход
```
J(θ) — ожидаемая дисконтированная награда
```

### ДЕЙСТВИЕ: Оптимизировать параметры агента

### ПСЕВДОКОД
```python
def compute_agent_objective(
    trajectories: List[Trajectory],
    gamma: float = 0.99
) -> float:
    """
    J(θ) = E[Σ γᵗ R(sₜ, aₜ)]
    """
    total_return = 0.0
    n_samples = 0
    
    for traj in trajectories:
        G = 0.0
        for t, (state, action, reward) in enumerate(traj):
            G += (gamma ** t) * reward
        
        total_return += G
        n_samples += 1
    
    return total_return / n_samples if n_samples > 0 else 0.0


def optimize_agent(
    agent: Agent,
    trajectories: List[Trajectory],
    learning_rate: float = 0.001
):
    """
    Обновление параметров для максимизации J(θ)
    """
    objective = compute_agent_objective(trajectories, agent.gamma)
    
    # Gradient ascent (упрощённо)
    gradient = compute_policy_gradient(trajectories, agent.policy, agent.gamma)
    
    agent.policy.parameters += learning_rate * gradient
    
    return objective
```

---

# ЧАСТЬ 6: МУЛЬТИ-АГЕНТНОЕ СОГЛАСОВАНИЕ

---

## 6.1 Consensus Condition — Условие консенсуса

### Область: Multi-Agent Systems

### Формула
$$\lim_{t \to \infty} \|x_i(t) - x_j(t)\| = 0$$

### Входы
```
xᵢ(t), xⱼ(t) — состояния агентов i и j
```

### Выход
```
True если консенсус достигнут
```

### ДЕЙСТВИЕ: Проверить достижение консенсуса

### ПСЕВДОКОД
```python
def check_consensus(
    agent_states: Dict[AgentID, State],
    threshold: float = 1e-3
) -> Tuple[bool, float]:
    """
    lim ||xᵢ - xⱼ|| = 0
    """
    states = list(agent_states.values())
    
    if len(states) < 2:
        return True, 0.0
    
    # Вычисляем максимальное расстояние между агентами
    max_distance = 0.0
    for i in range(len(states)):
        for j in range(i + 1, len(states)):
            dist = np.linalg.norm(states[i] - states[j])
            max_distance = max(max_distance, dist)
    
    consensus_reached = max_distance < threshold
    
    return consensus_reached, max_distance


def update_towards_consensus(
    agent_id: AgentID,
    neighbors: List[AgentID],
    agent_states: Dict[AgentID, State],
    coupling_strength: float = 0.5
) -> State:
    """
    ẋᵢ = Σ aᵢⱼ(xⱼ - xᵢ)
    """
    current_state = agent_states[agent_id]
    
    if not neighbors:
        return current_state
    
    # Среднее соседей
    neighbor_states = [agent_states[n] for n in neighbors]
    mean_neighbor = np.mean(neighbor_states, axis=0)
    
    # Движение к среднему
    update = coupling_strength * (mean_neighbor - current_state)
    
    return current_state + update
```

---

## 6.2 Agent Dynamics with Neighbors — Динамика с соседями

### Область: Multi-Agent

### Формула
$$\dot{x}_i = f\left(x_i, \sum_{j \in N_i} x_j, u_i \right)$$

### Входы
```
xᵢ    — состояние агента i
Nᵢ    — множество соседей
Σⱼ∈Nᵢ xⱼ — сумма состояний соседей
uᵢ    — локальное управление
```

### Выход
```
ẋᵢ — изменение состояния
```

### ДЕЙСТВИЕ: Обновить состояние с учётом соседей

### ПСЕВДОКОД
```python
class MultiAgentSystem:
    def __init__(self, coupling: float = 0.5):
        self.coupling = coupling
        self.agents = {}
        self.topology = {}  # adjacency list
    
    def step(self, dt: float):
        """Один шаг симуляции"""
        new_states = {}
        
        for agent_id in self.agents:
            neighbors = self.topology.get(agent_id, [])
            
            # Локальная динамика
            local_dynamics = self.compute_local_dynamics(
                self.agents[agent_id]
            )
            
            # Влияние соседей
            neighbor_influence = np.zeros_like(local_dynamics)
            if neighbors:
                neighbor_states = [self.agents[n] for n in neighbors]
                neighbor_influence = self.coupling * np.mean(
                    [ns - self.agents[agent_id] for ns in neighbor_states],
                    axis=0
                )
            
            # Обновление
            new_states[agent_id] = (
                self.agents[agent_id] + 
                (local_dynamics + neighbor_influence) * dt
            )
        
        self.agents = new_states
    
    def compute_local_dynamics(self, state: State) -> np.array:
        """f(xᵢ, uᵢ) — локальная динамика агента"""
        # Пример: стремление к целевому состоянию
        return -0.1 * (state - state.target)
```

---

# ЧАСТЬ 7: НЕЙРОННЫЕ СЕТИ

---

## 7.1 Hebbian Learning — Правило Хебба

### Область: Neural Networks

### Формула
$$\dot{w}_{ij} = \eta \cdot x_i \cdot x_j - \lambda w_{ij}$$

### Входы
```
η  — learning rate
λ  — forgetting rate
xᵢ, xⱼ — активности нейронов
```

### Выход
```
ẘᵢⱼ — изменение веса
```

### ДЕЙСТВИЕ: Обучить ассоциации между паттернами

### ПСЕВДОКОД
```python
def hebbian_update(
    w: float,
    pre_synaptic: float,
    post_synaptic: float,
    eta: float = 0.01,
    lambda_forget: float = 0.001
) -> float:
    """
    ẘᵢⱼ = η × xᵢ × xⱼ - λ × wᵢⱼ
    """
    # Hebbian strengthening
    strengthening = eta * pre_synaptic * post_synaptic
    
    # Forgetting (защита от переполнения)
    forgetting = lambda_forget * w
    
    return w + strengthening - forgetting


def update_memory_associations(
    memory: AssociativeMemory,
    pattern_a: np.array,
    pattern_b: np.array,
    strength: float = 0.1
):
    """
    Усилить связь между паттернами A и B
    """
    for i in range(len(pattern_a)):
        for j in range(len(pattern_b)):
            # Активации
            x_i = pattern_a[i]
            x_j = pattern_b[j]
            
            # Hebbian update
            memory.weights[i, j] = hebbian_update(
                memory.weights[i, j],
                x_i, x_j,
                eta=strength
            )
```

---

## 7.2 LSTM Forget Gate — Вентиль забывания

### Область: Neural Networks

### Формула
$$f_t = \sigma(W_f \cdot [h_{t-1}, x_t] + b_f)$$

### Входы
```
h_{t-1} — предыдущее скрытое состояние
xₜ      — текущий вход
W_f, b_f — веса и bias вентиля
```

### Выход
```
fₜ ∈ [0, 1] — доля предыдущего состояния сохранить
```

### ДЕЙСТВИЕ: Решить что забыть из памяти

### ПСЕВДОКОД
```python
def compute_forget_gate(
    hidden_prev: np.array,
    input_current: np.array,
    W_f: np.array,
    b_f: np.array
) -> float:
    """
    fₜ = σ(W_f · [h_{t-1}, xₜ] + b_f)
    """
    concatenated = np.concatenate([hidden_prev, input_current])
    logits = W_f @ concatenated + b_f
    return sigmoid(logits)


def lstm_cell(
    cell_state_prev: np.array,
    hidden_prev: np.array,
    input_current: np.array,
    weights: LSTMWeights
) -> Tuple[np.array, np.array]:
    """
    Полный LSTM cell с forget gate
    """
    # Forget gate
    f = compute_forget_gate(
        hidden_prev, input_current,
        weights.W_f, weights.b_f
    )
    
    # Input gate
    i = sigmoid(weights.W_i @ np.concatenate([hidden_prev, input_current]) + weights.b_i)
    
    # Candidate values
    g = tanh(weights.W_g @ np.concatenate([hidden_prev, input_current]) + weights.b_g)
    
    # Output gate
    o = sigmoid(weights.W_o @ np.concatenate([hidden_prev, input_current]) + weights.b_o)
    
    # Update cell state
    cell_state_new = f * cell_state_prev + i * g
    
    # Update hidden state
    hidden_new = o * tanh(cell_state_new)
    
    return cell_state_new, hidden_new


def memory_decay(
    cell_state: np.array,
    importance: float,
    decay_rate: float = 0.01
) -> np.array:
    """
    Забывание пропорционально важности
    """
    # Чем важнее, тем медленнее забываем
    effective_decay = decay_rate / (1 + importance)
    return cell_state * (1 - effective_decay)
```

---

# ЧАСТЬ 8: ТЕОРИЯ УПРАВЛЕНИЯ

---

## 8.1 LQR Cost Function — Функция стоимости LQR

### Область: Optimal Control

### Формула
$$J = \int_0^T (x^T Q x + u^T R u) dt$$

### Входы
```
Q — матрица штрафа за состояние
R — матрица штрафа за управление
x — состояние
u — управление
```

### Выход
```
J — суммарная стоимость
```

### ДЕЙСТВИЕ: Оценить стоимость траектории

### ПСЕВДОКОД
```python
def compute_lqr_cost(
    trajectory: List[Tuple[np.array, np.array]],
    Q: np.array,
    R: np.array
) -> float:
    """
    J = Σ (xᵀQx + uᵀRu)
    """
    total_cost = 0.0
    
    for state, control in trajectory:
        state_cost = state @ Q @ state
        control_cost = control @ R @ control
        total_cost += state_cost + control_cost
    
    return total_cost


# Пример для агента
def compute_agent_trajectory_cost(
    states: List[State],
    controls: List[Control],
    state_weights: dict,  # Веса для каждой переменной
    control_cost: float   # Стоимость единицы управления
) -> float:
    Q = np.diag([state_weights[k] for k in sorted(state_weights.keys())])
    R = np.eye(len(controls[0])) * control_cost
    
    trajectory = list(zip(states, controls))
    return compute_lqr_cost(trajectory, Q, R)
```

---

## 8.2 Riccati Equation — Уравнение Риккати

### Область: Optimal Control

### Формула
$$A^T P + P A - P B R^{-1} B^T P + Q = 0$$

### Входы
```
A, B — матрицы системы
Q, R — матрицы стоимости
```

### Выход
```
P — решение (матрица Riccati)
K = R^{-1} B^T P — оптимальный коэффициент усиления
```

### ДЕЙСТВИЕ: Найти оптимальное управление LQR

### ПСЕВДОКОД
```python
def solve_lqr(
    A: np.array,
    B: np.array,
    Q: np.array,
    R: np.array,
    max_iterations: int = 100,
    tolerance: float = 1e-8
) -> Tuple[np.array, np.array]:
    """
    AᵀP + PA - PBR⁻¹BᵀP + Q = 0
    Решение итеративным методом
    """
    n = A.shape[0]
    P = Q.copy()  # Initial guess
    
    for _ in range(max_iterations):
        # Solve Lyapunov equation for P
        # P_{k+1} = Q + AᵀP_kA - AᵀP_kB(R + BᵀP_kB)⁻¹BᵀP_kA
        PBT = P @ B
        R_BT_PB = R + B.T @ PBT
        R_BT_PB_inv = np.linalg.inv(R_BT_PB)
        
        P_new = (
            Q 
            + A.T @ P @ A 
            - A.T @ PBT @ R_BT_PB_inv @ B.T @ P @ A
        )
        
        # Check convergence
        diff = np.max(np.abs(P_new - P))
        P = P_new
        
        if diff < tolerance:
            break
    
    # Optimal feedback gain
    K = np.linalg.inv(R + B.T @ P @ B) @ B.T @ P @ A
    
    return P, K


def lqr_controller(
    state: np.array,
    target_state: np.array,
    K: np.array
) -> np.array:
    """
    u = -K × (x - x_target)
    """
    error = state - target_state
    return -K @ error
```

---

# ЧАСТЬ 9: ПОИСК И ПЛАНИРОВАНИЕ

---

## 9.1 UCB1 Exploration-Exploitation — Баланс исследования и использования

### Область: MCTS / Bandits

### Формула
$$P_{ucb} = \frac{V_i}{n_i} + c \sqrt{\frac{\ln N}{n_i}}$$

### Входы
```
Vᵢ/nᵢ — средняя ценность узла i
nᵢ     — количество посещений узла i
N      — общее количество посещений
c      — параметр exploration
```

### Выход
```
P_ucb — приоритет для выбора
```

### ДЕЙСТВИЕ: Выбрать между exploration и exploitation

### ПСЕВДОКОД
```python
def ucb1_score(
    node_value: float,
    visit_count: int,
    total_visits: int,
    exploration_constant: float = 1.414  # sqrt(2)
) -> float:
    """
    P_ucb = Vᵢ/nᵢ + c × sqrt(ln N / nᵢ)
    """
    if visit_count == 0:
        return float('inf')  # Непосещённые узлы имеют наивысший приоритет
    
    exploitation = node_value / visit_count
    exploration = exploration_constant * np.sqrt(np.log(total_visits) / visit_count)
    
    return exploitation + exploration


class MCTSNode:
    def __init__(self):
        self.visit_count = 0
        self.total_value = 0.0
        self.children = {}
    
    def ucb_score(self, parent_visits: int, c: float = 1.414) -> float:
        return ucb1_score(
            self.total_value,
            self.visit_count,
            parent_visits,
            c
        )


def select_ucb(node: MCTSNode, parent_visits: int) -> MCTSNode:
    """Выбрать лучший дочерний узел по UCB"""
    if not node.children:
        return node
    
    best_child = None
    best_score = float('-inf')
    
    for child in node.children.values():
        score = child.ucb_score(parent_visits)
        if score > best_score:
            best_score = score
            best_child = child
    
    return best_child
```

---

## 9.2 Cosine Similarity — Косинусное сходство

### Область: Information Retrieval

### Формула
$$\text{Sim}(q, k) = \frac{q \cdot k}{\|q\| \cdot \|k\|} = \frac{\sum_i q_i k_i}{\sqrt{\sum_i q_i^2} \sqrt{\sum_i k_i^2}}$$

### Входы
```
q — вектор запроса
k — вектор ключа
```

### Выход
```
Sim ∈ [-1, 1] — сходство
```

### ДЕЙСТВИЕ: Измерить семантическое сходство

### ПСЕВДОКОД
```python
def cosine_similarity(vec_a: np.array, vec_b: np.array) -> float:
    """
    Sim(q, k) = q·k / (||q|| × ||k||)
    """
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return np.dot(vec_a, vec_b) / (norm_a * norm_b)


def find_most_similar(
    query: np.array,
    candidates: List[np.array]
) -> Tuple[int, float]:
    """
    Найти наиболее похожий вектор
    """
    best_idx = 0
    best_score = float('-inf')
    
    for i, candidate in enumerate(candidates):
        score = cosine_similarity(query, candidate)
        if score > best_score:
            best_score = score
            best_idx = i
    
    return best_idx, best_score
```

---

## 9.3 Scaled Dot-Product Attention — Внимание

### Область: Transformers

### Формула
$$\text{Attention}(Q, K, V) = \text{softmax}\left( \frac{Q K^T}{\sqrt{d_k}} \right) V$$

### Входы
```
Q — Query matrix
K — Key matrix
V — Value matrix
d_k — размерность ключей
```

### Выход
```
Attention — взвешенная сумма value vectors
```

### ДЕЙСТВИЕ: Вычислить attention для контекста

### ПСЕВДОКОД
```python
def scaled_dot_product_attention(
    Q: np.array,  # (seq_len, d_k)
    K: np.array,  # (seq_len, d_k)
    V: np.array,  # (seq_len, d_v)
    mask: np.array = None
) -> np.array:
    """
    Attention(Q, K, V) = softmax(QKᵀ/√d_k) × V
    """
    d_k = Q.shape[-1]
    
    # QK^T
    scores = Q @ K.T / np.sqrt(d_k)  # (seq_len, seq_len)
    
    # Маска (опционально)
    if mask is not None:
        scores = np.where(mask, scores, -1e9)
    
    # Softmax
    attention_weights = softmax(scores, axis=-1)
    
    # V weighted sum
    output = attention_weights @ V
    
    return output, attention_weights


class MultiHeadAttention:
    def __init__(self, d_model: int, n_heads: int):
        self.d_model = d_model
        self.n_heads = n_heads
        self.d_k = d_model // n_heads
        
        self.W_Q = ...  # Projections
        self.W_K = ...
        self.W_V = ...
        self.W_O = ...
    
    def forward(self, query, key, value, mask=None):
        batch_size = query.shape[0]
        
        # Linear projections
        Q = self.W_Q @ query  # (batch, seq, d_model)
        K = self.W_K @ key
        V = self.W_V @ value
        
        # Reshape for multi-head
        Q = Q.view(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)
        K = K.view(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)
        V = V.view(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)
        
        # Attention
        attn_output, _ = scaled_dot_product_attention(Q, K, V, mask)
        
        # Concatenate heads
        attn_output = attn_output.transpose(1, 2).contiguous().view(
            batch_size, -1, self.d_model
        )
        
        # Final projection
        return self.W_O @ attn_output
```

---

## 9.4 BM25 Scoring — Ранжирование документов

### Область: Information Retrieval

### Формула
$$\text{Score}(D, Q) = \sum_i \text{IDF}(q_i) \cdot \frac{f(q_i, D) \cdot (k_1 + 1)}{f(q_i, D) + k_1 \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}} \right)}$$

### Входы
```
f(qᵢ, D) — частота терма в документе
|D|      — длина документа
avgdl    — средняя длина коллекции
IDF(qᵢ) — inverse document frequency
k₁, b   — параметры (обычно k₁=1.5, b=0.75)
```

### Выход
```
Score — релевантность документа запросу
```

### ДЕЙСТВИЕ: Ранжировать документы по запросу

### ПСЕВДОКОД
```python
class BM25:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_freqs = {}  # term -> doc frequency
        self.avgdl = 0
        self.N = 0
        self.idf = {}
    
    def fit(self, corpus: List[List[str]]):
        """Подсчёт IDF для коллекции"""
        self.N = len(corpus)
        
        # Document frequencies
        for doc in corpus:
            self.avgdl += len(doc)
            seen = set()
            for term in doc:
                if term not in seen:
                    self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1
                    seen.add(term)
        
        self.avgdl /= self.N
        
        # IDF для каждого терма
        for term, df in self.doc_freqs.items():
            self.idf[term] = np.log(
                (self.N - df + 0.5) / (df + 0.5) + 1
            )
    
    def score(self, query: List[str], document: List[str]) -> float:
        """
        Score(D, Q) = Σ IDF(qᵢ) × (f(qᵢ,D)(k₁+1))/(f(qᵢ,D) + k₁(1-b+b×|D|/avgdl))
        """
        doc_len = len(document)
        doc_freq = Counter(document)
        
        score = 0.0
        for term in query:
            if term not in self.idf:
                continue
            
            f = doc_freq.get(term, 0)
            idf = self.idf[term]
            
            # Term frequency component
            tf_component = (
                f * (self.k1 + 1)
            ) / (
                f + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
            )
            
            score += idf * tf_component
        
        return score
```

---

# ЧАСТЬ 10: ДИНАМИКА ПАМЯТИ

---

## 10.1 Memory Decay — Затухание памяти

### Область: Memory Systems

### Формула
$$W(t) = W_0 \cdot e^{-\lambda t}$$

### Входы
```
W₀   — начальный вес
λ    — скорость затухания
t    — время
```

### Выход
```
W(t) ∈ [0, W₀] — текущий вес
```

### ДЕЙСТВИЕ: Рассчитать "силу" воспоминания

### ПСЕВДОКОД
```python
def memory_strength(
    initial_weight: float,
    decay_rate: float,
    time_elapsed: float
) -> float:
    """
    W(t) = W₀ × e^{-λt}
    """
    return initial_weight * np.exp(-decay_rate * time_elapsed)


class MemoryItem:
    def __init__(self, content, strength: float = 1.0):
        self.content = content
        self.strength = strength
        self.created_at = time.time()
        self.last_accessed = time.time()
    
    def get_current_strength(self) -> float:
        """Получить текущую силу с учётом затухания"""
        elapsed = time.time() - self.last_accessed
        return memory_strength(1.0, self.strength, elapsed)
    
    def reinforce(self, amount: float = 0.1):
        """Усилить воспоминание"""
        self.strength = min(1.0, self.strength + amount)
        self.last_accessed = time.time()


class DecayingMemory:
    def __init__(self, decay_rate: float = 0.01):
        self.decay_rate = decay_rate
        self.items = []
    
    def add(self, item: MemoryItem):
        self.items.append(item)
    
    def get_active_memories(self, threshold: float = 0.1) -> List[MemoryItem]:
        """Получить воспоминания выше порога"""
        return [
            item for item in self.items
            if item.get_current_strength() > threshold
        ]
    
    def prune(self, threshold: float = 0.01):
        """Удалить слабые воспоминания"""
        self.items = self.get_active_memories(threshold)
```

---

## 10.2 Memory Priority — Приоритет памяти

### Область: Memory Systems

### Формула
$$I = w_1 \cdot \text{Recency}(t) + w_2 \cdot \text{Importance} + w_3 \cdot \text{Relevance}(q, k)$$

### Входы
```
Recency(t) — новизна (1 если недавно)
Importance  — важность события
Relevance   — релевантность к запросу
w₁, w₂, w₃ — веса
```

### Выход
```
I ∈ [0, 1] — приоритет для recall
```

### ДЕЙСТВИЕ: Определить что вспомнить

### ПСЕВДОКОД
```python
def compute_memory_priority(
    memory: MemoryItem,
    current_time: float,
    query: np.array = None,
    weights: Tuple[float, float, float] = (0.3, 0.3, 0.4)
) -> float:
    """
    I = w₁×Recency + w₂×Importance + w₃×Relevance
    """
    w1, w2, w3 = weights
    
    # Recency: экспоненциальное затухание
    time_since_access = current_time - memory.last_accessed
    recency = np.exp(-0.1 * time_since_access)  # Чем больше время, тем меньше
    
    # Importance: из самого воспоминания
    importance = memory.importance
    
    # Relevance: если есть запрос
    if query is not None and hasattr(memory, 'embedding'):
        relevance = cosine_similarity(query, memory.embedding)
    else:
        relevance = 0.5  # Default
    
    return w1 * recency + w2 * importance + w3 * relevance


def prioritize_memories(
    memories: List[MemoryItem],
    query: np.array = None,
    top_k: int = 10
) -> List[MemoryItem]:
    """Выбрать top-k приоритетных воспоминаний"""
    current_time = time.time()
    
    scored = [
        (memory, compute_memory_priority(memory, current_time, query))
        for memory in memories
    ]
    
    scored.sort(key=lambda x: x[1], reverse=True)
    
    return [m for m, _ in scored[:top_k]]
```

---

## 10.3 InfoNCE Loss — Contrastive Loss

### Область: Representation Learning

### Формула
$$\mathcal{L}_{\text{InfoNCE}} = -\log \frac{\exp(\text{sim}(q, k_+) / \tau)}{\exp(\text{sim}(q, k_+) / \tau) + \sum_i \exp(\text{sim}(q, k_i^-) / \tau)}$$

### Входы
```
q    — query embedding
k₊   — positive key
kᵢ⁻  — negative keys
τ    — temperature
```

### Выход
```
L — contrastive loss
```

### ДЕЙСТВИЕ: Contrastive learning для эмбеддингов

### ПСЕВДОКОД
```python
def info_nce_loss(
    query: np.array,
    positive_key: np.array,
    negative_keys: List[np.array],
    temperature: float = 0.07
) -> float:
    """
    L = -log exp(sim(q,k₊)/τ) / (exp(sim(q,k₊)/τ) + Σ exp(sim(q,kᵢ⁻)/τ))
    """
    # Positive similarity
    pos_sim = cosine_similarity(query, positive_key) / temperature
    
    # Negative similarities
    neg_sims = [
        cosine_similarity(query, neg) / temperature
        for neg in negative_keys
    ]
    
    # Log-softmax
    pos_exp = np.exp(pos_sim)
    neg_exp_sum = sum(np.exp(ns) for ns in neg_sims)
    
    loss = -pos_sim + np.log(pos_exp + neg_exp_sum)
    
    return loss


class ContrastiveLearner:
    def __init__(self, temperature: float = 0.07):
        self.temperature = temperature
        self.embedding_model = ...
    
    def contrastive_update(
        self,
        anchors: np.array,
        positives: np.array,
        negatives: np.array
    ) -> float:
        """
        Обновить модель на основе contrastive loss
        """
        total_loss = 0.0
        
        for anchor, pos, negs in zip(anchors, positives, negatives):
            anchor_emb = self.embedding_model(anchor)
            pos_emb = self.embedding_model(pos)
            neg_embs = [self.embedding_model(n) for n in negs]
            
            loss = info_nce_loss(
                anchor_emb, pos_emb, neg_embs, self.temperature
            )
            total_loss += loss
        
        # Backpropagation
        total_loss.backward()
        
        return total_loss.item()
```

---

# ЧАСТЬ 11: КАЛМАН И ФИЛЬТРАЦИЯ

---

## 11.1 Kalman Filter Update — Обновление фильтра Калмана

### Область: State Estimation

### Формула
$$\hat{H}_{t|t} = \hat{H}_{t|t-1} + K_t (z_t - C_t \hat{H}_{t|t-1})$$

### Входы
```
Ĥ_{t|t-1} — предсказанное состояние
zₜ        — наблюдение
Cₜ        — матрица наблюдения
Kₜ        — коэффициент усиления Калмана
```

### Выход
```
Ĥ_{t|t} — обновлённая оценка состояния
```

### ДЕЙСТВИЕ: Фильтровать шумные наблюдения

### ПСЕВДОКОД
```python
class KalmanFilter:
    def __init__(
        self,
        state_dim: int,
        obs_dim: int,
        A: np.array,  # Transition matrix
        B: np.array,  # Control matrix
        C: np.array,  # Observation matrix
        Q: np.array,  # Process noise
        R: np.array   # Measurement noise
    ):
        self.A = A
        self.B = B
        self.C = C
        self.Q = Q
        self.R = R
        
        self.state = np.zeros(state_dim)
        self.P = np.eye(state_dim)  # Error covariance
    
    def predict(self, u: np.array = None) -> np.array:
        """Предсказание"""
        if u is not None:
            self.state = self.A @ self.state + self.B @ u
        else:
            self.state = self.A @ self.state
        
        self.P = self.A @ self.P @ self.A.T + self.Q
        return self.state
    
    def update(self, z: np.array) -> np.array:
        """
        Ĥ_{t|t} = Ĥ_{t|t-1} + Kₜ(zₜ - CₜĤ_{t|t-1})
        """
        # Innovation (ошибка предсказания)
        y = z - self.C @ self.state
        
        # Kalman gain
        S = self.C @ self.P @ self.C.T + self.R
        K = self.P @ self.C.T @ np.linalg.inv(S)
        
        # Update state
        self.state = self.state + K @ y
        
        # Update covariance
        I = np.eye(len(self.state))
        self.P = (I - K @ self.C) @ self.P
        
        return self.state


# Пример: фильтрация оценки прибыльности
def filter_profitability_estimate(
    kf: KalmanFilter,
    raw_estimate: float,
    measurement_uncertainty: float
) -> float:
    """
    Фильтрация шумных оценок агента
    """
    # Создаём pseudo-measurement
    kf.R[0, 0] = measurement_uncertainty ** 2
    
    return kf.update(np.array([raw_estimate]))[0]
```

---

## 11.2 EWC Regularization — Защита от забывания

### Область: Continual Learning

### Формула
$$\mathcal{L}(\theta) = \mathcal{L}_{\text{new}}(\theta) + \sum_i \frac{\lambda}{2} F_i (\theta_i - \theta_{i,\text{old}})^2$$

### Входы
```
L_new  — loss на новой задаче
θ      — текущие параметры
θ_old  — параметры после предыдущей задачи
Fᵢ     — Fisher information
λ      — сила regularization
```

### Выход
```
L — total loss с regularization
```

### ДЕЙСТВИЕ: Обучаться без катастрофического забывания

### ПСЕВДОКОД
```python
class EWCAgent:
    def __init__(self, lambda_ewc: float = 1000):
        self.lambda_ewc = lambda_ewc
        self.optimal_params = {}  # θ* для каждой задачи
        self.fisher_info = {}      # Fᵢ для каждой задачи
    
    def compute_fisher_information(
        self,
        model: nn.Module,
        data: List,
        n_samples: int = 100
    ) -> np.array:
        """
        Вычисление Fisher Information Matrix
        """
        model.eval()
        fisher = {name: torch.zeros_like(param) 
                   for name, param in model.named_parameters()}
        
        for _ in range(n_samples):
            sample = random.choice(data)
            
            model.zero_grad()
            output = model(sample.input)
            loss = model.loss(output, sample.target)
            loss.backward()
            
            for name, param in model.named_parameters():
                if param.grad is not None:
                    fisher[name] += param.grad.data ** 2
        
        # Normalize
        for name in fisher:
            fisher[name] /= n_samples
        
        return fisher
    
    def ewc_loss(
        self,
        new_loss: float,
        model: nn.Module,
        task_id: int
    ) -> float:
        """
        L = L_new + Σ λ/2 × Fᵢ × (θᵢ - θ*ᵢ)²
        """
        total_loss = new_loss
        
        for name, param in model.named_parameters():
            if name in self.optimal_params:
                # Параметр участвовал в предыдущих задачах
                fisher = self.fisher_info[name]
                optimal = self.optimal_params[name]
                
                penalty = 0.5 * self.lambda_ewc * torch.sum(
                    fisher * (param - optimal) ** 2
                )
                total_loss = total_loss + penalty
        
        return total_loss
    
    def after_task(self, model: nn.Module, task_id: int):
        """Сохранить параметры и Fisher после задачи"""
        self.optimal_params = {
            name: param.clone().detach()
            for name, param in model.named_parameters()
        }
        self.fisher_info = self.compute_fisher_information(
            model, self.get_task_data(task_id)
        )
```

---

# ЧАСТЬ 12: СПЕЦИАЛИЗИРОВАННЫЕ СИСТЕМЫ

---

## 12.1 BioBlue U-Function — U-функция

### Область: BioBlue

### Формула
$$D(h_i) = \frac{1}{2} \cdot \left( \frac{h_i - h_i^*}{\sigma_i} \right)^2$$

### Входы
```
hᵢ    — текущее значение переменной
h*ᵢ   — оптимальное значение
σᵢ    — допустимое отклонение
```

### Выход
```
D(hᵢ) ∈ [0, ∞) — отклонение от оптимума
```

### ДЕЙСТВИЕ: Измерить отклонение переменной

### ПСЕВДОКОД
```python
def compute_u_function(
    current: float,
    target: float,
    tolerance: float
) -> float:
    """
    D(hᵢ) = 1/2 × ((hᵢ - h*ᵢ)/σᵢ)²
    """
    deviation = current - target
    return 0.5 * (deviation / tolerance) ** 2


def compute_total_homeostatic_deviation(
    current_state: dict,
    target_state: dict,
    tolerances: dict
) -> float:
    """Суммарное отклонение по всем переменным"""
    total = 0.0
    for key in target_state:
        if key in current_state and key in tolerances:
            total += compute_u_function(
                current_state[key],
                target_state[key],
                tolerances[key]
            )
    return total
```

---

## 12.2 Metabolic Budget — Метаболический бюджет

### Область: Genesis

### Формула
$$M_t = M_{t-1} - \left( w_1 \cdot \frac{\text{Tokens}_{\text{used}}}{\text{Context}_{\text{max}}} + w_2 \cdot \text{ExecutionTime}_{\text{sec}} \right)$$

### Входы
```
Tokens_used       — использованные токены
Context_max       — максимальный контекст
ExecutionTime_sec — время выполнения
w₁, w₂            — веса
```

### Выход
```
Mₜ ∈ (-∞, M₀) — оставшийся бюджет
```

### ДЕЙСТВИЕ: Отслеживать consumption ресурсов

### ПСЕВДОКОД
```python
class MetabolicBudget:
    def __init__(
        self,
        initial_budget: float = 1.0,
        w1: float = 0.6,
        w2: float = 0.4
    ):
        self.budget = initial_budget
        self.w1 = w1
        self.w2 = w2
        self.history = []
    
    def consume(
        self,
        tokens_used: int,
        context_max: int,
        execution_time: float
    ) -> float:
        """
        Mₜ = M_{t-1} - (w₁ × Tokens_used/Context_max + w₂ × ExecutionTime)
        """
        token_consumption = self.w1 * (tokens_used / context_max)
        time_consumption = self.w2 * execution_time / 60  # Нормализуем к минутам
        
        consumption = token_consumption + time_consumption
        self.budget -= consumption
        
        self.history.append({
            'tokens': tokens_used,
            'time': execution_time,
            'remaining': self.budget
        })
        
        return self.budget
    
    def is_depleted(self, threshold: float = 0.1) -> bool:
        """Проверка исчерпания бюджета"""
        return self.budget < threshold
    
    def reset(self):
        """Сброс бюджета для нового цикла"""
        self.budget = 1.0
        self.history = []
```

---

## 12.3 Cognitive Budget — Когнитивный бюджет

### Область: Genesis

### Формула
$$B_t = \max\left(0, \frac{\text{Budget}_{\text{remaining}}}{\text{Budget}_{\text{allocated}}} \right)$$

### Входы
```
Budget_remaining — оставшийся бюджет
Budget_allocated — выделенный бюджет
```

### Выход
```
Bₜ ∈ [0, 1] — нормализованный когнитивный бюджет
```

### ДЕЙСТВИЕ: Оценить доступность когнитивных ресурсов

### ПСЕВДОКОД
```python
def compute_cognitive_budget(
    remaining: float,
    allocated: float
) -> float:
    """
    Bₜ = max(0, Budget_remaining / Budget_allocated)
    """
    if allocated <= 0:
        return 0.0
    
    budget = remaining / allocated
    return max(0.0, budget)


class CognitiveBudgetManager:
    def __init__(self, total_budget: float = 100.0):
        self.total = total_budget
        self.allocated = {}
        self.remaining = {}
    
    def allocate(self, task_id: str, amount: float) -> bool:
        """Выделить бюджет задаче"""
        if amount > self.get_available():
            return False
        
        self.allocated[task_id] = amount
        self.remaining[task_id] = amount
        return True
    
    def spend(self, task_id: str, amount: float) -> float:
        """Потратить часть бюджета"""
        if task_id not in self.remaining:
            return 0.0
        
        spent = min(amount, self.remaining[task_id])
        self.remaining[task_id] -= spent
        return spent
    
    def get_available(self) -> float:
        """Доступный бюджет"""
        allocated_sum = sum(self.allocated.values())
        return max(0, self.total - allocated_sum)
    
    def get_utilization(self, task_id: str) -> float:
        """Использование бюджета задачи"""
        if task_id not in self.allocated:
            return 0.0
        
        return compute_cognitive_budget(
            self.remaining[task_id],
            self.allocated[task_id]
        )
```

---

## 12.4 Stability Coherence — Стабильность контекста

### Область: Genesis

### Формула
$$C_t = 1.0 - \frac{\text{Current\_KV\_Cache\_Size}}{\text{Max\_Allowed\_Context}}$$

### Входы
```
Current_KV_Cache_Size — заполненность контекста
Max_Allowed_Context   — максимальный размер
```

### Выход
```
Cₜ ∈ [0, 1] — стабильность (больше = лучше)
```

### ДЕЙСТВИЕ: Оценить стабильность контекста

### ПСЕВДОКОД
```python
def compute_stability(
    current_cache_size: int,
    max_context: int
) -> float:
    """
    Cₜ = 1 - Current_KV / Max_Allowed
    """
    if max_context == 0:
        return 0.0
    
    return 1.0 - (current_cache_size / max_context)


def should_compress_context(
    current_tokens: int,
    max_tokens: int,
    threshold: float = 0.8
) -> bool:
    """
    Решить когда сжимать контекст
    """
    utilization = current_tokens / max_tokens
    return utilization > threshold


class ContextStabilityMonitor:
    def __init__(self, max_context: int):
        self.max_context = max_context
        self.stability_history = []
    
    def record(self, cache_size: int):
        """Записать стабильность"""
        stability = compute_stability(cache_size, self.max_context)
        self.stability_history.append(stability)
    
    def average_stability(self, window: int = 10) -> float:
        """Средняя стабильность за окно"""
        if not self.stability_history:
            return 1.0
        
        recent = self.stability_history[-window:]
        return sum(recent) / len(recent)
    
    def is_unstable(self, threshold: float = 0.3) -> bool:
        """Проверка нестабильности"""
        return self.average_stability() < threshold
```

---

# СВОДНАЯ ТАБЛИЦА: КИБЕРНЕТИЧЕСКИЕ ФОРМУЛЫ → ДЕЙСТВИЯ

| ID | Формула | Область | ДЕЙСТВИЕ | Правило |
|----|---------|---------|----------|---------|
| 1 | ẋ = f(x, u, d) | Wiener | Update state | Всегда |
| 2 | e(t) = r(t) - y(t) | Feedback | Compute error | Всегда |
| 3 | u(t) = Kp × e(t) | Control | Apply control | P-control |
| 4 | u(t) = Kp×e + Ki×∫e + Kd×de/dt | PID | Full PID control | PID-control |
| 5 | H = -Σ p(xᵢ)log₂p(xᵢ) | Shannon | Measure entropy | Управление неопределённостью |
| 6 | xₒ(I) ≈ const | Golubitsky | Maintain setpoint | При отклонении |
| 7 | V̇(x) ≤ 0 | Lyapunov | Check stability | V̇ ≤ 0 → stable |
| 8 | D(H) = Σ |h* - h|^p | Allostasis | Compute drive | High D → high priority |
| 9 | Rₜ = D(Hₜ) - D(Hₜ₊₁) | RL | Compute reward | Drive reduction |
| 10 | V^π(s) = Σₐπ(a\|s)Σₛ'P... | Bellman | Evaluate state | V > threshold |
| 11 | Q^π(s,a) = Σₛ'P(R+γV) | Bellman | Evaluate action | max Q → best action |
| 12 | Q ← Q + α(r + γmaxQ' - Q) | RL | Update Q-value | TD learning |
| 13 | ∇J = E[Σ∇log π(a\|s)G] | RL | Policy gradient | Policy update |
| 14 | F = D_KL[q\|\|p] - log p(x) | Friston | Free energy | Minimize F |
| 15 | π* = argmin F(μ, π) | Friston | Optimal policy | Minimize free energy |
| 16 | μ̇ = D_μ × ∂F/∂μ | Friston | Update beliefs | Bayesian update |
| 17 | c_{t+1} = f_θ(cₜ, aₜ, oₜ) | Agent | Update context | All steps |
| 18 | aₜ ~ π_θ(\|cₜ) | Agent | Sample action | Policy-based |
| 19 | J(θ) = E[Σ γᵗR] | Agent | Agent objective | Maximize J |
| 20 | lim\|\|xᵢ-xⱼ\|\| = 0 | Consensus | Check consensus | Distance < ε |
| 21 | ẋᵢ = Σ aᵢⱼ(xⱼ-xᵢ) | Multi-Agent | Move to consensus | Agent update |
| 22 | ẘᵢⱼ = ηxᵢxⱼ - λwᵢⱼ | Hebb | Learn association | Hebbian update |
| 23 | fₜ = σ(Wf·[hₜ₋₁,xₜ]+bf) | LSTM | Forget gate | fₜ > 0.5 → forget |
| 24 | J = ∫(xᵀQx + uᵀRu)dt | LQR | Compute cost | Minimize J |
| 25 | AᵀP + PA - PBR⁻¹BᵀP + Q = 0 | Riccati | Solve LQR | Optimal K |
| 26 | P_ucb = V/n + c√(lnN/n) | MCTS | UCB exploration | Max UCB → select |
| 27 | Sim(q,k) = q·k/(\|\|q\|\|\|\|k\|\|) | IR | Compute similarity | Cosine similarity |
| 28 | Attn(Q,K,V) = softmax(QKᵀ/√d)V | Transformer | Attention | Weighted sum |
| 29 | Score(D,Q) = Σ IDF × ... | BM25 | Rank documents | Higher score |
| 30 | W(t) = W₀e^{-λt} | Memory | Memory decay | Exponential decay |
| 31 | I = w₁Recency + w₂Imp + w₃Rel | Memory | Memory priority | Higher I → recall |
| 32 | L = -log exp(sim)/Z | InfoNCE | Contrastive loss | Minimize L |
| 33 | Ĥₜₜ = Ĥₜₜ₋₁ + K(zₜ - CĤₜₜ₋₁) | Kalman | Filter estimate | Bayesian update |
| 34 | L = L_new + Σ λ/2 F(θ-θ*)² | EWC | Continual learning | No forgetting |
| 35 | D(h) = 1/2((h-h*)/σ)² | BioBlue | U-function | Deviation measure |
| 36 | Mₜ = Mₜ₋₁ - (w₁T/C + w₂T) | Genesis | Metabolic budget | M > threshold |
| 37 | Bₜ = Budget_remain/alloc | Genesis | Cognitive budget | B ∈ [0,1] |
| 38 | Cₜ = 1 - KV/Max | Genesis | Stability | C > threshold |

---

*Документ создан: 2026-07-08*
*Версия: 1.0*
*Статус: Кибернетический маппинг готов*
