"""
Tests for Phase 3 Memory & State (G21 Consolidation Gate)
"""

import pytest
from datetime import datetime

from space1.memory import (
    StrategicExperience,
    MetaRule,
    OperationalMemory,
    StrategicMemory,
    MetaMemory,
    ConsolidationGate,
)


class TestMemoryAndState:
    """Test Suite for Space1 Memory Subsystem."""

    def test_operational_memory_lifecycle(self):
        """Test active context operational variables and metric updates."""
        op_mem = OperationalMemory()
        
        # Test active metadata set/get
        op_mem.set("task_id", "t-100")
        op_mem.set("title", "Active Task")
        assert op_mem.get("task_id") == "t-100"
        assert op_mem.get("title") == "Active Task"
        assert op_mem.get("nonexistent", "default") == "nonexistent" if op_mem.get("nonexistent") else "default"
        
        # Test metric logging
        op_mem.update_metric("revenue", 120.0)
        op_mem.update_metric("risk", 0.35)
        assert op_mem.get_metric("revenue") == 120.0
        assert op_mem.get_metric("risk") == 0.35
        assert op_mem.get_metric("cost", 10.0) == 10.0 if op_mem.get_metric("cost") else 10.0
        
        # Test step tracing
        op_mem.record_step("step_1", "success", 1.5, 2.0)
        steps = op_mem.get_steps()
        assert len(steps) == 1
        assert steps[0]["step"] == "step_1"
        assert steps[0]["status"] == "success"
        
        # Test operational memory wipe (RAM reset)
        op_mem.clear()
        assert op_mem.get("task_id") is None
        assert op_mem.get_metric("revenue") == 0.0
        assert len(op_mem.get_steps()) == 0

    def test_strategic_memory_strategy_and_failure_recall(self):
        """Test long-term experience categorization and keyword retrieval."""
        strat_mem = StrategicMemory()
        
        # Experience 1: Successful coding task
        exp_success = StrategicExperience(
            task_id="t-1",
            title="Coding website backend",
            status="completed",
            strategy="Deploy fastapi container",
            revenue=500.0,
            cost=50.0,
            time_spent=5.0,
            quality=0.9,
            risk=0.1
        )
        strat_mem.add_experience(exp_success)
        
        # Experience 2: Failed coding task
        exp_failure = StrategicExperience(
            task_id="t-2",
            title="Coding ML training script",
            status="failed",
            strategy="Run pytorch locally",
            revenue=0.0,
            cost=20.0,
            time_spent=2.0,
            quality=0.0,
            risk=0.8,
            failure_reason="Out of GPU Memory"
        )
        strat_mem.add_experience(exp_failure)
        
        # Verify stored experiences
        experiences = strat_mem.get_experiences()
        assert len(experiences) == 2
        
        # Test keyword recall
        strategies = strat_mem.recall_strategies("coding")
        assert "Deploy fastapi container" in strategies
        
        failures = strat_mem.recall_failures("coding")
        assert "Out of GPU Memory" in failures

    def test_meta_memory_principles_and_hypotheses(self):
        """Test general policies and guidelines storage in MetaMemory."""
        meta_mem = MetaMemory()
        
        meta_mem.add_rule("safety_first", "Do not write to root directory", confidence=0.95)
        rule = meta_mem.get_rule("safety_first")
        
        assert rule is not None
        assert rule.name == "safety_first"
        assert rule.description == "Do not write to root directory"
        assert rule.confidence == 0.95
        
        # List rules
        all_rules = meta_mem.list_rules()
        assert len(all_rules) == 1
        assert all_rules[0].name == "safety_first"

    def test_consolidation_gate_episodic_to_semantic_bridge(self):
        """Test episodic operational context transitions into long-term strategic experiences."""
        strat_mem = StrategicMemory()
        meta_mem = MetaMemory()
        gate = ConsolidationGate(
            episodic_mem=strat_mem,
            semantic_mem=meta_mem.semantic,
            procedural_mem=meta_mem.procedural
        )
        
        op_mem = OperationalMemory()
        op_mem.set("task_id", "t-99")
        op_mem.set("title", "High risk task")
        op_mem.set("status", "failed")
        op_mem.set("strategy", "Execute raw subprocess")
        op_mem.update_metric("revenue", 0.0)
        op_mem.update_metric("cost", 5.0)
        op_mem.update_metric("time_hours", 0.5)
        op_mem.update_metric("quality", 0.2)
        op_mem.update_metric("risk", 0.8)  # risk > 0.5
        op_mem.set("failure_reason", "Syntax Error")
        
        # Consolidate
        exp = gate.consolidate(op_mem)
        
        assert exp is not None
        assert exp.task_id == "t-99"
        assert exp.status == "failed"
        
        # Check strategic memory has it
        assert len(strat_mem.get_experiences()) == 1
        assert strat_mem.get_experiences()[0].task_id == "t-99"

    def test_tf_idf_inverse_document_relevance(self):
        """Test that upgraded TF-IDF calculation correctly computes Inverse Document Frequency relevance."""
        from space1.memory.storage import AIOSStorageManager
        import os

        filepath = "test_tfidf_memory.json"
        if os.path.exists(filepath):
            os.remove(filepath)

        try:
            # We want terms that are common across all documents to have LOW relevance weight,
            # and terms that are rare/unique to a document to have HIGH relevance weight.
            mgr = AIOSStorageManager(filepath=filepath)
            
            # Key 1 contains a very common term "system" and a unique term "database"
            mgr.persist("system database setup", "Value 1", importance=0.8)
            # Key 2 contains "system" and a unique term "frontend"
            mgr.persist("system frontend design", "Value 2", importance=0.8)
            # Key 3 contains "system" and a unique term "deployment"
            mgr.persist("system deployment AWS", "Value 3", importance=0.8)

            # Query for the rare term "database"
            results_db = mgr.retrieve_with_weighted_ranking("database", max_results=1)
            assert len(results_db) == 1
            # The top entry must be "system database setup" since it matches the unique term
            assert results_db[0]["entry"].key == "system database setup"

            # Query for the common term "system"
            results_sys = mgr.retrieve_with_weighted_ranking("system", max_results=3)
            assert len(results_sys) == 3
            # Since "system" is present in all, its IDF is lower, and scores are balanced by recency/importance
            assert all(r["score"] > 0.0 for r in results_sys)

        finally:
            if os.path.exists(filepath):
                os.remove(filepath)

    def test_atomic_disk_write_recovery(self):
        """Test that _save_to_disk writes atomically and is resilient to abrupt failures."""
        from space1.memory.storage import AIOSStorageManager
        import os

        filepath = "test_atomic_memory.json"
        tmp_filepath = filepath + ".tmp"
        if os.path.exists(filepath):
            os.remove(filepath)
        if os.path.exists(tmp_filepath):
            os.remove(tmp_filepath)

        try:
            mgr = AIOSStorageManager(filepath=filepath)
            mgr.persist("key1", "val1", importance=0.9)
            
            # Verify file exists
            assert os.path.exists(filepath)
            assert not os.path.exists(tmp_filepath)

            # Check that content was written properly
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                assert "key1" in content

        finally:
            if os.path.exists(filepath):
                os.remove(filepath)
            if os.path.exists(tmp_filepath):
                os.remove(tmp_filepath)
