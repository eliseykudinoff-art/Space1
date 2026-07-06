"""
🖥️ AI Super Router — Агрегатор вычислительных мощностей
=========================================================
Объединяет бесплатные GPU/CPU ресурсы:
- Google Colab (T4/V100)
- Kaggle Kernels (P100/T4, 30ч/неделю)
- Lightning AI (бесплатный GPU)
- SageMaker Studio Lab (T4, 4ч/сессия)
- Petals (децентрализованный inference)
- HuggingFace Spaces (бесплатный CPU/GPU)
"""

import asyncio
import time
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from enum import Enum

logger = logging.getLogger("ai_router.compute")


class ComputeStatus(Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    QUOTA_EXCEEDED = "quota_exceeded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class ComputeType(Enum):
    GPU_T4 = "gpu_t4"
    GPU_V100 = "gpu_v100"
    GPU_A100 = "gpu_a100"
    GPU_P100 = "gpu_p100"
    GPU_L4 = "gpu_l4"
    CPU = "cpu"
    TPU = "tpu"
    DECENTRALIZED = "decentralized"


@dataclass
class ComputeProvider:
    """Провайдер вычислительных мощностей."""
    name: str
    id: str
    compute_type: ComputeType
    url: str
    
    # Лимиты
    max_session_hours: float = 4.0
    weekly_hours: float = 30.0
    ram_gb: float = 16.0
    vram_gb: float = 16.0
    
    # Состояние
    status: ComputeStatus = ComputeStatus.UNKNOWN
    hours_used_this_week: float = 0.0
    current_session_start: Optional[float] = None
    
    # Подключение
    connection_url: Optional[str] = None  # ngrok/tunnel URL
    api_endpoint: Optional[str] = None
    
    # Метаданные
    requires_interaction: bool = True  # Нужно ли вручную запускать
    auto_shutdown: bool = True         # Автоматически выключается
    notes: str = ""
    
    def remaining_hours(self) -> float:
        """Оставшиеся часы на этой неделе."""
        return max(0, self.weekly_hours - self.hours_used_this_week)
    
    def is_session_active(self) -> bool:
        """Активна ли текущая сессия."""
        if not self.current_session_start:
            return False
        elapsed = (time.time() - self.current_session_start) / 3600
        return elapsed < self.max_session_hours


@dataclass
class ComputeTask:
    """Задача для выполнения на вычислительном ресурсе."""
    id: str
    type: str  # "inference", "training", "processing"
    requirements: Dict[str, Any] = field(default_factory=dict)
    # requirements: {"min_vram_gb": 8, "min_ram_gb": 16, "gpu_required": True}
    
    status: str = "pending"
    assigned_provider: Optional[str] = None
    result: Optional[Any] = None


class ComputeAggregator:
    """
    Агрегатор бесплатных вычислительных мощностей.
    
    Умный переключатель:
    - Отслеживает квоты каждого провайдера
    - Автоматически переключается при исчерпании
    - Приоритезирует по доступности и мощности
    """
    
    def __init__(self):
        self.providers: Dict[str, ComputeProvider] = {}
        self._init_default_providers()
    
    def _init_default_providers(self):
        """Инициализация известных бесплатных провайдеров."""
        
        defaults = [
            ComputeProvider(
                name="Google Colab (Free)",
                id="colab_free",
                compute_type=ComputeType.GPU_T4,
                url="https://colab.research.google.com",
                max_session_hours=4.0,
                weekly_hours=40.0,  # ~5-6 часов/день
                ram_gb=12.7,
                vram_gb=15.0,
                requires_interaction=True,
                auto_shutdown=True,
                notes="T4 GPU. Засыпает при неактивности (~90 мин). Нужен ngrok для туннеля."
            ),
            ComputeProvider(
                name="Kaggle Kernels",
                id="kaggle",
                compute_type=ComputeType.GPU_T4,
                url="https://www.kaggle.com/code",
                max_session_hours=12.0,
                weekly_hours=30.0,
                ram_gb=13.0,
                vram_gb=15.0,
                requires_interaction=True,
                auto_shutdown=True,
                notes="T4 или P100. 30ч GPU/неделю. Более стабильный чем Colab."
            ),
            ComputeProvider(
                name="Lightning AI (Free)",
                id="lightning",
                compute_type=ComputeType.GPU_T4,
                url="https://lightning.ai",
                max_session_hours=4.0,
                weekly_hours=22.0,
                ram_gb=16.0,
                vram_gb=16.0,
                requires_interaction=True,
                auto_shutdown=True,
                notes="Бесплатный GPU Studio. Полноценная IDE."
            ),
            ComputeProvider(
                name="SageMaker Studio Lab",
                id="sagemaker_lab",
                compute_type=ComputeType.GPU_T4,
                url="https://studiolab.sagemaker.aws",
                max_session_hours=4.0,
                weekly_hours=28.0,  # 4ч GPU/день
                ram_gb=16.0,
                vram_gb=16.0,
                requires_interaction=True,
                auto_shutdown=True,
                notes="4 часа GPU/сессия. Нужна заявка на доступ (бесплатно)."
            ),
            ComputeProvider(
                name="HuggingFace Spaces (Free CPU)",
                id="hf_spaces_cpu",
                compute_type=ComputeType.CPU,
                url="https://huggingface.co/spaces",
                max_session_hours=999.0,  # Работает постоянно
                weekly_hours=168.0,       # 24/7
                ram_gb=16.0,
                vram_gb=0,
                requires_interaction=False,
                auto_shutdown=False,
                notes="Бесплатный CPU (2 vCPU, 16GB RAM). Работает 24/7. Засыпает при неактивности."
            ),
            ComputeProvider(
                name="Oracle Cloud (Always Free ARM)",
                id="oracle_arm",
                compute_type=ComputeType.CPU,
                url="https://cloud.oracle.com",
                max_session_hours=999.0,
                weekly_hours=168.0,
                ram_gb=24.0,
                vram_gb=0,
                requires_interaction=False,
                auto_shutdown=False,
                notes="4 ARM cores + 24GB RAM. Работает 24/7. Docker. Нужна карта для верификации."
            ),
            ComputeProvider(
                name="Petals (Decentralized)",
                id="petals",
                compute_type=ComputeType.DECENTRALIZED,
                url="https://petals.dev",
                max_session_hours=999.0,
                weekly_hours=168.0,
                ram_gb=0,
                vram_gb=0,
                requires_interaction=False,
                auto_shutdown=False,
                notes="Распределённый inference больших моделей (Llama 405B). Скорость зависит от сети."
            ),
            ComputeProvider(
                name="Google Cloud Shell",
                id="gcloud_shell",
                compute_type=ComputeType.CPU,
                url="https://shell.cloud.google.com",
                max_session_hours=12.0,
                weekly_hours=60.0,  # ~50ч/неделю
                ram_gb=5.0,
                vram_gb=0,
                requires_interaction=True,
                auto_shutdown=True,
                notes="Бесплатная VM с Docker. Сбрасывается после 12ч. 5GB RAM."
            ),
            ComputeProvider(
                name="GitHub Codespaces (Free)",
                id="github_codespaces",
                compute_type=ComputeType.CPU,
                url="https://github.com/codespaces",
                max_session_hours=999.0,
                weekly_hours=60.0,  # 60 часов/месяц бесплатно
                ram_gb=8.0,
                vram_gb=0,
                requires_interaction=False,
                auto_shutdown=True,
                notes="60 часов/месяц бесплатно. Docker-in-Docker. 2-4 cores, 8GB RAM."
            ),
            ComputeProvider(
                name="Gradient (Paperspace Free)",
                id="gradient",
                compute_type=ComputeType.GPU_T4,
                url="https://www.paperspace.com/gradient",
                max_session_hours=6.0,
                weekly_hours=20.0,
                ram_gb=8.0,
                vram_gb=8.0,
                requires_interaction=True,
                auto_shutdown=True,
                notes="Бесплатные GPU notebooks. M4000/P5000. Ограниченная доступность."
            ),
        ]
        
        for provider in defaults:
            self.providers[provider.id] = provider
    
    def select_compute(self, 
                       gpu_required: bool = False,
                       min_vram_gb: float = 0,
                       min_ram_gb: float = 4,
                       prefer_persistent: bool = False) -> Optional[ComputeProvider]:
        """
        Выбирает лучший доступный вычислительный ресурс.
        
        Args:
            gpu_required: Нужен ли GPU
            min_vram_gb: Минимум VRAM
            min_ram_gb: Минимум RAM
            prefer_persistent: Предпочитать постоянно работающие
        """
        candidates = []
        
        for provider in self.providers.values():
            # Фильтрация
            if provider.status == ComputeStatus.UNAVAILABLE:
                continue
            if provider.status == ComputeStatus.QUOTA_EXCEEDED:
                continue
            if gpu_required and provider.vram_gb == 0:
                continue
            if provider.vram_gb < min_vram_gb:
                continue
            if provider.ram_gb < min_ram_gb:
                continue
            if provider.remaining_hours() <= 0:
                continue
            
            # Scoring
            score = 0.0
            score += provider.remaining_hours() * 2  # Больше часов = лучше
            score += provider.vram_gb * 3            # Больше VRAM = лучше
            score += provider.ram_gb * 1
            
            if prefer_persistent and not provider.auto_shutdown:
                score += 50
            if not provider.requires_interaction:
                score += 20  # Автоматические предпочтительнее
            
            candidates.append((score, provider))
        
        if not candidates:
            return None
        
        candidates.sort(key=lambda x: -x[0])
        return candidates[0][1]
    
    def register_session(self, provider_id: str, connection_url: str):
        """Регистрирует активную сессию."""
        provider = self.providers.get(provider_id)
        if provider:
            provider.status = ComputeStatus.AVAILABLE
            provider.current_session_start = time.time()
            provider.connection_url = connection_url
            provider.api_endpoint = connection_url
            logger.info(f"✅ Сессия зарегистрирована: {provider.name} → {connection_url}")
    
    def end_session(self, provider_id: str, hours_used: float):
        """Завершает сессию и обновляет квоту."""
        provider = self.providers.get(provider_id)
        if provider:
            provider.hours_used_this_week += hours_used
            provider.current_session_start = None
            provider.connection_url = None
            
            if provider.remaining_hours() <= 0:
                provider.status = ComputeStatus.QUOTA_EXCEEDED
            else:
                provider.status = ComputeStatus.UNKNOWN
            
            logger.info(f"🔚 Сессия завершена: {provider.name} ({hours_used:.1f}ч использовано, осталось {provider.remaining_hours():.1f}ч)")
    
    def get_status_report(self) -> Dict[str, Any]:
        """Полный отчёт о вычислительных ресурсах."""
        report = {
            "total_providers": len(self.providers),
            "available": 0,
            "total_gpu_hours_remaining": 0,
            "total_cpu_hours_remaining": 0,
            "providers": {}
        }
        
        for pid, p in self.providers.items():
            is_gpu = p.vram_gb > 0
            remaining = p.remaining_hours()
            
            if p.status == ComputeStatus.AVAILABLE:
                report["available"] += 1
            
            if is_gpu:
                report["total_gpu_hours_remaining"] += remaining
            else:
                report["total_cpu_hours_remaining"] += remaining
            
            report["providers"][pid] = {
                "name": p.name,
                "type": p.compute_type.value,
                "status": p.status.value,
                "ram_gb": p.ram_gb,
                "vram_gb": p.vram_gb,
                "remaining_hours": round(remaining, 1),
                "session_active": p.is_session_active(),
                "connection_url": p.connection_url,
                "requires_interaction": p.requires_interaction,
            }
        
        return report
    
    def reset_weekly_quotas(self):
        """Сброс недельных квот (вызывать раз в неделю)."""
        for provider in self.providers.values():
            provider.hours_used_this_week = 0
            if provider.status == ComputeStatus.QUOTA_EXCEEDED:
                provider.status = ComputeStatus.UNKNOWN
        logger.info("🔄 Недельные квоты сброшены")
