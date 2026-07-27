"""Тесты [MED-07]: ConsolidationGate — реальный перенос памяти."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from datetime import datetime

from space1.memory.core import (
    ConsolidationGate, EpisodicMemory, SemanticMemory, ProceduralMemory,
    OperationalMemory, Episode, Skill
)


def make_op_mem(**kwargs):
    """Создать OperationalMemory с тестовыми данными."""
    op = OperationalMemory()
    op.set("task_id", kwargs.get("task_id", "task-001"))
    op.set("title", kwargs.get("title", "Test Task"))
    op.set("client_id", kwargs.get("client_id", "client-001"))
    op.set("status", kwargs.get("status", "completed"))
    op.set("category_probs", kwargs.get("category_probs", {"code": 0.8}))
    op.set("action_plan", kwargs.get("action_plan", ["step1", "step2"]))
    op.update_metric("quality", kwargs.get("quality", 0.9))
    op.update_metric("risk", kwargs.get("risk", 0.2))
    op.update_metric("revenue", kwargs.get("revenue", 200.0))
    op.update_metric("cost", kwargs.get("cost", 50.0))
    op.update_metric("time_hours", kwargs.get("time_hours", 2.0))
    return op


class TestMed07Consolidation:
    """ConsolidationGate должен реально переносить память."""

    def test_semantic_facts_extracted(self):
        """После consolidate в semantic memory должны появиться факты."""
        episodic = EpisodicMemory()
        semantic = SemanticMemory()
        procedural = ProceduralMemory()
        gate = ConsolidationGate(episodic, semantic, procedural)

        op = make_op_mem(task_id="task-001", quality=0.9, risk=0.2, revenue=200.0, cost=50.0)
        episode = gate.consolidate(op)

        assert episode is not None
        # Должны быть факты о категории, риске, качестве, прибыльности
        facts = semantic._facts
        assert any("category_preference" in k for k in facts), "Category preference fact missing"
        assert any("risk_profile" in k for k in facts), "Risk profile fact missing"
        assert any("quality_outcome" in k for k in facts), "Quality outcome fact missing"
        assert any("profitability" in k for k in facts), "Profitability fact missing"

    def test_procedural_skill_from_action_plan(self):
        """Успешный action_plan должен стать procedural skill."""
        episodic = EpisodicMemory()
        semantic = SemanticMemory()
        procedural = ProceduralMemory()
        gate = ConsolidationGate(episodic, semantic, procedural)

        op = make_op_mem(
            task_id="task-002",
            title="Build API",
            status="completed",
            action_plan=["design", "implement", "test"],
            category_probs={"api": 0.9}
        )
        gate.consolidate(op)

        # Должен появиться skill от action_plan
        skills = procedural._skills
        assert any("action_plan" in k for k in skills), "Action plan skill missing"

    def test_failed_task_no_action_plan_skill(self):
        """Неуспешный task НЕ должен создавать action_plan skill."""
        episodic = EpisodicMemory()
        semantic = SemanticMemory()
        procedural = ProceduralMemory()
        gate = ConsolidationGate(episodic, semantic, procedural)

        op = make_op_mem(
            task_id="task-003",
            title="Failed Task",
            status="failed",
            action_plan=["step1", "step2"]
        )
        gate.consolidate(op)

        skills = procedural._skills
        assert not any("action_plan" in k for k in skills), "Failed task should not create action_plan skill"

    def test_pattern_elevation_high_quality(self):
        """3+ эпизода с высоким качеством → elevated pattern в semantic."""
        episodic = EpisodicMemory()
        semantic = SemanticMemory()
        procedural = ProceduralMemory()
        gate = ConsolidationGate(episodic, semantic, procedural)

        for i in range(3):
            op = make_op_mem(
                task_id=f"task-{i}",
                quality=0.9,
                risk=0.2,
                status="completed"
            )
            gate.consolidate(op)

        facts = semantic._facts
        assert "pattern_high_quality_consistency" in facts, "High quality pattern not elevated"

    def test_pattern_elevation_low_risk(self):
        """3+ эпизода с низким риском → elevated pattern в semantic."""
        episodic = EpisodicMemory()
        semantic = SemanticMemory()
        procedural = ProceduralMemory()
        gate = ConsolidationGate(episodic, semantic, procedural)

        for i in range(3):
            op = make_op_mem(
                task_id=f"task-{i}",
                quality=0.7,
                risk=0.1,
                status="completed"
            )
            gate.consolidate(op)

        facts = semantic._facts
        assert "pattern_low_risk_consistency" in facts, "Low risk pattern not elevated"

    def test_episodic_memory_cleared_after_consolidate(self):
        """Operational memory должен очищаться после consolidate."""
        episodic = EpisodicMemory()
        semantic = SemanticMemory()
        procedural = ProceduralMemory()
        gate = ConsolidationGate(episodic, semantic, procedural)

        op = make_op_mem(task_id="task-clear")
        op.set("test_key", "test_value")
        gate.consolidate(op)

        assert op.get("test_key") is None, "Operational memory should be cleared"
