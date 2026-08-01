# TRACE_01 — Формирование сигнала запроса к LLM

> **Дата:** 2026-08-01  
> **Метод:** от фактической точки вызова LLM вверх по цепочке; код = источник вопросов к спецификации.  
> **Код править не требуется** на этом шаге — фиксируем пробелы.

---

## 1. Точка входа (где реально уходит запрос)

**Файл:** `srs/orchestrator/core.py`  
**Место:** `PipelineOrchestrator.dispatch_full_cycle` → **Stage VIII** →  
`self.ai_super_router.route_prompt_detailed(system_prompt=..., user_prompt=...)`

### 1.1 Что реально уходит в LLM

```text
system_prompt = "Execute specialized subroutine"   # константа, без состояния агента

user_prompt = f"""You are {spec_name} executing Action: {action.name}

Task Context:
- Title: {task.title}
- Description: {task.description}
- Requirements: {getattr(task, 'requirements', 'N/A')}
- Priority: {task.priority...}
- Deadline: {task.deadline}
- Estimated Hours: {task.estimated_hours}

Please provide the implementation or response for this action.
"""
```

Дальше: `AISuperRouter.route_prompt_detailed` → (опционально) `SuperRouterClient.complete(prompt=user_prompt, system_prompt=...)`.

### 1.2 Чего в сигнале **нет**

| Ожидаемый по `03` §II / архитектуре элемент | В Stage VIII prompt |
|--------------------------------------------|---------------------|
| StatusBlock (H, deviations, plan, trend) | нет |
| Mission / tone / survival guidelines | нет |
| Γ / soft principles summary | нет |
| budget / C_t / token budget remaining | нет |
| recalled memory / lessons | нет |
| previous failed attempt diagnosis | нет |
| specialist-specific tool schema | нет |
| `source` (OWNER_DIRECT / MARKETPLACE) | нет |

**Вывод:** «сигнал» = плоский шаблон задачи + имя специалиста. Гомеостаз, очередь, Γ, StatusBlock на запрос **не влияют**.

---

## 2. Соседние конструкции в коде (не подключены к LLM)

### 2.1 `SignalToContextSynthesizer.synthesize` (тот же файл)

- Строит `OrchestratorContext.prompt` из:
  - `HomeostaticRegulator.update_all(metrics)` → pressures
  - `regulator.get_mode()` → survival / growth / normal
  - tone + guidelines (три ветки if/elif)
  - `memory.recall_strategies(urgent[0])`
  - title задачи
- **Нигде в `dispatch_full_cycle` не вызывается.**  
  Тесты `tests/test_med01_signal_synthesizer.py` проверяют только «не None».

### 2.2 Stage II — `AIOSContextManager.render_status_block`

```python
status_block = self.context_mgr.render_status_block(
    homeostasis_h=H,
    deviations=[],          # ← всегда пусто
    remaining_plan=[task.title],
    memory_snippets=snippets,
)
```

- Результат пишется в `trace`, **не передаётся** в Stage VIII.
- `deviations=[]` — top-3 вклад в stress **не вычисляется**.
- TrendOf(H, w=5) — **нет**.
- После декомпозиции plan не обновляется в StatusBlock (нет recitation на каждом шаге).

### 2.3 Две разные «Synthesizer»-сущности

| Имя в коде/доках | Смысл |
|------------------|--------|
| `SignalToContextSynthesizer` (G10) | сигнал гомеостаза → prompt (не в пайплайне) |
| Synthesizer `03` §VIII.5 | сведение $o_1..o_n$ в deliverable **после** исполнения |

Коллизия имён без явного разведения в `08_GLOSSARY` / `01`.

---

## 3. Цепочка вверх: из чего *должен* складываться сигнал

По `03_PIPELINE_MATH.md` (cf46601) **Часть II — Этап 2**:

**Вход:** $\mathbf x$, $H_{TZ}$ (этап 1); $H$, $\Lambda$; память; после VI — plan remaining.  
**Выход:** структурированный системный контекст для **всех** LLM-вызовов ниже.

Канон:

$$\mathrm{StatusBlock}(t)=\mathrm{render}\big(H(t),\{(v_j,target_j,dev_j)\}_{\mathrm{top\text{-}3}},\,\mathrm{TrendOf}(H,5),\,\mathrm{Plan}_{remaining}(t)\big)$$

Свойства:

1. `render` — **шаблонизация**, не LLM и не выбор из 4 текстов SignalBridge.
2. StatusBlock **переписывается каждый шаг** (recitation / Manus) и дописывается в конец контекста.
3. Не заменяет $\mathcal D(T)$: решение ACCEPT/REJECT — код; LLM только исполняет/декомпозирует/рефлексирует **в осведомлённом** контексте.

`04_ARCHITECTURE` согласуется: Synthesizer (VIII.5) — deliverable; этап 2 — мост сигнал→промпт.

---

## 4. Формулы, которые *участвуют* (или должны)

| Формула | Роль относительно LLM-сигнала |
|---------|--------------------------------|
| $H$, stress, ratios (`02` §IV.7) | числа внутри StatusBlock; mode survival/normal |
| $\Lambda$ (`02` §IV.8) | диагностика в блоке (в `03` II.1 вход); в коде Stage II **не** |
| top-3 deviations | вклад в stress; в коде `deviations=[]` |
| TrendOf(H,5) | направление H; **нет в коде** |
| Plan_remaining | после Stage VI; в коде до VI только title |
| UCB1 specialist select | *кто* говорит в prompt (`spec_name`); не *что* в system context |
| Γ / Mission | не должны решать за LLM «делать ли», но **должны** ограничивать tone/budget в system side |
| $C_t$, token budget | лимит длины / max_tokens запроса; в Stage VIII prompt **нет** |

`SignalToContextSynthesizer` использует **другую** логику: PID-pressures + mode string, не StatusBlock-формулу `03` §II.2. Это **третья** конкурирующая семантика «контекста» (StatusBlock / pressures-prompt / плоский Stage VIII).

---

## 5. Поведение при разных значениях метрик (факт кода)

| Состояние агента | Stage II | Stage VIII LLM prompt | Фактическое поведение LLM-вызова |
|------------------|----------|-------------------------|----------------------------------|
| H → CRITICAL, balance низкий | H в status_block (trace only) | тот же system/user шаблон | LLM **не** получает «survival only» |
| OWNER_DIRECT / emergency | scheduler (частично) | source не в prompt | исполнитель не знает системной критичности |
| Высокий stress | mode в synthesizer (не вызван) | без tone | нет conservative guidelines |
| После fail attempt | — | нет диагноза ошибки в prompt | RETRY без «что сломалось» (вопреки `03` про StatusBlock + fail) |
| Пустой plan / 1 action | remaining_plan=[title] | action.name + task fields | ок по минимуму |

**Логика агента «как будто в survival»** существует только:

- в `evaluate_decision_rule` / Mission thresholds (до EXECUTE),
- в мёртвом `SignalToContextSynthesizer`,
- **не** в тексте, который видит LLM на исполнении.

Итог: после ACCEPT поведение генерации **инвариантно** к H, Mission, source, C_t (кроме косвенных эффектов: другой specialist, другой decomposer — если они сами читают state; текущий Stage VIII prompt — нет).

---

## 6. Достаточность документации

### 6.1 Что сказано хорошо

- `03` §II.1–II.2: отказ от SignalBridge, StatusBlock, recitation, render без LLM, отличие от $\mathcal D$.
- Вход/выход этапа 2.
- Связь fail → обновление StatusBlock (`03` около retry).

### 6.2 Пробелы / неточности (спека должна закрыть явно)

| ID | Пробел | Почему всплыл в коде |
|----|--------|---------------------|
| **T1** | Не сказано, **какой** LLM-вызов обязан включать StatusBlock (decomp / every tool / verifier / only reflection) | Stage VIII шлёт prompt без блока |
| **T2** | Не зафиксирован **контракт сборки messages**: `system = ?`, `user = StatusBlock + task + action`, order, max tokens | system = одна фраза; user = ad-hoc f-string |
| **T3** | Не запрещён параллельный «давление→prompt» канал рядом со StatusBlock | `SignalToContextSynthesizer` = третья семантика |
| **T4** | Не определено вычисление top-3 deviations (формула вклада в stress) | `deviations=[]` |
| **T5** | TrendOf(H,5): структура хранения истории H | нет |
| **T6** | Обновление StatusBlock **после** каждого atomic action / fail — обязательный шаг пайплайна или рекомендация | в коде нет цикла recitation |
| **T7** | Имя Synthesizer: signal→prompt vs deliverable VIII.5 | два смысла |
| **T8** | Должен ли system_prompt нести Mission tone / Γ summary | сейчас константа |
| **T9** | `source` / emergency в контексте исполнителя — да/нет | нет в prompt |
| **T10** | Связь Stage II output → Stage VI/VIII **интерфейс данных** (поле task.metadata["status_block"]?) | status_block локальная переменная |

Пока T1–T10 открыты, любая реализация Stage VIII «имеет право» остаться плоским шаблоном — и по Мёрфи останется.

---

## 7. Черновик контракта (предложение в спеку, не код)

```text
LLMExecutionRequest:
  system:  fixed_role_preamble(specialist)
           + optional MissionTone (from Mission, not from LLM)
           + hard constraints summary (Γ_hard list ids only)
  user:    StatusBlock(t)          # обязательно, render() из §II.2
           + TaskEnvelope(title, description, source, deadline, …)
           + ActionEnvelope(name, inputs, guardrails G_i)
           + optional LastFailureDiagnosis
  meta:    max_tokens from B_comp / C_t policy
           temperature policy by Mission (таблица)

Invariant:
  StatusBlock is produced only by render() (no LLM).
  Decision D(T) never reads LLM output for ACCEPT/REJECT.
  No alternate pressure→prose channel without StatusBlock fields.
```

Детализацию T1–T10 — следующий шаг документа `03` (или `03_STAGE2_CONTEXT.md` amendment), точечно.

---

## 8. Связь с уже принятыми boundaries

`02_BOUNDARIES_AND_APPLICATION.md`:

- $C_t$ ≠ balance → влияет на **meta.max_tokens / can_call**, не на текст task fields.
- Mission имена → tone table для system preamble (T8).
- source не отключает Γ → в prompt можно **упоминать** source, нельзя писать «skip compliance».

---

*TRACE_01 v1.0 · 2026-08-01*
