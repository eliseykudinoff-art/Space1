"""
🌐 AI Super Router — Главный модуль (v2.0 + Память)
=====================================================
Запуск: python main.py [команда]

Команды:
  serve       — Запустить как OpenAI-совместимый API сервер
  health      — Проверить здоровье всех провайдеров
  models      — Показать доступные модели
  compute     — Показать вычислительные ресурсы
  scan        — Поиск новых бесплатных ресурсов
  chat        — Интерактивный чат (с памятью!)
  status      — Полный статус системы
  memory      — Управление памятью (stats/search/facts/entities/paradigm)
"""

import asyncio
import sys
import json
import yaml
import logging
import time
from pathlib import Path
from typing import List, Optional

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("ai_router")

# Импорты модулей
from core.router import Provider, RoutingStrategy
from core.client import SuperRouterClient
from core.health_checker import HealthChecker
from core.memory import Memory, MemoryConfig
from compute.aggregator import ComputeAggregator
from discovery.scanner import ResourceScanner


def load_providers(config_path: str = "config/providers.yaml") -> List[Provider]:
    """Загружает провайдеров из YAML конфига."""
    path = Path(config_path)
    if not path.exists():
        logger.error(f"❌ Конфиг не найден: {config_path}")
        sys.exit(1)
    
    with open(path) as f:
        config = yaml.safe_load(f)
    
    providers = []
    for p_data in config.get("providers", []):
        api_key = p_data.get("api_key", "")
        
        provider = Provider(
            name=p_data["name"],
            id=p_data["id"],
            base_url=p_data["base_url"],
            api_key=api_key,
            models=p_data.get("models", []),
            format=p_data.get("format", "openai"),
            health_url=p_data.get("health_url", ""),
            limits=p_data.get("limits", {"rpm": 10, "rpd": 1000, "tpm": 50000}),
            credit_card_required=p_data.get("credit_card_required", False),
            notes=p_data.get("notes", ""),
            priority=p_data.get("priority", 5),
        )
        providers.append(provider)
    
    return providers


def load_memory_config(config_path: str = "config/providers.yaml") -> MemoryConfig:
    """Загружает настройки памяти из конфига."""
    path = Path(config_path)
    config = MemoryConfig()
    
    if path.exists():
        with open(path) as f:
            data = yaml.safe_load(f)
        
        mem_cfg = data.get("memory", {})
        if mem_cfg:
            config.storage_dir = mem_cfg.get("storage_dir", config.storage_dir)
            config.max_session_messages = mem_cfg.get("max_session_messages", config.max_session_messages)
            config.max_context_tokens = mem_cfg.get("max_context_tokens", config.max_context_tokens)
            config.max_facts = mem_cfg.get("max_facts", config.max_facts)
            config.auto_extract_facts = mem_cfg.get("auto_extract_facts", config.auto_extract_facts)
            config.include_facts_in_context = mem_cfg.get("include_facts_in_context", config.include_facts_in_context)
            config.max_relevant_facts = mem_cfg.get("max_relevant_facts", config.max_relevant_facts)
    
    return config


async def cmd_health(providers: List[Provider]):
    """Проверка здоровья всех провайдеров."""
    print("\n🏥 Проверка здоровья провайдеров...\n")
    
    checker = HealthChecker(timeout=10.0)
    router_providers = {p.id: p for p in providers}
    results = await checker.check_all(router_providers)
    
    print(f"{'Провайдер':<30} {'Статус':<12} {'Латентность':<12} {'Ошибка'}")
    print("─" * 80)
    
    for pid, result in sorted(results.items(), key=lambda x: -x[1].is_alive):
        status = "✅ OK" if result.is_alive else "❌ DOWN"
        latency = f"{result.latency_ms:.0f}ms" if result.is_alive else "—"
        error = result.error or ""
        name = router_providers[pid].name[:28]
        print(f"{name:<30} {status:<12} {latency:<12} {error[:30]}")
    
    active = sum(1 for r in results.values() if r.is_alive)
    print(f"\n📊 Итого: {active}/{len(results)} провайдеров доступны")


async def cmd_models(providers: List[Provider]):
    """Показать все доступные модели."""
    print("\n📋 Доступные модели:\n")
    
    checker = HealthChecker(timeout=10.0)
    router_providers = {p.id: p for p in providers}
    await checker.check_all(router_providers)
    
    print(f"{'Модель':<45} {'Провайдер':<25} {'Статус'}")
    print("─" * 85)
    
    for p in providers:
        if p.api_key.startswith("YOUR_"):
            status = "⚙️ Нужен ключ"
        elif p.status.value == "active":
            status = "✅ Готова"
        elif p.status.value == "unavailable":
            status = "❌ Недоступна"
        else:
            status = f"⚠️ {p.status.value}"
        
        for model in p.models:
            print(f"{model[:43]:<45} {p.name[:23]:<25} {status}")


async def cmd_compute():
    """Показать вычислительные ресурсы."""
    print("\n🖥️ Вычислительные ресурсы:\n")
    
    aggregator = ComputeAggregator()
    report = aggregator.get_status_report()
    
    print(f"{'Ресурс':<30} {'Тип':<12} {'RAM':<8} {'VRAM':<8} {'Часов осталось':<15} {'Авто?'}")
    print("─" * 90)
    
    for pid, info in report["providers"].items():
        auto = "✅" if not info["requires_interaction"] else "👤"
        print(f"{info['name'][:28]:<30} {info['type']:<12} {info['ram_gb']:.0f}GB{'':<4} {info['vram_gb']:.0f}GB{'':<4} {info['remaining_hours']:<15} {auto}")
    
    print(f"\n📊 GPU часов доступно: {report['total_gpu_hours_remaining']:.0f}ч")
    print(f"📊 CPU часов доступно: {report['total_cpu_hours_remaining']:.0f}ч")


async def cmd_scan():
    """Поиск новых ресурсов."""
    print("\n🔍 Поиск новых бесплатных ресурсов...\n")
    
    scanner = ResourceScanner()
    resources = await scanner.scan_all()
    
    if resources:
        print(f"Найдено {len(resources)} ресурсов:\n")
        for r in resources[:20]:
            verified = "✅" if r.verified else "❓"
            print(f"  {verified} [{r.type}] {r.name[:50]}")
            print(f"     URL: {r.url}")
            if r.description:
                print(f"     {r.description[:80]}")
            print()
    else:
        print("Новых ресурсов не найдено.")


async def cmd_chat(providers: List[Provider], memory: Memory):
    """Интерактивный чат с памятью."""
    print("\n💬 AI Super Router — Интерактивный чат (с памятью 🧠)")
    print("    Введите сообщение или 'quit' для выхода")
    print("    Команды:")
    print("      /status        — Статус роутера")
    print("      /models        — Доступные модели")
    print("      /memory        — Статистика памяти")
    print("      /facts         — Все сохранённые факты")
    print("      /search <q>    — Поиск по памяти")
    print("      /paradigm <p>  — Установить парадигму (или /paradigm off)")
    print("      /session new   — Начать новую сессию")
    print("      /history       — История текущей сессии")
    print()
    
    client = SuperRouterClient(providers)
    await client.start()
    
    # Начинаем сессию
    session_id = memory.start_session()
    print(f"    📂 Сессия: {session_id}")
    
    # Показываем что помним
    stats = memory.get_stats()
    if stats["total_facts"] > 0:
        print(f"    🧠 В памяти: {stats['total_facts']} фактов, {stats['total_entities']} сущностей")
    print()
    
    try:
        while True:
            try:
                user_input = input("\n👤 Вы: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            
            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "q"):
                break
            
            # --- Команды ---
            if user_input.startswith("/status"):
                status = client.get_status()
                print(json.dumps(status, indent=2, ensure_ascii=False))
                continue
            
            if user_input.startswith("/models"):
                models = client.get_models()
                for m in models:
                    print(f"  {m['model']} ({m['provider']})")
                continue
            
            if user_input.startswith("/memory"):
                stats = memory.get_stats()
                print(f"\n🧠 Статистика памяти:")
                print(f"   Фактов: {stats['total_facts']}")
                print(f"   Сущностей: {stats['total_entities']}")
                print(f"   Сессий: {stats['total_sessions']}")
                print(f"   Текущая сессия: {stats['current_session']['messages']} сообщений")
                print(f"   Модели использованы: {', '.join(stats['current_session']['models_used']) or '—'}")
                print(f"   Провайдеры: {', '.join(stats['current_session']['providers_used']) or '—'}")
                print(f"   Парадигма: {stats['active_paradigm'] or 'не задана'}")
                if stats["facts_by_category"]:
                    print(f"   Факты по категориям: {stats['facts_by_category']}")
                continue
            
            if user_input.startswith("/facts"):
                facts = memory.get_facts()
                if facts:
                    print(f"\n📌 Сохранённые факты ({len(facts)}):")
                    for f in facts:
                        print(f"   [{f['category']}] {f['content']} (tags: {', '.join(f['tags'])})")
                else:
                    print("   Фактов пока нет.")
                continue
            
            if user_input.startswith("/search "):
                query = user_input[8:].strip()
                results = memory.search_memory(query)
                if results:
                    print(f"\n🔍 Найдено {len(results)} результатов:")
                    for r in results:
                        if r["type"] == "fact":
                            print(f"   📌 [{r['category']}] {r['content']}")
                        else:
                            print(f"   🏷️ [{r['entity_type']}] {r['name']}: {r['description']}")
                else:
                    print("   Ничего не найдено.")
                continue
            
            if user_input.startswith("/paradigm"):
                arg = user_input[9:].strip()
                if arg.lower() in ("off", "none", "reset", ""):
                    memory.set_paradigm(None)
                    print("   🔮 Парадигма сброшена")
                else:
                    memory.set_paradigm(arg)
                    print(f"   🔮 Парадигма установлена: {arg}")
                continue
            
            if user_input.startswith("/session"):
                arg = user_input[8:].strip()
                if arg == "new":
                    memory.end_session()
                    session_id = memory.start_session()
                    print(f"   📂 Новая сессия: {session_id}")
                continue
            
            if user_input.startswith("/history"):
                if memory._current_session and memory._current_session.messages:
                    print(f"\n📜 История ({len(memory._current_session.messages)} сообщений):")
                    for msg in memory._current_session.messages[-10:]:
                        role = "👤" if msg.role == "user" else "🤖"
                        model_info = f" [{msg.provider}/{msg.model}]" if msg.model else ""
                        print(f"   {role}{model_info} {msg.content[:100]}")
                else:
                    print("   История пуста.")
                continue
            
            if user_input.startswith("/add_fact "):
                fact_text = user_input[10:].strip()
                memory.add_fact(fact_text, category="manual")
                print(f"   📌 Факт добавлен: {fact_text}")
                continue
            
            # --- Обычный запрос с контекстом из памяти ---
            try:
                # 1. Получаем контекст из памяти (включает историю + факты)
                context = memory.get_context(user_input)
                
                # 2. Собираем полный список messages для провайдера
                #    context["messages"] = вся история + текущее сообщение
                #    context["system_prompt"] = system prompt обогащённый фактами
                full_messages = []
                if context["system_prompt"]:
                    full_messages.append({"role": "system", "content": context["system_prompt"]})
                full_messages.extend(context["messages"])
                
                # 3. Отправляем запрос с полной историей
                response = await client.complete(
                    messages=full_messages,
                    max_tokens=2048,
                    temperature=0.7,
                )
                
                # 4. Записываем обмен в память
                memory.record_exchange(
                    user_message=user_input,
                    assistant_response=response.text,
                    model=response.model,
                    provider=response.provider_name,
                    tokens_used=response.tokens_used,
                )
                
                # 5. Выводим ответ
                print(f"\n🤖 [{response.provider_name} / {response.model}] ({response.latency_ms:.0f}ms):")
                print(f"   {response.text}")
                
                # 6. Показываем мета-информацию о контексте
                meta = context["metadata"]
                if meta["facts_used"] > 0:
                    print(f"   💡 (использовано {meta['facts_used']} фактов из памяти)")
                if len(context["messages"]) > 1:
                    print(f"   📜 (контекст: {len(context['messages'])} сообщений)")
                
            except RuntimeError as e:
                print(f"\n❌ Ошибка: {e}")
                # При ошибке — получаем handoff-контекст для retry с другим провайдером
                handoff = memory.get_handoff_context()
                if handoff:
                    print(f"   📋 Контекст сохранён, пробую другого провайдера...")
                    try:
                        response = await client.complete(
                            prompt=user_input,
                            system_prompt=context["system_prompt"],
                            handoff_context=handoff,
                            max_tokens=2048,
                            temperature=0.7,
                        )
                        memory.record_exchange(
                            user_message=user_input,
                            assistant_response=response.text,
                            model=response.model,
                            provider=response.provider_name,
                            tokens_used=response.tokens_used,
                        )
                        print(f"\n🤖 [{response.provider_name} / {response.model}] ({response.latency_ms:.0f}ms):")
                        print(f"   {response.text}")
                    except RuntimeError as e2:
                        print(f"   ❌ Все провайдеры недоступны: {e2}")
    
    finally:
        # Сохраняем сессию при выходе
        memory.end_session()
        await client.stop()
        print("\n💾 Сессия сохранена. До встречи!")


async def cmd_serve(providers: List[Provider], memory: Memory, host: str = "0.0.0.0", port: int = 8000):
    """Запуск OpenAI-совместимого API сервера с памятью."""
    try:
        from aiohttp import web
    except ImportError:
        print("❌ Установите aiohttp: pip install aiohttp")
        return
    
    client = SuperRouterClient(providers)
    await client.start()
    
    # Словарь сессий по session_id (для мульти-клиентов)
    sessions = {}
    
    async def handle_chat_completions(request):
        """POST /v1/chat/completions — с поддержкой памяти."""
        try:
            data = await request.json()
            messages = data.get("messages", [])
            model = data.get("model")
            max_tokens = data.get("max_tokens", 2048)
            temperature = data.get("temperature", 0.7)
            
            # Опциональные параметры памяти (расширение API)
            session_id = data.get("session_id", "default")
            use_memory = data.get("use_memory", True)
            paradigm = data.get("paradigm")
            
            # Извлекаем промпт
            prompt = messages[-1]["content"] if messages else ""
            system_prompt = None
            for msg in messages:
                if msg.get("role") == "system":
                    system_prompt = msg["content"]
                    break
            
            # Управление сессией
            if session_id not in sessions:
                sessions[session_id] = memory.start_session(session_id)
            
            # Устанавливаем парадигму если передана
            if paradigm:
                memory.set_paradigm(paradigm)
            
            # Обогащаем контекст из памяти
            if use_memory:
                context = memory.get_context(prompt, system_prompt)
                # Собираем полные messages: system (обогащённый) + история + текущий
                full_messages = []
                if context["system_prompt"]:
                    full_messages.append({"role": "system", "content": context["system_prompt"]})
                full_messages.extend(context["messages"])
            else:
                # Без памяти — передаём messages как есть от клиента
                full_messages = messages
                context = {"metadata": {"facts_used": 0}}
            
            # Запрос к LLM с полной историей
            response = await client.complete(
                messages=full_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                preferred_model=model,
            )
            
            # Записываем в память
            if use_memory:
                memory.record_exchange(
                    user_message=prompt,
                    assistant_response=response.text,
                    model=response.model,
                    provider=response.provider_name,
                    tokens_used=response.tokens_used,
                )
            
            # Формат OpenAI
            result = {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": response.model,
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": response.text},
                    "finish_reason": response.finish_reason,
                }],
                "usage": {
                    "prompt_tokens": len(prompt.split()),
                    "completion_tokens": response.tokens_used,
                    "total_tokens": response.tokens_used + len(prompt.split()),
                },
                "_router_meta": {
                    "provider": response.provider_name,
                    "provider_id": response.provider_id,
                    "latency_ms": response.latency_ms,
                    "session_id": session_id,
                    "memory_facts_used": context["metadata"]["facts_used"] if use_memory else 0,
                }
            }
            return web.json_response(result)
            
        except Exception as e:
            logger.error(f"Ошибка в chat/completions: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def handle_models(request):
        """GET /v1/models"""
        models = client.get_models()
        return web.json_response({
            "object": "list",
            "data": [
                {
                    "id": m["model"],
                    "object": "model",
                    "owned_by": m["provider"],
                }
                for m in models
            ]
        })
    
    async def handle_status(request):
        """GET /status"""
        router_status = client.get_status()
        memory_stats = memory.get_stats()
        return web.json_response({
            "router": router_status,
            "memory": memory_stats,
        })
    
    async def handle_memory_search(request):
        """GET /memory/search?q=query"""
        query = request.query.get("q", "")
        if not query:
            return web.json_response({"error": "Parameter 'q' required"}, status=400)
        results = memory.search_memory(query)
        return web.json_response({"results": results})
    
    async def handle_memory_facts(request):
        """GET /memory/facts"""
        category = request.query.get("category")
        facts = memory.get_facts(category)
        return web.json_response({"facts": facts})
    
    async def handle_memory_add_fact(request):
        """POST /memory/facts — добавить факт вручную."""
        data = await request.json()
        content = data.get("content", "")
        category = data.get("category", "manual")
        tags = data.get("tags", [])
        if not content:
            return web.json_response({"error": "Field 'content' required"}, status=400)
        memory.add_fact(content, category, tags)
        return web.json_response({"status": "ok", "content": content})
    
    async def handle_memory_paradigm(request):
        """POST /memory/paradigm — установить парадигму."""
        data = await request.json()
        paradigm = data.get("paradigm")
        memory.set_paradigm(paradigm)
        return web.json_response({"status": "ok", "paradigm": paradigm})
    
    app = web.Application()
    
    # Стандартные OpenAI-совместимые эндпоинты
    app.router.add_post("/v1/chat/completions", handle_chat_completions)
    app.router.add_get("/v1/models", handle_models)
    
    # Расширенные эндпоинты
    app.router.add_get("/status", handle_status)
    app.router.add_get("/memory/search", handle_memory_search)
    app.router.add_get("/memory/facts", handle_memory_facts)
    app.router.add_post("/memory/facts", handle_memory_add_fact)
    app.router.add_post("/memory/paradigm", handle_memory_paradigm)
    
    print(f"\n🚀 AI Super Router API v2.0 (с памятью 🧠) запущен на http://{host}:{port}")
    print(f"   OpenAI-совместимый: http://{host}:{port}/v1/chat/completions")
    print(f"   Статус + память:    http://{host}:{port}/status")
    print(f"   Модели:             http://{host}:{port}/v1/models")
    print(f"   Поиск по памяти:    http://{host}:{port}/memory/search?q=...")
    print(f"   Факты:              http://{host}:{port}/memory/facts")
    print(f"   Парадигма:          POST http://{host}:{port}/memory/paradigm")
    print(f"\n   Расширения API (в теле запроса /v1/chat/completions):")
    print(f"     session_id: str   — ID сессии (для сохранения контекста)")
    print(f"     use_memory: bool  — использовать память (default: true)")
    print(f"     paradigm: str     — активная парадигма восприятия")
    print()
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    
    # Ждём вечно
    await asyncio.Event().wait()


async def cmd_memory(memory: Memory):
    """Управление памятью."""
    if len(sys.argv) < 3:
        print("\n🧠 Управление памятью:")
        print("  python main.py memory stats      — Статистика")
        print("  python main.py memory facts      — Все факты")
        print("  python main.py memory entities   — Все сущности")
        print("  python main.py memory search <q> — Поиск")
        print("  python main.py memory sessions   — Список сессий")
        print("  python main.py memory add <text> — Добавить факт")
        print("  python main.py memory clear      — Очистить (осторожно!)")
        return
    
    subcmd = sys.argv[2].lower()
    
    if subcmd == "stats":
        stats = memory.get_stats()
        print(f"\n🧠 Статистика памяти:")
        print(f"   Фактов: {stats['total_facts']}")
        print(f"   Сущностей: {stats['total_entities']}")
        print(f"   Сессий: {stats['total_sessions']}")
        if stats["facts_by_category"]:
            print(f"   По категориям: {json.dumps(stats['facts_by_category'], ensure_ascii=False)}")
        if stats["entities_by_type"]:
            print(f"   По типам: {json.dumps(stats['entities_by_type'], ensure_ascii=False)}")
    
    elif subcmd == "facts":
        category = sys.argv[3] if len(sys.argv) > 3 else None
        facts = memory.get_facts(category)
        print(f"\n📌 Факты ({len(facts)}):")
        for f in facts:
            print(f"   [{f['category']}] {f['content']}")
            if f['tags']:
                print(f"       tags: {', '.join(f['tags'])}")
    
    elif subcmd == "entities":
        entities = memory.storage.get_all_entities()
        print(f"\n🏷️ Сущности ({len(entities)}):")
        for e in entities:
            print(f"   [{e.entity_type}] {e.name}: {e.description[:60]}")
            if e.relations:
                for r in e.relations:
                    print(f"       → {r['relation_type']} → {r['target_name']}")
    
    elif subcmd == "search":
        query = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
        if not query:
            print("   Укажите запрос: python main.py memory search <запрос>")
            return
        results = memory.search_memory(query)
        print(f"\n🔍 Результаты для '{query}' ({len(results)}):")
        for r in results:
            if r["type"] == "fact":
                print(f"   📌 [{r['category']}] {r['content']}")
            else:
                print(f"   🏷️ [{r['entity_type']}] {r['name']}: {r['description']}")
    
    elif subcmd == "sessions":
        sessions = memory.storage.list_sessions(limit=20)
        print(f"\n📂 Последние сессии ({len(sessions)}):")
        for s in sessions:
            from datetime import datetime
            dt = datetime.fromtimestamp(s["started"]).strftime("%Y-%m-%d %H:%M")
            print(f"   {dt} | {s['id']} | {s['message_count']} сообщ. | {s['topic'] or s['summary'][:50]}")
    
    elif subcmd == "add":
        text = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
        if not text:
            print("   Укажите факт: python main.py memory add <текст факта>")
            return
        memory.add_fact(text, category="manual")
        print(f"   📌 Факт добавлен: {text}")
    
    elif subcmd == "clear":
        confirm = input("   ⚠️ Удалить ВСЮ память? (yes/no): ").strip()
        if confirm.lower() == "yes":
            import shutil
            storage_dir = Path(memory.config.storage_dir)
            if storage_dir.exists():
                shutil.rmtree(storage_dir)
                print("   🗑️ Память очищена.")
            else:
                print("   Память уже пуста.")
        else:
            print("   Отменено.")
    
    else:
        print(f"   ❌ Неизвестная подкоманда: {subcmd}")


async def cmd_status(providers: List[Provider], memory: Memory):
    """Полный статус системы."""
    print("\n" + "═" * 60)
    print("   🌐 AI SUPER ROUTER v2.0 — ПОЛНЫЙ СТАТУС")
    print("═" * 60)
    
    # Здоровье API
    await cmd_health(providers)
    
    # Вычислительные ресурсы
    await cmd_compute()
    
    # Память
    stats = memory.get_stats()
    print(f"\n🧠 Память: {stats['total_facts']} фактов, {stats['total_entities']} сущностей, {stats['total_sessions']} сессий")
    if stats["active_paradigm"]:
        print(f"   🔮 Парадигма: {stats['active_paradigm']}")
    
    # Последнее сканирование
    scanner = ResourceScanner()
    report = scanner.get_report()
    print(f"\n🔍 Обнаружено ресурсов: {report['total_discovered']} (верифицировано: {report['verified']})")
    
    print("\n" + "═" * 60)


def main():
    """Точка входа."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    
    command = sys.argv[1].lower()
    providers = load_providers()
    
    # Инициализация памяти
    mem_config = load_memory_config()
    memory = Memory(mem_config)
    
    print(f"📦 Загружено {len(providers)} провайдеров")
    configured = sum(1 for p in providers if not p.api_key.startswith("YOUR_"))
    print(f"🔑 Настроено ключей: {configured}/{len(providers)}")
    
    stats = memory.get_stats()
    print(f"🧠 Память: {stats['total_facts']} фактов, {stats['total_entities']} сущностей")
    
    if command == "health":
        asyncio.run(cmd_health(providers))
    elif command == "models":
        asyncio.run(cmd_models(providers))
    elif command == "compute":
        asyncio.run(cmd_compute())
    elif command == "scan":
        asyncio.run(cmd_scan())
    elif command == "chat":
        asyncio.run(cmd_chat(providers, memory))
    elif command == "serve":
        host = sys.argv[2] if len(sys.argv) > 2 else "0.0.0.0"
        port = int(sys.argv[3]) if len(sys.argv) > 3 else 8000
        asyncio.run(cmd_serve(providers, memory, host, port))
    elif command == "memory":
        asyncio.run(cmd_memory(memory))
    elif command == "status":
        asyncio.run(cmd_status(providers, memory))
    else:
        print(f"❌ Неизвестная команда: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
