"""
🔌 AI Super Router — Унифицированный клиент v2.0
=================================================
Единый интерфейс для всех провайдеров.
Автоматический retry и fallback.
Поддержка полной истории сообщений (multi-turn).
"""

import asyncio
import aiohttp
import time
import json
import logging
from typing import Optional, Dict, List, Any, AsyncGenerator
from dataclasses import dataclass

from .router import AIRouter, Provider, ProviderStatus, RoutingStrategy
from .health_checker import HealthChecker, PeriodicHealthMonitor

logger = logging.getLogger("ai_router.client")


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
        
        # Простой запрос (одно сообщение):
        response = await client.complete("Напиши hello world на Python")
        
        # Multi-turn (с историей):
        response = await client.complete(
            messages=[
                {"role": "system", "content": "Ты помощник"},
                {"role": "user", "content": "Привет"},
                {"role": "assistant", "content": "Привет! Чем помочь?"},
                {"role": "user", "content": "Расскажи о Python"},
            ]
        )
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
                       prompt: Optional[str] = None,
                       messages: Optional[List[Dict[str, str]]] = None,
                       system_prompt: Optional[str] = None,
                       max_tokens: int = 2048,
                       temperature: float = 0.7,
                       preferred_model: Optional[str] = None,
                       preferred_provider: Optional[str] = None,
                       handoff_context: Optional[str] = None) -> CompletionResponse:
        """
        Отправляет запрос с автоматическим fallback.
        
        Поддерживает два режима:
        1. Простой: prompt + system_prompt (одно сообщение)
        2. Multi-turn: messages (полная история диалога)
        
        Args:
            prompt: Текст запроса (простой режим)
            messages: Полная история сообщений (multi-turn режим)
                      Формат: [{"role": "user"|"assistant"|"system", "content": "..."}]
            system_prompt: Системный промпт (используется если нет system в messages)
            max_tokens: Максимум токенов в ответе
            temperature: Температура генерации
            preferred_model: Предпочтительная модель
            preferred_provider: Предпочтительный провайдер
            handoff_context: Контекст для передачи при смене провайдера
        
        Returns:
            CompletionResponse с ответом
        
        Raises:
            RuntimeError: Если все провайдеры недоступны
        """
        # Нормализуем входные данные в messages
        normalized_messages = self._normalize_messages(prompt, messages, system_prompt, handoff_context)
        
        # Оценка токенов
        total_text = " ".join(m["content"] for m in normalized_messages)
        estimated_tokens = len(total_text.split()) * 2 + max_tokens
        
        excluded_providers: List[str] = []
        
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
                    exclude=excluded_providers
                )
            
            if not provider:
                break
            
            # Выбираем модель
            model = self._select_model(provider, preferred_model)
            
            logger.debug(f"🔄 Попытка {attempt+1}: {provider.name} / {model}")
            
            try:
                start = time.time()
                response = await self._make_request(
                    provider, model, normalized_messages, max_tokens, temperature
                )
                latency = (time.time() - start) * 1000
                
                # Успех!
                tokens_used = response.get("usage", {}).get("total_tokens", estimated_tokens // 2)
                self.router.report_success(provider.id, tokens_used, latency)
                
                text = self._extract_text(response, provider)
                
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
                logger.warning(f"❌ {provider.name}: {error_str}")
                self.router.report_failure(provider.id, error_str)
                excluded_providers.append(provider.id)
                
                await asyncio.sleep(1)
        
        raise RuntimeError(
            f"Все провайдеры недоступны после {len(excluded_providers)} попыток. "
            f"Исключены: {excluded_providers}"
        )
    
    async def complete_stream(self,
                              prompt: Optional[str] = None,
                              messages: Optional[List[Dict[str, str]]] = None,
                              system_prompt: Optional[str] = None,
                              max_tokens: int = 2048,
                              temperature: float = 0.7) -> AsyncGenerator[str, None]:
        """Стриминг ответа (для провайдеров с поддержкой SSE)."""
        normalized_messages = self._normalize_messages(prompt, messages, system_prompt)
        total_text = " ".join(m["content"] for m in normalized_messages)
        estimated_tokens = len(total_text.split()) * 2 + max_tokens
        
        provider = self.router.select_provider(estimated_tokens=estimated_tokens)
        
        if not provider:
            yield "❌ Все провайдеры недоступны"
            return
        
        model = self._select_model(provider, None)
        
        if provider.format != "openai":
            # Для не-OpenAI форматов — обычный запрос
            response = await self.complete(messages=normalized_messages, max_tokens=max_tokens, temperature=temperature)
            yield response.text
            return
        
        url = f"{provider.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {provider.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": model,
            "messages": normalized_messages,
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
            response = await self.complete(messages=normalized_messages, max_tokens=max_tokens, temperature=temperature)
            yield response.text
    
    # ═══════════════════════════════════════════════════════════════
    # ВНУТРЕННИЕ МЕТОДЫ
    # ═══════════════════════════════════════════════════════════════
    
    def _normalize_messages(self, 
                            prompt: Optional[str] = None,
                            messages: Optional[List[Dict[str, str]]] = None,
                            system_prompt: Optional[str] = None,
                            handoff_context: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Нормализует входные данные в единый формат messages.
        
        Приоритет:
        1. Если передан messages — используем его
        2. Если передан prompt — строим messages из prompt + system_prompt
        3. Если есть handoff_context — вставляем его как system-сообщение
        """
        if messages:
            result = list(messages)
        elif prompt:
            result = []
            if system_prompt:
                result.append({"role": "system", "content": system_prompt})
            result.append({"role": "user", "content": prompt})
        else:
            raise ValueError("Необходимо передать prompt или messages")
        
        # Вставляем handoff-контекст при смене провайдера
        if handoff_context:
            # Ищем system-сообщение и дополняем его
            has_system = False
            for msg in result:
                if msg["role"] == "system":
                    msg["content"] += f"\n\n[Контекст предыдущего диалога: {handoff_context}]"
                    has_system = True
                    break
            if not has_system:
                result.insert(0, {
                    "role": "system", 
                    "content": f"[Контекст предыдущего диалога: {handoff_context}]"
                })
        
        return result
    
    def _select_model(self, provider: Provider, preferred: Optional[str]) -> str:
        """Выбирает модель из доступных у провайдера."""
        if preferred:
            for model in provider.models:
                if preferred.lower() in model.lower():
                    return model
        
        return provider.models[0] if provider.models else ""
    
    async def _make_request(self, provider: Provider, model: str,
                            messages: List[Dict[str, str]],
                            max_tokens: int, temperature: float) -> Dict:
        """Выполняет запрос к провайдеру в нужном формате."""
        
        if provider.format == "openai":
            return await self._request_openai(provider, model, messages, max_tokens, temperature)
        elif provider.format == "gemini":
            return await self._request_gemini(provider, model, messages, max_tokens, temperature)
        elif provider.format == "cohere":
            return await self._request_cohere(provider, model, messages, max_tokens, temperature)
        elif provider.format == "huggingface":
            return await self._request_huggingface(provider, model, messages, max_tokens, temperature)
        elif provider.format == "cloudflare":
            return await self._request_cloudflare(provider, model, messages, max_tokens, temperature)
        else:
            return await self._request_openai(provider, model, messages, max_tokens, temperature)
    
    async def _request_openai(self, provider, model, messages, max_tokens, temperature) -> Dict:
        """OpenAI-совместимый запрос (поддерживает полную историю)."""
        url = f"{provider.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {provider.api_key}",
            "Content-Type": "application/json",
        }
        
        # Для OpenRouter добавляем специальные заголовки
        if provider.id == "openrouter":
            headers["HTTP-Referer"] = "https://github.com/ai-super-router"
            headers["X-Title"] = "AI Super Router"
        
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
    
    async def _request_gemini(self, provider, model, messages, max_tokens, temperature) -> Dict:
        """Google Gemini API запрос (конвертирует messages → contents)."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={provider.api_key}"
        headers = {"Content-Type": "application/json"}
        
        # Конвертируем OpenAI messages → Gemini contents
        contents = []
        system_instruction = None
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                # Gemini поддерживает system_instruction
                system_instruction = content
            elif role == "user":
                contents.append({"role": "user", "parts": [{"text": content}]})
            elif role == "assistant":
                contents.append({"role": "model", "parts": [{"text": content}]})
        
        # Если нет contents (только system), добавляем пустой user
        if not contents:
            contents.append({"role": "user", "parts": [{"text": ""}]})
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature,
            }
        }
        
        # Добавляем system instruction если есть
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
        
        async with self._session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=120)) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                raise Exception(f"HTTP {resp.status}: {error_text[:200]}")
            
            data = await resp.json()
            text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            usage = data.get("usageMetadata", {})
            total_tokens = usage.get("totalTokenCount", len(text.split()) * 2)
            return {
                "choices": [{"message": {"content": text}, "finish_reason": "stop"}],
                "usage": {"total_tokens": total_tokens}
            }
    
    async def _request_cohere(self, provider, model, messages, max_tokens, temperature) -> Dict:
        """Cohere API запрос (конвертирует messages → chat_history + message)."""
        url = f"{provider.base_url}/chat"
        headers = {
            "Authorization": f"Bearer {provider.api_key}",
            "Content-Type": "application/json",
        }
        
        # Конвертируем messages → Cohere формат
        preamble = None
        chat_history = []
        current_message = ""
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                preamble = content
            elif role == "user":
                # Последнее user-сообщение станет message, остальные — в историю
                if current_message:
                    chat_history.append({"role": "USER", "message": current_message})
                current_message = content
            elif role == "assistant":
                chat_history.append({"role": "CHATBOT", "message": content})
        
        payload = {
            "model": model,
            "message": current_message or "Hello",
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if preamble:
            payload["preamble"] = preamble
        if chat_history:
            payload["chat_history"] = chat_history
        
        async with self._session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=120)) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                raise Exception(f"HTTP {resp.status}: {error_text[:200]}")
            
            data = await resp.json()
            text = data.get("text", "")
            tokens = data.get("meta", {}).get("tokens", {})
            total_tokens = tokens.get("input_tokens", 0) + tokens.get("output_tokens", 0)
            return {
                "choices": [{"message": {"content": text}, "finish_reason": "stop"}],
                "usage": {"total_tokens": total_tokens or len(text.split()) * 2}
            }
    
    async def _request_huggingface(self, provider, model, messages, max_tokens, temperature) -> Dict:
        """HuggingFace Inference API запрос (конкатенирует messages в prompt)."""
        url = f"https://api-inference.huggingface.co/models/{model}"
        headers = {
            "Authorization": f"Bearer {provider.api_key}",
            "Content-Type": "application/json",
        }
        
        # HuggingFace text-generation: конкатенируем всё в один промпт
        parts = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                parts.append(f"<|system|>\n{content}")
            elif role == "user":
                parts.append(f"<|user|>\n{content}")
            elif role == "assistant":
                parts.append(f"<|assistant|>\n{content}")
        parts.append("<|assistant|>\n")
        
        full_prompt = "\n".join(parts)
        
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
    
    async def _request_cloudflare(self, provider, model, messages, max_tokens, temperature) -> Dict:
        """Cloudflare Workers AI запрос (поддерживает messages)."""
        account_id = getattr(provider, 'account_id', provider.base_url.split('/accounts/')[1].split('/')[0] if '/accounts/' in provider.base_url else '')
        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}"
        headers = {
            "Authorization": f"Bearer {provider.api_key}",
            "Content-Type": "application/json",
        }
        
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
