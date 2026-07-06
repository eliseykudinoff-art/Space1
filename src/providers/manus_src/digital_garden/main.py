"""
🌱 Цифровой Сад — Management Core
====================================
Центральное ядро персональной экосистемы.

Архитектура:
  [Ты] → [Telegram/CLI] → [Management Core] → [Исполнители]
                                  ↕
                          [Память + Граф знаний]

Запуск:
  python main.py chat      — Интерактивный режим
  python main.py serve     — API-сервер (OpenAI-совместимый + расширения)
  python main.py status    — Статус системы
  python main.py memory    — Управление памятью
"""

import asyncio
import sys
import json
import logging
import time
from pathlib import Path

# Добавляем путь к ai_super_router для импорта
sys.path.insert(0, str(Path(__file__).parent.parent / "ai_super_router"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("garden")

from core.manager import ManagementCore, Executor, Intent


async def cmd_chat(core: ManagementCore):
    """Интерактивный чат с Management Core."""
    print("\n🌱 Цифровой Сад — Интерактивный режим")
    print("=" * 50)
    print("Команды: /status /memory /history /paradigm <name> /quit")
    print("=" * 50)
    
    while True:
        try:
            user_input = input("\n👤 > ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        
        if not user_input:
            continue
        
        if user_input in ("/quit", "/exit", "/q"):
            break
        
        if user_input == "/status":
            status = core.get_status()
            print(f"\n📊 Статус системы:")
            print(f"   Исполнители: {len(status['executors'])}")
            for eid, info in status["executors"].items():
                icon = "✅" if info["available"] else "❌"
                print(f"     {icon} {info['name']} ({info['type']}): {', '.join(info['capabilities'][:3])}...")
            print(f"   Память: {status['memory']['facts_count']} фактов, {status['memory']['entities_count']} сущностей")
            print(f"   Задач выполнено: {status['tasks_completed']}")
            continue
        
        if user_input == "/memory":
            if core.memory:
                stats = core.memory.get_stats()
                print(f"\n🧠 Память:")
                print(f"   Факты: {stats.get('facts_count', 0)}")
                print(f"   Сущности: {stats.get('entities_count', 0)}")
                print(f"   Сессий всего: {stats.get('sessions_count', 0)}")
                if core.memory.facts:
                    print(f"   Последние факты:")
                    for fact in list(core.memory.facts.values())[-5:]:
                        print(f"     • {fact.text}")
            continue
        
        if user_input == "/history":
            history = core.get_task_history(10)
            if history:
                print(f"\n📜 Последние задачи:")
                for t in history:
                    print(f"   [{t['intent']}] {t['query'][:60]}... → {t['executor'] or '?'} ({t['status']})")
            else:
                print("   История пуста.")
            continue
        
        if user_input.startswith("/paradigm "):
            paradigm = user_input[10:].strip()
            core.set_paradigm(paradigm)
            print(f"   🔮 Парадигма переключена: {paradigm}")
            continue
        
        if user_input.startswith("/fact "):
            fact = user_input[6:].strip()
            core.add_fact(fact)
            print(f"   📌 Факт добавлен: {fact}")
            continue
        
        # Обработка обычного запроса
        try:
            result = await core.process(user_input)
            
            print(f"\n🌱 [{result['intent']}] → {result['executor'] or 'internal'}")
            print(f"   {result['response']}")
            
            if result["facts_recalled"] > 0:
                print(f"   💡 (использовано {result['facts_recalled']} фактов из памяти)")
                
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")


async def cmd_serve(core: ManagementCore, port: int = 8080):
    """API-сервер с OpenAI-совместимым интерфейсом + расширения."""
    try:
        from aiohttp import web
    except ImportError:
        print("❌ Установите aiohttp: pip install aiohttp")
        return
    
    async def handle_chat_completions(request):
        """POST /v1/chat/completions"""
        data = await request.json()
        messages = data.get("messages", [])
        
        # Извлекаем последнее сообщение пользователя
        query = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                query = msg["content"]
                break
        
        if not query:
            return web.json_response({"error": "No user message"}, status=400)
        
        # Обрабатываем через Management Core
        result = await core.process(query)
        
        # Формат OpenAI
        response = {
            "id": f"chatcmpl-garden-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": result["executor"] or "management-core",
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": result["response"]},
                "finish_reason": "stop",
            }],
            "usage": {"prompt_tokens": len(query.split()), "completion_tokens": len(result["response"].split()), "total_tokens": 0},
            # Расширения Digital Garden
            "x_garden": {
                "intent": result["intent"],
                "executor": result["executor"],
                "memory_used": result["memory_used"],
                "facts_recalled": result["facts_recalled"],
                "task_id": result["task_id"],
            }
        }
        response["usage"]["total_tokens"] = response["usage"]["prompt_tokens"] + response["usage"]["completion_tokens"]
        
        return web.json_response(response)
    
    async def handle_process(request):
        """POST /garden/process — расширенный эндпоинт."""
        data = await request.json()
        query = data.get("query", "")
        context = data.get("context", {})
        
        result = await core.process(query, user_context=context)
        return web.json_response(result)
    
    async def handle_status(request):
        """GET /garden/status"""
        return web.json_response(core.get_status())
    
    async def handle_memory(request):
        """GET /garden/memory"""
        if core.memory:
            return web.json_response(core.memory.get_stats())
        return web.json_response({})
    
    async def handle_models(request):
        """GET /v1/models — список доступных 'моделей' (исполнителей)."""
        models = []
        for eid, executor in core.executors.items():
            models.append({
                "id": eid,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "digital-garden",
                "permission": [],
                "root": eid,
                "parent": None,
            })
        return web.json_response({"object": "list", "data": models})
    
    app = web.Application()
    app.router.add_post("/v1/chat/completions", handle_chat_completions)
    app.router.add_post("/garden/process", handle_process)
    app.router.add_get("/garden/status", handle_status)
    app.router.add_get("/garden/memory", handle_memory)
    app.router.add_get("/v1/models", handle_models)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    print(f"\n🌱 Цифровой Сад API запущен на http://0.0.0.0:{port}")
    print(f"   OpenAI-совместимый: POST /v1/chat/completions")
    print(f"   Расширенный:       POST /garden/process")
    print(f"   Статус:            GET  /garden/status")
    print(f"   Память:            GET  /garden/memory")
    print(f"\n   Для подключения из других сервисов:")
    print(f"   base_url = 'http://localhost:{port}/v1'")
    
    # Ждём бесконечно
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, asyncio.CancelledError):
        await runner.cleanup()


async def main():
    """Точка входа."""
    command = sys.argv[1] if len(sys.argv) > 1 else "chat"
    
    # Инициализация ядра
    config_path = "config/garden.yaml"
    if not Path(config_path).exists():
        config_path = None  # Используем defaults
    
    core = ManagementCore(config_path or "config/garden.yaml")
    await core.start()
    
    try:
        if command == "chat":
            await cmd_chat(core)
        elif command == "serve":
            port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
            await cmd_serve(core, port)
        elif command == "status":
            status = core.get_status()
            print(json.dumps(status, indent=2, ensure_ascii=False))
        elif command == "memory":
            if core.memory:
                stats = core.memory.get_stats()
                print(json.dumps(stats, indent=2, ensure_ascii=False))
        else:
            print(f"❌ Неизвестная команда: {command}")
            print("Доступные: chat, serve, status, memory")
    finally:
        await core.stop()


if __name__ == "__main__":
    asyncio.run(main())
