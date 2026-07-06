"""
🏥 AI Super Router — Проверка здоровья провайдеров
===================================================
Проверяет доступность серверов и моделей БЕЗ API-ключей (где возможно)
и С ключами (минимальный запрос для верификации).
"""

import asyncio
import aiohttp
import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from .router import Provider, ProviderStatus

logger = logging.getLogger("ai_router.health")


@dataclass
class HealthCheckResult:
    provider_id: str
    is_alive: bool
    latency_ms: float
    status_code: int
    models_available: List[str]
    error: Optional[str] = None
    checked_at: float = 0

    def __post_init__(self):
        if not self.checked_at:
            self.checked_at = time.time()


class HealthChecker:
    """
    Проверяет доступность провайдеров.
    
    Три уровня проверки:
    1. Ping (без ключа) — сервер отвечает?
    2. Models (с ключом) — какие модели доступны?
    3. Inference (с ключом) — модель реально работает?
    """
    
    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self.results: Dict[str, HealthCheckResult] = {}
    
    async def check_all(self, providers: Dict[str, Provider]) -> Dict[str, HealthCheckResult]:
        """Проверяет все провайдеры параллельно."""
        tasks = []
        for provider in providers.values():
            tasks.append(self._check_provider(provider))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, HealthCheckResult):
                self.results[result.provider_id] = result
            elif isinstance(result, Exception):
                logger.error(f"Health check error: {result}")
        
        return self.results
    
    async def _check_provider(self, provider: Provider) -> HealthCheckResult:
        """Полная проверка одного провайдера."""
        start = time.time()
        
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as session:
                
                # Уровень 1: Ping (без ключа)
                is_alive, status_code = await self._ping(session, provider)
                
                if not is_alive:
                    latency = (time.time() - start) * 1000
                    provider.status = ProviderStatus.UNAVAILABLE
                    return HealthCheckResult(
                        provider_id=provider.id,
                        is_alive=False,
                        latency_ms=latency,
                        status_code=status_code,
                        models_available=[],
                        error=f"Server unreachable (HTTP {status_code})"
                    )
                
                # Уровень 2: Проверка моделей (с ключом)
                models = await self._check_models(session, provider)
                
                latency = (time.time() - start) * 1000
                provider.status = ProviderStatus.ACTIVE
                provider.last_health_check = time.time()
                provider.avg_latency_ms = latency
                
                return HealthCheckResult(
                    provider_id=provider.id,
                    is_alive=True,
                    latency_ms=latency,
                    status_code=200,
                    models_available=models or provider.models,
                )
                
        except asyncio.TimeoutError:
            provider.status = ProviderStatus.UNAVAILABLE
            return HealthCheckResult(
                provider_id=provider.id,
                is_alive=False,
                latency_ms=self.timeout * 1000,
                status_code=0,
                models_available=[],
                error="Timeout"
            )
        except Exception as e:
            provider.status = ProviderStatus.ERROR
            return HealthCheckResult(
                provider_id=provider.id,
                is_alive=False,
                latency_ms=(time.time() - start) * 1000,
                status_code=0,
                models_available=[],
                error=str(e)
            )
    
    async def _ping(self, session: aiohttp.ClientSession, provider: Provider) -> Tuple[bool, int]:
        """
        Уровень 1: Проверка что сервер отвечает.
        Не требует API-ключа — просто HTTP GET на health_url.
        """
        try:
            # Пробуем без авторизации
            async with session.get(
                provider.health_url,
                headers={"User-Agent": "AI-Super-Router/1.0"},
                allow_redirects=True,
                ssl=True
            ) as resp:
                # Любой ответ (даже 401/403) означает что сервер жив
                if resp.status < 500:
                    return True, resp.status
                return False, resp.status
        except aiohttp.ClientError:
            return False, 0
    
    async def _check_models(self, session: aiohttp.ClientSession, provider: Provider) -> Optional[List[str]]:
        """
        Уровень 2: Проверка доступных моделей.
        Требует API-ключ.
        """
        if provider.api_key.startswith("YOUR_"):
            # Ключ не настроен — пропускаем
            return None
        
        models_url = self._get_models_url(provider)
        if not models_url:
            return None
        
        headers = self._get_auth_headers(provider)
        
        try:
            async with session.get(models_url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return self._parse_models_response(data, provider)
                else:
                    return None
        except Exception:
            return None
    
    async def check_inference(self, session: aiohttp.ClientSession, provider: Provider, model: str) -> bool:
        """
        Уровень 3: Проверка что модель реально отвечает.
        Минимальный запрос (1 токен).
        """
        if provider.api_key.startswith("YOUR_"):
            return False
        
        try:
            url, headers, payload = self._build_test_request(provider, model)
            
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status == 200:
                    return True
                elif resp.status == 429:
                    provider.status = ProviderStatus.RATE_LIMITED
                    return False
                else:
                    return False
        except Exception:
            return False
    
    def _get_models_url(self, provider: Provider) -> Optional[str]:
        """Возвращает URL для получения списка моделей."""
        format_urls = {
            "openai": f"{provider.base_url}/models",
            "gemini": f"https://generativelanguage.googleapis.com/v1beta/models?key={provider.api_key}",
            "cohere": "https://api.cohere.com/v1/models",
            "huggingface": None,  # HF не имеет единого /models
            "cloudflare": None,
        }
        return format_urls.get(provider.format)
    
    def _get_auth_headers(self, provider: Provider) -> Dict[str, str]:
        """Возвращает заголовки авторизации."""
        headers = {"Content-Type": "application/json"}
        
        if provider.format == "openai":
            headers["Authorization"] = f"Bearer {provider.api_key}"
        elif provider.format == "cohere":
            headers["Authorization"] = f"Bearer {provider.api_key}"
        elif provider.format == "huggingface":
            headers["Authorization"] = f"Bearer {provider.api_key}"
        elif provider.format == "cloudflare":
            headers["Authorization"] = f"Bearer {provider.api_key}"
        # Gemini использует key в URL
        
        return headers
    
    def _parse_models_response(self, data: dict, provider: Provider) -> List[str]:
        """Парсит ответ /models в зависимости от формата."""
        models = []
        
        if provider.format == "openai":
            for model in data.get("data", []):
                models.append(model.get("id", ""))
        elif provider.format == "gemini":
            for model in data.get("models", []):
                name = model.get("name", "").replace("models/", "")
                models.append(name)
        elif provider.format == "cohere":
            for model in data.get("models", []):
                models.append(model.get("name", ""))
        
        return models
    
    def _build_test_request(self, provider: Provider, model: str) -> Tuple[str, Dict, Dict]:
        """Строит минимальный тестовый запрос."""
        headers = self._get_auth_headers(provider)
        
        if provider.format == "openai":
            url = f"{provider.base_url}/chat/completions"
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 1,
                "temperature": 0,
            }
        elif provider.format == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={provider.api_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": "Hi"}]}],
                "generationConfig": {"maxOutputTokens": 1}
            }
        elif provider.format == "cohere":
            url = f"{provider.base_url}/chat"
            payload = {
                "model": model,
                "message": "Hi",
                "max_tokens": 1,
            }
        else:
            url = f"{provider.base_url}/chat/completions"
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 1,
            }
        
        return url, headers, payload


class PeriodicHealthMonitor:
    """Периодическая проверка здоровья в фоне."""
    
    def __init__(self, checker: HealthChecker, providers: Dict[str, Provider], interval: int = 300):
        self.checker = checker
        self.providers = providers
        self.interval = interval
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Запускает фоновый мониторинг."""
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info(f"🏥 Health monitor started (interval: {self.interval}s)")
    
    async def stop(self):
        """Останавливает мониторинг."""
        self._running = False
        if self._task:
            self._task.cancel()
    
    async def _monitor_loop(self):
        """Основной цикл мониторинга."""
        while self._running:
            try:
                results = await self.checker.check_all(self.providers)
                
                active = sum(1 for r in results.values() if r.is_alive)
                total = len(results)
                logger.info(f"🏥 Health check: {active}/{total} providers active")
                
                # Логируем проблемные
                for pid, result in results.items():
                    if not result.is_alive:
                        logger.warning(f"   ❌ {pid}: {result.error}")
                
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
            
            await asyncio.sleep(self.interval)
