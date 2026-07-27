"""
🌐 AI Super Router — Ядро маршрутизации
========================================
Автоматическое переключение между 20+ бесплатными AI API провайдерами.
Приоритет: бесперебойная работа.
"""

import asyncio
import time
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from enum import Enum
from datetime import datetime

logger = logging.getLogger("ai_router")


class ProviderStatus(Enum):
    ACTIVE = "active"
    RATE_LIMITED = "rate_limited"
    EXHAUSTED = "exhausted"       # Дневной лимит исчерпан
    UNAVAILABLE = "unavailable"   # Сервер не отвечает
    ERROR = "error"
    UNCHECKED = "unchecked"


class CapabilityType(Enum):
    """
    Типы capability, которые могут поддерживать провайдеры.
    
    BUG-028 FIX: Теперь роутер может проверять capability,
    а не только доступность сервера.
    """
    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    IMAGE_UNDERSTANDING = "image_understanding"
    IMAGE_GENERATION = "image_generation"
    FUNCTION_CALLING = "function_calling"
    STREAMING = "streaming"
    MULTIMODAL = "multimodal"
    LONG_CONTEXT = "long_context"
    REASONING = "reasoning"


class RoutingStrategy(Enum):
    MAXIMIZE_UPTIME = "maximize_uptime"
    MAXIMIZE_QUALITY = "maximize_quality"
    MAXIMIZE_SPEED = "maximize_speed"


@dataclass
class FallbackPolicy:
    """
    BUG-029 FIX: Политика fallback для детерминированного выбора.
    
    Определяет правила retry и fallback.
    """
    # Лимиты
    max_retries: int = 3
    max_cost_per_request: float = 0.01
    
    # Timeout для retry
    base_retry_delay_ms: int = 1000
    max_retry_delay_ms: int = 30000
    
    # Backoff policy
    backoff_multiplier: float = 2.0
    use_jitter: bool = True
    
    # Дополнительные правила
    skip_auth_errors: bool = True       # Пропускать auth ошибки без retry
    skip_client_errors: bool = True    # Пропускать 4xx ошибки без retry
    retry_on_rate_limit: bool = True    # Retry на rate limit
    
    def get_retry_delay(self, attempt: int, error_type: str = "TRANSIENT") -> float:
        """
        Рассчитать delay для retry.
        
        Args:
            attempt: Номер попытки (0-based)
            error_type: Тип ошибки
            
        Returns:
            Delay в секундах
        """
        import random
        import math
        
        # Базовый delay
        delay_ms = self.base_retry_delay_ms * (self.backoff_multiplier ** attempt)
        
        # Cap на максимум
        delay_ms = min(delay_ms, self.max_retry_delay_ms)
        
        # Добавляем jitter
        if self.use_jitter:
            jitter = delay_ms * 0.1 * random.random()
            delay_ms += jitter
        
        # Конвертируем в секунды
        return delay_ms / 1000.0


@dataclass
class RoutingDecision:
    """
    BUG-030 FIX: Запись решения о маршрутизации.
    
    Сохраняет причины выбора провайдера для аудита и объяснения.
    """
    # Выбранный провайдер
    provider_id: str
    provider_name: str
    
    # Параметры запроса
    prompt_length: int
    estimated_tokens: int
    preferred_model: Optional[str] = None
    required_capability: Optional[str] = None
    
    # Scoring components (для объяснения выбора)
    capacity_score: float = 0.0
    success_rate_score: float = 0.0
    latency_score: float = 0.0
    priority_score: float = 0.0
    total_score: float = 0.0
    
    # Все кандидаты с их score
    candidates: List[Dict[str, Any]] = field(default_factory=list)
    
    # Статистика
    timestamp: datetime = field(default_factory=datetime.now)
    attempt: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация для логирования."""
        return {
            "provider_id": self.provider_id,
            "provider_name": self.provider_name,
            "capacity_score": self.capacity_score,
            "success_rate_score": self.success_rate_score,
            "latency_score": self.latency_score,
            "priority_score": self.priority_score,
            "total_score": self.total_score,
            "candidates": self.candidates,
            "timestamp": self.timestamp.isoformat(),
            "attempt": self.attempt,
        }
    
    def get_explanation(self) -> str:
        """Получить человекочитаемое объяснение выбора."""
        parts = [
            f"Selected {self.provider_name} (score: {self.total_score:.2f})",
            f"capacity={self.capacity_score:.1f}",
            f"success={self.success_rate_score:.2f}",
            f"latency={self.latency_score:.1f}ms",
        ]
        if self.candidates:
            parts.append(f"(vs {len(self.candidates)} other candidates)")
        return ", ".join(parts)


@dataclass
class TokenBudget:
    """Отслеживание расхода токенов провайдера."""
    total_tokens_used_today: int = 0
    total_requests_today: int = 0
    requests_this_minute: int = 0
    last_minute_reset: float = field(default_factory=time.time)
    last_day_reset: float = field(default_factory=time.time)
    
    rpm_limit: int = 10
    rpd_limit: int = 1000
    tpm_limit: int = 50000
    
    def can_make_request(self, estimated_tokens: int = 500) -> bool:
        """Проверяет, можно ли сделать запрос не превысив лимиты."""
        now = time.time()
        
        # Сброс минутного счётчика
        if now - self.last_minute_reset >= 60:
            self.requests_this_minute = 0
            self.last_minute_reset = now
        
        # Сброс дневного счётчика
        if now - self.last_day_reset >= 86400:
            self.total_tokens_used_today = 0
            self.total_requests_today = 0
            self.last_day_reset = now
        
        # Проверки
        if self.requests_this_minute >= self.rpm_limit:
            return False
        if self.total_requests_today >= self.rpd_limit:
            return False
        if self.total_tokens_used_today + estimated_tokens > self.tpm_limit * 60 * 24:
            return False
        
        return True
    
    def record_usage(self, tokens_used: int):
        """Записывает использование."""
        self.total_tokens_used_today += tokens_used
        self.total_requests_today += 1
        self.requests_this_minute += 1
    
    def remaining_capacity_score(self) -> float:
        """Оценка оставшейся ёмкости (0.0 - 1.0)."""
        rpm_score = 1.0 - (self.requests_this_minute / max(self.rpm_limit, 1))
        rpd_score = 1.0 - (self.total_requests_today / max(self.rpd_limit, 1))
        return min(rpm_score, rpd_score)


@dataclass
class Provider:
    """Провайдер AI API."""
    name: str
    id: str
    base_url: str
    api_key: str
    models: List[str]
    format: str = "openai"  # openai, gemini, cohere, huggingface, cloudflare
    health_url: str = ""
    limits: Dict[str, int] = field(default_factory=lambda: {"rpm": 10, "rpd": 1000, "tpm": 50000})
    credit_card_required: bool = False
    notes: str = ""
    priority: int = 5  # 1-10, выше = предпочтительнее
    enabled: bool = True  # FIX: добавлено поле enabled
    
    # BUG-028 FIX: Добавлены capabilities
    capabilities: List[CapabilityType] = field(default_factory=list)
    
    # Состояние
    status: ProviderStatus = ProviderStatus.UNCHECKED
    budget: TokenBudget = field(default_factory=TokenBudget)
    last_health_check: float = 0
    last_error: Optional[str] = None
    avg_latency_ms: float = 0
    success_rate: float = 1.0
    
    # Статистика
    total_requests: int = 0
    total_failures: int = 0
    
    def __post_init__(self):
        self.budget = TokenBudget(
            rpm_limit=self.limits.get("rpm", 10),
            rpd_limit=self.limits.get("rpd", 1000),
            tpm_limit=self.limits.get("tpm", 50000),
        )
        
        # По умолчанию все провайдеры поддерживают text generation
        if not self.capabilities:
            self.capabilities = [CapabilityType.TEXT_GENERATION]
    
    def has_capability(self, capability: CapabilityType) -> bool:
        """Проверяет наличие capability у провайдера."""
        return capability in self.capabilities


class AIRouter:
    """
    Суперроутер бесплатных AI API.
    
    Автоматически:
    - Проверяет доступность серверов
    - Отслеживает лимиты и бюджет токенов
    - Переключается при отказе
    - Выбирает оптимального провайдера
    """
    
    def __init__(self, providers: List[Provider], strategy: RoutingStrategy = RoutingStrategy.MAXIMIZE_UPTIME):
        self.providers = {p.id: p for p in providers}
        self.strategy = strategy
        self.fallback_chain: List[str] = []
        self._build_fallback_chain()
        
        # Статистика
        self.total_requests = 0
        self.total_fallbacks = 0
        self.uptime_start = time.time()
    
    def _build_fallback_chain(self):
        """Строит цепочку fallback по приоритету и ёмкости."""
        sorted_providers = sorted(
            self.providers.values(),
            key=lambda p: (
                -p.priority,
                -p.limits.get("rpd", 0),
                -p.limits.get("tpm", 0),
            )
        )
        self.fallback_chain = [p.id for p in sorted_providers]
    
    def select_provider(self, 
                        estimated_tokens: int = 500,
                        preferred_model: Optional[str] = None,
                        exclude: Optional[List[str]] = None,
                        required_capability: Optional[CapabilityType] = None) -> Optional[Provider]:
        """
        Выбирает лучшего провайдера для запроса.
        
        BUG-028 FIX: Добавлен параметр required_capability для фильтрации
        по способностям провайдера.
        
        Args:
            estimated_tokens: Ожидаемое количество токенов
            preferred_model: Предпочтительная модель (если есть)
            exclude: Список ID провайдеров для исключения
            required_capability: Требуемая capability (BUG-028 FIX)
        
        Returns:
            Provider или None если все недоступны
        """
        exclude = exclude or []
        candidates = []
        
        for provider_id in self.fallback_chain:
            provider = self.providers[provider_id]
            
            # Пропускаем исключённых
            if provider_id in exclude:
                continue
            
            # BUG-028 FIX: Проверяем capability
            if required_capability and not provider.has_capability(required_capability):
                logger.debug(f"   ⏭️ {provider.name}: missing capability {required_capability.value}")
                continue
            
            # Пропускаем disabled провайдеров
            if not getattr(provider, 'enabled', True):
                continue

            # Пропускаем недоступных
            if provider.status in (ProviderStatus.UNAVAILABLE, ProviderStatus.EXHAUSTED, ProviderStatus.ERROR):
                continue
            
            # Проверяем бюджет
            if not provider.budget.can_make_request(estimated_tokens):
                provider.status = ProviderStatus.RATE_LIMITED
                continue
            
            # Проверяем наличие предпочтительной модели
            if preferred_model:
                has_model = any(preferred_model.lower() in m.lower() for m in provider.models)
                if not has_model:
                    continue
            
            # Считаем score
            score = self._calculate_score(provider, estimated_tokens)
            candidates.append((score, provider))
        
        if not candidates:
            if required_capability:
                logger.warning(f"⚠️ Все провайдеры недоступны с capability: {required_capability.value}")
            else:
                logger.warning("⚠️ Все провайдеры недоступны!")
            return None
        
        # Сортируем по score (выше = лучше)
        candidates.sort(key=lambda x: -x[0])
        selected = candidates[0][1]
        logger.debug(f"   ✅ Selected: {selected.name} (capabilities: {[c.value for c in selected.capabilities]})")
        return selected
    
    def _calculate_score(self, provider: Provider, estimated_tokens: int) -> float:
        """Рассчитывает score провайдера по стратегии."""
        score = 0.0
        
        if self.strategy == RoutingStrategy.MAXIMIZE_UPTIME:
            # Приоритет: оставшаяся ёмкость + надёжность
            score += provider.budget.remaining_capacity_score() * 40
            score += provider.success_rate * 30
            score += provider.priority * 3
        
        elif self.strategy == RoutingStrategy.MAXIMIZE_QUALITY:
            # Приоритет: качество модели + размер
            score += provider.priority * 10
            # Больше моделей = больше выбор
            score += len(provider.models) * 2
        
        elif self.strategy == RoutingStrategy.MAXIMIZE_SPEED:
            # Приоритет: скорость + доступность
            if provider.avg_latency_ms > 0:
                score += max(0, 100 - provider.avg_latency_ms / 100)
            else:
                score += 50  # Неизвестная скорость
            score += provider.success_rate * 20
        
        return score
    
    def report_success(self, provider_id: str, tokens_used: int, latency_ms: float):
        """Записывает успешный запрос."""
        provider = self.providers.get(provider_id)
        if not provider:
            return
        
        provider.budget.record_usage(tokens_used)
        provider.total_requests += 1
        provider.status = ProviderStatus.ACTIVE
        
        # Скользящее среднее latency
        if provider.avg_latency_ms == 0:
            provider.avg_latency_ms = latency_ms
        else:
            provider.avg_latency_ms = provider.avg_latency_ms * 0.8 + latency_ms * 0.2
        
        # Обновляем success rate
        provider.success_rate = 1.0 - (provider.total_failures / max(provider.total_requests, 1))
        
        self.total_requests += 1
    
    def report_failure(self, provider_id: str, error: str):
        """Записывает неудачный запрос."""
        provider = self.providers.get(provider_id)
        if not provider:
            return
        
        provider.total_failures += 1
        provider.total_requests += 1
        provider.last_error = error
        
        # Определяем тип ошибки
        if "429" in error or "rate" in error.lower():
            provider.status = ProviderStatus.RATE_LIMITED
        elif "401" in error or "403" in error:
            provider.status = ProviderStatus.ERROR
        else:
            provider.status = ProviderStatus.UNAVAILABLE
        
        # Обновляем success rate
        provider.success_rate = 1.0 - (provider.total_failures / max(provider.total_requests, 1))
        
        self.total_fallbacks += 1
    
    def get_status_report(self) -> Dict[str, Any]:
        """Генерирует отчёт о состоянии всех провайдеров."""
        report = {
            "total_requests": self.total_requests,
            "total_fallbacks": self.total_fallbacks,
            "uptime_seconds": time.time() - self.uptime_start,
            "strategy": self.strategy.value,
            "providers": {}
        }
        
        for pid, p in self.providers.items():
            report["providers"][pid] = {
                "name": p.name,
                "status": p.status.value,
                "success_rate": round(p.success_rate, 2),
                "avg_latency_ms": round(p.avg_latency_ms, 1),
                "requests_today": p.budget.total_requests_today,
                "tokens_today": p.budget.total_tokens_used_today,
                "remaining_capacity": round(p.budget.remaining_capacity_score(), 2),
                "last_error": p.last_error,
            }
        
        return report
    
    def get_available_models(self) -> List[Dict[str, str]]:
        """Возвращает список всех доступных моделей."""
        models = []
        for p in self.providers.values():
            if p.status not in (ProviderStatus.UNAVAILABLE, ProviderStatus.ERROR):
                for model in p.models:
                    models.append({
                        "model": model,
                        "provider": p.name,
                        "provider_id": p.id,
                        "status": p.status.value,
                    })
        return models
