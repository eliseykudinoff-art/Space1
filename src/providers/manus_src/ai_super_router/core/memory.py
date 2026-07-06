"""
🧠 AI Super Router — Модуль памяти и контекста
================================================
Сохранение контекста между вызовами, сменой модели/провайдера.
Поддержка:
  - Краткосрочная память (текущая сессия, история диалога)
  - Долгосрочная память (факты, сущности, предпочтения)
  - Контекстный менеджер (формирование промптов с учётом памяти)
  - Персистентность (всё сохраняется на диск, переживает перезагрузки)
"""

import json
import time
import hashlib
import logging
import os
import re
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Any, Tuple
from collections import deque
from datetime import datetime

logger = logging.getLogger("ai_router.memory")


# ═══════════════════════════════════════════════════════════════
# КОНФИГУРАЦИЯ
# ═══════════════════════════════════════════════════════════════

@dataclass
class MemoryConfig:
    """Настройки модуля памяти."""
    # Пути хранения
    storage_dir: str = "./memory_store"
    
    # Краткосрочная память
    max_session_messages: int = 50          # Макс. сообщений в сессии
    max_context_tokens: int = 4000          # Макс. токенов контекста для LLM
    
    # Долгосрочная память
    max_facts: int = 1000                   # Макс. фактов
    max_entities: int = 500                 # Макс. сущностей
    fact_relevance_decay: float = 0.95      # Затухание релевантности со временем
    
    # Автоизвлечение
    auto_extract_facts: bool = True         # Автоматически извлекать факты из диалогов
    auto_extract_entities: bool = True      # Автоматически извлекать сущности
    
    # Контекст
    include_facts_in_context: bool = True   # Добавлять факты в контекст LLM
    include_session_summary: bool = True    # Добавлять резюме сессии
    max_relevant_facts: int = 10            # Макс. фактов в контексте


# ═══════════════════════════════════════════════════════════════
# СТРУКТУРЫ ДАННЫХ
# ═══════════════════════════════════════════════════════════════

@dataclass
class Message:
    """Одно сообщение в диалоге."""
    role: str                   # user, assistant, system
    content: str
    timestamp: float = field(default_factory=time.time)
    model: str = ""             # Какая модель ответила
    provider: str = ""          # Какой провайдер использовался
    tokens_used: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Message":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class Fact:
    """Извлечённый факт о пользователе или мире."""
    id: str
    content: str                # Текст факта
    category: str               # user_info, preference, goal, context, knowledge
    source: str                 # Откуда извлечён (session_id, manual)
    timestamp: float = field(default_factory=time.time)
    relevance_score: float = 1.0
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Fact":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class Entity:
    """Сущность (человек, проект, концепция, инструмент)."""
    id: str
    name: str
    entity_type: str            # person, project, concept, tool, place, organization
    description: str = ""
    attributes: Dict[str, Any] = field(default_factory=dict)
    relations: List[Dict[str, str]] = field(default_factory=list)  # [{target_id, relation_type, description}]
    created: float = field(default_factory=time.time)
    updated: float = field(default_factory=time.time)
    access_count: int = 0
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Entity":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class Session:
    """Сессия диалога."""
    id: str
    started: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    messages: List[Message] = field(default_factory=list)
    summary: str = ""
    topic: str = ""
    models_used: List[str] = field(default_factory=list)
    providers_used: List[str] = field(default_factory=list)
    total_tokens: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════
# ХРАНИЛИЩЕ (файловое, без внешних зависимостей)
# ═══════════════════════════════════════════════════════════════

class FileStorage:
    """
    Персистентное хранилище на файловой системе.
    Работает без внешних зависимостей (SQLite, Redis, Qdrant).
    При масштабировании заменяется на Qdrant + NetworkX.
    """
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.facts_dir = self.base_dir / "facts"
        self.entities_dir = self.base_dir / "entities"
        self.sessions_dir = self.base_dir / "sessions"
        self.index_dir = self.base_dir / "index"
        
        # Создаём директории
        for d in [self.facts_dir, self.entities_dir, self.sessions_dir, self.index_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        # Индексы в памяти (загружаются при старте)
        self._facts_index: Dict[str, Fact] = {}
        self._entities_index: Dict[str, Entity] = {}
        self._keyword_index: Dict[str, List[str]] = {}  # keyword -> [fact_ids]
        
        self._load_indices()
    
    def _load_indices(self):
        """Загружает индексы из файлов при старте."""
        # Загрузка фактов
        for f in self.facts_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                fact = Fact.from_dict(data)
                self._facts_index[fact.id] = fact
            except Exception as e:
                logger.warning(f"Ошибка загрузки факта {f}: {e}")
        
        # Загрузка сущностей
        for f in self.entities_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                entity = Entity.from_dict(data)
                self._entities_index[entity.id] = entity
            except Exception as e:
                logger.warning(f"Ошибка загрузки сущности {f}: {e}")
        
        # Загрузка keyword-индекса
        kw_file = self.index_dir / "keywords.json"
        if kw_file.exists():
            try:
                self._keyword_index = json.loads(kw_file.read_text(encoding="utf-8"))
            except:
                self._keyword_index = {}
        
        # Перестроение keyword-индекса если пустой
        if not self._keyword_index and self._facts_index:
            self._rebuild_keyword_index()
        
        logger.info(f"📦 Память загружена: {len(self._facts_index)} фактов, {len(self._entities_index)} сущностей")
    
    def _rebuild_keyword_index(self):
        """Перестраивает keyword-индекс из фактов."""
        self._keyword_index = {}
        for fact_id, fact in self._facts_index.items():
            keywords = self._extract_keywords(fact.content)
            for kw in keywords:
                if kw not in self._keyword_index:
                    self._keyword_index[kw] = []
                if fact_id not in self._keyword_index[kw]:
                    self._keyword_index[kw].append(fact_id)
        self._save_keyword_index()
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Извлекает ключевые слова из текста (простой метод)."""
        # Убираем пунктуацию, приводим к нижнему регистру
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text.split()
        # Фильтруем стоп-слова и короткие
        stop_words = {
            'и', 'в', 'на', 'с', 'по', 'для', 'что', 'это', 'как', 'не', 'но',
            'а', 'или', 'от', 'до', 'из', 'к', 'у', 'о', 'за', 'при', 'так',
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'shall', 'to', 'of', 'in', 'for',
            'on', 'with', 'at', 'by', 'from', 'or', 'an', 'be', 'this', 'that',
            'он', 'она', 'оно', 'они', 'мы', 'вы', 'я', 'ты', 'его', 'её', 'их',
            'мой', 'твой', 'наш', 'ваш', 'свой', 'который', 'какой', 'такой',
            'все', 'всё', 'весь', 'каждый', 'другой', 'самый', 'быть', 'есть',
            'был', 'будет', 'может', 'нужно', 'надо', 'очень', 'уже', 'ещё',
            'тоже', 'также', 'только', 'если', 'когда', 'где', 'там', 'тут',
        }
        return [w for w in words if len(w) > 2 and w not in stop_words]
    
    def _save_keyword_index(self):
        """Сохраняет keyword-индекс на диск."""
        kw_file = self.index_dir / "keywords.json"
        kw_file.write_text(json.dumps(self._keyword_index, ensure_ascii=False, indent=1), encoding="utf-8")
    
    # --- Факты ---
    
    def save_fact(self, fact: Fact):
        """Сохраняет факт."""
        self._facts_index[fact.id] = fact
        filepath = self.facts_dir / f"{fact.id}.json"
        filepath.write_text(json.dumps(fact.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        
        # Обновляем keyword-индекс
        keywords = self._extract_keywords(fact.content)
        for kw in keywords:
            if kw not in self._keyword_index:
                self._keyword_index[kw] = []
            if fact.id not in self._keyword_index[kw]:
                self._keyword_index[kw].append(fact.id)
        self._save_keyword_index()
    
    def get_fact(self, fact_id: str) -> Optional[Fact]:
        return self._facts_index.get(fact_id)
    
    def get_all_facts(self) -> List[Fact]:
        return list(self._facts_index.values())
    
    def search_facts(self, query: str, limit: int = 10) -> List[Fact]:
        """Поиск фактов по ключевым словам (BM25-подобный)."""
        keywords = self._extract_keywords(query)
        if not keywords:
            return []
        
        # Подсчёт score для каждого факта
        scores: Dict[str, float] = {}
        for kw in keywords:
            fact_ids = self._keyword_index.get(kw, [])
            # IDF-подобный вес: чем реже слово, тем важнее
            idf = 1.0 / (1.0 + len(fact_ids) * 0.1)
            for fid in fact_ids:
                scores[fid] = scores.get(fid, 0) + idf
        
        # Добавляем relevance_score и access_count
        ranked = []
        for fid, score in scores.items():
            fact = self._facts_index.get(fid)
            if fact:
                # Комбинированный score: keyword match + relevance + freshness
                age_days = (time.time() - fact.timestamp) / 86400
                freshness = 1.0 / (1.0 + age_days * 0.01)
                combined = score * fact.relevance_score * freshness
                ranked.append((combined, fact))
        
        ranked.sort(key=lambda x: -x[0])
        return [f for _, f in ranked[:limit]]
    
    def delete_fact(self, fact_id: str):
        """Удаляет факт."""
        if fact_id in self._facts_index:
            del self._facts_index[fact_id]
            filepath = self.facts_dir / f"{fact_id}.json"
            if filepath.exists():
                filepath.unlink()
    
    # --- Сущности ---
    
    def save_entity(self, entity: Entity):
        """Сохраняет сущность."""
        self._entities_index[entity.id] = entity
        filepath = self.entities_dir / f"{entity.id}.json"
        filepath.write_text(json.dumps(entity.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        return self._entities_index.get(entity_id)
    
    def find_entity(self, name: str) -> Optional[Entity]:
        """Поиск сущности по имени."""
        name_lower = name.lower()
        for entity in self._entities_index.values():
            if entity.name.lower() == name_lower:
                return entity
        return None
    
    def get_all_entities(self) -> List[Entity]:
        return list(self._entities_index.values())
    
    def search_entities(self, query: str, entity_type: Optional[str] = None, limit: int = 10) -> List[Entity]:
        """Поиск сущностей."""
        query_lower = query.lower()
        results = []
        for entity in self._entities_index.values():
            if entity_type and entity.entity_type != entity_type:
                continue
            # Простой поиск по имени и описанию
            score = 0
            if query_lower in entity.name.lower():
                score += 10
            if query_lower in entity.description.lower():
                score += 5
            for tag in entity.tags:
                if query_lower in tag.lower():
                    score += 3
            if score > 0:
                results.append((score, entity))
        
        results.sort(key=lambda x: -x[0])
        return [e for _, e in results[:limit]]
    
    # --- Сессии ---
    
    def save_session(self, session: Session):
        """Сохраняет сессию."""
        filepath = self.sessions_dir / f"{session.id}.json"
        data = {
            "id": session.id,
            "started": session.started,
            "last_active": session.last_active,
            "summary": session.summary,
            "topic": session.topic,
            "models_used": session.models_used,
            "providers_used": session.providers_used,
            "total_tokens": session.total_tokens,
            "metadata": session.metadata,
            "messages": [m.to_dict() for m in session.messages],
        }
        filepath.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    
    def load_session(self, session_id: str) -> Optional[Session]:
        """Загружает сессию."""
        filepath = self.sessions_dir / f"{session_id}.json"
        if not filepath.exists():
            return None
        try:
            data = json.loads(filepath.read_text(encoding="utf-8"))
            session = Session(
                id=data["id"],
                started=data["started"],
                last_active=data["last_active"],
                summary=data.get("summary", ""),
                topic=data.get("topic", ""),
                models_used=data.get("models_used", []),
                providers_used=data.get("providers_used", []),
                total_tokens=data.get("total_tokens", 0),
                metadata=data.get("metadata", {}),
            )
            session.messages = [Message.from_dict(m) for m in data.get("messages", [])]
            return session
        except Exception as e:
            logger.error(f"Ошибка загрузки сессии {session_id}: {e}")
            return None
    
    def list_sessions(self, limit: int = 20) -> List[Dict]:
        """Список последних сессий (без сообщений)."""
        sessions = []
        for f in sorted(self.sessions_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:limit]:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                sessions.append({
                    "id": data["id"],
                    "started": data["started"],
                    "last_active": data["last_active"],
                    "topic": data.get("topic", ""),
                    "summary": data.get("summary", ""),
                    "message_count": len(data.get("messages", [])),
                })
            except:
                continue
        return sessions


# ═══════════════════════════════════════════════════════════════
# ИЗВЛЕЧЕНИЕ ФАКТОВ И СУЩНОСТЕЙ (без LLM, на правилах)
# ═══════════════════════════════════════════════════════════════

class FactExtractor:
    """
    Извлекает факты и сущности из текста.
    Базовая версия — на правилах и паттернах.
    При наличии LLM — может использовать его для более точного извлечения.
    """
    
    # Паттерны для извлечения фактов
    FACT_PATTERNS = [
        # "Я живу в ..." / "Я из ..."
        (r'я\s+(?:живу|нахожусь|обитаю)\s+(?:в|на)\s+(.+?)(?:\.|,|$)', 'user_info', 'location'),
        # "Меня зовут ..."
        (r'(?:меня\s+зовут|я\s+[-–—]\s*)\s*([А-ЯA-Z][а-яa-z]+)', 'user_info', 'name'),
        # "Мне ... лет"
        (r'мне\s+(\d+)\s+(?:лет|год|года)', 'user_info', 'age'),
        # "Я работаю / я ... по профессии"
        (r'я\s+(?:работаю|тружусь)\s+(.+?)(?:\.|,|$)', 'user_info', 'occupation'),
        # "Я хочу / мне нужно / моя цель"
        (r'(?:я\s+хочу|мне\s+нужно|моя\s+цель|планирую)\s+(.+?)(?:\.|,|$)', 'goal', 'goal'),
        # "Мне нравится / я люблю / я интересуюсь"
        (r'(?:мне\s+нравится|я\s+люблю|я\s+интересуюсь|увлекаюсь)\s+(.+?)(?:\.|,|$)', 'preference', 'interest'),
        # "Я умею / я могу / мой навык"
        (r'(?:я\s+умею|я\s+могу|мой\s+навык|владею)\s+(.+?)(?:\.|,|$)', 'user_info', 'skill'),
        # "Я не люблю / мне не нравится / раздражает"
        (r'(?:я\s+не\s+люблю|мне\s+не\s+нравится|раздражает|бесит)\s+(.+?)(?:\.|,|$)', 'preference', 'dislike'),
    ]
    
    # Паттерны для сущностей
    ENTITY_PATTERNS = [
        # Имена (с заглавной буквы, кириллица/латиница)
        (r'\b([А-ЯA-Z][а-яa-z]+(?:\s+[А-ЯA-Z][а-яa-z]+)?)\b', 'person'),
        # URL / сервисы
        (r'((?:https?://)?(?:[\w-]+\.)+[\w-]+(?:/\S*)?)', 'tool'),
    ]
    
    def extract_facts(self, text: str, source: str = "dialog") -> List[Fact]:
        """Извлекает факты из текста."""
        facts = []
        text_lower = text.lower()
        
        for pattern, category, tag in self.FACT_PATTERNS:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                content = match.group(1).strip() if match.groups() else match.group(0).strip()
                if len(content) > 3 and len(content) < 200:
                    fact_id = hashlib.md5(f"{category}:{content}".encode()).hexdigest()[:12]
                    fact = Fact(
                        id=fact_id,
                        content=content,
                        category=category,
                        source=source,
                        tags=[tag],
                    )
                    facts.append(fact)
        
        return facts
    
    def extract_facts_with_llm(self, text: str, llm_response: str, source: str = "dialog") -> List[Fact]:
        """
        Извлекает факты с помощью LLM (вызывается отдельно).
        Парсит структурированный ответ LLM.
        """
        facts = []
        # Ожидаемый формат от LLM: JSON-список фактов
        try:
            # Пытаемся найти JSON в ответе
            json_match = re.search(r'\[.*\]', llm_response, re.DOTALL)
            if json_match:
                items = json.loads(json_match.group())
                for item in items:
                    if isinstance(item, dict) and "content" in item:
                        fact_id = hashlib.md5(item["content"].encode()).hexdigest()[:12]
                        fact = Fact(
                            id=fact_id,
                            content=item["content"],
                            category=item.get("category", "knowledge"),
                            source=source,
                            tags=item.get("tags", []),
                        )
                        facts.append(fact)
        except (json.JSONDecodeError, AttributeError):
            pass
        
        return facts


# ═══════════════════════════════════════════════════════════════
# КОНТЕКСТНЫЙ МЕНЕДЖЕР
# ═══════════════════════════════════════════════════════════════

class ContextManager:
    """
    Формирует оптимальный контекст для LLM-запросов.
    
    Задачи:
    - Собрать релевантные факты из памяти
    - Сформировать историю диалога (с учётом лимита токенов)
    - Добавить метаданные (время, состояние, активная парадигма)
    - Обеспечить бесшовную смену модели/провайдера
    """
    
    def __init__(self, storage: FileStorage, config: MemoryConfig):
        self.storage = storage
        self.config = config
    
    def build_context(self, 
                      current_message: str,
                      session: Session,
                      system_prompt: Optional[str] = None,
                      paradigm: Optional[str] = None) -> Dict[str, Any]:
        """
        Строит полный контекст для LLM-запроса.
        
        Returns:
            {
                "system_prompt": str,       # Системный промпт с фактами
                "messages": List[Dict],     # История + текущее сообщение
                "metadata": Dict,           # Мета-информация для логирования
            }
        """
        # 1. Собираем релевантные факты
        relevant_facts = self._get_relevant_facts(current_message)
        
        # 2. Формируем системный промпт
        enhanced_system = self._build_system_prompt(system_prompt, relevant_facts, paradigm)
        
        # 3. Формируем историю (с учётом лимита токенов)
        history = self._build_history(session, current_message)
        
        # 4. Метаданные
        metadata = {
            "facts_used": len(relevant_facts),
            "history_messages": len(history) - 1,  # Без текущего
            "timestamp": time.time(),
            "paradigm": paradigm,
        }
        
        return {
            "system_prompt": enhanced_system,
            "messages": history,
            "metadata": metadata,
        }
    
    def _get_relevant_facts(self, query: str) -> List[Fact]:
        """Находит релевантные факты для запроса."""
        if not self.config.include_facts_in_context:
            return []
        
        facts = self.storage.search_facts(query, limit=self.config.max_relevant_facts)
        
        # Обновляем access_count
        for fact in facts:
            fact.access_count += 1
            fact.last_accessed = time.time()
            self.storage.save_fact(fact)
        
        return facts
    
    def _build_system_prompt(self, 
                             base_prompt: Optional[str],
                             facts: List[Fact],
                             paradigm: Optional[str]) -> str:
        """Формирует обогащённый системный промпт."""
        parts = []
        
        # Базовый промпт
        if base_prompt:
            parts.append(base_prompt)
        
        # Блок фактов о пользователе
        if facts:
            facts_text = "\n".join(f"- {f.content}" for f in facts)
            parts.append(
                f"\n[Контекст из памяти — что известно о пользователе и ситуации:]\n{facts_text}"
            )
        
        # Парадигмальная линза
        if paradigm:
            parts.append(
                f"\n[Активная парадигма восприятия: {paradigm}. "
                f"Интерпретируй и формулируй ответы через призму этой системы мышления, "
                f"но не навязывай её — используй как дополнительный ракурс.]"
            )
        
        # Временной контекст
        now = datetime.now()
        parts.append(
            f"\n[Текущее время: {now.strftime('%Y-%m-%d %H:%M')}, "
            f"день недели: {['Пн','Вт','Ср','Чт','Пт','Сб','Вс'][now.weekday()]}]"
        )
        
        return "\n".join(parts)
    
    def _build_history(self, session: Session, current_message: str) -> List[Dict[str, str]]:
        """Формирует историю диалога с учётом лимита токенов."""
        messages = []
        
        # Добавляем резюме предыдущей сессии если есть
        if session.summary and self.config.include_session_summary:
            messages.append({
                "role": "system",
                "content": f"[Резюме предыдущего контекста: {session.summary}]"
            })
        
        # Добавляем историю (последние N сообщений, с учётом токенов)
        token_budget = self.config.max_context_tokens
        history_messages = []
        
        for msg in reversed(session.messages):
            # Грубая оценка токенов (1 токен ≈ 4 символа для русского)
            msg_tokens = len(msg.content) // 3
            if token_budget - msg_tokens < 500:  # Оставляем запас
                break
            token_budget -= msg_tokens
            history_messages.insert(0, {"role": msg.role, "content": msg.content})
        
        messages.extend(history_messages)
        
        # Текущее сообщение
        messages.append({"role": "user", "content": current_message})
        
        return messages
    
    def summarize_for_handoff(self, session: Session) -> str:
        """
        Создаёт резюме сессии для передачи контекста при смене модели/провайдера.
        Вызывается когда роутер переключается на другого провайдера.
        """
        if not session.messages:
            return ""
        
        # Собираем ключевые моменты
        parts = []
        
        if session.topic:
            parts.append(f"Тема: {session.topic}")
        
        # Последние 3 обмена (user+assistant)
        recent_pairs = []
        i = len(session.messages) - 1
        while i >= 0 and len(recent_pairs) < 3:
            if session.messages[i].role == "assistant" and i > 0:
                user_msg = session.messages[i-1]
                if user_msg.role == "user":
                    recent_pairs.insert(0, (user_msg.content[:100], session.messages[i].content[:100]))
                    i -= 2
                    continue
            i -= 1
        
        if recent_pairs:
            parts.append("Последние обмены:")
            for user, assistant in recent_pairs:
                parts.append(f"  User: {user}...")
                parts.append(f"  AI: {assistant}...")
        
        return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════
# ГЛАВНЫЙ КЛАСС ПАМЯТИ
# ═══════════════════════════════════════════════════════════════

class Memory:
    """
    Главный интерфейс модуля памяти.
    
    Использование:
        memory = Memory(config)
        memory.start_session()
        
        # При каждом запросе:
        context = memory.get_context("Привет, как дела?")
        # ... отправить context в LLM ...
        memory.record_exchange(user_msg, assistant_msg, model, provider, tokens)
        
        # Система автоматически:
        # - Сохраняет историю
        # - Извлекает факты
        # - Формирует контекст с учётом памяти
        # - Обеспечивает бесшовную смену провайдера
    """
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        self.config = config or MemoryConfig()
        self.storage = FileStorage(self.config.storage_dir)
        self.context_manager = ContextManager(self.storage, self.config)
        self.fact_extractor = FactExtractor()
        
        # Текущая сессия
        self._current_session: Optional[Session] = None
        self._active_paradigm: Optional[str] = None
        
        logger.info("🧠 Модуль памяти инициализирован")
    
    # --- Управление сессиями ---
    
    def start_session(self, session_id: Optional[str] = None, topic: str = "") -> str:
        """Начинает новую сессию или возобновляет существующую."""
        if session_id:
            # Попытка загрузить существующую
            existing = self.storage.load_session(session_id)
            if existing:
                self._current_session = existing
                logger.info(f"📂 Возобновлена сессия: {session_id}")
                return session_id
        
        # Новая сессия
        new_id = session_id or hashlib.md5(str(time.time()).encode()).hexdigest()[:10]
        self._current_session = Session(id=new_id, topic=topic)
        
        # Подгружаем резюме последней сессии
        recent = self.storage.list_sessions(limit=1)
        if recent and recent[0]["summary"]:
            self._current_session.summary = recent[0]["summary"]
        
        logger.info(f"🆕 Новая сессия: {new_id}")
        return new_id
    
    def end_session(self, summary: str = ""):
        """Завершает текущую сессию."""
        if not self._current_session:
            return
        
        if summary:
            self._current_session.summary = summary
        elif not self._current_session.summary and self._current_session.messages:
            # Авто-резюме из последних сообщений
            self._current_session.summary = self._auto_summarize()
        
        self.storage.save_session(self._current_session)
        logger.info(f"💾 Сессия сохранена: {self._current_session.id}")
        self._current_session = None
    
    def _auto_summarize(self) -> str:
        """Автоматическое резюме сессии (простое, без LLM)."""
        if not self._current_session or not self._current_session.messages:
            return ""
        
        # Берём первое сообщение пользователя как тему
        user_messages = [m for m in self._current_session.messages if m.role == "user"]
        if not user_messages:
            return ""
        
        first = user_messages[0].content[:150]
        last = user_messages[-1].content[:150] if len(user_messages) > 1 else ""
        
        summary = f"Начало: {first}"
        if last and last != first:
            summary += f" | Конец: {last}"
        summary += f" | Сообщений: {len(self._current_session.messages)}"
        
        return summary
    
    # --- Основной рабочий цикл ---
    
    def get_context(self, 
                    message: str, 
                    system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Получить контекст для LLM-запроса.
        Вызывается ПЕРЕД отправкой запроса к провайдеру.
        
        Returns:
            {
                "system_prompt": str,
                "messages": List[Dict],
                "metadata": Dict,
            }
        """
        if not self._current_session:
            self.start_session()
        
        return self.context_manager.build_context(
            current_message=message,
            session=self._current_session,
            system_prompt=system_prompt,
            paradigm=self._active_paradigm,
        )
    
    def record_exchange(self,
                        user_message: str,
                        assistant_response: str,
                        model: str = "",
                        provider: str = "",
                        tokens_used: int = 0):
        """
        Записывает обмен (вопрос-ответ) в память.
        Вызывается ПОСЛЕ получения ответа от провайдера.
        """
        if not self._current_session:
            self.start_session()
        
        session = self._current_session
        
        # Записываем сообщения
        user_msg = Message(role="user", content=user_message)
        session.messages.append(user_msg)
        
        assistant_msg = Message(
            role="assistant", 
            content=assistant_response,
            model=model,
            provider=provider,
            tokens_used=tokens_used,
        )
        session.messages.append(assistant_msg)
        
        # Обновляем метаданные сессии
        session.last_active = time.time()
        session.total_tokens += tokens_used
        if model and model not in session.models_used:
            session.models_used.append(model)
        if provider and provider not in session.providers_used:
            session.providers_used.append(provider)
        
        # Автоизвлечение фактов
        if self.config.auto_extract_facts:
            self._extract_and_save_facts(user_message, session.id)
        
        # Обрезаем историю если превышен лимит
        if len(session.messages) > self.config.max_session_messages:
            # Сохраняем резюме обрезанной части
            cut_messages = session.messages[:len(session.messages) - self.config.max_session_messages]
            session.summary = self._summarize_messages(cut_messages, session.summary)
            session.messages = session.messages[-self.config.max_session_messages:]
        
        # Периодическое сохранение (каждые 5 сообщений)
        if len(session.messages) % 5 == 0:
            self.storage.save_session(session)
    
    def _extract_and_save_facts(self, text: str, source: str):
        """Извлекает и сохраняет факты из текста."""
        facts = self.fact_extractor.extract_facts(text, source)
        for fact in facts:
            # Проверяем дубликаты
            existing = self.storage.get_fact(fact.id)
            if not existing:
                self.storage.save_fact(fact)
                logger.debug(f"📌 Новый факт: {fact.content[:50]}")
    
    def _summarize_messages(self, messages: List[Message], existing_summary: str) -> str:
        """Создаёт резюме списка сообщений."""
        user_msgs = [m.content[:100] for m in messages if m.role == "user"]
        new_summary = " | ".join(user_msgs[:5])
        if existing_summary:
            return f"{existing_summary} → {new_summary}"
        return new_summary
    
    # --- Смена провайдера/модели ---
    
    def get_handoff_context(self) -> str:
        """
        Получить контекст для передачи при смене провайдера.
        Вызывается роутером при fallback на другого провайдера.
        """
        if not self._current_session:
            return ""
        return self.context_manager.summarize_for_handoff(self._current_session)
    
    # --- Управление фактами ---
    
    def add_fact(self, content: str, category: str = "knowledge", tags: Optional[List[str]] = None):
        """Вручную добавить факт."""
        fact_id = hashlib.md5(f"{category}:{content}".encode()).hexdigest()[:12]
        fact = Fact(
            id=fact_id,
            content=content,
            category=category,
            source="manual",
            tags=tags or [],
        )
        self.storage.save_fact(fact)
        logger.info(f"📌 Факт добавлен: {content[:50]}")
    
    def search_memory(self, query: str, limit: int = 10) -> List[Dict]:
        """Поиск по всей памяти (факты + сущности)."""
        results = []
        
        # Поиск фактов
        facts = self.storage.search_facts(query, limit=limit)
        for f in facts:
            results.append({
                "type": "fact",
                "content": f.content,
                "category": f.category,
                "tags": f.tags,
                "timestamp": f.timestamp,
            })
        
        # Поиск сущностей
        entities = self.storage.search_entities(query, limit=limit)
        for e in entities:
            results.append({
                "type": "entity",
                "name": e.name,
                "entity_type": e.entity_type,
                "description": e.description,
                "timestamp": e.created,
            })
        
        return results
    
    def get_facts(self, category: Optional[str] = None) -> List[Dict]:
        """Получить все факты (опционально по категории)."""
        facts = self.storage.get_all_facts()
        if category:
            facts = [f for f in facts if f.category == category]
        return [f.to_dict() for f in facts]
    
    # --- Управление сущностями ---
    
    def add_entity(self, name: str, entity_type: str, description: str = "", 
                   attributes: Optional[Dict] = None, tags: Optional[List[str]] = None):
        """Добавить сущность."""
        entity_id = hashlib.md5(f"{entity_type}:{name}".encode()).hexdigest()[:12]
        entity = Entity(
            id=entity_id,
            name=name,
            entity_type=entity_type,
            description=description,
            attributes=attributes or {},
            tags=tags or [],
        )
        self.storage.save_entity(entity)
        logger.info(f"🏷️ Сущность добавлена: {name} ({entity_type})")
    
    def add_relation(self, entity_name: str, target_name: str, relation_type: str, description: str = ""):
        """Добавить связь между сущностями."""
        entity = self.storage.find_entity(entity_name)
        target = self.storage.find_entity(target_name)
        
        if not entity:
            logger.warning(f"Сущность не найдена: {entity_name}")
            return
        if not target:
            logger.warning(f"Сущность не найдена: {target_name}")
            return
        
        entity.relations.append({
            "target_id": target.id,
            "target_name": target.name,
            "relation_type": relation_type,
            "description": description,
        })
        entity.updated = time.time()
        self.storage.save_entity(entity)
    
    # --- Парадигмальная линза ---
    
    def set_paradigm(self, paradigm: Optional[str]):
        """Устанавливает активную парадигму восприятия."""
        self._active_paradigm = paradigm
        if paradigm:
            logger.info(f"🔮 Парадигма: {paradigm}")
        else:
            logger.info("🔮 Парадигма сброшена")
    
    # --- Статистика ---
    
    def get_stats(self) -> Dict[str, Any]:
        """Статистика модуля памяти."""
        facts = self.storage.get_all_facts()
        entities = self.storage.get_all_entities()
        sessions = self.storage.list_sessions(limit=100)
        
        return {
            "total_facts": len(facts),
            "facts_by_category": self._count_by(facts, "category"),
            "total_entities": len(entities),
            "entities_by_type": self._count_by(entities, "entity_type"),
            "total_sessions": len(sessions),
            "current_session": {
                "id": self._current_session.id if self._current_session else None,
                "messages": len(self._current_session.messages) if self._current_session else 0,
                "models_used": self._current_session.models_used if self._current_session else [],
                "providers_used": self._current_session.providers_used if self._current_session else [],
            },
            "active_paradigm": self._active_paradigm,
            "storage_dir": self.config.storage_dir,
        }
    
    def _count_by(self, items: List, attr: str) -> Dict[str, int]:
        """Подсчёт по атрибуту."""
        counts = {}
        for item in items:
            val = getattr(item, attr, "unknown")
            counts[val] = counts.get(val, 0) + 1
        return counts


# ═══════════════════════════════════════════════════════════════
# ПРОМПТ ДЛЯ LLM-ИЗВЛЕЧЕНИЯ ФАКТОВ
# (используется когда LLM доступен для глубокого анализа)
# ═══════════════════════════════════════════════════════════════

FACT_EXTRACTION_PROMPT = """Проанализируй следующее сообщение пользователя и извлеки из него факты.

Категории фактов:
- user_info: информация о пользователе (имя, возраст, место, профессия, навыки)
- preference: предпочтения, вкусы, что нравится/не нравится
- goal: цели, планы, намерения
- context: текущая ситуация, обстоятельства
- knowledge: знания, убеждения, мнения

Верни JSON-массив фактов:
[
  {"content": "текст факта", "category": "категория", "tags": ["тег1", "тег2"]}
]

Если фактов нет — верни пустой массив [].
Извлекай только явно выраженные факты, не додумывай.

Сообщение пользователя:
{message}
"""

ENTITY_EXTRACTION_PROMPT = """Проанализируй текст и извлеки упомянутые сущности (люди, проекты, инструменты, места, организации, концепции).

Верни JSON-массив:
[
  {"name": "имя", "type": "person|project|tool|place|organization|concept", "description": "краткое описание из контекста"}
]

Если сущностей нет — верни [].

Текст:
{message}
"""
