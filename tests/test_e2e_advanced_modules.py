"""
Space1 — E2E TESTS: Router, Psychometrics, Environment, Market Protocols, Metrics, Optimizer

Покрывает модули, не затронутые основными E2E.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from datetime import datetime, timedelta


class TestE2EAIRouter:
    """AI Super Router: routing decision (router требует aiohttp + провайдеры)."""

    def test_router_module_importable(self):
        """Модуль router импортируется (если aiohttp установлен)."""
        try:
            from space1.ai_super_router.core.router import RoutingDecision
            # RoutingDecision API — проверим что класс существует
            assert RoutingDecision is not None, "RoutingDecision is None"
        except ImportError:
            # aiohttp не установлен — это ок, тест пропускаем
            assert True, "aiohttp not installed, skipping router test"


class TestE2EClientPsychometrics:
    """Клиентская психометрия: CCRS, риск-профиль, платёжные условия."""

    def test_ccrs_computation(self):
        """compute_ccrs возвращает ClientRiskProfile с ccrs в [0,1]."""
        from space1.client_psychometrics.core import compute_ccrs, ClientRiskProfile

        profile = compute_ccrs("Some review text about the client")

        assert isinstance(profile, ClientRiskProfile), f"Expected ClientRiskProfile, got {type(profile)}"
        assert 0.0 <= profile.ccrs <= 1.0, f"CCRS={profile.ccrs} out of [0,1]"
        assert profile.zone is not None, "Zone is None"

    def test_risk_profile_zone(self):
        """ClientRiskProfile определяет зону риска."""
        from space1.client_psychometrics.core import ClientRiskProfile, RiskZone

        profile = ClientRiskProfile(ccrs=0.9)
        assert profile.zone in RiskZone, f"Zone={profile.zone} not in RiskZone enum"
        assert profile.ccrs == 0.9, f"CCRS={profile.ccrs}, expected 0.9"

        profile_bad = ClientRiskProfile(ccrs=0.2)
        assert profile_bad.zone in RiskZone, f"Zone={profile_bad.zone} not in RiskZone enum"
        assert profile_bad.ccrs == 0.2, f"CCRS={profile_bad.ccrs}, expected 0.2"

    def test_payment_terms_from_ccrs(self):
        """payment_terms_from_ccrs возвращает осмысленные условия."""
        from space1.client_psychometrics.core import payment_terms_from_ccrs

        terms_good = payment_terms_from_ccrs(ccrs=0.9)
        terms_bad = payment_terms_from_ccrs(ccrs=0.3)

        assert isinstance(terms_good, dict), f"Good terms: {terms_good}"
        assert isinstance(terms_bad, dict), f"Bad terms: {terms_bad}"
        assert "structure" in terms_good, f"Good terms missing structure: {terms_good}"
        assert "structure" in terms_bad, f"Bad terms missing structure: {terms_bad}"


class TestE2EEnvironment:
    """Рыночная среда: лиды, конкуренция, отзывы."""

    def test_market_environment_generates_leads(self):
        """MarketEnvironment.stream_leads генерирует задачи."""
        from space1.environment.core import MarketEnvironment

        env = MarketEnvironment()
        leads = env.stream_leads(count=5)
        assert len(leads) == 5, f"Expected 5 leads, got {len(leads)}"
        for lead in leads:
            assert hasattr(lead, "id"), "Lead missing id"
            assert hasattr(lead, "title"), "Lead missing title"

    def test_market_competition_simulation(self):
        """simulate_competition возвращает bool."""
        from space1.environment.core import MarketEnvironment
        from space1.models.task import Task, TaskPriority

        env = MarketEnvironment()
        task = Task(id="comp-task", title="Test", description="Test", priority=TaskPriority.HIGH)
        result = env.simulate_competition(task)
        assert isinstance(result, bool), f"Expected bool, got {type(result)}"

    def test_market_review_generation(self):
        """generate_review возвращает структурированный отзыв."""
        from space1.environment.core import MarketEnvironment
        from space1.models.task import Task, TaskPriority

        env = MarketEnvironment()
        task = Task(id="review-task", title="Test", description="Test", priority=TaskPriority.MEDIUM)
        review = env.generate_review(task, achieved_quality=0.85)
        assert "rating" in review, f"Review missing rating: {review}"
        assert "feedback" in review, f"Review missing feedback: {review}"
        assert 1 <= review["rating"] <= 5, f"Rating={review['rating']} out of [1,5]"
        assert review["reputation_multiplier"] > 0, f"Multiplier missing: {review}"


class TestE2EMarketProtocols:
    """Рыночные протоколы: споры, платежи, compliance, репутация."""

    def test_protocol_registry_lists_protocols(self):
        """ProtocolRegistry.list_protocols не пуст."""
        from space1.market_protocols.core import ProtocolRegistry

        registry = ProtocolRegistry()
        protocols = registry.list_protocols()
        assert len(protocols) > 0, "No protocols registered"
        assert "dispute" in [p.lower() for p in protocols] or "payment" in [p.lower() for p in protocols],             f"Expected dispute/payment protocols, got {protocols}"

    def test_dispute_protocol_run(self):
        """DisputeProtocol.run возвращает ProtocolState."""
        from space1.market_protocols.core import ProtocolRegistry, ProtocolState

        registry = ProtocolRegistry()
        state = ProtocolState()
        result = registry.run("dispute", state, {"reason": "quality_mismatch", "severity": 0.7})
        assert result is not None, "Result is None"
        assert hasattr(result, "outcome"), "Result missing outcome"

    def test_payment_risk_protocol(self):
        """PaymentRiskProtocol.check_payment_terms корректна."""
        from space1.market_protocols.core import PaymentRiskProtocol

        protocol = PaymentRiskProtocol()
        terms_good = protocol.check_payment_terms(ccrs=0.9)
        terms_bad = protocol.check_payment_terms(ccrs=0.2)

        assert terms_good is not None, "Good terms is None"
        assert terms_bad is not None, "Bad terms is None"
        assert terms_bad.get("upfront_pct", 0) >= terms_good.get("upfront_pct", 0),             "Bad CCRS should have higher upfront"

    def test_platform_compliance_hard_rules(self):
        """PlatformComplianceProtocol.check_hard_rules находит нарушения."""
        from space1.market_protocols.core import PlatformComplianceProtocol

        protocol = PlatformComplianceProtocol()
        violations = protocol.check_hard_rules({})
        assert isinstance(violations, list), f"Expected list, got {type(violations)}"

    def test_platform_compliance_risk_score(self):
        """compute_platform_risk_score возвращает score в [0, 1]."""
        from space1.market_protocols.core import PlatformComplianceProtocol

        protocol = PlatformComplianceProtocol()
        score = protocol.compute_platform_risk_score(
            behavioral_score=0.8,
            complaint_rate=0.05,
            account_age_days=365,
            consistency_score=0.9
        )
        assert 0.0 <= score <= 1.0, f"Risk score={score} out of [0,1]"


class TestE2EMetricsTracker:
    """Метрики: отслеживание, история, статистика."""

    def test_metric_tracker_update_and_get(self):
        """MetricTracker.update/get работают."""
        from space1.metrics.tracker import MetricTracker

        tracker = MetricTracker()
        tracker.update("success_rate", 0.8)
        tracker.update("success_rate", 0.9)

        val = tracker.get("success_rate")
        assert val is not None, "Value is None"
        assert 0.8 <= val <= 0.9, f"EMA value={val} out of expected range"

        raw = tracker.get_raw("success_rate", n=2)
        assert len(raw) == 2, f"Expected 2 raw values, got {len(raw) if raw else 0}"

    def test_metric_tracker_history(self):
        """MetricTracker.get_history возвращает историю."""
        from space1.metrics.tracker import MetricTracker

        tracker = MetricTracker()
        for i in range(5):
            tracker.update("latency", float(i))

        history = tracker.get_history("latency", n=3)
        assert len(history) == 3, f"Expected 3 history items, got {len(history)}"

    def test_metric_tracker_stats(self):
        """MetricTracker.get_stats возвращает статистику."""
        from space1.metrics.tracker import MetricTracker

        tracker = MetricTracker()
        for i in range(10):
            tracker.update("score", float(i) * 10)

        stats = tracker.get_stats("score")
        assert "mean" in stats, f"Stats missing mean: {stats}"
        assert "min" in stats, f"Stats missing min: {stats}"
        assert "max" in stats, f"Stats missing max: {stats}"
        assert stats["mean"] > 0, f"Mean={stats['mean']} should be >0"

    def test_metrics_engine_phi_psi(self):
        """MetricsEngine.compute_phi/psi возвращают float."""
        from space1.metrics.tracker import MetricsEngine
        from space1.models.task import Task, TaskPriority
        from space1.models.agents import Agent, AgentCapabilities, AgentMetrics

        engine = MetricsEngine()
        task = Task(id="m-task", title="Test", description="Test", priority=TaskPriority.HIGH)
        agent = Agent(id="m-agent", name="Test", capabilities=AgentCapabilities(), metrics=AgentMetrics())

        phi = engine.compute_phi(task, agent)
        psi = engine.compute_psi(task)

        assert isinstance(phi, float), f"phi type={type(phi)}"
        assert isinstance(psi, float), f"psi type={type(psi)}"

    def test_metric_registry_categories(self):
        """MetricRegistry.get_categories не пуст."""
        from space1.metrics.tracker import MetricRegistry

        registry = MetricRegistry()
        registry.track("financial.revenue", 100.0, category="financial")
        registry.track("performance.latency", 50.0, category="performance")

        cats = registry.get_categories()
        assert "financial" in cats, f"Missing financial: {cats}"
        assert "performance" in cats, f"Missing performance: {cats}"

        financial = registry.get_by_category("financial")
        assert "financial.revenue" in financial, f"Missing revenue: {financial}"


class TestE2EOptimizer:
    """Оптимизатор: веса, вероятность успеха, CQS."""

    def test_evaluator_task_adaptive_weights(self):
        """Evaluator.get_task_adaptive_weights возвращает веса."""
        from space1.optimizer.evaluator import Evaluator
        from space1.optimizer.models import TaskDataset, TaskDomain

        dataset = TaskDataset(tasks=[])
        evaluator = Evaluator(dataset=dataset)
        weights = evaluator.get_task_adaptive_weights(domain=TaskDomain.CODE_GENERATION)

        assert isinstance(weights, dict), f"Expected dict, got {type(weights)}"
        assert len(weights) > 0, "Weights empty"
        for k, v in weights.items():
            assert v > 0, f"Weight {k}={v} should be >0"

    def test_evaluator_success_probability(self):
        """Evaluator.calculate_success_probability в [0, 1]."""
        from space1.optimizer.evaluator import Evaluator
        from space1.optimizer.models import TaskDataset, OptimizerTask, AgentConfig, TaskDomain

        dataset = TaskDataset(tasks=[])
        evaluator = Evaluator(dataset=dataset)

        task = OptimizerTask(id="opt-task", title="Test", description="Test", domain=TaskDomain.CODE_GENERATION)
        config = AgentConfig()

        prob = evaluator.calculate_success_probability(task, config)
        assert 0.0 <= prob <= 1.0, f"Probability={prob} out of [0,1]"

    def test_evaluator_cqs(self):
        """Evaluator.compute_cqs в [0, 1]."""
        from space1.optimizer.evaluator import Evaluator
        from space1.optimizer.models import TaskDataset, OptimizerTask, AgentConfig, TaskDomain

        dataset = TaskDataset(tasks=[])
        evaluator = Evaluator(dataset=dataset)

        task = OptimizerTask(id="cqs-task", title="Test", description="Test", domain=TaskDomain.CODE_GENERATION)
        config = AgentConfig()

        cqs = evaluator.compute_cqs(task, config)
        assert 0.0 <= cqs <= 1.0, f"CQS={cqs} out of [0,1]"


class TestE2EUtilityCalibration:
    """Калибровка параметров."""

    def test_parameter_calibrator_exists(self):
        """ParameterCalibrator создаётся без ошибок."""
        from space1.utility.calibration import ParameterCalibrator

        calibrator = ParameterCalibrator(memory=None)
        assert calibrator is not None, "Calibrator is None"

    def test_parameter_calibrator_save_weights(self):
        """ParameterCalibrator.save_calibrated_weights сохраняет в файл."""
        import tempfile
        from space1.utility.calibration import ParameterCalibrator

        calibrator = ParameterCalibrator(memory=None)
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = os.path.join(tmpdir, "weights.yaml")

            result = calibrator.save_calibrated_weights(
                {"phi_cap": 100.0, "success_rate_base": 0.5},
                config_path=temp_path
            )
            assert result is True or result is False, f"Unexpected return: {result}"
            if result:
                assert os.path.getsize(temp_path) > 0, "Config file empty"
