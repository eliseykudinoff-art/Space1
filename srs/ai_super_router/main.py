"""
🌐 AI Super Router — Главный модуль
=====================================
Запуск: python main.py [команда]

Команды:
  serve       — Запустить как OpenAI-совместимый API сервер
  health      — Проверить здоровье всех провайдеров
  models      — Показать доступные модели
  compute     — Показать вычислительные ресурсы
  scan        — Поиск новых бесплатных ресурсов
  chat        — Интерактивный чат
  status      — Полный статус системы
"""

import asyncio
import sys
import json
import yaml
import logging
from pathlib import Path
from typing import List

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("ai_router")

# Импорты модулей
from space1.ai_super_router.core.router import Provider, RoutingStrategy
from space1.ai_super_router.core.client import SuperRouterClient
from space1.ai_super_router.core.health_checker import HealthChecker
from space1.ai_super_router.compute.aggregator import ComputeAggregator
from space1.ai_super_router.discovery.scanner import ResourceScanner


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
        # Пропускаем провайдеров без ключа (заглушки)
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
            enabled=p_data.get("enabled", True),
        )
        providers.append(provider)
    
    return providers


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
    
    # Сначала проверяем здоровье
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


async def cmd_chat(providers: List[Provider]):
    """Интерактивный чат."""
    print("\n💬 AI Super Router — Интерактивный чат")
    print("    Введите сообщение или 'quit' для выхода")
    print("    Команды: /status, /models, /provider <id>\n")
    
    client = SuperRouterClient(providers)
    await client.start()
    
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
            
            if user_input.startswith("/status"):
                status = client.get_status()
                print(json.dumps(status, indent=2, ensure_ascii=False))
                continue
            
            if user_input.startswith("/models"):
                models = client.get_models()
                for m in models:
                    print(f"  {m['model']} ({m['provider']})")
                continue
            
            # Обычный запрос
            try:
                response = await client.complete(user_input)
                print(f"\n🤖 [{response.provider_name} / {response.model}] ({response.latency_ms:.0f}ms):")
                print(f"   {response.text}")
            except RuntimeError as e:
                print(f"\n❌ Ошибка: {e}")
    
    finally:
        await client.stop()


async def cmd_serve(providers: List[Provider], host: str = "0.0.0.0", port: int = 8000):
    """Запуск OpenAI-совместимого API сервера."""
    try:
        from aiohttp import web
    except ImportError:
        print("❌ Установите aiohttp: pip install aiohttp")
        return
    
    client = SuperRouterClient(providers)
    await client.start()
    
    async def handle_chat_completions(request):
        """POST /v1/chat/completions"""
        try:
            data = await request.json()
            messages = data.get("messages", [])
            model = data.get("model")
            max_tokens = data.get("max_tokens", 2048)
            temperature = data.get("temperature", 0.7)
            
            # Извлекаем промпт
            prompt = messages[-1]["content"] if messages else ""
            system_prompt = None
            for msg in messages:
                if msg.get("role") == "system":
                    system_prompt = msg["content"]
                    break
            
            response = await client.complete(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                preferred_model=model,
            )
            
            # Формат OpenAI
            return web.json_response({
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
                }
            })
        except Exception as e:
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
        return web.json_response(client.get_status())
    
    import time
    app = web.Application()
    app.router.add_post("/v1/chat/completions", handle_chat_completions)
    app.router.add_get("/v1/models", handle_models)
    app.router.add_get("/status", handle_status)
    
    print(f"\n🚀 AI Super Router API запущен на http://{host}:{port}")
    print(f"   OpenAI-совместимый endpoint: http://{host}:{port}/v1/chat/completions")
    print(f"   Статус: http://{host}:{port}/status")
    print(f"   Модели: http://{host}:{port}/v1/models\n")
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    
    # Ждём вечно
    await asyncio.Event().wait()


async def cmd_status(providers: List[Provider]):
    """Полный статус системы."""
    print("\n" + "═" * 60)
    print("   🌐 AI SUPER ROUTER — ПОЛНЫЙ СТАТУС")
    print("═" * 60)
    
    # Здоровье API
    await cmd_health(providers)
    
    # Вычислительные ресурсы
    await cmd_compute()
    
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
    
    print(f"📦 Загружено {len(providers)} провайдеров")
    
    configured = sum(1 for p in providers if not p.api_key.startswith("YOUR_"))
    print(f"🔑 Настроено ключей: {configured}/{len(providers)}")
    
    if command == "health":
        asyncio.run(cmd_health(providers))
    elif command == "models":
        asyncio.run(cmd_models(providers))
    elif command == "compute":
        asyncio.run(cmd_compute())
    elif command == "scan":
        asyncio.run(cmd_scan())
    elif command == "chat":
        asyncio.run(cmd_chat(providers))
    elif command == "serve":
        host = sys.argv[2] if len(sys.argv) > 2 else "0.0.0.0"
        port = int(sys.argv[3]) if len(sys.argv) > 3 else 8000
        asyncio.run(cmd_serve(providers, host, port))
    elif command == "status":
        asyncio.run(cmd_status(providers))
    else:
        print(f"❌ Неизвестная команда: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
