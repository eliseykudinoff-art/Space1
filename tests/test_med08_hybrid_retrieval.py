"""Тесты [MED-08]: EpisodicMemory hybrid retrieval (BM25 + vector)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from datetime import datetime, timedelta

from space1.memory.core import EpisodicMemory, Episode


def make_episode(title, strategy="", status="completed", client_id=None,
                 quality=0.7, risk=0.2, phi=100.0, categories=None):
    return Episode(
        task_id=f"task-{hash(title) % 10000}",
        title=title,
        capability_vector=tuple([0.5] * 17),
        category_probs=categories or {"code": 0.8},
        action_plan=["step1", "step2"],
        attempt_history=[],
        quality_actual=quality,
        phi_task=phi,
        reflection_triggers=[],
        client_id=client_id,
        revenue=phi + 50,
        cost=50.0,
        time_spent=2.0,
        risk=risk,
        status=status,
        failure_reason=None,
        strategy=strategy,
    )


class TestMed08HybridRetrieval:
    """EpisodicMemory должен поддерживать hybrid retrieval (BM25 + vector)."""

    def test_hybrid_retrieve_finds_relevant(self):
        """hybrid_retrieve должен находить релевантные эпизоды по запросу."""
        mem = EpisodicMemory()

        ep1 = make_episode("Build REST API with Python Flask", categories={"api": 0.9, "python": 0.8})
        ep2 = make_episode("Debug JavaScript frontend bug", categories={"frontend": 0.9, "js": 0.8})
        ep3 = make_episode("Deploy Python microservice to AWS", categories={"python": 0.9, "devops": 0.7})

        mem.add_episode(ep1)
        mem.add_episode(ep2)
        mem.add_episode(ep3)

        results = mem.hybrid_retrieve("python api", k=2)

        # Должен найти ep1 и ep3 (оба про python)
        titles = [ep.title for ep in results]
        assert len(results) == 2
        assert "Python" in " ".join(titles) or "python" in " ".join(titles).lower()

    def test_bm25_score_ranks_higher_for_exact_match(self):
        """Точное совпадение ключевых слов должно давать более высокий BM25 score."""
        mem = EpisodicMemory()

        ep1 = make_episode("Python machine learning model training")
        ep2 = make_episode("Java enterprise application development")

        mem.add_episode(ep1)
        mem.add_episode(ep2)

        # Принудительно строим индекс
        mem._build_tfidf_index()

        score1 = mem._bm25_score("python machine learning", 0)
        score2 = mem._bm25_score("python machine learning", 1)

        assert score1 > score2, "Exact match should have higher BM25 score"

    def test_vector_similarity_ranks_semantic_match(self):
        """Vector similarity должен находить семантически близкие документы."""
        mem = EpisodicMemory()

        ep1 = make_episode("Python API development with Flask")
        ep2 = make_episode("JavaScript frontend framework React")

        mem.add_episode(ep1)
        mem.add_episode(ep2)

        mem._build_tfidf_index()

        sim1 = mem._vector_similarity("python flask backend", 0)
        sim2 = mem._vector_similarity("python flask backend", 1)

        assert sim1 > sim2, "Semantic match should have higher vector similarity"

    def test_recall_strategies_uses_hybrid(self):
        """recall_strategies должен использовать hybrid retrieval."""
        mem = EpisodicMemory()

        ep1 = make_episode("Build authentication API", strategy="jwt_token_auth", status="completed")
        ep2 = make_episode("Fix CSS layout bug", strategy="flexbox_grid", status="completed")
        ep3 = make_episode("Implement OAuth2 flow", strategy="oauth2_pkce", status="completed")

        mem.add_episode(ep1)
        mem.add_episode(ep2)
        mem.add_episode(ep3)

        strategies = mem.recall_strategies("authentication")

        # Должен найти jwt_token_auth и oauth2_pkce (оба про auth)
        assert len(strategies) >= 1
        assert any("auth" in s.lower() for s in strategies)

    def test_empty_query_falls_back_to_priority(self):
        """Пустой query должен использовать priority-only retrieval."""
        mem = EpisodicMemory()

        ep1 = make_episode("Old task", quality=0.5)
        ep2 = make_episode("Recent task", quality=0.9)

        # Устанавливаем timestamp вручную
        ep1.timestamp = datetime.now() - timedelta(days=10)
        ep2.timestamp = datetime.now()

        mem.add_episode(ep1)
        mem.add_episode(ep2)

        results = mem.retrieve("", k=2)

        # Recent task должна быть первой
        assert results[0].title == "Recent task"

    def test_tfidf_index_rebuilt_on_add(self):
        """Индекс должен перестраиваться при добавлении нового эпизода."""
        mem = EpisodicMemory()

        ep1 = make_episode("First task")
        mem.add_episode(ep1)

        mem._build_tfidf_index()
        assert not mem._tfidf_dirty

        ep2 = make_episode("Second task")
        mem.add_episode(ep2)

        assert mem._tfidf_dirty, "Index should be marked dirty after add"
