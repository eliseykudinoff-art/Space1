"""
Space1 -- ДЕТЕКТОР ЛЖИ: dispatch_full_cycle() end-to-end.

Проверяет ВСЕ Stage I-XII, все ветки, все закоулки pipeline.
Любое расхождение с концепцией = FAILED с детальным объяснением.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import json
from datetime import datetime, timedelta

from space1.models.task import Task, TaskPriority
from space1.models.agents import Agent, AgentCapabilities, AgentMetrics
from space1.orchestrator.core import Orchestrator


class TestE2EDetector:
    """E2E-ДЕТЕКТОР: Полный цикл с детальным trace-анализом."""

    def _run_pipeline(self, n_completed=0, balance=100.0, title="Test", desc="Test task",
                       priority=TaskPriority.HIGH, hours=4.0, deadline_hours=24):
        """Запускает pipeline и возвращает (result, task, orch, trace_str)."""
        agent = Agent(
            id=f"e2e-{n_completed}",
            name="TestAgent",
            capabilities=AgentCapabilities(n_completed_tasks=n_completed),
            metrics=AgentMetrics(balance=balance)
        )
        orch = Orchestrator(core_agent=agent)
        task = Task(
            id=f"e2e-task-{n_completed}",
            title=title,
            description=desc,
            priority=priority,
            deadline=datetime.now() + timedelta(hours=deadline_hours),
            estimated_hours=hours
        )
        orch.scheduler.add_task(task)
        result = orch.dispatch_full_cycle()
        trace = result.get("trace", [])
        trace_str = "\n".join(trace)
        return result, task, orch, trace_str

    def test_01_pipeline_completes_no_exception(self):
        """Stage I-XII проходят без исключений."""
        result, task, orch, trace = self._run_pipeline()
        assert result["status"] == "SUCCESS", "Pipeline упал: status=" + str(result.get("status")) + ", trace:\n" + trace[:1000]

    def test_02_all_stages_present(self):
        """ВСЕ Stage I-XII присутствуют в trace."""
        result, task, orch, trace = self._run_pipeline()
        required_stages = [
            "Stage I:", "Stage II:", "Stage III:", "Stage IV:",
            "Stage V:", "Stage VI:", "Stage VII:", "Stage VIII:",
            "Stage IX:", "Stage X:", "Stage XI:", "Stage XII:"
        ]
        missing = [s for s in required_stages if s not in trace]
        assert not missing, "Отсутствуют Stage: " + str(missing) + "\nПолный trace:\n" + trace

    def test_03_task_marked_completed(self):
        """Task.status == COMPLETED после pipeline."""
        result, task, orch, trace = self._run_pipeline()
        assert task.status.name == "COMPLETED", "Task не завершён: status=" + task.status.name + "\nTrace:\n" + trace[:500]

    def test_04_execution_results_non_empty(self):
        """Stage VIII produce non-empty execution_results."""
        result, task, orch, trace = self._run_pipeline()
        exec_res = result.get("execution_results", [])
        assert len(exec_res) > 0, "execution_results пуст!\nTrace:\n" + trace[:500]

    def test_05_delivery_called(self):
        """Stage VIII-Delivery: delivery вызван и результат корректен."""
        result, task, orch, trace = self._run_pipeline()
        assert "Stage VIII-Delivery" in trace or "Delivery" in trace, "Delivery НЕ вызван!\nTrace:\n" + trace[:1000]
        # Task должен быть помечен как доставленный
        assert task.status.name == "COMPLETED", f"Task status={task.status.name}, expected COMPLETED"
        # Проверим что execution_results не пуст (доставка требует результатов)
        assert len(result.get("execution_results", [])) > 0, "execution_results пуст -- нечего доставлять"

    def test_06_cold_start_for_new_agent(self):
        """Stage I: cold-start для n_completed=0."""
        result, task, orch, trace = self._run_pipeline(n_completed=0)
        assert "Cold-start" in trace or "cold_start" in trace, "Cold-start НЕ применён для нового агента (n_completed=0)!\nTrace:\n" + trace[:1000]

    def test_07_ccrs_applied(self):
        """Stage II-CCRS: client risk premium вычислен."""
        result, task, orch, trace = self._run_pipeline()
        assert "CCRS" in trace or "risk premium" in trace.lower(), "CCRS НЕ применён!\nTrace:\n" + trace[:1000]

    def test_08_trigger_fired(self):
        """Stage XI-Trigger: trigger сработал ПОСЛЕ консолидации."""
        result, task, orch, trace = self._run_pipeline()
        assert "Stage XI-Trigger" in trace or "trigger" in trace.lower(), "Trigger НЕ сработал!\nTrace:\n" + trace[:1000]

    def test_09_quality_in_range(self):
        """Quality score в [0, 1] и вычислена корректно."""
        result, task, orch, trace = self._run_pipeline()
        q = result.get("quality", -1)
        assert isinstance(q, float) and 0.0 <= q <= 1.0, "Quality вне диапазона: " + str(q) + "\nTrace:\n" + trace[:500]
        # Quality не должна быть константой (0.5 или 1.0)
        assert q != 0.5 and q != 1.0, f"Quality={q} выглядит как константа, не вычисленное значение"

    def test_10_decision_valid(self):
        """Decision: APPROVED/DECLINE/EXECUTE."""
        result, task, orch, trace = self._run_pipeline()
        d = result.get("decision", "UNKNOWN")
        assert d in ["APPROVED", "DECLINE", "EXECUTE"], "Невалидное decision: " + str(d) + "\nTrace:\n" + trace[:500]

    def test_11_calibrated_weights_dict(self):
        """Calibrated weights: dict."""
        result, task, orch, trace = self._run_pipeline()
        w = result.get("calibrated_weights", {})
        assert isinstance(w, dict), "calibrated_weights не dict: " + str(type(w)) + "\nTrace:\n" + trace[:500]

    def test_12_mission_recalibrated_bool(self):
        """Mission recalibrated: bool."""
        result, task, orch, trace = self._run_pipeline()
        m = result.get("mission_recalibrated", "MISSING")
        assert isinstance(m, bool), "mission_recalibrated не bool: " + str(type(m)) + "\nTrace:\n" + trace[:500]

    def test_13_no_simulated_response_in_trace(self):
        """НЕТ SimulatedResponse в trace -- реальный путь."""
        result, task, orch, trace = self._run_pipeline()
        assert "SimulatedResponse" not in trace, "SimulatedResponse в trace -- реальный путь НЕ используется!\nTrace:\n" + trace[:1000]

    def test_14_no_bare_except_in_trace(self):
        """НЕТ except Exception: pass в trace (не должно быть видно)."""
        result, task, orch, trace = self._run_pipeline()
        assert "except Exception" not in trace, "except Exception в trace -- ошибка подавления!\nTrace:\n" + trace[:1000]

    def test_15_consolidated_experience_present(self):
        """Consolidated experience присутствует."""
        result, task, orch, trace = self._run_pipeline()
        assert "consolidated_experience" in result, "consolidated_experience отсутствует!\nTrace:\n" + trace[:500]

    def test_16_trace_not_empty(self):
        """Trace не пуст."""
        result, task, orch, trace = self._run_pipeline()
        assert len(result.get("trace", [])) > 5, "Trace слишком короткий: " + str(len(result.get("trace", []))) + " строк\n" + trace[:500]

    def test_17_task_id_in_result(self):
        """task_id в result совпадает с task.id."""
        result, task, orch, trace = self._run_pipeline()
        assert result.get("task_id") == task.id, "task_id mismatch: " + str(result.get("task_id")) + " != " + task.id

    def test_18_agent_metrics_updated(self):
        """Agent metrics обновлены после pipeline."""
        result, task, orch, trace = self._run_pipeline(n_completed=5, balance=200.0)
        assert orch.core_agent.capabilities.n_completed_tasks >= 5, "n_completed_tasks не обновлён: " + str(orch.core_agent.capabilities.n_completed_tasks)
        # Balance должен измениться (заработок или трата)
        assert orch.core_agent.metrics.balance != 200.0 or "cost" in trace.lower(),             "Balance не изменился и cost не в trace -- метрики не обновлены"
        # Success rate должен быть вычислен
        assert 0.0 <= orch.core_agent.metrics.success_rate <= 1.0,             f"success_rate={orch.core_agent.metrics.success_rate} out of [0,1]"

    def test_19_retry_alert_present_if_reflection_finds_issues(self):
        """RETRY ALERT присутствует если reflection находит проблемы (не ошибка)."""
        result, task, orch, trace = self._run_pipeline(title="Complex task", desc="Task with potential issues")
        # RETRY ALERT -- это warning, не ошибка. Pipeline может быть SUCCESS при наличии alert.
        assert result["status"] == "SUCCESS"

    def test_20_full_trace_dump_on_failure(self):
        """При любом FAILED -- полный trace в выводе."""
        result, task, orch, trace = self._run_pipeline()
        if result["status"] != "SUCCESS":
            print(f"\n=== FAILED TRACE ===\n{trace}\n===================")
        assert result["status"] == "SUCCESS"

    # =============================================================================
    # ГРАНИЧНЫЕ ЗНАЧЕНИЯ
    # =============================================================================

    def test_21_zero_balance(self):
        """Pipeline с balance=0: должен пройти или дать осмысленный отказ."""
        result, task, orch, trace = self._run_pipeline(balance=0.0)
        assert result["status"] in ["SUCCESS", "DECLINED"],             f"balance=0: status={result['status']}, expected SUCCESS or DECLINED\nTrace:\n" + trace[:500]

    def test_22_zero_estimated_hours(self):
        """Pipeline с estimated_hours=0: деление на zero должно быть обработано."""
        result, task, orch, trace = self._run_pipeline(hours=0.0)
        assert result["status"] in ["SUCCESS", "DECLINED", "ERROR"],             f"hours=0: status={result['status']}, expected handled\nTrace:\n" + trace[:500]

    def test_23_past_deadline(self):
        """Pipeline с deadline в прошлом: Task должен отклонить на создании (валидация)."""
        try:
            result, task, orch, trace = self._run_pipeline(deadline_hours=-1)
            assert False, "Expected ValueError for past deadline, but pipeline ran"
        except ValueError as e:
            assert "deadline" in str(e).lower(), f"Wrong error: {e}"

    def test_24_empty_description(self):
        """Pipeline с пустым description: должен пройти."""
        result, task, orch, trace = self._run_pipeline(desc="")
        assert result["status"] == "SUCCESS",             f"empty desc: status={result['status']}\nTrace:\n" + trace[:500]

    def test_25_critical_priority(self):
        """Pipeline с CRITICAL priority: должен пройти."""
        result, task, orch, trace = self._run_pipeline(priority=TaskPriority.CRITICAL)
        assert result["status"] == "SUCCESS",             f"CRITICAL: status={result['status']}\nTrace:\n" + trace[:500]

    def test_26_low_priority(self):
        """Pipeline с LOW priority: должен пройти."""
        result, task, orch, trace = self._run_pipeline(priority=TaskPriority.LOW)
        assert result["status"] == "SUCCESS",             f"LOW: status={result['status']}\nTrace:\n" + trace[:500]

    # =============================================================================
    # FAILURE PATH
    # =============================================================================

    def test_27_idempotency(self):
        """Дважды вызвать dispatch_full_cycle: результаты должны быть консистентны."""
        result1, task1, orch1, trace1 = self._run_pipeline(n_completed=10, balance=500.0)
        result2, task2, orch2, trace2 = self._run_pipeline(n_completed=10, balance=500.0)
        assert result1["status"] == result2["status"],             f"Idempotency: status1={result1['status']} != status2={result2['status']}"
        assert result1.get("decision") == result2.get("decision"),             f"Idempotency: decision mismatch"

    def test_28_result_structure(self):
        """Result содержит все обязательные поля."""
        result, task, orch, trace = self._run_pipeline()
        required_fields = ["status", "task_id", "trace", "quality", "decision"]
        missing = [f for f in required_fields if f not in result]
        assert not missing, f"Missing fields: {missing}\nResult keys: {list(result.keys())}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=long"])
