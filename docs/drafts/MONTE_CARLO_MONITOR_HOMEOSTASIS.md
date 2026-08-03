# Монте-Карло: Monitor ↔ Homeostasis — полный отчёт

> **2026-08-03** · N=400 · T=100 · seed=42 · `srs/monitoring/monte_carlo.py`
> Рисунки: `docs/drafts/mc_figs/` · данные: `docs/drafts/mc_stats.json`

## 1. Постановка

Связка gauges → Monitor (threshold, dedupe) → Event → Homeostasis (S/G, D, mode).
Режимы: calm, idle, stress_mild, crisis (до t=65 удар, затем calm), mixed.
Jitter: b, λ_S, θ_rev, θ_break.
Chronic (idle/calm): mean S[t≥50] > 0.55. Recovery (crisis): mean S[90:100] < 0.4.

## 2. Глобальные итоги

| Метрика | Значение |
|---------|----------|
| mean S overall | 0.422 |
| p50 / p95 mean-S | 0.490 / 0.776 |
| **idle chronic** | **0.0** |
| **calm chronic** | **0.0** |
| **crisis recovery** | **1.0** |

## 3. По режимам (mean / p50 / p95)

**Calm:** S_mean 0.025/0.023/0.053 · prospective ~50% · events ~2 · chronic 0

**Idle:** S_mean 0.155/0.155/0.187 · S_final ~0.24 · events **0** · revision ~35% · chronic 0

**Stress mild:** S_mean 0.72 · urgent ~87% · break ~51% · events ~36

**Crisis:** S_mean 0.72 · S_final **0.026** · break ~67% · events ~115 · recovery **100%**

**Mixed:** S_mean 0.49 · urgent ~52% · break ~17% · events ~14

## 4. Рисунки

- `mc_figs/mc_S_paths.png` — траектории S(t)
- `mc_figs/mc_S_mean_box.png` — box mean S
- `mc_figs/mc_mode_stack.png` — mode occupancy
- `mc_figs/mc_crisis_final_S.png` — финальный S после кризиса
- `mc_figs/mc_events_vs_S.png` — events vs S
- `mc_figs/mc_corr.png` — корреляции
- `mc_figs/mc_chronic_rate.png` — chronic rate

## 5. Интерпретация

Idle: S_{t+1}≈S e^{-λ} + boredom → S_eq∈[0.15,0.30] ✓
Crisis tail: e^{-0.12·35}≈0.015 → S_final→0 ✓
Dedupe ограничивает event storm.
Anomaly не входит в map → не двигает S.

## 6. Ограничения

Синтетический мир; нет реальных лагов биржи; backlog мало сэмплирован; не полная Bayesian-калибровка.

## 7. Вывод

Связка согласована: нет хронического stress на idle/calm, кризис обратим, mild держит urgent, flood нет.

```bash
python srs/monitoring/monte_carlo.py
```
