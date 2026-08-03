# HOMEOSTASIS_MATH_v0 — Формулы гомеостаза и гормонального пульса

> **Статус:** черновик полной темы гомеостаза (математика модуля).
> **Дата:** 2026-08-03
> **Интеграция в `02_MATHEMATICAL_CORE.md`:** отложена.
> **Родитель:** `HOMEOSTASIS.md`, `HOMEOSTASIS_EVENTS_v0.md`.
> **Не входит:** выбор LLM, Φ-оптимизация, job-types из пульса.

---

## 0. Иерархия величин

| Уровень | Символ | Смысл |
|---------|--------|--------|
| Событие | e ∈ E | Из HOMEOSTASIS_EVENTS_v0 |
| Пульс | S(t), G(t) | stress, go |
| Ошибки состояния | ε_i(t) | по осям h_i |
| Drive | D(t) | скаляр нужды состояния |
| URGE | U_urge(t) | вход в ревизию |
| Режим | ρ(t) | аллостатический множитель |
| Load | L(t) | накопленная нагрузка |

Гормоны обновляют S, G. Мотор строит U_urge, ρ, L. Ревизия смотрит U_urge и {h_i}.
Метрики Φ, Ψ не «управляются гормонами»; входят в h_i и в события.

---

## 1. Состояние и drive

Оси I (v0, расширяется): resource, runway, compliance_exposure, competence, reputation, workload (band), progress_debt, idle_time.

Setpoint: h*_i(t) = h*_i,0 + Δ_i^allo(t)  (сначала Δ=0).

Ошибка ε_i: для higher_better (h*-h)/z; lower_better (h-h*)/z; band — dist до полосы / z.

d_i = max(0, ε_i)

**Drive:**

D(t) = Σ_i w_i · d_i(t)^p ,  p∈{1,2}, w_i≥0, Σw_i=1

D — не приказ «иди зарабатывать».

---

## 2. Гормональный пульс

### 2.1 Каналы

S(t) ∈ [0, S_max], G(t) ∈ [0, G_max]
S(0)=S_0, G(0)=G_0 (cold-start).

### 2.2 Затухание (heartbeat)

S ← S · e^(-λ_S Δt)
G ← G · e^(-λ_G Δt)

Обычно λ_G > λ_S (go гаснет быстрее).

### 2.3 Отклик на событие

S ← clip(S + a_S(e), 0, S_max)
G ← clip(G + a_G(e), 0, G_max)

Амплитуды a_S, a_G — из конфига; качественно:

| Класс | a_S | a_G |
|-------|-----|-----|
| RES exhausted / BUDGET_BLOCK | spike +0.4…0.8 | 0 |
| RES low / RATE_LIMIT | +0.15…0.35 | 0 |
| EXT reject | +0.2…0.4 | 0 |
| EXT major warning | +0.35…0.7 | 0 |
| COMPLIANCE_HIT | +0.4…0.8 | 0 |
| EXEC NO_PROGRESS / VERIFIER_FAIL | +0.2…0.4 | 0 |
| LOOP / DEAD_END | +0.5…0.9 | 0 |
| STEP_OK | −0.05…0 | +0.1…0.25 |
| TASK_DONE | −0.1…−0.25 | +0.3…0.5 |
| TASK_FAILED | +0.3…0.5 | 0 |
| IDLE no significant work | +0.05…0.2 | 0 |
| IDLE queue empty | +0.02…0.1 | 0 |
| OUT better than expected | soft− | +0.2…0.4 |
| OUT worse | +0.2…0.4 | 0 |
| BLOCK_CLEARED | −0.1…−0.3 | +0.2…0.4 |
| OWNER.EMERGENCY | +0.5…1.0 | 0 |

### 2.4 Скука

τ_idle — время с последней значимой работы.

a_S^boredom = 0 если τ < τ_0;
иначе b · (τ−τ_0)/(τ_0+τ)

На heartbeat: S ← clip(S + a_S^boredom, 0, S_max).

Инвариант: при долгом idle равновесие S > 0 (подпитка vs decay).

---

## 3. Мотор (fast)

### 3.1 URGE

U_raw = α_S·S + α_D·D + α_G·max(0, G_floor−G)   (α_G можно 0 в v0)

U_urge = ρ(t) · U_raw

revision_needed ⇔ U_urge ≥ θ_rev

### 3.2 Обрыв петли

break_loop = 1 ⇔ I_trap=1  ∨  S ≥ θ_break

Не назначает работу — только запрет продолжать тот же EXEC-цикл без ревизии.

### 3.3 Сводка комфорта (опционально)

H_motor = 1 − sat(D / D_ref)

Не замена старого H из 02 и не замена S.

---

## 4. Упрощённый RPE

r(t) = D(t) − D(t⁺)    # уменьшение drive = лучше

δ(t) = r(t) − V(t)

V ← V + η_V · δ

δ логировать; авто-калибровка w_i — Post-MVP.

---

## 5. Мотор (slow / аллостаз)

L ← (1−α_L)L + α_L · ψ(S, D, n_fail)

ψ = β_S·S + β_D·sat(D/D_ref) + β_f·sat(n_fail/n_ref)

ρ = clip(ρ_0 + κ_L·L, ρ_min, ρ_max)

Опционально: θ_rev(t) = θ_0·(1 − κ_θ·sat(L/L_ref)) ≥ θ_min

Сдвиг setpoint Δ_i^allo — медленный, v0 можно 0.

---

## 6. Алгоритм шага

1. Decay S,G
2. Если событие — apply a_S, a_G
3. Heartbeat — boredom
4. Обновить h_i снаружи
5. D
6. L, ρ (slow реже)
7. U_urge
8. break_loop
9. revision_needed?
10. При исходе — δ, V

**Выходы модуля:** S, G, D, U_urge, L, ρ, revision_needed, break_loop, (H_motor), (delta).

**Не выходы:** job-type, specialist, model_id.

---

## 7. Cold-start параметры (символы)

S_max=G_max≈1; λ_G>λ_S; Σw_i=1; p=1; α_S≈α_D≈0.5; θ_rev≈0.3; θ_break≈0.7; ρ_0=1.
Всё — внешний конфиг.

---

## 8. Связь со старым H / Λ

| Старое | Здесь |
|--------|--------|
| H (4 ratio) | Близко к H_motor(D), но D шире; отдельно S |
| Λ | Рядом с L, не смешивать с U_urge |
| PID pressures | Влить в h_i или устареют |

---

## 9. Модуль принципиально не делает

Не оптимизирует Φ; не выбирает LLM; не создаёт MARKETPLACE-задачи; не заменяет Γ_hard; не говорит EARN при низком balance — только S/D/revision_needed.

---

## 10. Критерии закрытия темы (документально)

- [x] Роли контуров
- [x] Словарь событий
- [x] Формулы S,G, decay, boredom
- [x] Drive D
- [x] U_urge, break_loop
- [x] L, ρ, RPE δ
- [x] Выходной контракт и cold-start
- [ ] Калибровка на логах — код
- [ ] Перенос в 02 — позже
- [ ] Оркестратор — техдолг

---

*HOMEOSTASIS_MATH_v0 · 2026-08-03*
