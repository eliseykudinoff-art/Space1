#!/bin/bash
# oh.sh - OpenHands Session Helper
# Однострочники для управления сессией

# Цвета
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

WORKSPACE="${1:-.}"

echo -e "${BLUE}╔══════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   OpenHands Session Helper         ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════╝${NC}"

# Parse command
CMD="${2:-}"

case "$CMD" in
    # Сохранить checkpoint
    save|s)
        echo -e "${GREEN}💾 Creating checkpoint...${NC}"
        cd "$WORKSPACE"
        git add . 2>/dev/null
        git commit -m "Checkpoint $(date '+%Y-%m-%d %H:%M')" 2>/dev/null && \
            echo -e "${GREEN}✅ Done${NC}" || \
            echo -e "${YELLOW}📝 Nothing to save${NC}"
        ;;
    
    # Показать историю
    log|l)
        echo -e "${BLUE}📜 Recent checkpoints:${NC}"
        cd "$WORKSPACE"
        git log --oneline -10 2>/dev/null || echo "Not a git repo"
        ;;
    
    # Восстановить
    restore|r)
        echo -e "${YELLOW}⚠️ Select checkpoint to restore:${NC}"
        cd "$WORKSPACE"
        echo "Recent:"
        git log --oneline -5
        echo ""
        read -p "Enter commit hash (first 8 chars): " HASH
        if [ -n "$HASH" ]; then
            git checkout "$HASH" 2>/dev/null && \
                echo -e "${GREEN}✅ Restored${NC}" || \
                echo -e "${RED}❌ Failed${NC}"
        fi
        ;;
    
    # Статус
    status|st)
        echo -e "${BLUE}📊 Session Status:${NC}"
        cd "$WORKSPACE"
        echo "Changes: $(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
        echo "Last:    $(git log --oneline -1 2>/dev/null || echo 'None')"
        if [ -f .session_state.json ]; then
            echo "State:   $(grep -o '"goal": "[^"]*"' .session_state.json | head -1 || echo 'No goal')"
        fi
        ;;
    
    # Добавить задачу
    done|d)
        TASK="${3:-}"
        if [ -z "$TASK" ]; then
            read -p "Task completed: " TASK
        fi
        if [ -n "$TASK" ]; then
            cd "$WORKSPACE"
            # Добавляем в session_state если есть
            if [ -f .session_state.json ]; then
                python3 -c "
import json
with open('.session_state.json') as f:
    s = json.load(f)
s.setdefault('completed_tasks', []).append('$TASK')
s['updated_at'] = '$(date -Iseconds)'
with open('.session_state.json', 'w') as f:
    json.dump(s, f, indent=2)
"
            fi
            git add . 2>/dev/null
            git commit -m "Done: $TASK" 2>/dev/null
            echo -e "${GREEN}✅ Marked: $TASK${NC}"
        fi
        ;;
    
    # Генерация recovery промпта
    prompt|p)
        echo -e "${BLUE}📋 Recovery Prompt:${NC}"
        echo "```"
        cat << 'PROMPT'
Load state from .session_state.json if exists, then run:
- git log --oneline -5
- git status
- cat .session_state.json 2>/dev/null || echo "No state file"
Continue from tasks described in the state.
PROMPT
        echo "```"
        ;;
    
    # Помощь
    help|h|*)
        echo ""
        echo "Commands:"
        echo "  oh.sh <dir> save     (s)     - Save checkpoint"
        echo "  oh.sh <dir> log      (l)     - Show history"
        echo "  oh.sh <dir> restore  (r)     - Restore checkpoint"
        echo "  oh.sh <dir> status   (st)    - Show status"
        echo "  oh.sh <dir> done     (d)     - Mark task done"
        echo "  oh.sh <dir> prompt  (p)     - Show recovery prompt"
        echo ""
        echo "Examples:"
        echo "  oh.sh . s                    - Save current"
        echo "  oh.sh . d 'Fixed login bug'   - Mark task done"
        echo "  oh.sh . p                    - Show recovery prompt"
        echo ""
        ;;
esac
