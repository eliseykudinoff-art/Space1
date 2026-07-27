# 🌐 AI Super Router

**Суперроутер бесплатных AI API + Агрегатор вычислительных мощностей**

Единая точка доступа к 20+ бесплатным AI-провайдерам с автоматическим переключением, мониторингом здоровья, отслеживанием лимитов и поиском новых ресурсов.

---

## 📋 Содержание

- [Возможности](#возможности)
- [Архитектура](#архитектура)
- [Быстрый старт](#быстрый-старт)
- [Провайдеры](#провайдеры)
- [Вычислительные ресурсы](#вычислительные-ресурсы)
- [Команды](#команды)
- [API-сервер](#api-сервер)
- [Модуль обнаружения](#модуль-обнаружения)
- [Настройка](#настройка)

---

## 🚀 Возможности

### Задача 1: Суперроутер AI API

| Функция | Описание |
|---------|----------|
| **20+ провайдеров** | Google Gemini, Groq, Cerebras, OpenRouter, Mistral, Cohere, HuggingFace, Cloudflare, SambaNova, Together, NVIDIA, Fireworks, DeepInfra, Novita, Lepton, GitHub Models, Perplexity, Hyperbolic, Chutes, Glhf, Requesty, Ollama |
| **Автоматический fallback** | При отказе одного провайдера мгновенно переключается на следующий |
| **Health check без ключей** | Проверяет доступность серверов HTTP-пингом (не нужен API-ключ) |
| **Health check с ключами** | Проверяет доступные модели и делает тестовый запрос |
| **Отслеживание лимитов** | Считает RPM, RPD, TPM для каждого провайдера |
| **3 стратегии** | maximize_uptime / maximize_quality / maximize_speed |
| **OpenAI-совместимый API** | Работает как drop-in замена OpenAI API |
| **Стриминг** | Поддержка SSE для провайдеров с OpenAI-форматом |

### Задача 2: Агрегатор вычислительных мощностей

| Ресурс | Тип | Бесплатно | Часов/неделю |
|--------|-----|-----------|--------------|
| Google Colab | GPU T4 | ✅ | ~40ч |
| Kaggle Kernels | GPU T4/P100 | ✅ | 30ч |
| Lightning AI | GPU T4 | ✅ | 22ч |
| SageMaker Studio Lab | GPU T4 | ✅ | 28ч |
| HuggingFace Spaces | CPU 16GB | ✅ | 24/7 |
| Oracle Cloud | CPU 24GB ARM | ✅ | 24/7 |
| Petals | Decentralized | ✅ | 24/7 |
| Google Cloud Shell | CPU 5GB | ✅ | ~60ч |
| GitHub Codespaces | CPU 8GB | ✅ | 60ч/мес |
| Gradient (Paperspace) | GPU | ✅ | ~20ч |

**Итого бесплатных GPU-часов: ~140ч/неделю**
**Итого бесплатных CPU-часов: 24/7 (постоянные сервисы)**

### Бонус: Модуль обнаружения новых ресурсов

- Периодически сканирует GitHub, Reddit, API провайдеров
- Находит новые бесплатные модели и ресурсы
- Верифицирует доступность
- Автоматически пополняет пул

---

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────┐
│              AI Super Router                      │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │  Router   │  │  Health   │  │  Discovery    │  │
│  │  Engine   │  │  Checker  │  │  Scanner      │  │
│  └─────┬────┘  └─────┬────┘  └──────┬───────┘  │
│        │              │               │          │
│  ┌─────▼──────────────▼───────────────▼──────┐  │
│  │           Unified Client                    │  │
│  │   (OpenAI-compatible API server)            │  │
│  └─────────────────┬─────────────────────────┘  │
│                    │                             │
├────────────────────┼─────────────────────────────┤
│                    ▼                             │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐    │
│  │Goog│ │Groq│ │Cere│ │Open│ │Mist│ │ ...│    │
│  │le  │ │    │ │bras│ │Rout│ │ral │ │    │    │
│  └────┘ └────┘ └────┘ └────┘ └────┘ └────┘    │
│                                                  │
│  ┌──────────────────────────────────────────┐   │
│  │         Compute Aggregator                │   │
│  │  Colab │ Kaggle │ Lightning │ Oracle │... │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

---

## ⚡ Быстрый старт

### 1. Установка

```bash
# Клонируем / распаковываем
cd ai_super_router

# Устанавливаем зависимости
pip install -r requirements.txt
```

### 2. Настройка ключей

Откройте `config/providers.yaml` и замените `YOUR_*_KEY` на реальные ключи.

**Минимум для старта** (бесплатно, без карты):
1. Google AI Studio: https://aistudio.google.com/apikey
2. Groq: https://console.groq.com/keys
3. OpenRouter: https://openrouter.ai/keys
4. HuggingFace: https://huggingface.co/settings/tokens

### 3. Проверка

```bash
# Проверить здоровье провайдеров
python main.py health

# Показать доступные модели
python main.py models

# Показать вычислительные ресурсы
python main.py compute
```

### 4. Использование

```bash
# Интерактивный чат (автоматически выбирает лучшего провайдера)
python main.py chat

# Запуск как API-сервер (OpenAI-совместимый)
python main.py serve

# Поиск новых бесплатных ресурсов
python main.py scan
```

---

## 🔑 Провайдеры — Где получить ключи

| # | Провайдер | Ключ | Карта? | Лимит/день |
|---|-----------|------|--------|------------|
| 1 | Google AI Studio | https://aistudio.google.com/apikey | ❌ | 1500 req |
| 2 | Groq | https://console.groq.com/keys | ❌ | 14400 req |
| 3 | Cerebras | https://cloud.cerebras.ai/ | ❌ | 1000 req |
| 4 | OpenRouter | https://openrouter.ai/keys | ❌ | 200 req |
| 5 | Mistral | https://console.mistral.ai/api-keys | ❌ | 500 req |
| 6 | Cohere | https://dashboard.cohere.com/api-keys | ❌ | 1000 req |
| 7 | HuggingFace | https://huggingface.co/settings/tokens | ❌ | 1000 req |
| 8 | Cloudflare | https://dash.cloudflare.com/profile/api-tokens | ❌ | 10000 req |
| 9 | SambaNova | https://cloud.sambanova.ai/ | ❌ | 100 req |
| 10 | Together | https://api.together.xyz/settings/api-keys | ❌ | 1000 req |
| 11 | NVIDIA NIM | https://build.nvidia.com/ | ❌ | 500 req |
| 12 | Fireworks | https://fireworks.ai/api-keys | ❌ | 500 req |
| 13 | DeepInfra | https://deepinfra.com/dash/api_keys | ❌ | 1000 req |
| 14 | Novita | https://novita.ai/dashboard/key | ❌ | 500 req |
| 15 | Lepton | https://dashboard.lepton.ai/ | ❌ | 500 req |
| 16 | GitHub Models | GitHub PAT | ❌ | 150 req |
| 17 | Perplexity | https://www.perplexity.ai/settings/api | ✅ | 50 req |
| 18 | Hyperbolic | https://app.hyperbolic.xyz/ | ❌ | 1000 req |
| 19 | Chutes | https://chutes.ai/ | ❌ | 500 req |
| 20 | Glhf | https://glhf.chat/ | ❌ | 200 req |
| 21 | Requesty | https://requesty.ai/ | ❌ | 500 req |
| 22 | Ollama (свой) | — | ❌ | ∞ |

**Суммарно при всех ключах: ~33,000+ запросов/день**

---

## 🖥️ Вычислительные ресурсы — Подключение

### Google Colab (как Ollama-сервер)

Используйте `colab_ollama_cell.py` из предыдущих архивов:
1. Запустите ячейку в Colab
2. Скопируйте ngrok URL
3. Вставьте в `config/providers.yaml` → `ollama_local` → `base_url`

### Kaggle

```python
# В Kaggle Notebook:
!pip install ollama
!ollama serve &
!ngrok http 11434
```

### Oracle Cloud (24/7 сервер)

Используйте `setup_openhands.sh` из архива OpenHands — на том же сервере можно запустить и Ollama.

---

## 📡 API-сервер

Запуск:
```bash
python main.py serve 0.0.0.0 8000
```

Использование (совместим с любым OpenAI-клиентом):
```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="any-string"  # Роутер сам управляет ключами
)

response = client.chat.completions.create(
    model="auto",  # Роутер выберет лучшую доступную модель
    messages=[{"role": "user", "content": "Привет!"}]
)
print(response.choices[0].message.content)
```

### Endpoints

| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/v1/chat/completions` | Генерация (OpenAI-формат) |
| GET | `/v1/models` | Список моделей |
| GET | `/status` | Полный статус роутера |

---

## 🔍 Модуль обнаружения

Автоматически ищет новые бесплатные ресурсы:

```bash
# Ручной запуск
python main.py scan
```

Источники:
- GitHub awesome-lists (free-llm-api-resources, cool-ai-stuff, free-ai-tools)
- OpenRouter API (новые бесплатные модели)
- Reddit (r/LocalLLaMA, r/MachineLearning)

При запуске как сервер — сканирует автоматически раз в сутки.

---

## ⚙️ Настройка

### Стратегии маршрутизации

В `config/providers.yaml`:

```yaml
router:
  strategy: "maximize_uptime"     # Приоритет: бесперебойность
  # strategy: "maximize_quality"  # Приоритет: качество модели
  # strategy: "maximize_speed"    # Приоритет: скорость ответа
```

### Приоритет провайдеров

Добавьте `priority: 1-10` к провайдеру (10 = максимальный приоритет):

```yaml
- name: "Groq"
  priority: 9  # Предпочитать Groq за скорость
```

### Предпочтительные модели

```yaml
router:
  prefer_models:
    - "llama-3.3-70b"    # Сначала пробуем 70B
    - "qwen2.5-72b"      # Потом Qwen
    - "llama-3.1-8b"     # Fallback на 8B
```

---

## 🛠️ Для разработчиков

### Программное использование

```python
import asyncio
from core.client import SuperRouterClient
from core.router import Provider, RoutingStrategy

# Загрузка провайдеров
from main import load_providers
providers = load_providers()

async def example():
    client = SuperRouterClient(providers, strategy=RoutingStrategy.MAXIMIZE_UPTIME)
    await client.start()
    
    # Простой запрос
    response = await client.complete("Объясни квантовые вычисления простыми словами")
    print(f"[{response.provider_name}] {response.text}")
    
    # С предпочтениями
    response = await client.complete(
        prompt="Напиши функцию сортировки",
        preferred_model="llama-3.3-70b",
        max_tokens=1000,
    )
    
    await client.stop()

asyncio.run(example())
```

### Добавление нового провайдера

1. Добавьте запись в `config/providers.yaml`
2. Если формат нестандартный — добавьте метод `_request_<format>` в `core/client.py`

---

## 📊 Максимизация токенов

При использовании всех 22 провайдеров:

| Метрика | Значение |
|---------|----------|
| Запросов/день | ~33,000+ |
| Токенов/день | ~50,000,000+ |
| Уникальных моделей | 50+ |
| Провайдеров без карты | 21 из 22 |
| GPU-часов/неделю | ~140ч |
| CPU 24/7 серверов | 3 (HF Spaces, Oracle, Petals) |

---

## ⚠️ Ограничения

- Бесплатные лимиты могут меняться без предупреждения
- Некоторые провайдеры могут быть недоступны в РФ (нужен VPN)
- Скорость Petals зависит от количества участников сети
- Colab/Kaggle засыпают при неактивности
- Модуль discovery находит ресурсы, но не может автоматически получить ключи

---

## 📁 Структура проекта

```
ai_super_router/
├── main.py                    # Точка входа + CLI
├── requirements.txt           # Зависимости
├── config/
│   └── providers.yaml         # Конфигурация провайдеров
├── core/
│   ├── __init__.py
│   ├── router.py              # Ядро маршрутизации
│   ├── client.py              # Унифицированный клиент
│   └── health_checker.py      # Проверка здоровья
├── compute/
│   ├── __init__.py
│   └── aggregator.py          # Агрегатор вычислительных мощностей
└── discovery/
    ├── __init__.py
    └── scanner.py             # Поиск новых ресурсов
```

---

## 🎯 Интеграция с экосистемой

Этот роутер — фундамент **ИТ-отдела** персональной экосистемы:

- **Дневник с ИИ** → использует роутер для генерации ответов
- **CRM** → использует для генерации тёплых сообщений
- **Дизайн-система** → использует для кодогенерации
- **Информационное ядро** → использует для анализа и суммаризации
- **MetaGPT / OpenHands** → подключаются к роутеру как к единому LLM-бэкенду

Настройка в MetaGPT/OpenHands:
```yaml
# config.yaml
llm:
  base_url: "http://localhost:8000/v1"
  api_key: "super-router"
  model: "auto"
```
