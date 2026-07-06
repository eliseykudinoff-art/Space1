# 🧬 Унифицированная модель AI-агента: 17 факторов × 6 функций решения

## Обзор

Этот документ интегрирует:
1. **17 факторов** из `capability.txt` (ROI, коэффициенты, синергии)
2. **6 функций решения** из `atomic_decomposition_model.md` (δ, f*, c*, m*, p*, φ)

> ⚠️ **Примечание:** Изначально в математической модели было только 11 факторов. 
> Анализ выявил **6 пропущенных факторов** (x₁₂-x₁₇), которые теперь добавлены.

---

## 📊 Карта соответствия факторов и функций

| Фактор (xᵢ) | Название | Функция нашей модели | Статус |
|-------------|---------|---------------------|--------|
| x₁ | LLM Capability | m* (выбор модели) | ✅ |
| x₂ | Tool Calling | ActionType | ✅ |
| x₃ | MCP Integration | Plugin system | 📋 |
| x₄ | Memory | Context | ✅ |
| x₅ | Multi-Agent | Orchestration | ✅ |
| x₆ | Self-Correction | Validation loop | ✅ |
| x₇ | Prompt Engineering | PromptSelector | ✅ |
| x₈ | Cost Tiering | ModelTier | ✅ |
| x₉ | Grounding | RAG retrieval | ✅ |
| x₁₀ | Fine-tuning | Specialized models | 📋 |
| x₁₁ | Browser Automation | External actions | ✅ |
| **x₁₂** | **Guardrails** | **Safety validation** | **❌ NEW** |
| **x₁₃** | **Test-Time Compute** | **Reasoning loop** | **❌ NEW** |
| **x₁₄** | **Design Patterns** | **Strategy selection** | **❌ NEW** |
| **x₁₅** | **Evaluation** | **Benchmark tracking** | **❌ NEW** |
| **x₁₆** | **Continual Learning** | **Knowledge base** | **❌ NEW** |
| **x₁₇** | **Inference Opt** | **Optimization layer** | **❌ NEW** |

---

## 🔗 Матрица синергий

Из документа capability.txt:

| Пара факторов | Δγ (эффект) | Влияние на |
|--------------|-------------|-----------|
| x₁ + x₇ | +0.08 | m* (лучший промт = дешевле модель) |
| x₂ + x₉ | +0.12 | ActionType (Grounding улучшает tools) |
| x₅ + x₆ | +0.15 | Orchestration (агенты исправляют друг друга) |
| x₁ + x₈ | — | m* (Cost tiering определяет модель) |

### Формула синергии

$$\gamma_{syn} = \sum_{(i,j) \in synergies} \Delta\gamma_{ij} \cdot x_i \cdot x_j$$

где $x_i \in \{0, 1\}$ для бинарных факторов.

### Полная матрица синергий (11 + 6 новых)

| Пара | Δγ | Механизм | Новый? |
|------|-----|----------|--------|
| x₁ + x₇ | +0.08 | Улучшенный промпт компенсирует слабую модель | — |
| x₂ + x₉ | +0.12 | Grounding делает tool calls точнее | — |
| x₅ + x₆ | +0.15 | Multi-agent + Self-correction | — |
| x₁ + x₁₀ | +0.05 | Fine-tuning усиливает базовую модель | — |
| **x₆ + x₁₄** | **+0.15** | Self-correction + Reflection | ✅ |
| **x₄ + x₁₆** | **+0.10** | Memory + Continual Learning | ✅ |
| **x₂ + x₁₂** | **+0.08** | Tool Calling + Guardrails | ✅ |
| **x₁ + x₁₃** | **+0.12** | LLM + Reasoning (test-time) | ✅ |
| **x₁₇ + x₈** | **+0.06** | Inference Opt + Cost tiering | ✅ |

---

## 📐 Расширенная целевая функция

### Текущая (из atomic_decomposition_model.md):

$$D^*(T) = \arg\max_D [\mathcal{U}(D) - \lambda \cdot \mathcal{C}(D)]$$

### Расширенная (с синергиями):

$$\boxed{D^*(T) = \arg\max_D \left[ \mathcal{U}(D) + \gamma_{syn} \cdot \Phi_R(D) - \lambda \cdot \mathcal{C}(D) \right]}$$

где:
- $\mathcal{U}(D)$ — базовая утилита
- $\gamma_{syn}$ — бонус от синергий
- $\Phi_R(D)$ — риск-взвешенная прибыль
- $\mathcal{C}(D)$ — стоимость

---

## 🎯 Реализация: Что добавить

### 1. Grounding Module (x₉)

```python
class GroundingModule:
    """Retrieval-Augmented Generation для фактических знаний"""
    
    def ground(self, action: AtomicAction) -> Context:
        """
        RAG-style retrieval для уменьшения hallucination
        
        Формула: Score(c) = Relevance(a, c) - λ · Cost(c)
        """
        # 1. Embed action description
        query_emb = embed(action.description)
        
        # 2. Retrieve top-k relevant docs
        candidates = self.vector_db.search(query_emb, k=5)
        
        # 3. Filter by relevance threshold
        grounded = [c for c in candidates if c.score > 0.7]
        
        # 4. Return as context
        return Context(documents=grounded)
```

**ROI из документа:** Наивысший для сложных задач

### 2. Fine-tuning Evaluator (x₁₀)

```python
class FineTuningEvaluator:
    """Оценка целесообразности fine-tuning"""
    
    def should_finetune(self, task_pattern: str, n_monthly: int) -> bool:
        """
        Окупается при n_monthly > 500 (из документа)
        
        Формула: E[improvement] · n_monthly > C_finetune
        """
        C_ft = 5000  # Примерная стоимость fine-tuning
        improvement = 0.15  # Ожидаемый прирост качества
        
        roi = (improvement * n_monthly) / C_ft
        return roi > 1.0
```

### 3. ROI-based Tool Selection (x₁₁)

```python
def select_tools_roi(
    available_tools: Dict, 
    task_emb: np.ndarray,
    budget: float
) -> List[str]:
    """
    ROI = ΔS / Cost = (β · relevance · (1 - risk)) / cost
    
    Жадный выбор по убыванию ROI
    """
    tool_roi = []
    for tool_id, params in available_tools.items():
        relevance = cosine_similarity(task_emb, params.embedding)
        delta_s = params.beta * relevance * (1 - params.risk)
        roi = delta_s / params.cost
        tool_roi.append((tool_id, roi))
    
    # Сортировка и выбор
    tool_roi.sort(key=lambda x: x[1], reverse=True)
    
    selected = []
    total_cost = 0.0
    for tool_id, roi in tool_roi:
        cost = available_tools[tool_id].cost
        if total_cost + cost <= budget:
            selected.append(tool_id)
            total_cost += cost
    
    return selected
```

---

## 📋 Roadmap интеграции

### Фаза 1: Быстрые улучшения (1-2 дня)

| Задача | Фактор | effort |
|--------|--------|--------|
| Добавить синергии в метрики | x₁+x₇, x₂+x₉, x₅+x₆ | 2h |
| Улучшить ROI tool selection | x₁₁ | 4h |
| Добавить validation с self-correction | x₆ | 4h |

### Фаза 2: Средние изменения (1-2 недели)

| Задача | Фактор | effort |
|--------|--------|--------|
| Grounding module (RAG) | x₉ | 2d |
| Cost tiering refinement | x₈ | 1d |
| Memory persistence improvements | x₄ | 2d |

### Фаза 3: Большие изменения (1-2 месяца)

| Задача | Фактор | effort |
|--------|--------|--------|
| Fine-tuning evaluator | x₁₀ | 1w |
| Multi-agent orchestration | x₅ | 2w |
| Simulation environment | All | 2w |

---

## 🆕 Новые факторы (ранее пропущенные)

> Подробная формализация 6 пропущенных факторов из 17 доступных.

### x₁₂: Guardrails & Safety

**Формула снижения риска:**

$$C_{risk}(x) = \sum_{j} P_j \cdot L_j \cdot (1 - R_{guardrails,j})$$

```python
class GuardrailsValidator:
    def validate(self, action: AtomicAction) -> ValidationResult:
        risks = {
            "financial": self.check_financial_limits(action),
            "security": self.check_security(action),
            "destructive": self.check_destructive(action),
        }
        
        total_risk = sum(r * w for r, w in risks.items())
        
        if total_risk > self.threshold:
            return ValidationResult(
                approved=False,
                reason=f"Risk level {total_risk} exceeds {self.threshold}",
                mitigation=self.suggest_safer_alternative(action)
            )
        
        return ValidationResult(approved=True, risk_level=total_risk)
```

**Синергия:** $x_{12} + x_2$ (Guardrails усиливают безопасность tool calls)

---

### x₁₃: Test-Time Compute (Reasoning)

**Влияние на Success Rate:**

$$S_{reason} = S(x) + \beta_{reason} \cdot \log(1 + \frac{T_{think}}{T_{base}})$$

**Time penalty:**

$$T_{reason} = T(x) \cdot (1 + 0.25 \cdot \frac{T_{think}}{T_{base}})$$

```python
class ReasoningLoop:
    def __init__(self, base_agent):
        self.agent = base_agent
        self.max_think_ratio = 0.5  # max 50% time на рассуждения
    
    def execute_with_reasoning(self, task: Task) -> Result:
        thoughts = []
        for attempt in range(self.max_attempts):
            # Chain-of-thought
            reasoning = self.agent.think(task, context=thoughts)
            thoughts.append(reasoning)
            
            # Action
            result = self.agent.act(task, reasoning)
            
            # Verification
            if self.verify(result, task):
                return result
        
        return result  # Return best effort
```

---

### x₁₄: Agentic Design Patterns

**Supported patterns:**

| Паттерн | α_p | Применение |
|---------|-----|------------|
| ReAct | +0.08 | Exploration, ambiguous tasks |
| Reflection | +0.12 | Quality-critical outputs |
| Planning | +0.15 | Complex multi-step tasks |

```python
class PatternSelector:
    PATTERNS = {
        "react": ReActPattern(),
        "reflection": ReflectionPattern(),
        "planning": PlanningPattern(),
    }
    
    def select(self, task: Task) -> Pattern:
        complexity = self.estimate_complexity(task)
        ambiguity = self.estimate_ambiguity(task)
        
        if complexity > 0.8:
            return self.PATTERNS["planning"]
        elif task.quality_critical:
            return self.PATTERNS["reflection"]
        elif ambiguity > 0.5:
            return self.PATTERNS["react"]
        else:
            return None  # No pattern overhead
```

**Синергия:** $x_{14} + x_6$ (Patterns усиливают self-correction)

---

### x₁₅: Evaluation & Benchmarking

**Calibration:**

$$\hat{S}(x) = 0.7 \cdot S_{measured} + 0.3 \cdot S_{predicted}$$

```python
class BenchmarkEvaluator:
    BENCHMARKS = {
        "GAIA": 0.745,      # General AI assistant
        "SWE-bench": 0.15,  # Software engineering
        "WebArena": 0.80,   # Web interaction
        "RLI": 0.025,       # Real freelance tasks
        "ARC-AGI": 0.30,    # Generalization
    }
    
    def calibrate(self, measured_success: float, benchmark: str) -> float:
        alpha = 0.7  # Weight on measured
        expected = self.BENCHMARKS.get(benchmark, 0.5)
        return alpha * measured_success + (1 - alpha) * expected
    
    def track_improvement(self) -> Dict:
        return {
            "success_rate_trend": self.calc_trend(self.history),
            "cost_efficiency_trend": self.calc_trend(self.cost_history),
            "recommended_next_factor": self.suggest_next_optimization(),
        }
```

---

### x₁₆: Continual Learning

**Knowledge accumulation:**

$$K(t) = K_0 + \eta_{learn} \cdot \sum_{\tau < t} \Delta K(\tau) \cdot (1 - \frac{K(\tau)}{K_{max}})$$

**Forgetting factor:**

$$S_{cl}(x) = S(x) \cdot (1 - 0.05 \cdot e^{-0.1 \cdot days})$$

```python
class ContinualLearning:
    def __init__(self, memory: AgentMemory):
        self.memory = memory
        self.knowledge_base = {}
        self.forgetting_rate = 0.05
    
    def learn(self, task: Task, result: Result, approach: str):
        task_type = self.classify(task)
        
        if result.success:
            self.memory.add_successful_pattern(task_type, approach)
            self.knowledge_base[task_type] = {
                "approach": approach,
                "success_rate": self.get_success_rate(task_type),
                "last_used": datetime.now(),
            }
        else:
            self.memory.add_failed_pattern(task_type, approach)
    
    def get_adaptive_success_rate(self, base_rate: float, days_since_update: float) -> float:
        decay = self.forgetting_rate * math.exp(-0.1 * days_since_update)
        return base_rate * (1 - decay)
    
    def suggest_approach(self, task: Task) -> Optional[str]:
        similar = self.find_similar_tasks(task)
        if not similar:
            return None
        
        # Transfer learning
        for past_task, approach in similar:
            if past_task.success:
                similarity = self.cosine_sim(task.embedding, past_task.embedding)
                if similarity > 0.7:
                    return approach
        
        return None
```

---

### x₁₇: Inference Optimization

**Speedup factors:**

| Оптимизация | δ_o | Примечание |
|------------|-----|-----------|
| Caching | 0.10 | 10% latency reduction |
| Quantization INT8 | 0.20 | |
| Flash Attention | 0.15 | |
| Speculative Decoding | 0.30 | |
| Batch Processing | 0.25 | |

**Combined speedup:**

$$T_{opt} = T(x) \cdot \prod_{o} (1 - \delta_o)$$

```python
class InferenceOptimizer:
    def __init__(self):
        self.optimizations = {
            "cache": CacheOptimizer(),
            "quantization": QuantizationOptimizer(bits=8),
            "flash_attention": FlashAttention(),
            "speculative": SpeculativeDecoding(),
            "batch": BatchProcessor(),
        }
    
    def apply_all(self, agent: Agent) -> Agent:
        total_speedup = 1.0
        for opt_name, opt in self.optimizations.items():
            if opt.is_applicable(agent):
                agent = opt.apply(agent)
                total_speedup *= (1 - opt.speedup_factor)
        
        print(f"Total speedup: {1/total_speedup:.2f}x")
        return agent
    
    def calculate_cost_savings(self, original_cost: float) -> float:
        # Кэширование: 75% токенов за 10% цены
        cache_savings = 0.65 * 0.90  # 65% cached, 90% cost
        
        # Квантизация: ~50% cost reduction
        quant_savings = 0.50
        
        return original_cost * (1 - cache_savings) * (1 - quant_savings)
```

---

## 📊 Сводка новых факторов

| ID | Фактор | β (на S) | δ (на T) | Priority | Implementation |
|----|--------|----------|----------|----------|----------------|
| x₁₂ | Guardrails | +0.05 | +0.02 | **HIGH** | Safety validator |
| x₁₃ | Test-Time Compute | +0.18 | +0.25 | Medium | Reasoning loop |
| x₁₄ | Design Patterns | +0.10 | -0.05 | Medium | Pattern selector |
| x₁₅ | Evaluation | +0.08 | +0.03 | Low | Benchmark tracker |
| x₁₆ | Continual Learning | +0.12 | -0.10 | Medium | Knowledge base |
| x₁₇ | Inference Opt | 0 | -0.20 | **HIGH** | Optimization layer |

---

*Документ обновлён: 2026-07-05*
*Добавлено: 6 пропущенных факторов (x₁₂-x₁₇)*

## 📊 Таблица коэффициентов (из capability.txt)

| Индекс | Фактор | α (влияние на S) | Оптимум |备注|
|--------|--------|------------------|---------|----|
| x₁ | LLM Capability | α₁ · C_llm | Зависит от задачи | Сигмоида |
| x₂ | Tool Calling | +0.20 | Binary | Критичен |
| x₃ | MCP | +0.05 | Binary | Стандартизация |
| x₄ | Memory | β₁M + β₂M² | Максимум | Ключевой |
| x₅ | Multi-Agent | α·log(N) | 4-8 | Спад после 8 |
| x₆ | Self-Correction | β₁L + β₂L² | ~3 | >3 = negative ROI |
| x₇ | Prompting | β₁Q + β₂Q² | ~0.8 | 10x improvement |
| x₈ | Cost Tiering | θ* ≈ 0.55 | Tiers | 77% экономия |
| x₉ | Grounding | β·d | d > 0.5 | Highest ROI |
| x₁₀ | Fine-tuning | β·(1-e^(-λN)) | N > 500/mo | Amortized |
| x₁₁ | External Tools | ΣβₖTₖ | ROI greedy | 6.5x ROI |

---

## 🔧 Код: Интеграция в AtomicDecomposer

```python
# Расширение AtomicDecomposer
class AtomicDecomposer:
    def __init__(self):
        self.prompt_selector = PromptSelector()  # x₇
        self.context_manager = ContextManager()  # x₄
        self.grounding = GroundingModule()       # x₉ (NEW)
        self.tool_roi = ToolROISelector()        # x₁₁ (NEW)
        
        # Синергии
        self.synergies = {
            ('x1', 'x7'): 0.08,
            ('x2', 'x9'): 0.12,
            ('x5', 'x6'): 0.15,
        }
    
    def decompose(self, task: str, context: Context = None) -> DecompositionResult:
        # 1. δ(T) - решение о декомпозиции
        need_decompose = self.decisions.need_decompose(task)
        
        # 2. Генерация действий
        actions = self.pipeline.generate_actions(task)
        
        # 3. Для каждого действия:
        for action in actions:
            # Grounding (x₉)
            action.context = self.grounding.ground(action)
            
            # m* - выбор модели (x₁, x₈)
            action.model = self.decisions.choose_model(action)
            
            # f* - формат (x₂)
            action.output_format = self.decisions.choose_format(action.action_type)
            
            # ROI-based tools (x₁₁)
            action.tools = self.tool_roi.select(action, budget=self.budget)
        
        # 4. Синергии (x₁+x₇, x₂+x₉, x₅+x₆)
        synergy_bonus = self._calculate_synergy_bonus(actions)
        
        # 5. Validation с self-correction (x₆)
        result = self.pipeline.validate(actions)
        if result.quality < self.min_quality:
            result = self._self_correct(result)
        
        result.synergy_bonus = synergy_bonus
        return result
```

---

## ✅ Чеклист интеграции

- [ ] Добавить GroundingModule
- [ ] Добавить ToolROISelector  
- [ ] Добавить FineTuningEvaluator
- [ ] Реализовать синергии в метриках
- [ ] Обновить тесты
- [ ] Документировать коэффициенты

---

*Создано: 2026-07-05*
*Интеграция: capability.txt × atomic_decomposition_model.md*