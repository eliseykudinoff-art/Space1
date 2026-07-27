"""
Memory and State Module — CoALA Four-Level Memory Architecture

Per 05_MEMORY_AND_STATE.md:
- Working Memory: Active context (not a separate store)
- Episodic Memory: Past events with temporal index + vector search + hybrid retrieval
- Semantic Memory: Facts/preferences with asymmetric confidence update
- Procedural Memory: Skill Library with success_rate gate and decay

Provides:
- OperationalMemory (Working Memory)
- EpisodicMemory (past episodes with priority formula I)
- SemanticMemory (facts with 0.9/0.7 asymmetric update)
- ProceduralMemory/SkillLibrary (skills with success_rate>0.7 gate)
- ConsolidationGate (episodic → semantic bridge)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import math
import re


# =============================================================================
# Working Memory (Part II) — Not a separate store, current context
# =============================================================================

class OperationalMemory:
    """
    Working Memory — current context window of the LLM call.
    
    Per 05_MEMORY_AND_STATE.md Part II:
    - Not a separate persistent store
    - Current contents of the context window at a specific pipeline step
    - Limited by computational budget C_t (compression when approaching limit)
    """
    
    def __init__(self):
        self._context: Dict[str, Any] = {}
        self._active_metrics: Dict[str, float] = {}
        self._current_steps: List[Dict[str, Any]] = []
    
    def clear(self) -> None:
        """Clear active context and metrics."""
        self._context.clear()
        self._active_metrics.clear()
        self._current_steps.clear()
    
    def set(self, key: str, value: Any) -> None:
        """Set operational context variable."""
        self._context[key] = value
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get operational context variable."""
        return self._context.get(key, default)
    
    def record_step(self, step_name: str, status: str, duration: float, cost: float) -> None:
        """Record a trace of an atomic execution step."""
        self._current_steps.append({
            "step": step_name,
            "status": status,
            "duration": duration,
            "cost": cost,
            "timestamp": datetime.now().isoformat()
        })
        
    def get_steps(self) -> List[Dict[str, Any]]:
        """Get list of recorded steps."""
        return list(self._current_steps)
    
    def update_metric(self, name: str, value: float) -> None:
        """Update active context numeric metric."""
        self._active_metrics[name] = float(value)
        
    def get_metric(self, name: str, default: float = 0.0) -> float:
        """Get active context numeric metric."""
        return self._active_metrics.get(name, default)


# =============================================================================
# Episodic Memory (Part III) — Past events with hybrid retrieval
# =============================================================================

@dataclass
class Episode:
    """
    Episode — an episodic memory entry per 05_MEMORY_AND_STATE.md §III.1.
    
    Format: (T_raw, x, p, A, attempt_history, Q_actual, Phi_task, reflection_triggers)
    Plus: timestamp, client_id (optional), embedding (for vector retrieval)
    
    All fields have defaults for legacy compatibility.
    """
    task_id: str = ""
    title: str = ""
    capability_vector: Tuple[float, ...] = field(default_factory=lambda: tuple())
    category_probs: Dict[str, float] = field(default_factory=dict)
    action_plan: List[str] = field(default_factory=list)
    attempt_history: List[Dict[str, Any]] = field(default_factory=list)
    quality_actual: float = 0.5
    quality: float = 0.5  # Legacy alias for quality_actual
    phi_task: float = 0.0
    reflection_triggers: List[str] = field(default_factory=list)
    client_id: Optional[str] = None
    embedding: Optional[List[float]] = None
    revenue: float = 0.0
    cost: float = 0.0
    time_spent: float = 1.0
    risk: float = 0.1
    status: str = "completed"
    strategy: str = ""  # Legacy field for compatibility
    failure_reason: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def importance(self, q_min: float = 0.5) -> float:
        """
        Importance = |Q_actual - q_min| per §III.2.
        Deviation from expected in either direction carries more information.
        """
        return abs(self.quality_actual - q_min)
    
    def recency(self, current_time: datetime, decay_rate: float = 0.1) -> float:
        """
        Recency = e^(-lambda * (t - t_episode)) per §III.2.
        Same exponential form as Phi_forget (§IV.6).
        """
        delta_t = (current_time - self.timestamp).total_seconds() / 3600.0  # hours
        return math.exp(-decay_rate * delta_t)


class EpisodicMemory:
    """
    Episodic Memory — past events with hybrid (BM25 + vector + temporal) retrieval.

    Per 05_MEMORY_AND_STATE.md Part III:
    - Format: Episode contract (see above)
    - Priority formula: I = w1*Recency + w2*Importance + w3*Relevance (w1+w2+w3=1)
    - Hybrid search: BM25 + vector RRF (MED-08)
    - Temporal index for queries like "last 3 tasks with this client"
    """

    def __init__(
        self,
        w1: float = 0.4,  # Recency weight
        w2: float = 0.3,  # Importance weight
        w3: float = 0.3,  # Relevance weight
        decay_rate: float = 0.1,
        decay_days: float = 30.0,
        bm25_k1: float = 1.5,
        bm25_b: float = 0.75,
    ):
        self._episodes: List[Episode] = []
        self._by_client: Dict[str, List[int]] = {}  # client_id -> episode indices
        self._w1, self._w2, self._w3 = w1, w2, w3
        self._decay_rate = decay_rate
        self._decay_hours = decay_days * 24
        self._bm25_k1 = bm25_k1
        self._bm25_b = bm25_b
        # TF-IDF cache (lazily built)
        self._tfidf_index: Optional[Dict] = None
        self._tfidf_dirty: bool = True

    def add_episode(self, episode: Episode) -> None:
        """Add an episode to episodic memory."""
        self._episodes.append(episode)
        idx = len(self._episodes) - 1
        self._tfidf_dirty = True  # Mark index for rebuild

        # Temporal index by client
        if episode.client_id:
            if episode.client_id not in self._by_client:
                self._by_client[episode.client_id] = []
            self._by_client[episode.client_id].append(idx)

    def get_episodes(self) -> List[Episode]:
        """Get all stored episodes."""
        return list(self._episodes)

    def get_by_client(self, client_id: str) -> List[Episode]:
        """Get recent episodes for a specific client (temporal index)."""
        indices = self._by_client.get(client_id, [])
        return [self._episodes[i] for i in sorted(indices, reverse=True)[:10]]

    def priority(self, episode: Episode, query: str = "") -> float:
        """
        Compute episode priority I per §III.2:
        I = w1*Recency + w2*Importance + w3*Relevance
        """
        now = datetime.now()
        recency = episode.recency(now, self._decay_rate)
        importance = episode.importance()

        # Relevance via hybrid retrieval
        relevance = 0.0
        if query:
            relevance = self._hybrid_relevance(query, episode)

        return self._w1 * recency + self._w2 * importance + self._w3 * relevance

    # -------------------------------------------------------------------------
    # MED-08: Hybrid Retrieval (BM25 + Vector)
    # -------------------------------------------------------------------------

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization: lowercase, split on non-alphanumeric."""
        return re.findall(r'[a-z]+', text.lower())

    def _build_tfidf_index(self) -> None:
        """Build TF-IDF index from episode titles and strategies."""
        if not self._tfidf_dirty or not self._episodes:
            return

        # Corpus: episode texts
        corpus = []
        for ep in self._episodes:
            text = f"{ep.title} {ep.strategy} {' '.join(ep.category_probs.keys())}"
            corpus.append(self._tokenize(text))

        # Document frequencies
        df: Dict[str, int] = {}
        for doc in corpus:
            seen = set(doc)
            for term in seen:
                df[term] = df.get(term, 0) + 1

        N = len(corpus)
        idf: Dict[str, float] = {}
        for term, freq in df.items():
            idf[term] = math.log((N - freq + 0.5) / (freq + 0.5) + 1.0)

        # TF vectors (normalized by doc length)
        doc_lengths = [len(d) for d in corpus]
        avgdl = sum(doc_lengths) / max(len(doc_lengths), 1)

        tf_vectors: List[Dict[str, float]] = []
        for i, doc in enumerate(corpus):
            tf: Dict[str, int] = {}
            for term in doc:
                tf[term] = tf.get(term, 0) + 1

            # BM25 TF normalization
            tf_norm: Dict[str, float] = {}
            for term, freq in tf.items():
                denom = freq + self._bm25_k1 * (1 - self._bm25_b + self._bm25_b * doc_lengths[i] / avgdl)
                tf_norm[term] = freq / denom if denom > 0 else 0.0

            tf_vectors.append(tf_norm)

        # TF-IDF vectors
        tfidf_vectors: List[Dict[str, float]] = []
        for tf_norm in tf_vectors:
            vec: Dict[str, float] = {}
            for term, tf_val in tf_norm.items():
                vec[term] = tf_val * idf.get(term, 0.0)
            tfidf_vectors.append(vec)

        self._tfidf_index = {
            "vectors": tfidf_vectors,
            "idf": idf,
            "avgdl": avgdl,
            "doc_lengths": doc_lengths,
        }
        self._tfidf_dirty = False

    def _bm25_score(self, query: str, doc_idx: int) -> float:
        """Compute BM25-like score for query against document."""
        if self._tfidf_index is None:
            return 0.0

        query_terms = self._tokenize(query)
        if not query_terms:
            return 0.0

        vec = self._tfidf_index["vectors"][doc_idx]
        score = 0.0
        for term in query_terms:
            score += vec.get(term, 0.0)
        return score

    def _vector_similarity(self, query: str, doc_idx: int) -> float:
        """Cosine similarity between query and document TF-IDF vectors."""
        if self._tfidf_index is None:
            return 0.0

        query_terms = self._tokenize(query)
        if not query_terms:
            return 0.0

        # Query vector (binary TF)
        q_vec: Dict[str, float] = {}
        for term in query_terms:
            q_vec[term] = q_vec.get(term, 0.0) + 1.0

        # Normalize query vector
        q_norm = math.sqrt(sum(v * v for v in q_vec.values()))
        if q_norm == 0:
            return 0.0

        d_vec = self._tfidf_index["vectors"][doc_idx]

        # Dot product
        dot = 0.0
        for term, q_val in q_vec.items():
            dot += q_val * d_vec.get(term, 0.0)

        # Doc norm
        d_norm = math.sqrt(sum(v * v for v in d_vec.values()))
        if d_norm == 0:
            return 0.0

        return dot / (q_norm * d_norm)

    def _hybrid_relevance(self, query: str, episode: Episode) -> float:
        """Hybrid relevance: combine BM25 + vector via simple average."""
        self._build_tfidf_index()

        # Find episode index
        try:
            doc_idx = self._episodes.index(episode)
        except ValueError:
            return 0.0

        bm25 = self._bm25_score(query, doc_idx)
        vector = self._vector_similarity(query, doc_idx)

        # Normalize BM25 to [0, 1] using sigmoid-like scaling
        bm25_norm = min(1.0, bm25 / 5.0)  # heuristic scaling

        # Hybrid: equal weight
        return 0.5 * bm25_norm + 0.5 * vector

    def hybrid_retrieve(self, query: str = "", k: int = 5) -> List[Episode]:
        """
        MED-08: Hybrid retrieval combining BM25, vector similarity, and temporal priority.
        Uses RRF (Reciprocal Rank Fusion) to combine rankings.
        """
        if not self._episodes:
            return []

        self._build_tfidf_index()

        # Rank by each method
        bm25_ranks: Dict[int, int] = {}
        vector_ranks: Dict[int, int] = {}
        priority_ranks: Dict[int, int] = {}

        # BM25 ranking
        bm25_scores = [(self._bm25_score(query, i), i) for i in range(len(self._episodes))]
        bm25_scores.sort(reverse=True, key=lambda x: x[0])
        for rank, (_, idx) in enumerate(bm25_scores):
            bm25_ranks[idx] = rank + 1

        # Vector ranking
        vec_scores = [(self._vector_similarity(query, i), i) for i in range(len(self._episodes))]
        vec_scores.sort(reverse=True, key=lambda x: x[0])
        for rank, (_, idx) in enumerate(vec_scores):
            vector_ranks[idx] = rank + 1

        # Priority ranking (temporal + importance)
        pri_scores = [(self.priority(self._episodes[i], query), i) for i in range(len(self._episodes))]
        pri_scores.sort(reverse=True, key=lambda x: x[0])
        for rank, (_, idx) in enumerate(pri_scores):
            priority_ranks[idx] = rank + 1

        # RRF fusion: score = sum(1 / (k + rank)) for each method
        rrf_scores: Dict[int, float] = {}
        for i in range(len(self._episodes)):
            # Check decay
            age_hours = (datetime.now() - self._episodes[i].timestamp).total_seconds() / 3600.0
            if age_hours > self._decay_hours * 3:
                continue

            rrf = 0.0
            rrf += 1.0 / (60 + bm25_ranks.get(i, 999))
            rrf += 1.0 / (60 + vector_ranks.get(i, 999))
            rrf += 1.0 / (60 + priority_ranks.get(i, 999))
            rrf_scores[i] = rrf

        # Sort by RRF score
        sorted_indices = sorted(rrf_scores.keys(), key=lambda i: rrf_scores[i], reverse=True)
        return [self._episodes[i] for i in sorted_indices[:k]]

    def retrieve(self, query: str = "", k: int = 5) -> List[Episode]:
        """
        Retrieve top-k episodes using hybrid retrieval (MED-08).
        Falls back to keyword-only if query is empty.
        """
        if not query:
            # Legacy: priority-only retrieval
            if not self._episodes:
                return []
            scored = []
            for ep in self._episodes:
                age_hours = (datetime.now() - ep.timestamp).total_seconds() / 3600.0
                if age_hours > self._decay_hours * 3:
                    continue
                scored.append((self.priority(ep, ""), ep))
            scored.sort(reverse=True, key=lambda x: x[0])
            return [ep for _, ep in scored[:k]]

        return self.hybrid_retrieve(query, k)

    def recall_strategies(self, keyword: str) -> List[str]:
        """Recall successful strategies matching a keyword using hybrid retrieval."""
        episodes = self.hybrid_retrieve(keyword, k=20)
        strategies = []
        for ep in episodes:
            if ep.status == "completed":
                strategies.append(ep.strategy or ep.title)
        return strategies[:10]

    def recall_failures(self, keyword: str) -> List[str]:
        """Recall failure reasons for failed tasks matching keyword using hybrid retrieval."""
        episodes = self.hybrid_retrieve(keyword, k=20)
        failures = []
        for ep in episodes:
            if ep.status == "failed":
                failures.append(ep.failure_reason or "Unknown")
        return failures[:10]


@dataclass
class SemanticFact:
    """
    Semantic Fact — key-value with asymmetric confidence update.
    
    Per 05_MEMORY_AND_STATE.md §IV:
    - confidence_{t+1} = 0.9*confidence_t + 0.1 (confirmation)
    - confidence_{t+1} = 0.7*confidence_t (contradiction)
    - confidence_effective = confidence_t * (0.5)^contradictions * e^(-lambda*age)
    """
    key: str
    value: str
    confidence: float = 0.5
    contradictions: int = 0
    related_to: List[str] = field(default_factory=list)
    source_episode_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def effective_confidence(self, decay_rate: float = 0.01) -> float:
        """Compute effective confidence with decay."""
        age_days = (datetime.now() - self.updated_at).total_seconds() / 86400.0
        return self.confidence * (0.5 ** self.contradictions) * math.exp(-decay_rate * age_days)


class SemanticMemory:
    """
    Semantic Memory — facts and preferences with asymmetric confidence update.
    
    Per 05_MEMORY_AND_STATE.md Part IV:
    - Key-value storage with optional graph links (related_to)
    - Asymmetric update: 0.9x confirmation, 0.7x contradiction
    - Non-resettable contradiction counter (0.5)^contradictions penalty
    - Facts elevated from Episodic Memory during consolidation
    """
    
    def __init__(self, decay_rate: float = 0.01):
        self._facts: Dict[str, SemanticFact] = {}
        self._decay_rate = decay_rate
    
    def add_fact(
        self, 
        key: str, 
        value: str, 
        confidence: float = 0.5,
        related_to: List[str] | None = None,
        source_episode_id: str | None = None
    ) -> None:
        """Add a new semantic fact."""
        self._facts[key] = SemanticFact(
            key=key,
            value=value,
            confidence=confidence,
            related_to=related_to or [],
            source_episode_id=source_episode_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def confirm(self, key: str) -> bool:
        """
        Confirm an existing fact: confidence = 0.9 * confidence + 0.1.
        Returns False if fact not found.
        """
        if key not in self._facts:
            return False
        fact = self._facts[key]
        fact.confidence = 0.9 * fact.confidence + 0.1
        fact.confidence = min(1.0, fact.confidence)
        fact.updated_at = datetime.now()
        return True
    
    def contradict(self, key: str) -> bool:
        """
        Contradict an existing fact: confidence = 0.7 * confidence, contradictions += 1.
        Returns False if fact not found.
        """
        if key not in self._facts:
            return False
        fact = self._facts[key]
        fact.confidence = 0.7 * fact.confidence
        fact.contradictions += 1
        fact.updated_at = datetime.now()
        return True
    
    def get_fact(self, key: str, use_effective: bool = True) -> Optional[SemanticFact]:
        """Get a semantic fact by key."""
        fact = self._facts.get(key)
        if fact and use_effective:
            # Return a copy with effective confidence for display
            result = dataclass_from_dict(SemanticFact, fact.__dict__.copy())
            result.confidence = fact.effective_confidence(self._decay_rate)
            return result
        return fact
    
    def get_all_facts(self, min_confidence: float = 0.1) -> List[SemanticFact]:
        """Get all facts with effective confidence above threshold."""
        result = []
        for fact in self._facts.values():
            eff = fact.effective_confidence(self._decay_rate)
            if eff >= min_confidence:
                f = dataclass_from_dict(SemanticFact, fact.__dict__.copy())
                f.confidence = eff
                result.append(f)
        return result
    
    def get_related(self, key: str) -> List[SemanticFact]:
        """Get facts related to a given fact."""
        fact = self._facts.get(key)
        if not fact:
            return []
        return [self._facts[r] for r in fact.related_to if r in self._facts]


def dataclass_from_dict(cls, d):
    """Helper to create a dataclass from dict."""
    return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


# =============================================================================
# Procedural Memory / Skill Library (Part V)
# =============================================================================

@dataclass
class Skill:
    """
    Skill — a learnable procedure in the Skill Library.
    
    Per 05_MEMORY_AND_STATE.md §V.2:
    - success_rate > 0.7 gate for activation
    - 30-day / 90-day decay for unused skills
    """
    name: str
    description: str
    success_rate: float = 0.5
    usage_count: int = 0
    last_used: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    
    def is_active(self, min_success_rate: float = 0.7) -> bool:
        """Skill is active if success_rate > min_success_rate."""
        return self.success_rate > min_success_rate
    
    def effective_success_rate(self, short_decay_days: int = 30, long_decay_days: int = 90) -> float:
        """
        Apply decay for unused skills per §V.4.
        - 30 days unused: starts decaying
        - 90 days unused: heavily decayed
        """
        days_unused = (datetime.now() - self.last_used).total_seconds() / 86400.0
        
        if days_unused < short_decay_days:
            return self.success_rate
        elif days_unused < long_decay_days:
            # Linear decay from success_rate to success_rate/2
            decay_progress = (days_unused - short_decay_days) / (long_decay_days - short_decay_days)
            return self.success_rate * (1.0 - 0.5 * decay_progress)
        else:
            # Hard floor at 50% of original
            return self.success_rate * 0.5


class ProceduralMemory:
    """
    Procedural Memory / Skill Library.
    
    Per 05_MEMORY_AND_STATE.md Part V:
    - Skill Library with success_rate gate (threshold > 0.7)
    - 30-day / 90-day decay for unused skills
    - Retrieved by semantic match to current task
    """
    
    def __init__(self, min_success_rate: float = 0.7):
        self._skills: Dict[str, Skill] = {}
        self._min_success_rate = min_success_rate
    
    def add_skill(self, skill: Skill) -> bool:
        """Add a new skill to the library. Returns False if below threshold."""
        if skill.success_rate < self._min_success_rate:
            return False
        self._skills[skill.name] = skill
        return True
    
    def record_usage(self, skill_name: str, success: bool) -> bool:
        """Record skill usage and update success rate."""
        if skill_name not in self._skills:
            return False
        
        skill = self._skills[skill_name]
        skill.usage_count += 1
        
        # Update success rate: weighted moving average
        alpha = 0.1  # Learning rate
        new_success = 1.0 if success else 0.0
        skill.success_rate = (1 - alpha) * skill.success_rate + alpha * new_success
        skill.last_used = datetime.now()
        return True
    
    def get_active_skills(self) -> List[Skill]:
        """Get all active skills (success_rate > threshold)."""
        return [s for s in self._skills.values() if s.is_active(self._min_success_rate)]
    
    def get_skill(self, name: str) -> Optional[Skill]:
        """Get a specific skill."""
        return self._skills.get(name)
    
    def find_skills(self, query: str) -> List[Skill]:
        """Find skills matching a query string."""
        results = []
        query_lower = query.lower()
        for skill in self._skills.values():
            if skill.is_active(self._min_success_rate):
                if query_lower in skill.name.lower() or query_lower in skill.description.lower():
                    results.append(skill)
                elif any(query_lower in tag.lower() for tag in skill.tags):
                    results.append(skill)
        return sorted(results, key=lambda s: s.effective_success_rate(), reverse=True)


# =============================================================================
# Legacy Aliases (for backwards compatibility)
# =============================================================================

StrategicExperience = Episode  # Alias for existing code


@dataclass
class MetaRule:
    """Legacy alias for ProceduralMemory rules."""
    name: str
    description: str
    confidence: float = 0.5
    updated_at: datetime = field(default_factory=datetime.now)


class StrategicMemory(EpisodicMemory):
    """
    Legacy alias for backwards compatibility.
    Use EpisodicMemory instead.
    
    Provides add_experience/get_experiences methods for legacy code compatibility.
    """
    
    def add_experience(self, experience) -> None:
        """Legacy compatibility method - adds episode to episodic memory."""
        self.add_episode(experience)
    
    def get_experiences(self) -> List[Any]:
        """Legacy compatibility method - returns list of episodes."""
        return self.get_episodes()
    
    def get_recent_episodes(self, limit: int = 10) -> List[Any]:
        """Get recent episodes, sorted by timestamp descending."""
        episodes = self.get_episodes()
        # Sort by timestamp descending
        episodes_sorted = sorted(episodes, key=lambda e: e.timestamp if hasattr(e, 'timestamp') else datetime.now(), reverse=True)
        return episodes_sorted[:limit]


class MetaMemory:
    """
    Legacy wrapper combining Semantic and Procedural memory.
    For backwards compatibility with existing code.
    """
    
    def __init__(self):
        self.semantic = SemanticMemory()
        self.procedural = ProceduralMemory()
    
    def add_rule(self, name: str, description: str, confidence: float = 0.5) -> None:
        """Add a rule (stored as semantic fact)."""
        self.semantic.add_fact(name, description, confidence)
    
    def get_rule(self, name: str) -> Optional[MetaRule]:
        """Get a rule."""
        fact = self.semantic.get_fact(name, use_effective=False)
        if fact:
            return MetaRule(
                name=fact.key,
                description=fact.value,
                confidence=fact.confidence,
                updated_at=fact.updated_at
            )
        return None
    
    def list_rules(self) -> List[MetaRule]:
        """List all rules."""
        return [
            MetaRule(name=f.key, description=f.value, confidence=f.confidence, updated_at=f.updated_at)
            for f in self.semantic.get_all_facts()
        ]


# =============================================================================
# Consolidation Gate (Part I, III, IV)
# =============================================================================

class ConsolidationGate:
    """
    Consolidation Gate — episodic → semantic + procedural memory bridge.

    Per 05_MEMORY_AND_STATE.md Part I, III, IV, V:
    - Episodes are consolidated into Episodic Memory
    - Semantic facts extracted from episode outcomes (category, risk, quality, profit)
    - Procedural skills recorded from successful action plans
    - Patterns elevated to Semantic when consistently repeated (3+ episodes)
    """

    def __init__(
        self, 
        episodic_mem: EpisodicMemory,
        semantic_mem: SemanticMemory,
        procedural_mem: ProceduralMemory
    ):
        self.episodic = episodic_mem
        self.semantic = semantic_mem
        self.procedural = procedural_mem

    def consolidate(self, op_mem: OperationalMemory) -> Optional[Episode]:
        """
        Consolidate operational memory into long-term memory stores.

        Creates an Episode from OperationalMemory, then:
        1. Stores in EpisodicMemory
        2. Extracts Semantic facts (category, risk, quality, profit)
        3. Records Procedural skills (successful action plans)
        4. Elevates repeated patterns to Semantic facts

        Returns the created Episode.
        """
        task_id = op_mem.get("task_id")
        if not task_id:
            return None

        episode = Episode(
            task_id=task_id,
            title=op_mem.get("title", "Untitled Task"),
            capability_vector=tuple(op_mem.get("capability_vector", [0.5] * 17)),
            category_probs=op_mem.get("category_probs", {"code": 0.5}),
            action_plan=op_mem.get("action_plan", []),
            attempt_history=op_mem.get_steps(),
            quality_actual=op_mem.get_metric("quality", 0.7),
            phi_task=op_mem.get_metric("revenue", 0.0) - op_mem.get_metric("cost", 0.0),
            reflection_triggers=op_mem.get("reflection_triggers", []),
            client_id=op_mem.get("client_id"),
            revenue=op_mem.get_metric("revenue", 0.0),
            cost=op_mem.get_metric("cost", 0.0),
            time_spent=op_mem.get_metric("time_hours", 1.0),
            risk=op_mem.get_metric("risk", 0.1),
            status="completed" if op_mem.get("status") != "failed" else "failed",
            failure_reason=op_mem.get("failure_reason")
        )

        # 1. Store in episodic memory
        self.episodic.add_episode(episode)

        # 2. Update semantic facts
        self._update_semantic(episode)

        # 3. Update procedural skills
        self._update_procedural(episode)

        # 4. Elevate patterns if repeated
        self._elevate_patterns(episode)

        # Clear operational memory
        op_mem.clear()

        return episode

    def _update_semantic(self, episode: Episode) -> None:
        """Extract semantic facts from episode outcome."""
        # Category preference facts
        for category, prob in episode.category_probs.items():
            key = f"category_preference_{category}"
            existing = self.semantic._facts.get(key)
            if existing:
                existing.confidence = 0.7 * existing.confidence + 0.3 * prob
                existing.updated_at = datetime.now()
            else:
                self.semantic.add_fact(
                    key=key,
                    value=f"Task category '{category}' with probability {prob:.2f}",
                    confidence=prob,
                    source_episode_id=episode.task_id
                )

        # Risk profile fact
        risk_level = "low" if episode.risk < 0.3 else "medium" if episode.risk < 0.7 else "high"
        risk_key = f"risk_profile_{episode.task_id[:8]}"
        self.semantic.add_fact(
            key=risk_key,
            value=f"Risk level: {risk_level} (score={episode.risk:.2f})",
            confidence=1.0 - episode.risk,
            source_episode_id=episode.task_id
        )

        # Quality outcome fact
        quality_key = f"quality_outcome_{episode.task_id[:8]}"
        self.semantic.add_fact(
            key=quality_key,
            value=f"Quality achieved: {episode.quality_actual:.2f}",
            confidence=episode.quality_actual,
            source_episode_id=episode.task_id
        )

        # Profitability fact
        if episode.phi_task != 0.0:
            profit_key = f"profitability_{episode.task_id[:8]}"
            profit_level = "profitable" if episode.phi_task > 0 else "unprofitable"
            self.semantic.add_fact(
                key=profit_key,
                value=f"Task was {profit_level} (phi={episode.phi_task:.2f})",
                confidence=min(1.0, max(0.0, 0.5 + episode.phi_task / 100)),
                source_episode_id=episode.task_id
            )

        # Legacy client-specific confirm/contradict
        client_key = f"client_{episode.client_id}_style" if episode.client_id else None
        if client_key:
            if episode.status == "completed":
                self.semantic.confirm(client_key)
            else:
                self.semantic.contradict(client_key)

    def _update_procedural(self, episode: Episode) -> None:
        """Record procedural skills from episode outcome."""
        # Category skills
        for category in episode.category_probs:
            skill_name = f"category_{category}"
            skill = self.procedural.get_skill(skill_name)

            if skill is None:
                self.procedural.add_skill(Skill(
                    name=skill_name,
                    description=f"Skill for {category} tasks",
                    tags=[category]
                ))

            success = episode.status == "completed"
            self.procedural.record_usage(skill_name, success)

        # MED-07: Store successful action_plan as procedural skill
        if episode.status == "completed" and episode.action_plan:
            plan_key = f"action_plan_{episode.title[:20].replace(' ', '_')}"
            existing_skill = self.procedural.get_skill(plan_key)

            if existing_skill is None:
                self.procedural.add_skill(Skill(
                    name=plan_key,
                    description=f"Successful action plan for: {episode.title}",
                    tags=list(episode.category_probs.keys()) + ["action_plan"],
                    success_rate=0.8,
                    usage_count=1
                ))
            else:
                self.procedural.record_usage(plan_key, success=True)

    def _elevate_patterns(self, episode: Episode) -> None:
        """Elevate repeated patterns to semantic memory."""
        all_eps = self.episodic.get_episodes()
        if len(all_eps) < 3:
            return

        # Pattern 1: High quality consistency
        recent_quality = [e.quality_actual for e in all_eps[-5:] if e.status == "completed"]
        if len(recent_quality) >= 3 and all(q > 0.8 for q in recent_quality[-3:]):
            self.semantic.add_fact(
                key="pattern_high_quality_consistency",
                value="Recent tasks consistently achieve high quality (Q > 0.8)",
                confidence=sum(recent_quality[-3:]) / 3,
                source_episode_id=episode.task_id
            )

        # Pattern 2: Low risk consistency
        recent_risk = [e.risk for e in all_eps[-5:] if e.status == "completed"]
        if len(recent_risk) >= 3 and all(r < 0.3 for r in recent_risk[-3:]):
            self.semantic.add_fact(
                key="pattern_low_risk_consistency",
                value="Recent tasks consistently show low risk (risk < 0.3)",
                confidence=1.0 - sum(recent_risk[-3:]) / 3,
                source_episode_id=episode.task_id
            )

        # Pattern 3: Profitable consistency
        recent_phi = [e.phi_task for e in all_eps[-5:] if e.status == "completed"]
        if len(recent_phi) >= 3 and all(p > 0 for p in recent_phi[-3:]):
            self.semantic.add_fact(
                key="pattern_profitable_consistency",
                value="Recent tasks are consistently profitable",
                confidence=min(1.0, sum(recent_phi[-3:]) / 30),
                source_episode_id=episode.task_id
            )

        # Pattern 4: Client-specific (legacy)
        if episode.client_id:
            client_eps = self.episodic.get_by_client(episode.client_id)
            if len(client_eps) >= 3:
                qualities = [e.quality_actual for e in client_eps[:3]]
                if all(q > 0.8 for q in qualities):
                    key = f"client_{episode.client_id}_high_quality"
                    self.semantic.add_fact(
                        key=key,
                        value="Client consistently requires high quality (Q > 0.8)",
                        confidence=0.7,
                        source_episode_id=episode.task_id
                    )


# CoALA taxonomy aliases
WorkingMemory = OperationalMemory
ProceduralMemory_Legacy = MetaMemory
