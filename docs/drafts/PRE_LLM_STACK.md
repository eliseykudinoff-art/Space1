# Pre-LLM upper stack (до промпта)

Граница: **всё до Stage VIII** (`route_prompt_detailed`).
`SignalToContextSynthesizer` **не трогаем**.

## Порядок стадий

```
IDLE / queue
  → I  Reception (scheduler, cold-start)
  → II Context: H/stress + memory + CCRS + StatusBlock
  → III Complexity + predict_estimates (φ̂, ψ̂, q̂)
  → IV Gamma hard veto
  → V  Decision cascade D(T) → EXECUTE|DECLINE|CLARIFY|REJECT
  → VI Decompose
  → VII Specialist UCB1
  → VIII LLM  ← граница
```

## Кто чем рулит (P0)

| Блок | Роль до LLM | Life |
|------|-------------|------|
| Idle | IDLE_TICK | **да** |
| H/stress Stage II | low H → CLARIFY | **life S/U → H** |
| Legacy homeo | fallback без self.life | dual only base |
| φ̂ψ̂q̂ | U, psi, q checks | косвенно |
| Γ hard/soft | REJECT / soft U | events post |
| mission_profile | пороги D(T) | urgent→SURVIVAL, prospective→GROWTH |
| Mission object | **не в dispatch** | gap |
| monitor gauges | axes | **да** |

## Decision cascade

1. Γ hard → REJECT
2. ψ>ψ_max или C<C_min → DECLINE
3. H_TZ / VoI / **H_val < H_clarify** → CLARIFY
4. U>0 и q̂≥q_min → EXECUTE
5. else DECLINE

Mission **множит пороги**, не пишет в S/G.

## Инвариант

До EXECUTE можно отсеять заказ **без LLM**. Life = напряжение + акцент миссии; Γ/φ/правила = отбор.
