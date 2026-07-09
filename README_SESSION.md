# 🛠️ OpenHands Session Recovery System

## Быстрый старт

### Первый запуск (один раз):
```bash
./setup_session.sh
```

### При краше сессии:
Скопируйте в новую сессию OpenHands:
```
Load state from .session_state.json, then git log --oneline -5, git status, and continue from tasks described there.
```

---

## Команды

| Команда | Что делает |
|---------|------------|
| `./oh.sh . s` | Сохранить checkpoint |
| `./oh.sh . d "Задача"` | Отметить выполненную задачу |
| `./oh.sh . st` | Показать статус |
| `./oh.sh . l` | История checkpoints |
| `./oh.sh . p` | Показать recovery промпт |

---

## Workflow

1. **Начало:** `./oh.sh . s`
2. **Работа:** `./oh.sh . d "Сделал X"` после каждой задачи
3. **Крах:** Новая сессия → Recovery промпт → Агент подхватывает

---

Подробнее: `OPENHANDS_SESSION_GUIDE.md` (если есть в репозитории)
