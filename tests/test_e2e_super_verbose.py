"""
Space1 — SUPER VERBOSE E2E TESTS

Полноценные End-to-End тесты с максимальным логированием.
Каждый тест:
1. Принимает входные данные
2. Подробно описывает каждый шаг вычислений
3. Сопровождает числовые значения текстовыми описаниями
4. Сохраняет все принты в файл для анализа

Автосохранение: результаты сохраняются в reports/e2e_test_logs/
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

# =============================================================================
# LOGGING AND FILE OUTPUT SYSTEM
# =============================================================================

class E2ETestLogger:
    """
    Централизованный логгер для E2E тестов.
    Автоматически сохраняет все выводы в файл.
    """
    _instance = None
    _logs: List[str] = []
    _test_name: str = ""
    _output_dir: Path = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def start_test(cls, test_name: str, output_dir: str = None):
        """Начать новый тест, очистить логи."""
        cls._test_name = test_name
        cls._logs = []
        cls._output_dir = Path(output_dir) if output_dir else Path(__file__).parent.parent / "reports" / "e2e_test_logs"
        cls._output_dir.mkdir(parents=True, exist_ok=True)
        cls.log(f"{'='*80}")
        cls.log(f"E2E TEST STARTED: {test_name}")
        cls.log(f"Timestamp: {datetime.now().isoformat()}")
        cls.log(f"{'='*80}")
    
    @classmethod
    def log(cls, message: str, level: str = "INFO"):
        """Добавить сообщение в лог и напечатать."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        formatted = f"[{timestamp}] [{level:8}] {message}"
        cls._logs.append(formatted)
        print(formatted)
    
    @classmethod
    def log_value(cls, name: str, value: Any, description: str = "", unit: str = ""):
        """Логировать значение с описанием."""
        desc_part = f" — {description}" if description else ""
        unit_part = f" [{unit}]" if unit else ""
        cls.log(f"  {name}: {value}{unit_part}{desc_part}")
    
    @classmethod
    def log_dict(cls, data: Dict, title: str = "", indent: int = 2):
        """Логировать словарь в читаемом формате."""
        if title:
            cls.log(title)
        for key, value in data.items():
            if isinstance(value, dict):
                cls.log(f"{' ' * indent}{key}:")
                for k2, v2 in value.items():
                    cls.log(f"{' ' * (indent+2)}{k2}: {v2}")
            else:
                cls.log(f"{' ' * indent}{key}: {value}")
    
    @classmethod
    def log_table(cls, headers: List[str], rows: List[List[Any]], title: str = ""):
        """Логировать таблицу."""
        if title:
            cls.log(title)
        cls.log("  " + " | ".join(str(h)[:20] for h in headers))
        cls.log("  " + "-" * (24 * len(headers)))
        for row in rows:
            cls.log("  " + " | ".join(str(v)[:20] for v in row))
    
    @classmethod
    def log_calculation(cls, formula: str, steps: List[Tuple[str, Any]], result: Any):
        """Логировать пошаговое вычисление."""
        cls.log(f"  📐 Formula: {formula}")
        for i, (desc, val) in enumerate(steps):
            cls.log(f"      Step {i+1}: {desc} = {val}")
        cls.log(f"      ─────────────────────────────")
        cls.log(f"      Result: {result}")
    
    @classmethod
    def log_enum(cls, enum_value: Enum, all_values: List[Enum] = None):
        """Логировать enum с описанием."""
        cls.log(f"  Enum: {enum_value.name} = {enum_value.value}")
        if all_values:
            cls.log(f"    All values: {[v.name for v in all_values]}")
    
    @classmethod
    def end_test(cls, passed: bool = True, error: str = None):
        """Завершить тест, сохранить логи в файл."""
        cls.log(f"{'='*80}")
        if passed:
            cls.log(f"✅ E2E TEST PASSED: {cls._test_name}")
        else:
            cls.log(f"❌ E2E TEST FAILED: {cls._test_name}")
            if error:
                cls.log(f"   Error: {error}")
        cls.log(f"{'='*80}")
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = cls._test_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
        filename = cls._output_dir / f"e2e_{safe_name}_{timestamp}.log"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("\n".join(cls._logs))
        
        cls.log(f"📁 Logs saved to: {filename}")
        cls._logs = []
        return filename


# =============================================================================
# HELPER: VALUE DESCRIPTIONS
# =============================================================================

class ValueDescribers:
    """Хелпер для текстовых описаний значений."""
    
    @staticmethod
    def describe_quality(q: float) -> str:
        """Описать качество от 0 до 1."""
        if q >= 0.9: return "Отличное (премиум)"
        elif q >= 0.8: return "Хорошее (высокое)"
        elif q >= 0.7: return "Приемлемое (стандарт)"
        elif q >= 0.5: return "Низкое (требует улучшения)"
        elif q >= 0.3: return "Очень низкое (критическое)"
        else: return "Неприемлемое (брак)"
    
    @staticmethod
    def describe_priority(p: float) -> str:
        """Описать приоритет."""
        if p >= 0.9: return "КРИТИЧЕСКИЙ"
        elif p >= 0.7: return "Высокий"
        elif p >= 0.4: return "Средний"
        else: return "Низкий"
    
    @staticmethod
    def describe_phi(phi: float) -> str:
        """Описать прибыльность."""
        if phi >= 100: return "Очень высокая"
        elif phi >= 50: return "Высокая"
        elif phi >= 20: return "Средняя"
        elif phi >= 5: return "Низкая"
        elif phi >= 0: return "Минимальная"
        else: return "Убыточная"
    
    @staticmethod
    def describe_psi(psi: float) -> str:
        """Описать риск."""
        if psi >= 0.8: return "КРИТИЧЕСКИЙ РИСК"
        elif psi >= 0.6: return "Высокий риск"
        elif psi >= 0.4: return "Средний риск"
        elif psi >= 0.2: return "Низкий риск"
        else: return "Минимальный риск"
    
    @staticmethod
    def describe_decision(decision: str) -> str:
        """Описать решение."""
        decisions = {
            "EXECUTE": "✅ ВЫПОЛНИТЬ — действие одобрено",
            "DECLINE": "⏸️ ОТКЛОНИТЬ — невыгодно или рискованно",
            "REJECT": "🚫 ОТКЛОНИТЬ — нарушены hard rules",
            "CLARIFY": "❓ УТОЧНИТЬ — недостаточно информации"
        }
        return decisions.get(decision, decision)


# =============================================================================
# E2E PATH 1: TASK LIFECYCLE
# =============================================================================

class TestE2ETaskLifecycleVerbose:
    """
    E2E-01: Полный цикл жизни задачи с максимальным логированием.
    
    Путь: create_task → start → execute → assess_quality → complete
    """
    
    def test_task_lifecycle_full_verbose(self):
        """Подробный тест полного lifecycle задачи."""
        E2ETestLogger.start_test("task_lifecycle_full_verbose")
        log = E2ETestLogger.log
        lval = E2ETestLogger.log_value
        ldesc = ValueDescribers.describe_priority
        
        from space1.models.task import Task, TaskStatus, TaskPriority, TaskComplexityClassifier
        
        # === STEP 1: TASK CREATION ===
        log("="*60)
        log("STEP 1: TASK CREATION")
        log("="*60)
        
        task_id = "e2e-task-001"
        task_title = "Implement critical database migration"
        task_description = "Urgent database leak fix with API refactoring"
        
        lval("Task ID", task_id)
        lval("Title", task_title)
        lval("Description", task_description)
        
        # Classify complexity
        classifier = TaskComplexityClassifier()
        complexity, entropy, routing = classifier.predict_complexity(task_title, task_description)
        
        lval("Predicted Complexity", f"{complexity:.3f} — {ldesc(complexity)}")
        lval("Entropy (uncertainty)", f"{entropy:.3f} bits")
        lval("Suggested Routing", routing)
        
        # Create task with priority
        priority = TaskPriority.HIGH
        deadline = datetime.now() + timedelta(hours=24)
        
        task = Task(
            id=task_id,
            title=task_title,
            description=task_description,
            priority=priority,
            deadline=deadline
        )
        
        lval("Priority", priority.name, ldesc(priority.value))
        lval("Deadline", deadline.isoformat())
        lval("Initial Status", task.status.name, "Задача создана и ожидает")
        
        log(f"Task created: {task}")
        
        # === STEP 2: TASK START ===
        log("="*60)
        log("STEP 2: TASK START")
        log("="*60)
        
        started = task.start()
        lval("start() returned", started)
        lval("Status after start", task.status.name)
        lval("started_at", task.started_at.isoformat() if task.started_at else None)
        
        assert task.status == TaskStatus.IN_PROGRESS, f"Expected IN_PROGRESS, got {task.status}"
        
        # === STEP 3: SIMULATE EXECUTION ===
        log("="*60)
        log("STEP 3: SIMULATE EXECUTION")
        log("="*60)
        
        # Simulate agent execution
        from space1.models.agents import Agent, AgentCapabilities, AgentMetrics
        
        agent = Agent(
            id="e2e-agent-001",
            name="Test Agent",
            capabilities=AgentCapabilities(),
            metrics=AgentMetrics()
        )
        
        lval("Agent ID", agent.id)
        lval("Agent Name", agent.name)
        lval("Agent Balance", agent.metrics.balance, "USD")
        lval("Agent Reputation", agent.metrics.success_rate, "0-1")
        
        # Simulate work
        work_hours = 2.5
        quality_score = 0.85
        
        lval("Simulated work hours", work_hours, "hours")
        lval("Simulated quality", f"{quality_score:.2f} — {ValueDescribers.describe_quality(quality_score)}")
        
        # === STEP 4: COMPUTE UTILITY ===
        log("="*60)
        log("STEP 4: COMPUTE UTILITY (Φ, Ψ, Q)")
        log("="*60)
        
        from space1.utility import compute_phi, compute_psi, compute_quality
        
        # Input values
        price = 150.0  # Expected price
        quality = quality_score
        cost = 30.0  # Agent cost
        time_hours = work_hours
        
        lval("Price (revenue)", price, "USD")
        lval("Quality", quality, "0-1")
        lval("Cost", cost, "USD")
        lval("Time", time_hours, "hours")
        
        # Compute Φ (Profit)
        log("--- Computing Φ (Profit) ---")
        phi = compute_phi(price, quality, cost, time_hours)
        
        b_Q = 0.1 * max(0, quality - 0.7) - 0.2 * max(0, 0.7 - quality)
        modulated_price = price * (1 + b_Q)
        duration = max(time_hours, 0.1)
        phi_calc = (modulated_price - cost) / duration
        
        lval("b_Q (quality bonus)", f"{b_Q:.4f}")
        lval("Modulated Price", f"{modulated_price:.2f} USD")
        lval("Duration (max(time, 0.1))", duration, "hours")
        lval("Φ (Profit)", f"{phi:.2f} USD/hour — {ValueDescribers.describe_phi(phi)}")
        
        # Compute Ψ (Risk)
        log("--- Computing Ψ (Risk) ---")
        psi = compute_psi(task, agent)
        lval("Ψ (Risk)", f"{psi:.4f} — {ValueDescribers.describe_psi(psi)}")
        
        # Compute Q (Quality)
        log("--- Computing Q (Quality) ---")
        q_score = compute_quality(quality, 0.9, 0.8, 0.85)
        lval("Q (Quality Score)", f"{q_score:.4f} — {ValueDescribers.describe_quality(q_score)}")
        
        # === STEP 5: EVALUATE DECISION ===
        log("="*60)
        log("STEP 5: EVALUATE DECISION RULE")
        log("="*60)
        
        from space1.utility import evaluate_decision_rule, VetoType
        
        gamma_hard = 0.0  # No hard violations
        psi_max = 0.7
        C_t = agent.metrics.balance  # Available budget
        C_min = 10.0
        H_TZ = 0.3  # Task uncertainty
        H_TZ_max = 0.5
        VoI = 5.0  # Value of information
        C_info = 10.0  # Cost of information
        H_val = 0.8  # Human validation
        H_clarify = 0.3
        U_val = phi / 50.0  # Normalized utility
        Q_predicted = quality
        q_min = 0.5
        
        lval("γ_hard", gamma_hard)
        lval("Ψ_max (risk threshold)", psi_max)
        lval("C_t (available budget)", C_t, "USD")
        lval("C_min (min budget)", C_min, "USD")
        lval("H_TZ (task uncertainty)", H_TZ)
        lval("H_TZ_max", H_TZ_max)
        lval("VoI", VoI)
        lval("C_info", C_info)
        lval("H_val", H_val)
        lval("U_val (normalized)", f"{U_val:.4f}")
        lval("Q_predicted", Q_predicted)
        lval("q_min", q_min)
        
        decision = evaluate_decision_rule(
            gamma_hard=gamma_hard,
            psi=psi,
            psi_max=psi_max,
            C_t=C_t,
            C_min=C_min,
            H_TZ=H_TZ,
            H_TZ_max=H_TZ_max,
            VoI=VoI,
            C_info=C_info,
            H_val=H_val,
            H_clarify=H_clarify,
            U_val=U_val,
            Q_predicted=Q_predicted,
            q_min=q_min,
            veto_type=VetoType.NONE,
            mission_profile="BALANCED"
        )
        
        lval("DECISION", decision, ValueDescribers.describe_decision(decision))
        
        # === STEP 6: TASK COMPLETION ===
        log("="*60)
        log("STEP 6: TASK COMPLETION")
        log("="*60)
        
        if decision == "EXECUTE":
            completed = task.complete()
            lval("complete() returned", completed)
            lval("Final Status", task.status.name)
            lval("completed_at", task.completed_at.isoformat() if task.completed_at else None)
            
            # Verify
            assert task.status == TaskStatus.COMPLETED
        else:
            log("⚠️ Task NOT executed due to decision rule")
        
        E2ETestLogger.end_test(passed=True)


# =============================================================================
# E2E PATH 2: UTILITY COMPUTATION PIPELINE
# =============================================================================

class TestE2EUtilityComputationVerbose:
    """
    E2E-02: Полный pipeline вычисления UPH (Utility, Profit, Quality).
    
    Путь: compute_phi → compute_psi → compute_quality → evaluate_decision_rule
    """
    
    def test_utility_pipeline_verbose(self):
        """Подробный тест pipeline вычислений."""
        E2ETestLogger.start_test("utility_pipeline_verbose")
        log = E2ETestLogger.log
        lval = E2ETestLogger.log_value
        
        from space1.utility import compute_phi, compute_psi, compute_quality, evaluate_decision_rule
        from space1.models.task import Task, TaskPriority
        from space1.models.agents import Agent, AgentCapabilities, AgentMetrics
        
        log("="*60)
        log("UTILITY PIPELINE TEST")
        log("="*60)
        
        # === TEST CASES ===
        test_cases = [
            {
                "name": "HIGH_QUALITY_FAST_CHEAP",
                "price": 200.0, "quality": 0.95, "cost": 20.0, "time": 1.0,
                "description": "Отличное качество, быстро, дешево"
            },
            {
                "name": "LOW_QUALITY_SLOW_EXPENSIVE",
                "price": 100.0, "quality": 0.4, "cost": 80.0, "time": 5.0,
                "description": "Низкое качество, медленно, дорого"
            },
            {
                "name": "AVERAGE_BALANCED",
                "price": 150.0, "quality": 0.7, "cost": 50.0, "time": 2.5,
                "description": "Средние показатели, сбалансировано"
            },
            {
                "name": "PERFECT_STANDARD",
                "price": 100.0, "quality": 0.7, "cost": 30.0, "time": 2.0,
                "description": "Стандартная задача без бонусов/штрафов"
            },
            {
                "name": "BELOW_EXPECTED_QUALITY",
                "price": 100.0, "quality": 0.5, "cost": 30.0, "time": 2.0,
                "description": "Качество ниже ожидаемого (0.7) — штраф"
            },
            {
                "name": "ABOVE_EXPECTED_QUALITY",
                "price": 100.0, "quality": 0.9, "cost": 30.0, "time": 2.0,
                "description": "Качество выше ожидаемого — бонус"
            }
        ]
        
        results = []
        
        for tc in test_cases:
            log("")
            log(f"┌{'─'*60}┐")
            log(f"│ TEST CASE: {tc['name']:<43}│")
            log(f"└{'─'*60}┘")
            log(f"Description: {tc['description']}")
            
            price = tc["price"]
            quality = tc["quality"]
            cost = tc["cost"]
            time_hours = tc["time"]
            
            lval("Price", price, "USD")
            lval("Quality", f"{quality:.2f} — {ValueDescribers.describe_quality(quality)}")
            lval("Cost", cost, "USD")
            lval("Time", time_hours, "hours")
            
            # === Φ COMPUTATION ===
            log("--- Φ (Profit) Computation ---")
            
            Q_expected = 0.7
            kappa_bonus = 0.1
            kappa_penalty = 0.2
            
            b_Q = kappa_bonus * max(0, quality - Q_expected) - kappa_penalty * max(0, Q_expected - quality)
            
            E2ETestLogger.log_calculation(
                formula="Φ = (P × (1 + b_Q) - C) / T",
                steps=[
                    ("P (price)", price),
                    ("Q_expected", Q_expected),
                    ("κ_bonus × max(0, Q-Q_exp)", f"{kappa_bonus} × {max(0, quality - Q_expected)} = {kappa_bonus * max(0, quality - Q_expected):.4f}"),
                    ("κ_penalty × max(0, Q_exp-Q)", f"{kappa_penalty} × {max(0, Q_expected - quality)} = {kappa_penalty * max(0, Q_expected - quality):.4f}"),
                    ("b_Q", b_Q),
                    ("P × (1 + b_Q)", price * (1 + b_Q)),
                    ("C (cost)", cost),
                    ("T (time)", time_hours)
                ],
                result=None
            )
            
            phi = compute_phi(price, quality, cost, time_hours)
            lval("Φ (Profit)", f"{phi:.2f} USD/hour", ValueDescribers.describe_phi(phi))
            
            # === Ψ COMPUTATION ===
            log("--- Ψ (Risk) Computation ---")
            
            task = Task(
                id="psi-test",
                title="Test",
                description="Test",
                priority=TaskPriority.MEDIUM,
                deadline=datetime.now() + timedelta(hours=24)
            )
            agent = Agent(
                id="psi-agent",
                name="Test Agent",
                capabilities=AgentCapabilities(),
                metrics=AgentMetrics()
            )
            
            psi = compute_psi(task, agent)
            lval("Ψ (Risk)", f"{psi:.4f}", ValueDescribers.describe_psi(psi))
            
            # === Q COMPUTATION ===
            log("--- Q (Quality) Computation ---")
            
            completeness = quality
            accuracy = 0.85
            fullfillment = 0.9
            consistency = 0.8
            
            q_score = compute_quality(completeness, accuracy, fullfillment, consistency)
            lval("Completeness", completeness)
            lval("Accuracy", accuracy)
            lval("Fullfillment", fullfillment)
            lval("Consistency", consistency)
            lval("Q (Weighted)", f"{q_score:.4f}", ValueDescribers.describe_quality(q_score))
            
            # === DECISION ===
            log("--- Decision Rule ---")
            
            u_val = phi / 100.0
            decision = evaluate_decision_rule(
                gamma_hard=0.0,
                psi=psi,
                psi_max=0.7,
                C_t=100.0,
                C_min=10.0,
                H_TZ=0.3,
                H_TZ_max=0.5,
                VoI=5.0,
                C_info=10.0,
                H_val=0.8,
                H_clarify=0.3,
                U_val=u_val,
                Q_predicted=quality,
                q_min=0.5
            )
            
            lval("U_val (normalized)", f"{u_val:.4f}")
            lval("Decision", decision, ValueDescribers.describe_decision(decision))
            
            results.append({
                "name": tc["name"],
                "price": price,
                "quality": quality,
                "phi": phi,
                "psi": psi,
                "q": q_score,
                "decision": decision
            })
        
        # === SUMMARY TABLE ===
        log("")
        log("="*60)
        log("SUMMARY TABLE")
        log("="*60)
        
        E2ETestLogger.log_table(
            headers=["Case", "Price", "Quality", "Φ", "Ψ", "Q", "Decision"],
            rows=[
                [r["name"], f"${r['price']:.0f}", f"{r['quality']:.2f}", 
                 f"{r['phi']:.1f}", f"{r['psi']:.3f}", f"{r['q']:.2f}", r["decision"]]
                for r in results
            ],
            title="All test cases:"
        )
        
        E2ETestLogger.end_test(passed=True)
    
    def test_phi_with_platform_fees(self):
        """Тест Φ с комиссиями платформы."""
        E2ETestLogger.start_test("phi_with_platform_fees")
        log = E2ETestLogger.log
        lval = E2ETestLogger.log_value
        
        from space1.utility import compute_phi
        
        log("="*60)
        log("Φ WITH PLATFORM FEES")
        log("="*60)
        
        price = 100.0
        quality = 0.8
        cost = 20.0
        time_hours = 2.0
        C_platform = 0.10  # 10% platform fee
        C_processing = 0.05  # 5% processing fee
        
        lval("Price", price, "USD")
        lval("Quality", quality)
        lval("Cost", cost, "USD")
        lval("Time", time_hours, "hours")
        lval("C_platform", f"{C_platform*100:.0f}%")
        lval("C_processing", f"{C_processing*100:.0f}%")
        
        phi = compute_phi(
            price, quality, cost, time_hours,
            C_platform=C_platform,
            C_processing=C_processing
        )
        
        # Manual calculation
        b_Q = 0.1 * max(0, quality - 0.7)
        modulated_price = price * (1 + b_Q)
        fees = C_platform + C_processing
        after_fees = modulated_price * (1 - fees)
        phi_calc = (after_fees - cost) / time_hours
        
        lval("b_Q", f"{b_Q:.4f}")
        lval("Modulated Price", f"{modulated_price:.2f} USD")
        lval("Total Fees", f"{fees*100:.0f}%")
        lval("After Fees", f"{after_fees:.2f} USD")
        lval("Φ (with fees)", f"{phi:.2f} USD/hour")
        lval("Φ (no fees, for comparison)", f"{compute_phi(price, quality, cost, time_hours):.2f}")
        
        assert abs(phi - phi_calc) < 0.01, f"Expected {phi_calc}, got {phi}"
        
        E2ETestLogger.end_test(passed=True)


# =============================================================================
# E2E PATH 3: DECISION CASCADE TESTS
# =============================================================================

class TestE2EDecisionCascadeVerbose:
    """
    E2E-03: Тесты каскада решений с разными профилями миссий.
    """
    
    def test_decision_cascade_all_profiles(self):
        """Тест всех профилей миссий."""
        E2ETestLogger.start_test("decision_cascade_all_profiles")
        log = E2ETestLogger.log
        lval = E2ETestLogger.log_value
        
        from space1.utility import evaluate_decision_rule, VetoType
        
        log("="*60)
        log("DECISION CASCADE — ALL MISSION PROFILES")
        log("="*60)
        
        profiles = ["BALANCED", "SURVIVAL", "GROWTH", "CHARITY"]
        
        profile_descriptions = {
            "BALANCED": "Сбалансированный профиль — умеренный риск и качество",
            "SURVIVAL": "Выживание — минимальный риск, сохранение ресурсов",
            "GROWTH": "Рост — готовность к риску ради качества",
            "CHARITY": "Благотворительность — минимум требований к качеству"
        }
        
        results = []
        
        for profile in profiles:
            log(f"\n{'─'*60}")
            log(f"PROFILE: {profile}")
            log(f"{'─'*60}")
            log(f"Description: {profile_descriptions[profile]}")
            
            # Same inputs, different profile
            gamma_hard = 0.0
            psi = 0.5  # Medium risk
            psi_max = 0.6
            C_t = 50.0
            C_min = 10.0
            H_TZ = 0.4
            H_TZ_max = 0.5
            VoI = 5.0
            C_info = 10.0
            H_val = 0.7
            H_clarify = 0.3
            U_val = 0.6
            Q_predicted = 0.6
            q_min = 0.5
            
            lval("γ_hard", gamma_hard)
            lval("ψ (input)", psi)
            lval("ψ_max (default)", psi_max)
            lval("C_t", C_t)
            lval("C_min (default)", C_min)
            lval("Q_predicted", Q_predicted)
            lval("q_min (default)", q_min)
            
            decision = evaluate_decision_rule(
                gamma_hard=gamma_hard,
                psi=psi,
                psi_max=psi_max,
                C_t=C_t,
                C_min=C_min,
                H_TZ=H_TZ,
                H_TZ_max=H_TZ_max,
                VoI=VoI,
                C_info=C_info,
                H_val=H_val,
                H_clarify=H_clarify,
                U_val=U_val,
                Q_predicted=Q_predicted,
                q_min=q_min,
                veto_type=VetoType.NONE,
                mission_profile=profile
            )
            
            lval("Decision", decision, ValueDescribers.describe_decision(decision))
            
            results.append({
                "profile": profile,
                "psi_max": psi_max,
                "q_min": q_min,
                "C_min": C_min,
                "decision": decision
            })
        
        # Summary
        log("\n" + "="*60)
        log("PROFILE COMPARISON")
        log("="*60)
        
        E2ETestLogger.log_table(
            headers=["Profile", "ψ_max", "q_min", "C_min", "Decision"],
            rows=[
                [r["profile"], r["psi_max"], r["q_min"], r["C_min"], r["decision"]]
                for r in results
            ]
        )
        
        E2ETestLogger.end_test(passed=True)
    
    def test_decision_hard_veto(self):
        """Тест HARD veto — критическое нарушение правил."""
        E2ETestLogger.start_test("decision_hard_veto")
        log = E2ETestLogger.log
        lval = E2ETestLogger.log_value
        
        from space1.utility import evaluate_decision_rule, VetoType
        
        log("="*60)
        log("DECISION WITH HARD VETO")
        log("="*60)
        
        # Scenario: Agent tries to access forbidden resource
        gamma_hard = float('-inf')  # Hard violation detected
        psi = 0.1  # Low risk
        psi_max = 0.9
        C_t = 100.0
        C_min = 5.0
        H_TZ = 0.1
        H_TZ_max = 0.5
        VoI = 0.0
        C_info = 10.0
        H_val = 0.9
        H_clarify = 0.3
        U_val = 1.0  # Very high utility
        Q_predicted = 0.95  # Very high quality
        q_min = 0.3
        
        lval("γ_hard", gamma_hard, "INFINITE (HARD VIOLATION)")
        lval("ψ", psi)
        lval("U_val", U_val, "Very high")
        lval("Q_predicted", Q_predicted, "Very high")
        
        decision = evaluate_decision_rule(
            gamma_hard=gamma_hard,
            psi=psi,
            psi_max=psi_max,
            C_t=C_t,
            C_min=C_min,
            H_TZ=H_TZ,
            H_TZ_max=H_TZ_max,
            VoI=VoI,
            C_info=C_info,
            H_val=H_val,
            H_clarify=H_clarify,
            U_val=U_val,
            Q_predicted=Q_predicted,
            q_min=q_min,
            veto_type=VetoType.HARD
        )
        
        lval("Decision", decision, ValueDescribers.describe_decision(decision))
        
        assert decision == "REJECT", f"Expected REJECT, got {decision}"
        
        log("✅ Hard veto correctly rejected high-utility action")
        
        E2ETestLogger.end_test(passed=True)


# =============================================================================
# E2E PATH 4: AGENT LIFECYCLE
# =============================================================================

class TestE2EAgentLifecycleVerbose:
    """
    E2E-04: Полный цикл жизни агента.
    """
    
    def test_agent_lifecycle_verbose(self):
        """Подробный тест lifecycle агента."""
        E2ETestLogger.start_test("agent_lifecycle_verbose")
        log = E2ETestLogger.log
        lval = E2ETestLogger.log_value
        
        from space1.models.agents import Agent, AgentCapabilities, AgentMetrics
        
        log("="*60)
        log("AGENT LIFECYCLE TEST")
        log("="*60)
        
        # === AGENT CREATION ===
        log("\n--- Agent Creation ---")
        
        agent_id = "agent-e2e-001"
        agent_name = "Production Agent Alpha"
        
        lval("Agent ID", agent_id)
        lval("Agent Name", agent_name)
        
        # Create capabilities
        capabilities = AgentCapabilities()
        lval("Initial Capabilities", "Default (all 0.0 or neutral)")
        
        # Create metrics
        metrics = AgentMetrics(
            balance=100.0,
            token_budget=50.0,
            success_rate=0.75,
        )
        
        lval("Initial Balance", metrics.balance, "USD")
        lval("Token Budget", metrics.token_budget, "tokens")
        lval("Success Rate", f"{metrics.success_rate:.2f}", ValueDescribers.describe_quality(metrics.success_rate))
        lval("Rating", f"{metrics.rating:.3f}")
        
        # Create agent
        agent = Agent(
            id=agent_id,
            name=agent_name,
            capabilities=capabilities,
            metrics=metrics
        )
        
        lval("Agent Created", "Yes")
        lval("Agent ID", agent.id)
        lval("Agent Name", agent.name)
        
        # === SIMULATE WORK ===
        log("\n--- Simulate Work ---")
        
        revenue_earned = 250.0
        tokens_spent = 15.0
        
        lval("Revenue Earned", revenue_earned, "USD")
        lval("Tokens Spent", tokens_spent, "tokens")
        
        # Update metrics
        agent.metrics.balance += revenue_earned
        agent.metrics.total_earned += revenue_earned
        agent.metrics.token_budget -= tokens_spent
        agent.metrics.tokens_used += tokens_spent
        
        lval("New Balance", agent.metrics.balance, "USD")
        lval("Total Earned", agent.metrics.total_earned, "USD")
        lval("New Token Budget", agent.metrics.token_budget, "tokens")
        lval("Tokens Used", agent.metrics.tokens_used, "tokens")
        
        # === REPUTATION UPDATE ===
        log("\n--- Reputation Update ---")
        
        from space1.utility import update_upsilon
        
        current_upsilon = update_upsilon(
            rating=agent.metrics.rating,
            n_reviews=agent.metrics.n_reviews,
            n_positive=agent.metrics.n_positive,
            metrics=None
        )
        
        lval("Υ (Reputation)", f"{current_upsilon:.4f}")
        
        E2ETestLogger.end_test(passed=True)


# =============================================================================
# RUN ALL TESTS
# =============================================================================

if __name__ == "__main__":
    print("="*80)
    print("SPACE1 SUPER VERBOSE E2E TESTS")
    print("="*80)
    print()
    
    # Create test instances
    tests = [
        TestE2ETaskLifecycleVerbose(),
        TestE2EUtilityComputationVerbose(),
        TestE2EDecisionCascadeVerbose(),
        TestE2EAgentLifecycleVerbose(),
    ]
    
    results = []
    
    for test in tests:
        test_name = test.__class__.__name__
        methods = [m for m in dir(test) if m.startswith("test_")]
        
        for method_name in methods:
            method = getattr(test, method_name)
            print(f"\n{'#'*80}")
            print(f"# Running: {test_name}.{method_name}")
            print(f"{'#'*80}")
            
            try:
                method()
                results.append((test_name, method_name, "PASSED"))
            except Exception as e:
                print(f"\n❌ EXCEPTION: {e}")
                import traceback
                traceback.print_exc()
                results.append((test_name, method_name, f"FAILED: {e}"))
    
    # Summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, _, r in results if r == "PASSED")
    total = len(results)
    
    for test_name, method_name, result in results:
        status = "✅" if result == "PASSED" else "❌"
        print(f"  {status} {test_name}.{method_name}: {result}")
    
    print(f"\nTotal: {passed}/{total} passed")
    print(f"Logs saved to: reports/e2e_test_logs/")
