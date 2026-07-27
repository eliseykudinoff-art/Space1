# ARCHIVE_MANIFEST.md — Реестр архивации исходных документов

> **Назначение:** практический список для владельца репозитория — какие файлы ветки `drafts` перенести в `ARCHIVE/` при внедрении нового канонического корпуса (`00`–`10`), и что именно каждый из них заменяет. Ни один документ не удаляется — только помечается как замещённый, с указанием, чем и почему (принцип, соблюдавшийся во всех 11 канонических документах на уровне отдельных формул, здесь применяется на уровне целых файлов).
> **Дата составления:** 2026-07-19, по итогам Фазы 7 (`Space1_Documentation_Rewrite_Plan.md`).

---

## Таблица архивации

| Файл в `drafts` | Статус | Заменён на | Причина |
|---|---|---|---|
| `MATHEMATICAL_FORMULAS.md` | → ARCHIVE | `02_MATHEMATICAL_CORE.md` | Все формулы пересмотрены, противоречия (H/Γ/Ω) устранены, Пост-MVP версии сохранены в реестре ядра Часть VI |
| `MATHEMATICAL_ANALYSIS.md` | → ARCHIVE | `02_MATHEMATICAL_CORE.md` | Самокритика учтена и устранена в каноне |
| `MATHEMATICAL_REVIEW.md` | → ARCHIVE | `02_MATHEMATICAL_CORE.md` | Найденные дефекты (Γ=-∞→U=+∞ и др.) исправлены в каноне |
| `MATHEMATICAL_WORKSPACE.md` | → ARCHIVE | `02_MATHEMATICAL_CORE.md` | Черновик, поглощён каноном |
| `CYBERNETICS_HOMEOSTASIS_FORMULAS.md` | → ARCHIVE | `02_MATHEMATICAL_CORE.md` Часть VIII, Часть VI | Разобрано построчно; принятое — в ядре, отклонённое — в реестре с условием возврата |
| `capability.txt` | → ARCHIVE (частично используется) | `02_MATHEMATICAL_CORE.md` Часть III (17 факторов), `07_CALIBRATION_AND_VALIDATION.md` (ссылки на BFCL/WebArena/RAGAS) | Сырой лог сессии; факторы и внешние бенчмарки перенесены, разговорная часть — нет |
| `capability_2.txt` | → ARCHIVE (частично используется) | `02_MATHEMATICAL_CORE.md` (Λ, происхождение H — Приложение А `Space1_Review_and_Roadmap.md`) | Тот же тип источника — ценное формализовано, лог сессии архивирован |
| `AGENT_CONTROL_ARCHITECTURE.md` | → ARCHIVE | `02_MATHEMATICAL_CORE.md` (матчасть), `04_ARCHITECTURE.md` (архитектурная часть) | Статичная `MissionFunction.get_weights()` отклонена в пользу динамической `MissionPolicy.calibrate()` |
| `FREELANCER_AGENT_ARCHITECTURE.md` | → ARCHIVE (источник идей, не эталон — по вашей поправке) | `04_ARCHITECTURE.md`, `01_CONCEPT.md` | Ролевая мультиагентность (Scout/Worker/Finance/Communicator) отклонена в пользу функционального разделения (практика Manus) |
| `COMPARATIVE_ANALYSIS_REPORT.md` | → ARCHIVE | `04_ARCHITECTURE.md` | «Грабл-бэг» из 16 формул без интеграции — каждая рассмотрена по существу, принятое или отклонено явно |
| `MEMORY_ANALYSIS_REPORT.md` | → ARCHIVE | `05_MEMORY_AND_STATE.md` Часть IX (запись M-1) | 9+ типов памяти — избыточно для MVP, 4-типовая CoALA дважды независимо подтверждена |
| `SYSTEM_MONITORING.md` | → ARCHIVE | `05_MEMORY_AND_STATE.md` §VII.1 | Конкурирующий набор режимов сведён в два независимых измерения с исходным набором Dormant/Active/Recovering/Suspended |
| `Task_Processing/complexity_classification_formula.md` | → ARCHIVE | `03_PIPELINE_MATH.md` §I.1 | Критический дефект (необъявленные веса) исправлен байесовским prior→posterior переходом |
| `Task_Processing/task_decomposition_model.md` | → ARCHIVE | `03_PIPELINE_MATH.md` §VI | Формализовано, связано с вектором факторов |
| `Task_Processing/atomic_decomposition_model.md` | → ARCHIVE | `03_PIPELINE_MATH.md` §VI | То же |
| `ACTION_FORMULA_CYBERNETICS.md` | → ARCHIVE | `03_PIPELINE_MATH.md` | Поглощено пайплайном |
| `ACTION_FORMULA_WORKFLOW.md` | → ARCHIVE | `03_PIPELINE_MATH.md` | Поглощено пайплайном |
| `NAMING_CONVENTION.md` | **Остаётся действующим, расширяется** | `08_GLOSSARY.md` (не заменяет, дополняет) | Единственный исходный документ, принятый без изменений по существу |
| `UNIFIED_VARIABLE_SYSTEM.md` | → ARCHIVE (частично используется) | `08_GLOSSARY.md`, `02_MATHEMATICAL_CORE.md` §II | Префиксная схема для C/T/S перенесена без изменений; собственная незамеченная коллизия (Ω) — обнаружена и устранена в каноне |
| `digital_garden/core/memory.py` | Код не трогаем, но фиксируется как технический долг | Целевое состояние — `05_MEMORY_AND_STATE.md` | Плоское keyword-хранилище не покрывает ни один из 4 канонических типов памяти |
| `digital_garden/protocols/mcp_client.py` | **Остаётся действующим кодом** | Описан как основа Tool Manager в `09_ECOSYSTEM_AND_INTEROP.md` §V.1 | Единственный найденный за весь разбор код, который не требует переделки — использовать как есть |
| Присланный документ «Интеграция лучших мировых разработок» | → ARCHIVE (источник, не документ репозитория) | `09_ECOSYSTEM_AND_INTEROP.md`, `10_SECURITY.md` §II | Разделы 6/9/10 → `09`, раздел 14 → `10` |
| `deep-research-report*.md` (4 файла) | → ARCHIVE | `Space1_Consolidated_Review.md` (уже был их синтезом) | Синтез существовал уже в репозитории до этой волны документации |
| `Space1_Consolidated_Review.md` | → ARCHIVE (сам стал источником) | `00_MASTER.md`, `Space1_Review_and_Roadmap.md` | Ревью учтено и превышено независимым анализом |

## Файлы, не найденные в предоставленном архиве, но упомянутые в других документах

`MISSING_FACTORS_ANALYSIS.md`, `FORMULAS_REFERENCE.md`, `CLEAN_MATHEMATICAL_MODEL.md`, `CRITICAL_MATHEMATICAL_REVIEW.md`, `MATHEMATICAL_QUESTIONS.md`, `DOCUMENTATION_ISSUES.md`, `DOCUMENTATION_CONSOLIDATION.md` — упоминались как источники в других файлах ветки `drafts`, но отсутствовали в переданном архиве (см. `Space1_Review_and_Roadmap.md`, Часть 0). Если они существуют в ветке `main` — стоит свериться, не осталось ли там неучтённого материала, прежде чем считать архивацию окончательной.

---

*Составлено: 2026-07-19, Фаза 7 плана переработки документации*
