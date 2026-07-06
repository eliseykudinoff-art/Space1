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

logger = logging.getLogger("ai_router")


class ProviderStatus(Enum):
    ACTIVE = "active"
    RATE_LIMITED = "rate_limited"
    EXHAUSTED = "exhausted"       # Дневной лимит исчерпан
    UNAVAILABLE = "unavailable"   # Сервер не отвечает
    ERROR = "error"
    UNCHECKED = "unchecked"


class RoutingStrategy(Enum):
    MAXIMIZE_UPTIME = "maximize_uptime"
    MAXIMIZE_QUALITY = "maximize_quality"
    MAXIMIZE_SPEED = "maximize_speed"


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
    format: str  # openai, gemini, cohere, huggingface, cloudflare
    health_url: str
    limits: Dict[str, int]
    credit_card_required: bool = False
    notes: str = ""
    priority: int = 5  # 1-10, выше = предпочтительнее
    
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
                        exclude: Optional[List[str]] = None) -> Optional[Provider]:
        """
        Выбирает лучшего провайдера для запроса.
        
        Args:
            estimated_tokens: Ожидаемое количество токенов
            preferred_model: Предпочтительная модель (если есть)
            exclude: Список ID провайдеров для исключения
        
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
            logger.warning("⚠️ Все провайдеры недоступны!")
            return None
        
        # Сортируем по score (выше = лучше)
        candidates.sort(key=lambda x: -x[0])
        return candidates[0][1]
    
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
