#!/usr/bin/env python3
"""
OpenHands Session State Manager
Хранит состояние сессии в одном месте (Gist, файл, и т.д.)
Достаточно дать ссылку агенту - он сам всё подхватит.
"""

import os
import json
import subprocess
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

@dataclass
class SessionState:
    """Состояние сессии"""
    project_name: str = ""
    goal: str = ""
    status: str = "in_progress"
    completed_tasks: list = None
    current_task: str = ""
    next_steps: list = None
    problems: str = ""
    last_checkpoint: str = ""
    files_modified: list = None
    important_notes: str = ""
    updated_at: str = ""
    
    def __post_init__(self):
        if self.completed_tasks is None:
            self.completed_tasks = []
        if self.next_steps is None:
            self.next_steps = []
        if self.files_modified is None:
            self.files_modified = []
        if not self.updated_at:
            self.updated_at = datetime.now().isoformat()


class SessionStateManager:
    """
    Менеджер состояния сессии
    Одно место хранения = одна ссылка = агент сразу в курсе
    """
    
    def __init__(self, workspace_dir: str = "."):
        self.workspace = Path(workspace_dir).resolve()
        self.state_file = self.workspace / ".session_state.json"
        self.gist_token = os.environ.get("GITHUB_TOKEN", "")
        
    # ==================== BASE OPERATIONS ====================
    
    def save_state(self, state: SessionState) -> str:
        """Сохранить состояние в локальный файл"""
        state.updated_at = datetime.now().isoformat()
        
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(asdict(state), f, indent=2, ensure_ascii=False)
        
        return str(self.state_file)
    
    def load_state(self) -> Optional[SessionState]:
        """Загрузить состояние"""
        if self.state_file.exists():
            with open(self.state_file, encoding="utf-8") as f:
                data = json.load(f)
            return SessionState(**data)
        return None
    
    def clear_state(self):
        """Очистить состояние"""
        if self.state_file.exists():
            self.state_file.unlink()
    
    # ==================== QUICK UPDATE ====================
    
    def update_goal(self, goal: str):
        """Обновить цель"""
        state = self.load_state() or SessionState()
        state.goal = goal
        self.save_state(state)
    
    def add_completed(self, task: str):
        """Добавить выполненную задачу"""
        state = self.load_state() or SessionState()
        if task not in state.completed_tasks:
            state.completed_tasks.append(task)
        self.save_state(state)
    
    def set_current(self, task: str):
        """Установить текущую задачу"""
        state = self.load_state() or SessionState()
        state.current_task = task
        self.save_state(state)
    
    def add_next_step(self, step: str):
        """Добавить следующий шаг"""
        state = self.load_state() or SessionState()
        if step not in state.next_steps:
            state.next_steps.append(step)
        self.save_state(state)
    
    def set_problem(self, problem: str):
        """Установить проблему"""
        state = self.load_state() or SessionState()
        state.problems = problem
        self.save_state(state)
    
    def clear_problem(self):
        """Очистить проблему"""
        state = self.load_state() or SessionState()
        state.problems = ""
        self.save_state(state)
    
    # ==================== GIT INTEGRATION ====================
    
    def create_checkpoint(self, message: str = "") -> str:
        """Создать git checkpoint и обновить состояние"""
        if not (self.workspace / ".git").exists():
            subprocess.run(["git", "init"], cwd=self.workspace, check=True)
            subprocess.run(["git", "add", "."], cwd=self.workspace, check=True)
            subprocess.run(["git", "commit", "-m", "Initial"], cwd=self.workspace, check=True)
        
        # Save current state
        self.save_state(self.load_state() or SessionState())
        
        # Git commit
        subprocess.run(["git", "add", "."], cwd=self.workspace, check=True)
        result = subprocess.run(
            ["git", "commit", "-m", message or "Checkpoint"],
            cwd=self.workspace,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            commit = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.workspace,
                capture_output=True,
                text=True
            ).stdout.strip()[:8]
            
            state = self.load_state() or SessionState()
            state.last_checkpoint = commit
            self.save_state(state)
            
            return commit
        return ""
    
    def get_git_status(self) -> str:
        """Получить git status"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.workspace,
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
        except:
            return ""
    
    def get_recent_commits(self, count: int = 5) -> list:
        """Получить недавние коммиты"""
        try:
            result = subprocess.run(
                ["git", "log", f"--oneline", f"-{count}"],
                cwd=self.workspace,
                capture_output=True,
                text=True
            )
            return [line for line in result.stdout.strip().split("\n") if line]
        except:
            return []
    
    # ==================== GIST SHARING ====================
    
    def publish_to_gist(self) -> Optional[str]:
        """
        Опубликовать состояние в GitHub Gist
        Возвращает URL Gist
        """
        if not self.gist_token:
            print("⚠️ GITHUB_TOKEN не установлен")
            return None
        
        state = self.load_state()
        if not state:
            print("⚠️ Нет сохранённого состояния")
            return None
        
        # Формируем контент для Gist
        content = self._format_state_for_gist(state)
        
        # Создаём Gist через GitHub API
        import urllib.request
        import urllib.error
        
        data = json.dumps({
            "description": f"OpenHands Session: {state.project_name or 'Project'}",
            "public": False,
            "files": {
                "SESSION_STATE.md": {
                    "content": content
                }
            }
        }).encode("utf-8")
        
        req = urllib.request.Request(
            "https://api.github.com/gists",
            data=data,
            headers={
                "Authorization": f"token {self.gist_token}",
                "Content-Type": "application/json",
                "Accept": "application/vnd.github.v3+json"
            },
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result.get("html_url")
        except urllib.error.HTTPError as e:
            print(f"❌ Gist error: {e.code}")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def update_gist(self, gist_id: str) -> bool:
        """Обновить существующий Gist"""
        if not self.gist_token:
            return False
        
        state = self.load_state()
        if not state:
            return False
        
        content = self._format_state_for_gist(state)
        
        import urllib.request
        import urllib.error
        
        data = json.dumps({
            "files": {
                "SESSION_STATE.md": {
                    "content": content
                }
            }
        }).encode("utf-8")
        
        req = urllib.request.Request(
            f"https://api.github.com/gists/{gist_id}",
            data=data,
            headers={
                "Authorization": f"token {self.gist_token}",
                "Content-Type": "application/json",
                "Accept": "application/vnd.github.v3+json"
            },
            method="PATCH"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return True
        except:
            return False
    
    def load_from_gist(self, gist_id: str) -> Optional[SessionState]:
        """Загрузить состояние из Gist"""
        import urllib.request
        
        gist_url = f"https://api.github.com/gists/{gist_id}"
        gist_url = gist_url.replace("api.github.com/gists/", "gist.githubusercontent.com/raw/")
        gist_url += "/SESSION_STATE.md"
        
        req = urllib.request.Request(gist_url, headers={"Accept": "text/plain"})
        
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                content = resp.read().decode("utf-8")
                return self._parse_gist_content(content)
        except:
            return None
    
    # ==================== FORMATTING ====================
    
    def _format_state_for_gist(self, state: SessionState) -> str:
        """Форматировать состояние для Gist/Markdown"""
        lines = [
            "# 📋 OpenHands Session State",
            "",
            f"**Updated:** {state.updated_at}",
            f"**Status:** {state.status}",
            "",
            "## 🎯 Goal",
            state.goal or "_No goal set_",
            "",
            "## ✅ Completed",
        ]
        
        if state.completed_tasks:
            for task in state.completed_tasks:
                lines.append(f"- [x] {task}")
        else:
            lines.append("_Nothing completed yet_")
        
        lines.extend([
            "",
            "## 🔄 Current Task",
            state.current_task or "_No current task_",
            "",
            "## 📌 Next Steps",
        ])
        
        if state.next_steps:
            for i, step in enumerate(state.next_steps, 1):
                lines.append(f"{i}. {step}")
        else:
            lines.append("_No steps defined_")
        
        lines.extend([
            "",
            "## ⚠️ Problems",
            state.problems or "_No problems_",
            "",
            "## 💾 Git Info",
            f"**Last Checkpoint:** `{state.last_checkpoint}`" if state.last_checkpoint else "_No checkpoints_",
            "",
            "## 📁 Modified Files",
        ])
        
        if state.files_modified:
            for f in state.files_modified[:10]:
                lines.append(f"- `{f}`")
        else:
            lines.append("_No tracked files_")
        
        lines.extend([
            "",
            "## 📝 Notes",
            state.important_notes or "_No notes_",
            "",
            "---",
            "*This state is auto-generated by OpenHands Session Manager*"
        ])
        
        return "\n".join(lines)
    
    def _parse_gist_content(self, content: str) -> Optional[SessionState]:
        """Парсить контент Gist обратно в SessionState"""
        # Простой парсинг - можно улучшить
        state = SessionState()
        
        lines = content.split("\n")
        current_section = ""
        
        for line in lines:
            if line.startswith("## "):
                current_section = line[3:].lower()
            elif "**Updated:**" in line:
                state.updated_at = line.split("**")[2]
            elif "**Status:**" in line:
                state.status = line.split("**")[2]
        
        return state
    
    # ==================== AGENT PROMPT ====================
    
    def generate_recovery_prompt(self) -> str:
        """
        Генерировать промпт для агента
        Одной ссылки достаточно - агент сам разберётся
        """
        state = self.load_state()
        if not state:
            return "⚠️ No session state found. Run `session_manager.py --action save` first."
        
        git_status = self.get_git_status()
        recent = self.get_recent_commits()
        
        prompt = f"""# 🆘 SESSION RECOVERY

Load state from: {self.state_file}

## Current Status
- **Project:** {state.project_name or 'Unknown'}
- **Goal:** {state.goal or 'Not set'}
- **Status:** {state.status}
- **Updated:** {state.updated_at}

## Completed Tasks
{chr(10).join(f'- [x] {t}' for t in state.completed_tasks) if state.completed_tasks else '- None'}

## Current Task
{state.current_task or '_Not set_'}

## Next Steps
{chr(10).join(f'{i}. {s}' for i, s in enumerate(state.next_steps, 1)) if state.next_steps else '- None'}

## Problems
{state.problems or '_None_'}

## Git
- **Last checkpoint:** `{state.last_checkpoint}`
- **Recent commits:**
{chr(10).join(f'  - {c}' for c in recent) if recent else '  - None'}

- **Uncommitted changes:** {'Yes' if git_status else 'None'}

## Quick Start
1. `cat {self.state_file}` - load full state
2. `git log --oneline -5` - see history
3. `git status` - check changes
4. Continue from: {state.current_task or state.next_steps[0] if state.next_steps else 'unknown'}

=== END RECOVERY DATA ==="""

        return prompt


# ==================== CLI ====================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenHands Session State Manager")
    parser.add_argument("--dir", "-d", default=".", help="Workspace directory")
    parser.add_argument("--action", "-a", 
                       choices=["save", "load", "prompt", "checkpoint", 
                               "update-goal", "add-done", "set-current", "add-step",
                               "gist-publish", "gist-load"],
                       default="load")
    parser.add_argument("--goal", help="Set project goal")
    parser.add_argument("--task", help="Task description")
    parser.add_argument("--message", "-m", help="Checkpoint message")
    parser.add_argument("--gist-id", help="Gist ID for gist operations")
    
    args = parser.parse_args()
    manager = SessionStateManager(args.dir)
    
    if args.action == "save":
        state = SessionState()
        state.project_name = input("Project name: ")
        state.goal = input("Goal: ")
        manager.save_state(state)
        print("✅ State saved")
        
    elif args.action == "load":
        state = manager.load_state()
        if state:
            print(manager._format_state_for_gist(state))
        else:
            print("No saved state")
            
    elif args.action == "prompt":
        print(manager.generate_recovery_prompt())
        
    elif args.action == "checkpoint":
        commit = manager.create_checkpoint(args.message or "Checkpoint")
        print(f"✅ Checkpoint: {commit}")
        
    elif args.action == "update-goal":
        manager.update_goal(args.goal or "")
        print("✅ Goal updated")
        
    elif args.action == "add-done":
        manager.add_completed(args.task or "")
        print("✅ Task added to completed")
        
    elif args.action == "set-current":
        manager.set_current(args.task or "")
        print("✅ Current task set")
        
    elif args.action == "add-step":
        manager.add_next_step(args.task or "")
        print("✅ Step added")
        
    elif args.action == "gist-publish":
        url = manager.publish_to_gist()
        if url:
            print(f"✅ Published: {url}")
        else:
            print("❌ Failed. Set GITHUB_TOKEN env variable")
            
    elif args.action == "gist-load":
        if args.gist_id:
            state = manager.load_from_gist(args.gist_id)
            if state:
                manager.save_state(state)
                print("✅ Loaded from Gist")
            else:
                print("❌ Failed to load")
