"""
🔌 AI Super Router — Унифицированный клиент
=============================================
Единый интерфейс для всех провайдеров.
Автоматический retry и fallback.
"""

import asyncio
import aiohttp
import time
import json
import logging
import re
from typing import Optional, Dict, List, Any, AsyncGenerator, Tuple
from dataclasses import dataclass
from enum import Enum

from .router import AIRouter, Provider, ProviderStatus, RoutingStrategy, CapabilityType
from .health_checker import HealthChecker, PeriodicHealthMonitor

logger = logging.getLogger("ai_router.client")


class ErrorType(Enum):
    """Классификация ошибок для retry策略."""
    TRANSIENT = "transient"       # Временные - можно retry
    RATE_LIMIT = "rate_limit"     # Rate limit - backoff нужен
    AUTH_ERROR = "auth_error"     # Auth ошибки - retry бесполезен
    SERVER_ERROR = "server_error" # 5xx - можно retry
    CLIENT_ERROR = "client_error" # 4xx кроме rate limit - не retry
    PERMANENT = "permanent"       # Постоянные - не retry
    NETWORK = "network"          # Сетевые проблемы


class ErrorClassifier:
    """
    Классификатор ошибок для определения retry стратегии.
    
    BUG-034 FIX: Раньше все ошибки обрабатывались одинаково,
    теперь ошибки классифицируются для правильного retry решения.
    """
    
    # Транзиентные ошибки - можно retry сразу
    TRANSIENT_PATTERNS = [
        "connection refused",
        "connection reset",
        "connection timeout",
        "temporary failure",
        "service unavailable",
        "bad gateway",
        "gateway timeout",
    ]
    
    # Rate limit ошибки
    RATE_LIMIT_PATTERNS = [
        "429",
        "rate limit",
        "rate_limit",
        "too many requests",
        "quota exceeded",
        "max retries",
    ]
    
    # Auth ошибки - retry бесполезен
    AUTH_PATTERNS = [
        "401",
        "403",
        "authentication",
        "unauthorized",
        "invalid api key",
        "api key invalid",
        "permission denied",
        "forbidden",
    ]
    
    # Server errors - можно retry
    SERVER_PATTERNS = [
        "500",
        "502",
        "503",
        "504",
        "internal server error",
        "bad gateway",
        "service unavailable",
        "gateway timeout",
    ]
    
    # Client errors - не retry
    CLIENT_PATTERNS = [
        "400",
        "bad request",
        "invalid request",
        "invalid parameters",
        "malformed",
        "validation error",
    ]
    
    # Permanent ошибки - не retry
    PERMANENT_PATTERNS = [
        "not found",
        "404",
        "method not allowed",
        "405",
        "unsupported",
        "model not found",
        "does not exist",
    ]
    
    @classmethod
    def classify(cls, error: str, status_code: int = 0) -> Tuple[ErrorType, bool]:
        """
        Классифицирует ошибку и определяет, нужно ли retry.
        
        Args:
            error: Текст ошибки
            status_code: HTTP статус код (если есть)
            
        Returns:
            Tuple[ErrorType, should_retry]
        """
        error_lower = error.lower()
        
        # Проверяем по паттернам в порядке приоритета
        # Rate limit - высший приоритет
        for pattern in cls.RATE_LIMIT_PATTERNS:
            if pattern.lower() in error_lower or str(status_code) in pattern:
                return ErrorType.RATE_LIMIT, True
        
        # Auth ошибки
        for pattern in cls.AUTH_PATTERNS:
            if pattern.lower() in error_lower or str(status_code) == pattern:
                return ErrorType.AUTH_ERROR, False
        
        # Permanent ошибки
        for pattern in cls.PERMANENT_PATTERNS:
            if pattern.lower() in error_lower or str(status_code) == pattern:
                return ErrorType.PERMANENT, False
        
        # Server errors
        for pattern in cls.SERVER_PATTERNS:
            if pattern.lower() in error_lower or str(status_code) in pattern:
                return ErrorType.SERVER_ERROR, True
        
        # Client errors
        for pattern in cls.CLIENT_PATTERNS:
            if pattern.lower() in error_lower or str(status_code) == pattern:
                return ErrorType.CLIENT_ERROR, False
        
        # Network/transient
        for pattern in cls.TRANSIENT_PATTERNS:
            if pattern.lower() in error_lower:
                return ErrorType.NETWORK, True
        
        # По умолчанию - transient (лучше попробовать, чем пропустить)
        if status_code >= 500:
            return ErrorType.SERVER_ERROR, True
        
        # Timeout
        if "timeout" in error_lower:
            return ErrorType.NETWORK, True
        
        # По умолчанию - TRANSIENT
        return ErrorType.TRANSIENT, True
    
    @classmethod
    def get_retry_delay(cls, error_type: ErrorType, attempt: int) -> float:
        """
        Возвращает delay перед retry в зависимости от типа ошибки.
        
        Args:
            error_type: Тип ошибки
            attempt: Номер попытки (0-based)
            
        Returns:
            Delay в секундах
        """
        base_delay = 1.0
        
        if error_type == ErrorType.RATE_LIMIT:
            # Exponential backoff для rate limit
            return min(60.0, base_delay * (2 ** attempt) * 5)
        elif error_type == ErrorType.SERVER_ERROR:
            # Standard exponential backoff
            return min(30.0, base_delay * (2 ** attempt))
        elif error_type == ErrorType.NETWORK:
            # Longer delay для network issues
            return min(15.0, base_delay * (2 ** attempt) * 2)
        else:
            # Minimal delay для остальных
            return base_delay * (2 ** min(attempt, 3))


class ResponseValidator:
    """
    Валидатор ответов от AI провайдеров.
    
    BUG-032 FIX: Раньше не было защиты от плохих ответов.
    Теперь ответы проверяются на минимальное качество.
    """
    
    # Минимальная длина ответа (символов)
    MIN_RESPONSE_LENGTH = 10
    
    # Минимальная длина ответа для кода (символов)
    MIN_CODE_RESPONSE_LENGTH = 50
    
    # Паттерны "плохих" ответов
    BAD_RESPONSE_PATTERNS = [
        "i'm sorry, but i can't",
        "i cannot",
        "unable to",
        "error",
        "something went wrong",
        "please try again",
        "null",
        "undefined",
        "none",
    ]
    
    @classmethod
    def validate_response(cls, response: Dict, prompt: str = "") -> Tuple[bool, str]:
        """
        Проверяет качество ответа от провайдера.
        
        Args:
            response: Ответ от провайдера
            prompt: Оригинальный промпт (для доп. проверок)
            
        Returns:
            Tuple[is_valid, reason]
        """
        # Проверяем наличие choices
        if "choices" not in response:
            return False, "Missing 'choices' in response"
        
        if not response["choices"]:
            return False, "Empty 'choices' in response"
        
        choice = response["choices"][0]
        
        # Проверяем наличие message
        if "message" not in choice:
            return False, "Missing 'message' in choice"
        
        message = choice["message"]
        
        # Проверяем наличие content
        if "content" not in message:
            return False, "Missing 'content' in message"
        
        content = message["content"]
        
        # Проверяем что content - строка
        if not isinstance(content, str):
            return False, f"Content is not a string: {type(content).__name__}"
        
        # Проверяем минимальную длину
        if len(content.strip()) < cls.MIN_RESPONSE_LENGTH:
            return False, f"Response too short: {len(content)} chars"
        
        # Проверяем на паттерны "плохих" ответов
        content_lower = content.lower()
        for pattern in cls.BAD_RESPONSE_PATTERNS:
            if pattern in content_lower:
                # Исключаем нормальные фразы
                if pattern == "error" and "error handling" in content_lower:
                    continue
                return False, f"Suspicious pattern in response: '{pattern}'"
        
        # Проверяем на "empty" контент
        if content.strip() in ["", "null", "undefined", "none"]:
            return False, "Response is empty or null"
        
        # Проверяем finish_reason
        finish_reason = choice.get("finish_reason", "")
        if finish_reason in ["length", "content_filter"]:
            return False, f"Bad finish_reason: {finish_reason}"
        
        return True, "OK"
    
    @classmethod
    def extract_and_validate(cls, response: Dict, prompt: str = "") -> Tuple[str, bool, str]:
        """
        Извлекает текст и валидирует ответ.
        
        Returns:
            Tuple[text, is_valid, reason]
        """
        # Сначала валидируем
        is_valid, reason = cls.validate_response(response, prompt)
        
        # Извлекаем текст
        try:
            text = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            text = ""
            is_valid = False
            reason = "Failed to extract content"
        
        return text, is_valid, reason


@dataclass
class CompletionResponse:
    """Унифицированный ответ от любого провайдера."""
    text: str
    model: str
    provider_id: str
    provider_name: str
    tokens_used: int
    latency_ms: float
    finish_reason: str = "stop"
    raw_response: Optional[Dict] = None


class SuperRouterClient:
    """
    Главный клиент суперроутера.
    
    Использование:
        client = SuperRouterClient(providers)
        response = await client.complete("Напиши hello world на Python")
    """
    
    def __init__(self, 
                 providers: List[Provider],
                 strategy: RoutingStrategy = RoutingStrategy.MAXIMIZE_UPTIME,
                 max_retries: int = 3,
                 health_check_interval: int = 300):
        
        self.router = AIRouter(providers, strategy)
        self.health_checker = HealthChecker(timeout=10.0)
        self.max_retries = max_retries
        self.health_check_interval = health_check_interval
        self._monitor: Optional[PeriodicHealthMonitor] = None
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def start(self):
        """Инициализация: проверка здоровья + запуск мониторинга."""
        self._session = aiohttp.ClientSession()
        
        # Первичная проверка здоровья
        logger.info("🚀 Запуск AI Super Router...")
        logger.info("🏥 Первичная проверка провайдеров...")
        
        results = await self.health_checker.check_all(self.router.providers)
        
        active = sum(1 for r in results.values() if r.is_alive)
        total = len(results)
        logger.info(f"✅ Готово: {active}/{total} провайдеров активны")
        
        # Запуск фонового мониторинга
        self._monitor = PeriodicHealthMonitor(
            self.health_checker, 
            self.router.providers, 
            self.health_check_interval
        )
        await self._monitor.start()
    
    async def stop(self):
        """Остановка клиента."""
        if self._monitor:
            await self._monitor.stop()
        if self._session:
            await self._session.close()
    
    async def complete(self,
                       prompt: str,
                       system_prompt: Optional[str] = None,
                       max_tokens: int = 2048,
                       temperature: float = 0.7,
                       preferred_model: Optional[str] = None,
                       preferred_provider: Optional[str] = None,
                       required_capability: Optional[CapabilityType] = None) -> CompletionResponse:
        """
        Отправляет запрос с автоматическим fallback.
        
        BUG-028 FIX: Добавлен параметр required_capability для выбора
        провайдера с нужными способностями.
        
        Args:
            prompt: Текст запроса
            system_prompt: Системный промпт (опционально)
            max_tokens: Максимум токенов в ответе
            temperature: Температура генерации
            preferred_model: Предпочтительная модель
            preferred_provider: Предпочтительный провайдер
            required_capability: Требуемая capability провайдера (BUG-028)
        
        Returns:
            CompletionResponse с ответом
        
        Raises:
            RuntimeError: Если все провайдеры недоступны
        """
        excluded_providers: List[str] = []
        estimated_tokens = len(prompt.split()) * 2 + max_tokens
        
        for attempt in range(self.max_retries * len(self.router.providers)):
            # Выбираем провайдера
            if preferred_provider and attempt == 0:
                provider = self.router.providers.get(preferred_provider)
                if not provider or not provider.budget.can_make_request(estimated_tokens):
                    provider = None
            else:
                provider = None
            
            if not provider:
                provider = self.router.select_provider(
                    estimated_tokens=estimated_tokens,
                    preferred_model=preferred_model,
                    exclude=excluded_providers,
                    required_capability=required_capability
                )
            
            if not provider:
                # Все провайдеры исчерпаны
                break
            
            # Выбираем модель
            model = self._select_model(provider, preferred_model)
            
            logger.debug(f"🔄 Попытка {attempt+1}: {provider.name} / {model}")
            
            try:
                start = time.time()
                response = await self._make_request(provider, model, prompt, system_prompt, max_tokens, temperature)
                latency = (time.time() - start) * 1000
                
                # BUG-032 FIX: Валидируем ответ перед возвратом
                text, is_valid, validation_reason = ResponseValidator.extract_and_validate(response, prompt)
                
                if not is_valid:
                    logger.warning(f"⚠️ Плохой ответ от {provider.name}: {validation_reason}")
                    # Считаем как transient ошибку - retry на другом провайдере
                    self.router.report_failure(provider.id, f"Bad response: {validation_reason}")
                    excluded_providers.append(provider.id)
                    await asyncio.sleep(0.5)
                    continue
                
                # Успех!
                tokens_used = response.get("usage", {}).get("total_tokens", estimated_tokens // 2)
                self.router.report_success(provider.id, tokens_used, latency)
                
                return CompletionResponse(
                    text=text,
                    model=model,
                    provider_id=provider.id,
                    provider_name=provider.name,
                    tokens_used=tokens_used,
                    latency_ms=latency,
                    finish_reason=self._extract_finish_reason(response, provider),
                    raw_response=response,
                )
                
            except Exception as e:
                error_str = str(e)
                
                # BUG-034 FIX: Классифицируем ошибку для правильного retry решения
                error_type, should_retry = ErrorClassifier.classify(error_str)
                logger.warning(f"❌ {provider.name}: [{error_type.value}] {error_str}")
                
                # Для permanent ошибок - не добавляем в retry loop
                if error_type in (ErrorType.PERMANENT, ErrorType.AUTH_ERROR, ErrorType.CLIENT_ERROR):
                    logger.error(f"   ⚠️ Не-retriable ошибка: {error_type.value}")
                    # Для auth ошибок - сразу исключаем провайдер
                    if error_type == ErrorType.AUTH_ERROR:
                        excluded_providers.append(provider.id)
                        # Пропускаем sleep, сразу к следующему провайдеру
                        continue
                
                self.router.report_failure(provider.id, error_str)
                excluded_providers.append(provider.id)
                
                # BUG-034 FIX: Адаптивный delay на основе типа ошибки
                if should_retry:
                    delay = ErrorClassifier.get_retry_delay(error_type, attempt)
                    logger.info(f"   ⏳ Retry через {delay:.1f}s")
                    await asyncio.sleep(delay)
                else:
                    # Для permanent ошибок - минимальный delay
                    await asyncio.sleep(0.5)
        
        raise RuntimeError(
            f"Все провайдеры недоступны после {len(excluded_providers)} попыток. "
            f"Исключены: {excluded_providers}"
        )
    
    async def complete_stream(self,
                              prompt: str,
                              system_prompt: Optional[str] = None,
                              max_tokens: int = 2048,
                              temperature: float = 0.7) -> AsyncGenerator[str, None]:
        """Стриминг ответа (для провайдеров с поддержкой SSE)."""
        provider = self.router.select_provider(estimated_tokens=len(prompt.split()) * 2 + max_tokens)
        
        if not provider:
            yield "❌ Все провайдеры недоступны"
            return
        
        model = self._select_model(provider, None)
        
        if provider.format != "openai":
            # Для не-OpenAI форматов — обычный запрос
            response = await self.complete(prompt, system_prompt, max_tokens, temperature)
            yield response.text
            return
        
        url = f"{provider.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {provider.api_key}",
            "Content-Type": "application/json",
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }
        
        try:
            async with self._session.post(url, headers=headers, json=payload) as resp:
                async for line in resp.content:
                    line = line.decode("utf-8").strip()
                    if line.startswith("data: ") and line != "data: [DONE]":
                        try:
                            data = json.loads(line[6:])
                            delta = data.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"Stream error: {e}")
            # Fallback на обычный запрос
            response = await self.complete(prompt, system_prompt, max_tokens, temperature)
            yield response.text
    
    def _select_model(self, provider: Provider, preferred: Optional[str]) -> str:
        """Выбирает модель из доступных у провайдера."""
        if preferred:
            for model in provider.models:
                if preferred.lower() in model.lower():
                    return model
        
        # Возвращаем первую (обычно лучшую) модель
        return provider.models[0] if provider.models else ""
    
    async def _make_request(self, provider: Provider, model: str,
                            prompt: str, system_prompt: Optional[str],
                            max_tokens: int, temperature: float) -> Dict:
        """Выполняет запрос к провайдеру в нужном формате."""
        
        if provider.format == "openai":
            return await self._request_openai(provider, model, prompt, system_prompt, max_tokens, temperature)
        elif provider.format == "gemini":
            return await self._request_gemini(provider, model, prompt, system_prompt, max_tokens, temperature)
        elif provider.format == "cohere":
            return await self._request_cohere(provider, model, prompt, system_prompt, max_tokens, temperature)
        elif provider.format == "huggingface":
            return await self._request_huggingface(provider, model, prompt, system_prompt, max_tokens, temperature)
        elif provider.format == "cloudflare":
            return await self._request_cloudflare(provider, model, prompt, system_prompt, max_tokens, temperature)
        else:
            # По умолчанию OpenAI-совместимый
            return await self._request_openai(provider, model, prompt, system_prompt, max_tokens, temperature)
    
    async def _request_openai(self, provider, model, prompt, system_prompt, max_tokens, temperature) -> Dict:
        """OpenAI-совместимый запрос."""
        url = f"{provider.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {provider.api_key}",
            "Content-Type": "application/json",
        }
        
        # Для OpenRouter добавляем специальные заголовки
        if provider.id == "openrouter":
            headers["HTTP-Referer"] = "https://github.com/ai-super-router"
            headers["X-Title"] = "AI Super Router"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        async with self._session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=120)) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                raise Exception(f"HTTP {resp.status}: {error_text[:200]}")
            return await resp.json()
    
    async def _request_gemini(self, provider, model, prompt, system_prompt, max_tokens, temperature) -> Dict:
        """Google Gemini API запрос."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={provider.api_key}"
        headers = {"Content-Type": "application/json"}
        
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": system_prompt}]})
            contents.append({"role": "model", "parts": [{"text": "Understood."}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature,
            }
        }
        
        async with self._session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=120)) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                raise Exception(f"HTTP {resp.status}: {error_text[:200]}")
            
            data = await resp.json()
            # Конвертируем в OpenAI-подобный формат
            text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            return {
                "choices": [{"message": {"content": text}, "finish_reason": "stop"}],
                "usage": {"total_tokens": len(text.split()) * 2}
            }
    
    async def _request_cohere(self, provider, model, prompt, system_prompt, max_tokens, temperature) -> Dict:
        """Cohere API запрос."""
        url = f"{provider.base_url}/chat"
        headers = {
            "Authorization": f"Bearer {provider.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": model,
            "message": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system_prompt:
            payload["preamble"] = system_prompt
        
        async with self._session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=120)) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                raise Exception(f"HTTP {resp.status}: {error_text[:200]}")
            
            data = await resp.json()
            text = data.get("text", "")
            return {
                "choices": [{"message": {"content": text}, "finish_reason": "stop"}],
                "usage": {"total_tokens": len(text.split()) * 2}
            }
    
    async def _request_huggingface(self, provider, model, prompt, system_prompt, max_tokens, temperature) -> Dict:
        """HuggingFace Inference API запрос."""
        url = f"https://api-inference.huggingface.co/models/{model}"
        headers = {
            "Authorization": f"Bearer {provider.api_key}",
            "Content-Type": "application/json",
        }
        
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        payload = {
            "inputs": full_prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                "return_full_text": False,
            }
        }
        
        async with self._session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=120)) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                raise Exception(f"HTTP {resp.status}: {error_text[:200]}")
            
            data = await resp.json()
            if isinstance(data, list) and data:
                text = data[0].get("generated_text", "")
            else:
                text = str(data)
            
            return {
                "choices": [{"message": {"content": text}, "finish_reason": "stop"}],
                "usage": {"total_tokens": len(text.split()) * 2}
            }
    
    async def _request_cloudflare(self, provider, model, prompt, system_prompt, max_tokens, temperature) -> Dict:
        """Cloudflare Workers AI запрос."""
        account_id = getattr(provider, 'account_id', provider.base_url.split('/accounts/')[1].split('/')[0] if '/accounts/' in provider.base_url else '')
        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}"
        headers = {
            "Authorization": f"Bearer {provider.api_key}",
            "Content-Type": "application/json",
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "messages": messages,
            "max_tokens": max_tokens,
        }
        
        async with self._session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=120)) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                raise Exception(f"HTTP {resp.status}: {error_text[:200]}")
            
            data = await resp.json()
            text = data.get("result", {}).get("response", "")
            return {
                "choices": [{"message": {"content": text}, "finish_reason": "stop"}],
                "usage": {"total_tokens": len(text.split()) * 2}
            }
    
    def _extract_text(self, response: Dict, provider: Provider) -> str:
        """Извлекает текст из ответа."""
        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            return str(response)
    
    def _extract_finish_reason(self, response: Dict, provider: Provider) -> str:
        """Извлекает причину остановки."""
        try:
            return response["choices"][0].get("finish_reason", "stop")
        except (KeyError, IndexError):
            return "unknown"
    
    def get_status(self) -> Dict[str, Any]:
        """Возвращает полный статус роутера."""
        return self.router.get_status_report()
    
    def get_models(self) -> List[Dict[str, str]]:
        """Возвращает все доступные модели."""
        return self.router.get_available_models()
