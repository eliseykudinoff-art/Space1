"""
AIOS Storage Manager Kernel Module with JSON Persistence and Vector TF-IDF Semantic Retrieval.

Reference: 04_ARCHITECTURE.md (Part IV / Part IV.4).
Manages persisted storage and memory indexing (Recency, Importance, Relevance).
"""

import os
import json
import math
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Set

logger = logging.getLogger("aios_storage")


class MemoryEntry:
    """Represents an item stored in Memory with metadata for semantic retrieval."""
    
    SCHEMA_VERSION = "1.0"  # BUG-037 FIX: Schema versioning for migration
    
    def __init__(self, key: str, value: Any, importance: float = 0.5, timestamp: Optional[datetime] = None):
        self.key = key
        self.value = value
        self.importance = importance  # [0.0, 1.0]
        self.timestamp = timestamp or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize memory entry to dictionary with schema version."""
        return {
            "key": self.key,
            "value": self.value,
            "importance": self.importance,
            "timestamp": self.timestamp.isoformat(),
            "_schema_version": self.SCHEMA_VERSION  # BUG-037 FIX: Include schema version
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        """Deserialize memory entry from dictionary with migration support."""
        # BUG-037 FIX: Handle schema migration
        schema_version = data.get("_schema_version", "0.0")
        
        # Future: Add migration logic here when schema changes
        # if schema_version != cls.SCHEMA_VERSION:
        #     data = cls._migrate(data, schema_version, cls.SCHEMA_VERSION)
        
        return cls(
            key=data["key"],
            value=data["value"],
            importance=data["importance"],
            timestamp=datetime.fromisoformat(data["timestamp"])
        )


class AIOSStorageManager:
    """
    AIOSStorageManager.
    Handles semantic and episodic memory persistence and performs weighted retrieval score indexing.
    Formula:
        Score = w1 * Recency + w2 * Importance + w3 * Relevance
    """
    
    # BUG-037 FIX: Storage schema version
    STORAGE_SCHEMA_VERSION = "1.0"
    
    def __init__(self, filepath: str = "storage_memory.json", w1: float = 0.3, w2: float = 0.4, w3: float = 0.3):
        self.filepath = filepath
        self.w1 = w1
        self.w2 = w2
        self.w3 = w3
        self._store: List[MemoryEntry] = []
        self._load_from_disk()
        
    def _load_from_disk(self) -> None:
        """Load persisted memories from JSON file if it exists."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                    # BUG-037 FIX: Check storage schema version
                    if isinstance(data, dict):
                        storage_version = data.get("_storage_version", "0.0")
                        if storage_version != self.STORAGE_SCHEMA_VERSION:
                            logger.warning(
                                f"Storage schema version mismatch: {storage_version} != {self.STORAGE_SCHEMA_VERSION}. "
                                "Migration may be needed."
                            )
                        # Load entries from "entries" field
                        entries = data.get("entries", data.get("memories", []))
                        self._store = [MemoryEntry.from_dict(item) for item in entries]
                    else:
                        # Legacy format: list of entries
                        self._store = [MemoryEntry.from_dict(item) for item in data]
                        
            except json.JSONDecodeError as e:
                # BUG-005 FIX: Log JSON parse errors instead of silently ignoring
                logger.warning(f"Failed to parse storage file '{self.filepath}': {e}. Starting with empty store.")
                self._store = []
            except OSError as e:
                logger.warning(f"Failed to read storage file '{self.filepath}': {e}. Starting with empty store.")
                self._store = []
            except Exception as e:
                logger.error(f"Unexpected error loading storage '{self.filepath}': {type(e).__name__}: {e}")
                self._store = []
            else:
                # BUG-039 FIX: Validate loaded state
                self._validate_state()
                logger.info(f"Loaded {len(self._store)} memory entries from storage (schema v{self.STORAGE_SCHEMA_VERSION})")
        else:
            logger.info(f"Storage file '{self.filepath}' not found. Starting with empty store.")
    
    def _validate_state(self) -> None:
        """
        BUG-039 FIX: Validate loaded state for invariants.
        
        Checks:
        - All entries have required fields
        - Timestamps are valid
        - Importance values are in [0, 1]
        - Keys are non-empty strings
        """
        invalid_entries = []
        
        for i, entry in enumerate(self._store):
            errors = []
            
            # Check key
            if not isinstance(entry.key, str) or not entry.key.strip():
                errors.append(f"Invalid key type or empty: {type(entry.key).__name__}")
            
            # Check timestamp
            if not isinstance(entry.timestamp, datetime):
                errors.append(f"Invalid timestamp type: {type(entry.timestamp).__name__}")
            elif entry.timestamp > datetime.now():
                errors.append(f"Future timestamp: {entry.timestamp}")
            
            # Check importance
            if not isinstance(entry.importance, (int, float)):
                errors.append(f"Invalid importance type: {type(entry.importance).__name__}")
            elif not (0.0 <= entry.importance <= 1.0):
                errors.append(f"Importance out of range: {entry.importance}")
            
            if errors:
                invalid_entries.append((i, entry.key, errors))
                logger.warning(f"Invalid memory entry at index {i}: {', '.join(errors)}")
        
        if invalid_entries:
            # Remove invalid entries
            indices_to_remove = set(i for i, _, _ in invalid_entries)
            self._store = [e for i, e in enumerate(self._store) if i not in indices_to_remove]
            logger.warning(f"Removed {len(invalid_entries)} invalid entries during validation")
                
    def _save_to_disk(self) -> None:
        """Serialize and persist memories atomically to JSON file."""
        temp_filepath = self.filepath + ".tmp"
        try:
            with open(temp_filepath, "w", encoding="utf-8") as f:
                # BUG-037 FIX: Include storage schema version
                data = {
                    "_storage_version": self.STORAGE_SCHEMA_VERSION,
                    "entries": [item.to_dict() for item in self._store]
                }
                json.dump(data, f, indent=2)
            # Atomic rename/replace to prevent corruption on abrupt exit
            os.replace(temp_filepath, self.filepath)
        except OSError as e:
            logger.error(f"Failed to write storage file '{self.filepath}': {e}")
            if os.path.exists(temp_filepath):
                try:
                    os.remove(temp_filepath)
                except OSError as cleanup_error:
                    logger.warning(f"Failed to cleanup temp file after write error: {cleanup_error}")
        except Exception as e:
            logger.error(f"Unexpected error saving storage: {type(e).__name__}: {e}")

    def persist(self, key: str, value: Any, importance: float = 0.5) -> None:
        """Store a value in persisted memory and sync to disk."""
        self._store.append(MemoryEntry(key, value, importance))
        self._save_to_disk()
        
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenizer for TF-IDF calculations."""
        # Clean special chars, lowercase, split
        cleaned = "".join(c if c.isalnum() else " " for c in text.lower())
        return [w for w in cleaned.split() if len(w) > 2]

    def _compute_tf(self, tokens: List[str]) -> Dict[str, float]:
        """Calculate Term Frequency (TF) weights."""
        if not tokens:
            return {}
        counts = {}
        for token in tokens:
            counts[token] = counts.get(token, 0.0) + 1.0
        # Normalise by max frequency
        max_freq = max(counts.values())
        return {k: v / max_freq for k, v in counts.items()}

    def _compute_idf(self) -> Dict[str, float]:
        """Calculate Inverse Document Frequency (IDF) weights across all stored keys."""
        idf = {}
        N = len(self._store)
        if N == 0:
            return {}
        
        # Calculate document frequency (DF) for each term across all entries
        df = {}
        for entry in self._store:
            tokens = set(self._tokenize(entry.key))
            for term in tokens:
                df[term] = df.get(term, 0) + 1
                
        # Compute IDF for each term: idf_t = ln(1.0 + N / (1.0 + df_t))
        for term, count in df.items():
            idf[term] = math.log(1.0 + (N / (1.0 + count)))
            
        return idf

    def _cosine_similarity_tfidf(self, tf1: Dict[str, float], tf2: Dict[str, float], idf: Dict[str, float]) -> float:
        """Calculate cosine similarity of TF-IDF vectors."""
        if not tf1 or not tf2:
            return 0.0
        # Dot product
        common_words = set(tf1.keys()) & set(tf2.keys())
        if not common_words:
            return 0.0
            
        dot_product = sum((tf1[w] * idf.get(w, 1.0)) * (tf2[w] * idf.get(w, 1.0)) for w in common_words)
        
        # Magnitude
        norm1 = math.sqrt(sum((v * idf.get(w, 1.0))**2 for w, v in tf1.items()))
        norm2 = math.sqrt(sum((v * idf.get(w, 1.0))**2 for w, v in tf2.items()))
        
        if norm1 * norm2 == 0.0:
            return 0.0
        return dot_product / (norm1 * norm2)

    def retrieve_with_weighted_ranking(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve memory entries ranked by weighted score using TF-IDF and Reciprocal Rank Fusion (RRF):
            Score = (w1 * Recency + w2 * Importance + w3 * Relevance) * RRF_Weight
        """
        now = datetime.now()
        N = len(self._store)
        if N == 0:
            return []
            
        query_tokens = self._tokenize(query)
        query_tf = self._compute_tf(query_tokens)
        
        # Calculate IDF across the store
        idf = self._compute_idf()
        
        # 1. Compute raw values for all items
        raw_items = []
        for idx, entry in enumerate(self._store):
            delta_hours = (now - entry.timestamp).total_seconds() / 3600.0
            recency = math.exp(-0.1 * delta_hours)
            importance = entry.importance
            entry_tokens = self._tokenize(entry.key)
            entry_tf = self._compute_tf(entry_tokens)
            relevance = self._cosine_similarity_tfidf(query_tf, entry_tf, idf)
            
            raw_items.append({
                "entry": entry,
                "recency": recency,
                "importance": importance,
                "relevance": relevance,
                "idx": idx
            })
            
        # 2. Compute rank mappings for each criterion
        # Recency rank
        raw_items.sort(key=lambda x: x["recency"], reverse=True)
        recency_ranks = {item["idx"]: rank + 1 for rank, item in enumerate(raw_items)}
        
        # Importance rank
        raw_items.sort(key=lambda x: x["importance"], reverse=True)
        importance_ranks = {item["idx"]: rank + 1 for rank, item in enumerate(raw_items)}
        
        # Relevance rank
        raw_items.sort(key=lambda x: x["relevance"], reverse=True)
        relevance_ranks = {item["idx"]: rank + 1 for rank, item in enumerate(raw_items)}
        
        # 3. Calculate blended scores using Reciprocal Rank Fusion (k_0 = 60.0)
        k_0 = 60.0
        final_results = []
        for item in raw_items:
            idx = item["idx"]
            r_rec = recency_ranks[idx]
            r_imp = importance_ranks[idx]
            r_rel = relevance_ranks[idx]
            
            # Reciprocal Rank Fusion formula
            rrf = (1.0 / (k_0 + r_rec)) + (1.0 / (k_0 + r_imp)) + (1.0 / (k_0 + r_rel))
            
            raw_score = self.w1 * item["recency"] + self.w2 * item["importance"] + self.w3 * item["relevance"]
            score = raw_score * (rrf * 20.0)  # scale factor to preserve score range
            
            final_results.append({
                "entry": item["entry"],
                "score": score
            })
            
        final_results.sort(key=lambda x: x["score"], reverse=True)
        return final_results[:max_results]
        
    def clear(self) -> None:
        """Clear memory store and delete file."""
        self._store.clear()
        if os.path.exists(self.filepath):
            try:
                os.remove(self.filepath)
            except OSError as e:
                # BUG-005 FIX: Log file deletion errors instead of silently ignoring
                logger.warning(f"Failed to delete storage file '{self.filepath}': {e}")
