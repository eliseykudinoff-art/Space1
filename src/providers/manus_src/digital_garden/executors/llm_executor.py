"""
🧠 LLM Executor — Адаптер для AI Super Router
================================================
Подключает Management Core к AI Super Router (22 провайдера).
Обеспечивает:
- Единый интерфейс для всех LLM-запросов
- Автоматический fallback при отказе провайдера
- Сохранение контекста при переключении
"""

import asyncio
import json
import logging
from typing import Optional, Dict, List, Any

logger = logging.getLogger("garden.executor.llm")

try:
    import aiohttp
except ImportError:
    aiohttp = None


class LLMExecutor:
    """
    Выполняет LLM-запросы через AI Super Router или напрямую через провайдеров.
    
    Использование:
        executor = LLMExecutor(base_url="http://localhost:8000/v1")
        response = await executor.complete(messages=[
            {"role": "system", "content": "Ты помощник."},
            {"role": "user", "content": "Привет!"},
        ])
    """
    
    def __init__(self, base_url: str = "http://localhost:8000/v1", 
                 api_key: str = "not-needed",
                 default_model: str = "auto"):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.default_model = default_model
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> 'aiohttp.ClientSession':
        """Получить или создать HTTP-сессию."""
        if not aiohttp:
            raise ImportError("Установите aiohttp: pip install aiohttp")
        
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
            )
        return self._session
    
    async def complete(self, messages: List[Dict[str, str]], 
                       model: Optional[str] = None,
                       temperature: float = 0.7,
                       max_tokens: int = 2048,
                       stream: bool = False) -> Dict[str, Any]:
        """
        Отправляет запрос на completion.
        
        Args:
            messages: Список сообщений [{role, content}]
            model: Модель (или "auto" для автовыбора)
            temperature: Креативность (0-2)
            max_tokens: Максимум токенов в ответе
            stream: Потоковый режим
        
        Returns:
            {
                "text": str,           # Текст ответа
                "model": str,          # Какая модель ответила
                "provider": str,       # Какой провайдер
                "tokens_used": int,    # Использовано токенов
                "finish_reason": str,  # stop/length/error
            }
        """
        session = await self._get_session()
        
        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }
        
        try:
            async with session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    choice = data["choices"][0]
                    usage = data.get("usage", {})
                    
                    return {
                        "text": choice["message"]["content"],
                        "model": data.get("model", "unknown"),
                        "provider": data.get("x_provider", "unknown"),
                        "tokens_used": usage.get("total_tokens", 0),
                        "finish_reason": choice.get("finish_reason", "stop"),
                    }
                else:
                    error_text = await resp.text()
                    logger.error(f"❌ LLM API error {resp.status}: {error_text[:200]}")
                    return {
                        "text": f"Ошибка LLM: {resp.status}",
                        "model": "error",
                        "provider": "error",
                        "tokens_used": 0,
                        "finish_reason": "error",
                    }
                    
        except asyncio.TimeoutError:
            logger.error("❌ LLM таймаут (120с)")
            return {
                "text": "Таймаут запроса к LLM",
                "model": "timeout",
                "provider": "timeout",
                "tokens_used": 0,
                "finish_reason": "error",
            }
        except Exception as e:
            logger.error(f"❌ LLM ошибка: {e}")
            return {
                "text": f"Ошибка: {e}",
                "model": "error",
                "provider": "error",
                "tokens_used": 0,
                "finish_reason": "error",
            }
    
    async def check_health(self) -> bool:
        """Проверка доступности LLM-бэкенда."""
        try:
            session = await self._get_session()
            async with session.get(
                f"{self.base_url}/models",
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                return resp.status == 200
        except Exception:
            return False
    
    async def list_models(self) -> List[str]:
        """Получить список доступных моделей."""
        try:
            session = await self._get_session()
            async with session.get(
                f"{self.base_url}/models",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return [m["id"] for m in data.get("data", [])]
        except Exception:
            pass
        return []
    
    async def close(self):
        """Закрыть HTTP-сессию."""
        if self._session and not self._session.closed:
            await self._session.close()
