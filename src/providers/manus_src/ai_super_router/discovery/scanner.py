"""
🔍 AI Super Router — Модуль обнаружения новых ресурсов
=======================================================
Периодически ищет в сети:
- Новые бесплатные AI API
- Новые бесплатные вычислительные мощности
- Обновления лимитов существующих провайдеров
"""

import asyncio
import aiohttp
import re
import json
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger("ai_router.discovery")


@dataclass
class DiscoveredResource:
    """Обнаруженный ресурс."""
    name: str
    type: str  # "api" | "compute"
    url: str
    description: str
    source: str  # Где нашли
    discovered_at: float
    verified: bool = False
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}
        if not self.discovered_at:
            self.discovered_at = time.time()


class ResourceScanner:
    """
    Сканер новых бесплатных ресурсов.
    
    Источники:
    1. GitHub — репозитории с коллекциями бесплатных API
    2. Reddit — r/LocalLLaMA, r/MachineLearning
    3. Awesome-lists — awesome-free-ai, awesome-llm
    4. Status pages — проверка новых моделей у существующих провайдеров
    """
    
    # Известные источники для мониторинга
    GITHUB_SOURCES = [
        "https://api.github.com/repos/cheahjs/free-llm-api-resources/contents/README.md",
        "https://api.github.com/repos/zukixa/cool-ai-stuff/contents/README.md",
        "https://api.github.com/repos/ShaikhWarsi/free-ai-tools/contents/README.md",
        "https://api.github.com/repos/Jeadie/awesome-free-ai/contents/README.md",
    ]
    
    PROVIDER_MODEL_ENDPOINTS = {
        "openrouter": "https://openrouter.ai/api/v1/models",
        "huggingface": "https://huggingface.co/api/models?filter=text-generation&sort=downloads&direction=-1&limit=20",
    }
    
    REDDIT_SEARCHES = [
        "https://www.reddit.com/r/LocalLLaMA/search.json?q=free+api&sort=new&restrict_sr=1&limit=10",
        "https://www.reddit.com/r/MachineLearning/search.json?q=free+gpu+cloud&sort=new&restrict_sr=1&limit=10",
    ]
    
    def __init__(self):
        self.discovered: List[DiscoveredResource] = []
        self.last_scan: float = 0
        self.scan_interval: int = 86400  # Раз в сутки
    
    async def scan_all(self) -> List[DiscoveredResource]:
        """Полное сканирование всех источников."""
        logger.info("🔍 Начинаю сканирование новых ресурсов...")
        
        new_resources = []
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": "AI-Super-Router-Discovery/1.0"}
        ) as session:
            
            # 1. GitHub awesome-lists
            github_results = await self._scan_github(session)
            new_resources.extend(github_results)
            
            # 2. Проверка новых моделей у провайдеров
            model_results = await self._scan_provider_models(session)
            new_resources.extend(model_results)
            
            # 3. Reddit (если доступен)
            reddit_results = await self._scan_reddit(session)
            new_resources.extend(reddit_results)
        
        self.discovered.extend(new_resources)
        self.last_scan = time.time()
        
        logger.info(f"🔍 Сканирование завершено: найдено {len(new_resources)} новых ресурсов")
        return new_resources
    
    async def _scan_github(self, session: aiohttp.ClientSession) -> List[DiscoveredResource]:
        """Сканирует GitHub-репозитории с коллекциями."""
        resources = []
        
        for url in self.GITHUB_SOURCES:
            try:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        content = data.get("content", "")
                        
                        # Декодируем base64
                        import base64
                        try:
                            text = base64.b64decode(content).decode("utf-8")
                        except Exception:
                            continue
                        
                        # Ищем URL-ы API-провайдеров
                        found = self._extract_api_urls(text)
                        for item in found:
                            resources.append(DiscoveredResource(
                                name=item["name"],
                                type="api",
                                url=item["url"],
                                description=item.get("description", ""),
                                source=url,
                                discovered_at=time.time(),
                            ))
            except Exception as e:
                logger.debug(f"GitHub scan error ({url}): {e}")
        
        return resources
    
    async def _scan_provider_models(self, session: aiohttp.ClientSession) -> List[DiscoveredResource]:
        """Проверяет новые бесплатные модели у провайдеров."""
        resources = []
        
        # OpenRouter — проверяем бесплатные модели
        try:
            async with session.get(self.PROVIDER_MODEL_ENDPOINTS["openrouter"]) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    models = data.get("data", [])
                    
                    free_models = [
                        m for m in models 
                        if m.get("pricing", {}).get("prompt") == "0" 
                        or ":free" in m.get("id", "")
                    ]
                    
                    for model in free_models:
                        resources.append(DiscoveredResource(
                            name=f"OpenRouter: {model.get('id', 'unknown')}",
                            type="api",
                            url="https://openrouter.ai",
                            description=f"Free model: {model.get('name', '')} (context: {model.get('context_length', 'unknown')})",
                            source="openrouter_models_api",
                            discovered_at=time.time(),
                            details={
                                "model_id": model.get("id"),
                                "context_length": model.get("context_length"),
                                "provider": "openrouter",
                            }
                        ))
        except Exception as e:
            logger.debug(f"OpenRouter scan error: {e}")
        
        return resources
    
    async def _scan_reddit(self, session: aiohttp.ClientSession) -> List[DiscoveredResource]:
        """Сканирует Reddit на предмет новых бесплатных ресурсов."""
        resources = []
        
        for url in self.REDDIT_SEARCHES:
            try:
                async with session.get(url, headers={"User-Agent": "AI-Router/1.0"}) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        posts = data.get("data", {}).get("children", [])
                        
                        for post in posts[:5]:
                            post_data = post.get("data", {})
                            title = post_data.get("title", "")
                            selftext = post_data.get("selftext", "")
                            post_url = f"https://reddit.com{post_data.get('permalink', '')}"
                            
                            # Ищем упоминания API/ресурсов
                            if any(kw in title.lower() for kw in ["free", "api", "gpu", "no credit card"]):
                                resources.append(DiscoveredResource(
                                    name=title[:100],
                                    type="api" if "api" in title.lower() else "compute",
                                    url=post_url,
                                    description=selftext[:200],
                                    source="reddit",
                                    discovered_at=time.time(),
                                ))
            except Exception as e:
                logger.debug(f"Reddit scan error: {e}")
        
        return resources
    
    def _extract_api_urls(self, text: str) -> List[Dict[str, str]]:
        """Извлекает URL-ы API из текста."""
        results = []
        
        # Паттерны для API endpoints
        patterns = [
            r'\[([^\]]+)\]\((https?://[^\)]+)\)',  # Markdown ссылки
            r'(https?://api\.[a-zA-Z0-9.-]+)',      # URL-ы начинающиеся с api.
        ]
        
        # Известные ключевые слова для фильтрации
        api_keywords = ["api", "inference", "ai", "llm", "model", "chat", "completion"]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    name, url = match[0], match[1]
                else:
                    name, url = match, match
                
                # Фильтруем по ключевым словам
                if any(kw in url.lower() or kw in name.lower() for kw in api_keywords):
                    results.append({"name": name, "url": url})
        
        return results
    
    async def verify_resource(self, resource: DiscoveredResource) -> bool:
        """Верифицирует обнаруженный ресурс (проверяет что URL отвечает)."""
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            ) as session:
                async with session.get(resource.url) as resp:
                    if resp.status < 500:
                        resource.verified = True
                        return True
        except Exception:
            pass
        
        resource.verified = False
        return False
    
    def get_report(self) -> Dict[str, Any]:
        """Отчёт о найденных ресурсах."""
        return {
            "last_scan": self.last_scan,
            "total_discovered": len(self.discovered),
            "verified": sum(1 for r in self.discovered if r.verified),
            "by_type": {
                "api": sum(1 for r in self.discovered if r.type == "api"),
                "compute": sum(1 for r in self.discovered if r.type == "compute"),
            },
            "recent": [
                {
                    "name": r.name,
                    "type": r.type,
                    "url": r.url,
                    "verified": r.verified,
                }
                for r in sorted(self.discovered, key=lambda x: -x.discovered_at)[:10]
            ]
        }


class PeriodicScanner:
    """Периодический сканер новых ресурсов."""
    
    def __init__(self, scanner: ResourceScanner, interval: int = 86400):
        self.scanner = scanner
        self.interval = interval
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Запуск периодического сканирования."""
        self._running = True
        self._task = asyncio.create_task(self._scan_loop())
        logger.info(f"🔍 Periodic scanner started (interval: {self.interval}s)")
    
    async def stop(self):
        """Остановка."""
        self._running = False
        if self._task:
            self._task.cancel()
    
    async def _scan_loop(self):
        """Цикл сканирования."""
        while self._running:
            try:
                new_resources = await self.scanner.scan_all()
                
                # Верифицируем новые
                for resource in new_resources:
                    await self.scanner.verify_resource(resource)
                    await asyncio.sleep(1)  # Не спамим
                
                verified = sum(1 for r in new_resources if r.verified)
                logger.info(f"🔍 Scan complete: {len(new_resources)} found, {verified} verified")
                
            except Exception as e:
                logger.error(f"Periodic scan error: {e}")
            
            await asyncio.sleep(self.interval)
