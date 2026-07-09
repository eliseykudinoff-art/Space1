#!/bin/bash
# setup_openhand_session.sh
# Быстрая настройка для любого проекта

set -e

echo "🔧 OpenHands Session Setup"
echo "=========================="

# Определяем директорию проекта
if [ -z "$1" ]; then
    PROJECT_DIR="$(pwd)"
else
    PROJECT_DIR="$1"
fi

cd "$PROJECT_DIR"

echo "📁 Project: $PROJECT_DIR"

# Инициализируем git если нужно
if [ ! -d ".git" ]; then
    echo "📦 Initializing git..."
    git init
    git add README.md 2>/dev/null || touch README.md && git add README.md
    git commit -m "Initial commit"
    echo "✅ Git initialized"
else
    echo "✅ Git already initialized"
fi

# Создаём session state файл
if [ ! -f ".session_state.json" ]; then
    echo '{"project_name": "", "goal": "", "status": "in_progress", "completed_tasks": [], "current_task": "", "next_steps": [], "problems": "", "last_checkpoint": "", "files_modified": [], "important_notes": "", "updated_at": ""}' > .session_state.json
    echo "✅ Session state created"
fi

# Копируем helper scripts
if [ ! -f "oh.sh" ]; then
    cp "$(dirname "$0")/oh.sh" .
    chmod +x oh.sh
    echo "✅ Helper script copied"
fi

# Первый checkpoint
echo "📸 Creating first checkpoint..."
git add .
git commit -m "Session start: $(date '+%Y-%m-%d %H:%M')" || true

echo ""
echo "=========================="
echo "✅ SETUP COMPLETE!"
echo ""
echo "📋 USAGE:"
echo ""
echo "  # Сохранить прогресс:"
echo "  ./oh.sh . s"
echo ""
echo "  # Показать историю:"
echo "  ./oh.sh . l"
echo ""
echo "  # Отметить выполненную задачу:"
echo "  ./oh.sh . d 'Написал тесты'"
echo ""
echo "  # Восстановить:"
echo "  ./oh.sh . r"
echo ""
echo "  # Статус:"
echo "  ./oh.sh . st"
echo ""
echo "=========================="
echo ""
echo "🔄 RECOVERY PROMPT (copy to new OpenHands session):"
echo ""
cat << 'EOF'
```
Load state from .session_state.json, then:
- git log --oneline -5
- git status
- cat .session_state.json
Continue from the tasks described in the state file.
```
EOF
echo ""
