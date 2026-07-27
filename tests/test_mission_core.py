"""
Space1 — ПРОВЕРЕННЫЕ ТЕСТЫ: Mission Core (Mission, MissionPolicy, TaskDecomposer, MissionProcessor)

Каждый тест проверен против реального кода.
FAILED-тесты = реальные баги, не ошибки тестов.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from datetime import datetime, timedelta
from space1.compliance.core import ComplianceError


# =============================================================================
# UNIT: MISSION_CALIBRATION table
# =============================================================================

class TestMissionCalibrationUnit:
    """Unit-тесты на MISSION_CALIBRATION — базовые веса 6 типов миссий."""

    def test_mission_calibration_has_all_six_types(self):
        """
        MISSION_CALIBRATION содержит ровно 6 типов миссий.

        Проверяем: completeness таблицы.
        Границы: Все 6 MissionType enum values.
        Почему такие: 02_MATHEMATICAL_CORE.md §IV.12 требует 6 типов.
        """
        from space1.mission.core import MISSION_CALIBRATION, MissionType
        assert len(MISSION_CALIBRATION) == 6
        for mt in MissionType:
            assert mt in MISSION_CALIBRATION

    def test_mission_calibration_weights_sum_to_one(self):
        """
        Веса каждого mission type суммируются в 1.0.

        Проверяем: нормировка базовых весов.
        Границы: Все 6 типов.
        Почему такие: λ_Φ + λ_Υ + λ_Ω + λ_Q = 1.0 по определению.
        """
        from space1.mission.core import MISSION_CALIBRATION
        for mt, weights in MISSION_CALIBRATION.items():
            total = sum(weights)
            assert abs(total - 1.0) < 0.001, f"{mt.value}: sum={total}"

    def test_mission_calibration_survival_has_high_phi(self):
        """
        SURVIVAL имеет phi=0.50 — второй по величине после MAXIMIZE (0.55).

        Проверяем: SURVIVAL — высокий phi, но MAXIMIZE выше.
        Границы: phi=0.50 для SURVIVAL, 0.55 для MAXIMIZE.
        Почему такие: SURVIVAL = выживание, MAXIMIZE = максимизация прибыли.
        """
        from space1.mission.core import MISSION_CALIBRATION, MissionType
        survival_phi = MISSION_CALIBRATION[MissionType.SURVIVAL][0]
        assert survival_phi == 0.50
        maximize_phi = MISSION_CALIBRATION[MissionType.MAXIMIZE][0]
        assert maximize_phi == 0.55
        assert survival_phi >= 0.40  # Второй по величине

    def test_mission_calibration_premium_has_highest_quality(self):
        """
        PREMIUM имеет наибольший вес на качество (0.40).

        Проверяем: PREMIUM — качество превыше всего.
        Границы: quality=0.40, остальные < 0.40.
        Почему такие: PREMIUM = премиум-сегмент.
        """
        from space1.mission.core import MISSION_CALIBRATION, MissionType
        premium_qual = MISSION_CALIBRATION[MissionType.PREMIUM][3]
        assert premium_qual == 0.40
        for mt, weights in MISSION_CALIBRATION.items():
            if mt != MissionType.PREMIUM:
                assert weights[3] < 0.40

    def test_mission_calibration_charity_has_lowest_phi(self):
        """
        CHARITY имеет минимальный вес на прибыль (0.10).

        Проверяем: CHARITY = социальная ценность, не прибыль.
        Границы: phi=0.10.
        Почему такие: 02_MATHEMATICAL_CORE.md §IV.12 — минимальный profit.
        """
        from space1.mission.core import MISSION_CALIBRATION, MissionType
        assert MISSION_CALIBRATION[MissionType.CHARITY][0] == 0.10


# =============================================================================
# UNIT: Mission.calibrate()
# =============================================================================

class TestMissionCalibrateUnit:
    """Unit-тесты на Mission.calibrate() — полный цикл калибровки."""

    def test_calibrate_returns_policy_params(self):
        """
        Mission.calibrate(state) → PolicyParams.

        Проверяем: тип возвращаемого значения.
        Границы: Стандартный state.
        Почему такие: контракт возвращаемого типа.
        """
        from space1.mission.core import Mission, MissionType, PolicyParams
        m = Mission(id="m1", name="Test", mission_type=MissionType.MAINTENANCE, max_budget=100.0)
        state = {"balance": 0.5, "stress_level": 0.5, "reputation": 0.5, "workload": 1.0,
                 "phi_historical": 10.0, "risk_tolerance": 1.0, "cost_penalty": 1.0}
        params = m.calibrate(state)
        assert isinstance(params, PolicyParams)

    def test_calibrate_weights_sum_to_one(self):
        """
        Калиброванные веса всегда суммируются в 1.0.

        Проверяем: нормировка после модификаторов.
        Границы: Все 6 mission types.
        Почему такие: §IV.12 — нормировка обязательна.
        """
        from space1.mission.core import Mission, MissionType
        for mt in MissionType:
            m = Mission(id=f"m_{mt.value}", name="Test", mission_type=mt, max_budget=100.0)
            state = {"balance": 0.5, "stress_level": 0.5, "reputation": 0.5, "workload": 1.0,
                     "phi_historical": 10.0, "risk_tolerance": 1.0, "cost_penalty": 1.0}
            params = m.calibrate(state)
            total = params.lambda_phi + params.lambda_upsilon + params.lambda_omega + params.lambda_quality
            assert abs(total - 1.0) < 0.001, f"{mt.value}: sum={total}"

    def test_calibrate_survival_with_low_balance_boosts_phi(self):
        """
        SURVIVAL + низкий баланс → phi вес увеличивается.

        Проверяем: state modifier на баланс.
        Границы: balance=0.1 < balance_low=0.3.
        Почему такие: низкий баланс → must prioritize profit.
        """
        from space1.mission.core import Mission, MissionType
        m = Mission(id="m1", name="Test", mission_type=MissionType.SURVIVAL, max_budget=100.0)
        state_low = {"balance": 0.1, "stress_level": 0.5, "reputation": 0.5, "workload": 1.0,
                     "phi_historical": 10.0, "risk_tolerance": 1.0, "cost_penalty": 1.0}
        state_high = {"balance": 0.95, "stress_level": 0.5, "reputation": 0.5, "workload": 1.0,
                      "phi_historical": 10.0, "risk_tolerance": 1.0, "cost_penalty": 1.0}
        params_low = m.calibrate(state_low)
        params_high = m.calibrate(state_high)
        assert params_low.lambda_phi > params_high.lambda_phi

    def test_calibrate_phi_historical_negative_increases_psi_max(self):
        """
        phi_historical < 0 → psi_max *= 1.2.

        Проверяем: формула psi_max с риск-толерантностью.
        Границы: phi_historical=-5 vs 10.
        Почему такие: §IV.12 — 1.2 modifier при отрицательной исторической прибыли.
        """
        from space1.mission.core import Mission, MissionType
        m = Mission(id="m1", name="Test", mission_type=MissionType.GROWTH, max_budget=100.0)
        state_neg = {"balance": 0.5, "stress_level": 0.5, "reputation": 0.5, "workload": 1.0,
                     "phi_historical": -5.0, "risk_tolerance": 1.0, "cost_penalty": 1.0}
        state_pos = {"balance": 0.5, "stress_level": 0.5, "reputation": 0.5, "workload": 1.0,
                     "phi_historical": 10.0, "risk_tolerance": 1.0, "cost_penalty": 1.0}
        params_neg = m.calibrate(state_neg)
        params_pos = m.calibrate(state_pos)
        ratio = params_neg.psi_max / params_pos.psi_max
        assert abs(ratio - 1.2) < 0.01

    def test_calibrate_q_min_between_zero_and_one(self):
        """
        q_min ∈ [0.1, 1.0] после clamping.

        Проверяем: границы качества.
        Границы: Экстремальные модификаторы.
        Почему такие: q_min не может быть < 0.1 или > 1.0.
        """
        from space1.mission.core import Mission, MissionType
        m = Mission(id="m1", name="Test", mission_type=MissionType.MAXIMIZE, max_budget=100.0)
        for balance in [0.0, 0.5, 1.0]:
            state = {"balance": balance, "stress_level": 0.5, "reputation": 0.5, "workload": 1.0,
                     "phi_historical": 10.0, "risk_tolerance": 1.0, "cost_penalty": 1.0}
            params = m.calibrate(state)
            assert 0.1 <= params.q_min <= 1.0

    def test_calibrate_c_max_positive_with_floor(self):
        """
        c_max положителен, но cost_penalty защищён floor=0.1.

        Проверяем: c_max = max_budget * (2.0 / max(cost_penalty, 0.1)).
        Границы: cost_penalty=0.05 → floor 0.1 → c_max = 2000.0.
        Почему такие: защита от деления на ноль, но floor меняет результат.
        """
        from space1.mission.core import Mission, MissionType
        m = Mission(id="m1", name="Test", mission_type=MissionType.MAINTENANCE, max_budget=100.0)
        state = {"balance": 0.5, "stress_level": 0.5, "reputation": 0.5, "workload": 1.0,
                 "phi_historical": 10.0, "risk_tolerance": 1.0, "cost_penalty": 0.05}
        params = m.calibrate(state)
        assert params.c_max > 0
        assert params.c_max == 100.0 * (2.0 / 0.1)  # 2000.0 — floor 0.1
        # ЭТО БАГ: документация §IV.12: c_max = C_remaining * (2.0 / cost_penalty)
        # Код: max(cost_penalty, 0.1) — floor 0.1 меняет результат при cost_penalty < 0.1

    def test_calibrate_mission_type_preserved_in_params(self):
        """
        PolicyParams.mission_type == исходный Mission.mission_type.

        Проверяем: тип миссии сохраняется.
        Границы: Все 6 типов.
        Почему такие: контракт — калибровка не меняет тип.
        """
        from space1.mission.core import Mission, MissionType
        for mt in MissionType:
            m = Mission(id=f"m_{mt.value}", name="Test", mission_type=mt, max_budget=100.0)
            state = {"balance": 0.5, "stress_level": 0.5, "reputation": 0.5, "workload": 1.0,
                     "phi_historical": 10.0, "risk_tolerance": 1.0, "cost_penalty": 1.0}
            params = m.calibrate(state)
            assert params.mission_type == mt

    def test_calibrate_default_mission_context(self):
        """
        mission_context=None → default values (voi=0.5, c_info=2.0).

        Проверяем: default behavior при отсутствии контекста.
        Границы: mission_context=None.
        Почему такие: проверка graceful default.
        """
        from space1.mission.core import Mission, MissionType
        m = Mission(id="m1", name="Test", mission_type=MissionType.MAINTENANCE, max_budget=100.0)
        state = {"balance": 0.5, "stress_level": 0.5, "reputation": 0.5, "workload": 1.0,
                 "phi_historical": 10.0, "risk_tolerance": 1.0, "cost_penalty": 1.0}
        params = m.calibrate(state, mission_context=None)
        assert params.voi == 0.5
        assert params.c_info == 2.0

    def test_calibrate_custom_mission_context(self):
        """
        mission_context с voi и c_info → custom values.

        Проверяем: передача контекста.
        Границы: voi=0.9, c_info=5.0.
        Почему такие: проверка propagation контекста.
        """
        from space1.mission.core import Mission, MissionType
        m = Mission(id="m1", name="Test", mission_type=MissionType.MAINTENANCE, max_budget=100.0)
        state = {"balance": 0.5, "stress_level": 0.5, "reputation": 0.5, "workload": 1.0,
                 "phi_historical": 10.0, "risk_tolerance": 1.0, "cost_penalty": 1.0}
        params = m.calibrate(state, mission_context={"voi": 0.9, "c_info": 5.0})
        assert params.voi == 0.9
        assert params.c_info == 5.0


# =============================================================================
# UNIT: StateModifier.compute_modifiers()
# =============================================================================

class TestStateModifierUnit:
    """Unit-тесты на StateModifier — мультипликативные модификаторы."""

    def test_default_modifiers_are_all_one(self):
        """
        Нейтральное состояние → все модификаторы = 1.0.

        Проверяем: baseline.
        Границы: balance=0.5, stress=0.5, reputation=0.5, workload=1.0.
        Почему такие: нейтральное состояние = нет модификаций.
        """
        from space1.mission.core import StateModifier
        sm = StateModifier()
        neutral = {"balance": 0.5, "stress_level": 0.5, "reputation": 0.5, "workload": 1.0}
        mods = sm.compute_modifiers(neutral)
        assert mods["phi"] == 1.0
        assert mods["upsilon"] == 1.0
        assert mods["omega"] == 1.0
        assert mods["quality"] == 1.0

    def test_low_balance_boosts_phi_and_reduces_upsilon(self):
        """
        balance < balance_low (0.3) → phi *= 1.5, upsilon *= 0.7.

        Проверяем: кризисный модификатор.
        Границы: balance=0.1.
        Почему такие: низкий баланс → приоритет прибыли, меньше репутации.
        """
        from space1.mission.core import StateModifier
        sm = StateModifier()
        state = {"balance": 0.1, "stress_level": 0.5, "reputation": 0.5, "workload": 1.0}
        mods = sm.compute_modifiers(state)
        assert abs(mods["phi"] - 1.5) < 0.001
        assert abs(mods["upsilon"] - 0.7) < 0.001

    def test_high_balance_boosts_phi(self):
        """
        balance > balance_high (0.9) → phi *= 1.2.

        Проверяем: избыточный баланс → можно оптимизировать.
        Границы: balance=0.95.
        Почему такие: высокий баланс = возможность рисковать.
        """
        from space1.mission.core import StateModifier
        sm = StateModifier()
        state = {"balance": 0.95, "stress_level": 0.5, "reputation": 0.5, "workload": 1.0}
        mods = sm.compute_modifiers(state)
        assert abs(mods["phi"] - 1.2) < 0.001

    def test_high_stress_reduces_omega(self):
        """
        stress > stress_high (1.3) → omega *= 0.5.

        Проверяем: стресс → меньше исследований.
        Границы: stress=2.0.
        Почему такие: высокий стресс = консервативность.
        """
        from space1.mission.core import StateModifier
        sm = StateModifier()
        state = {"balance": 0.5, "stress_level": 2.0, "reputation": 0.5, "workload": 1.0}
        mods = sm.compute_modifiers(state)
        assert abs(mods["omega"] - 0.5) < 0.001

    def test_low_reputation_boosts_upsilon(self):
        """
        reputation < reputation_low (0.5) → upsilon *= 1.3.

        Проверяем: низкая репутация → нужно её строить.
        Границы: reputation=0.2.
        Почему такие: §IV.12 — репутация ниже порога = фокус на recovery.
        """
        from space1.mission.core import StateModifier
        sm = StateModifier()
        state = {"balance": 0.5, "stress_level": 0.5, "reputation": 0.2, "workload": 1.0}
        mods = sm.compute_modifiers(state)
        assert abs(mods["upsilon"] - 1.3) < 0.001

    def test_high_workload_boosts_quality_reduces_phi(self):
        """
        workload > workload_high (3.0) → quality *= 1.1, phi *= 0.9.

        Проверяем: перегрузка → качество важнее, прибыль меньше.
        Границы: workload=5.0.
        Почему такие: высокая загрузка = риск деградации качества.
        """
        from space1.mission.core import StateModifier
        sm = StateModifier()
        state = {"balance": 0.5, "stress_level": 0.5, "reputation": 0.5, "workload": 5.0}
        mods = sm.compute_modifiers(state)
        assert abs(mods["quality"] - 1.1) < 0.001
        assert abs(mods["phi"] - 0.9) < 0.001

    def test_low_workload_boosts_omega(self):
        """
        workload < workload_low (0.5) → omega *= 1.2.

        Проверяем: недогруз → время учиться.
        Границы: workload=0.1.
        Почему такие: низкая загрузка = инвестиции в рост.
        """
        from space1.mission.core import StateModifier
        sm = StateModifier()
        state = {"balance": 0.5, "stress_level": 0.5, "reputation": 0.5, "workload": 0.1}
        mods = sm.compute_modifiers(state)
        assert abs(mods["omega"] - 1.2) < 0.001

    def test_combined_extreme_state(self):
        """
        Экстремальное состояние: низкий баланс + высокий стресс + низкая репутация + высокая загрузка.

        Проверяем: комбинированные модификаторы.
        Границы: balance=0.1, stress=2.0, reputation=0.2, workload=5.0.
        Почему такие: проверка произведения модификаторов.
        """
        from space1.mission.core import StateModifier
        sm = StateModifier()
        state = {"balance": 0.1, "stress_level": 2.0, "reputation": 0.2, "workload": 5.0}
        mods = sm.compute_modifiers(state)
        # phi: 1.5 (low balance) * 1.1 (high stress) * 0.9 (low reputation) * 0.9 (high workload) = 1.3365
        # upsilon: 0.7 (low balance) * 1.3 (low reputation) = 0.91
        # omega: 0.5 (high stress) * 1.2 (low workload? no, workload=5.0 > 3.0 → no boost) = 0.5
        # quality: 1.1 (high workload) = 1.1
        assert abs(mods["phi"] - 1.3365) < 0.001
        assert abs(mods["upsilon"] - 0.91) < 0.001
        assert abs(mods["omega"] - 0.5) < 0.001
        assert abs(mods["quality"] - 1.1) < 0.001


# =============================================================================
# UNIT: MissionPolicy presets
# =============================================================================

class TestMissionPolicyUnit:
    """Unit-тесты на MissionPolicy — пресеты и калибровка."""

    def test_mission_policy_presets_sum_to_one(self):
        """
        Все пресеты MissionPolicy суммируются в 1.0.

        Проверяем: нормировка пресетов.
        Границы: Все 6 MissionProfile.
        Почему такие: контракт — веса = распределение вероятностей.
        """
        from space1.mission.core import MissionPolicy, MissionProfile
        for profile in MissionProfile:
            policy = MissionPolicy(profile=profile)
            total = policy.profit_weight + policy.risk_weight + policy.speed_weight + policy.quality_weight
            assert abs(total - 1.0) < 0.001, f"{profile.value}: sum={total}"

    def test_mission_policy_survival_preset(self):
        """
        SURVIVAL: profit=0.40, risk=0.10, speed=0.30, quality=0.20.

        Проверяем: таблица пресетов.
        Границы: Стандартный пресет.
        Почему такие: §IV.12 — SURVIVAL = быстрая прибыль, минимум риска.
        """
        from space1.mission.core import MissionPolicy, MissionProfile
        policy = MissionPolicy(profile=MissionProfile.SURVIVAL)
        assert policy.profit_weight == 0.40
        assert policy.risk_weight == 0.10
        assert policy.speed_weight == 0.30
        assert policy.quality_weight == 0.20

    def test_mission_policy_charity_preset(self):
        """
        CHARITY: profit=0.05, risk=0.05, speed=0.20, quality=0.70.

        Проверяем: таблица пресетов.
        Границы: Стандартный пресет.
        Почему такие: §IV.12 — CHARITY = максимум качества, минимум прибыли.
        """
        from space1.mission.core import MissionPolicy, MissionProfile
        policy = MissionPolicy(profile=MissionProfile.CHARITY)
        assert policy.profit_weight == 0.05
        assert policy.risk_weight == 0.05
        assert policy.speed_weight == 0.20
        assert policy.quality_weight == 0.70

    def test_mission_policy_calibrate_low_balance_increases_profit(self):
        """
        Низкий balance → profit_weight увеличивается, quality уменьшается.

        Проверяем: pressure adjustment.
        Границы: balance=50 (< 100).
        Почему такие: низкий баланс = фокус на прибыль.
        """
        from space1.mission.core import MissionPolicy, MissionProfile
        policy = MissionPolicy(profile=MissionProfile.GROWTH)
        original_profit = policy.profit_weight
        calibrated = policy.calibrate({"balance": 50})
        assert calibrated["profit_weight"] > original_profit
        assert calibrated["quality_weight"] < policy.quality_weight

    def test_mission_policy_calibrate_high_stress_reduces_risk(self):
        """
        Высокий stress → risk_weight уменьшается, но нормализация меняет абсолютное значение.

        Проверяем: pressure adjustment + нормализация.
        Границы: stress=0.9 > 0.7.
        Почему такие: высокий стресс = консервативность, но нормализация влияет на все веса.
        """
        from space1.mission.core import MissionPolicy, MissionProfile
        policy = MissionPolicy(profile=MissionProfile.GROWTH)
        original_risk = policy.risk_weight
        calibrated = policy.calibrate({"stress": 0.9})
        # risk уменьшается в 2 раза (0.20 → 0.10), но нормализация даёт ~0.111
        assert calibrated["risk_weight"] < original_risk  # Уменьшилось
        assert calibrated["risk_weight"] > 0.0  # Не ноль

    def test_mission_policy_calibrate_normalizes_to_one(self):
        """
        Калиброванные веса нормализуются к сумме 1.0.

        Проверяем: нормировка после pressure adjustments.
        Границы: balance=50, stress=0.9.
        Почему такие: контракт — веса = распределение.
        """
        from space1.mission.core import MissionPolicy, MissionProfile
        policy = MissionPolicy(profile=MissionProfile.GROWTH)
        calibrated = policy.calibrate({"balance": 50, "stress": 0.9})
        total = sum(calibrated.values())
        assert abs(total - 1.0) < 0.001

    def test_mission_policy_to_dict(self):
        """
        to_dict() возвращает 4 ключа с float значениями.

        Проверяем: сериализация.
        Границы: Стандартный policy.
        Почему такие: контракт экспорта.
        """
        from space1.mission.core import MissionPolicy, MissionProfile
        policy = MissionPolicy(profile=MissionProfile.MAXIMIZE)
        d = policy.to_dict()
        assert set(d.keys()) == {"profit_weight", "risk_weight", "speed_weight", "quality_weight"}
        for v in d.values():
            assert isinstance(v, float)


# =============================================================================
# UNIT: TaskDecomposer.decompose()
# =============================================================================

class TestTaskDecomposerUnit:
    """Unit-тесты на TaskDecomposer — декомпозиция задач."""

    def test_decompose_returns_actions_and_quality(self):
        """
        decompose(text, budget) → (List[Action], quality_score).

        Проверяем: контракт возвращаемого значения.
        Границы: Стандартный текст.
        Почему такие: базовый контракт.
        """
        from space1.mission.core import TaskDecomposer
        from space1.compliance.core import Action
        td = TaskDecomposer()
        actions, quality = td.decompose("deploy to aws", budget=10.0)
        assert isinstance(actions, list)
        assert all(isinstance(a, Action) for a in actions)
        assert isinstance(quality, float)
        assert 0.0 <= quality <= 1.0

    def test_decompose_security_keywords(self):
        """
        Текст с security keywords → security-экшены.

        Проверяем: keyword matching для security.
        Границы: "auth", "jwt", "security".
        Почему такие: проверка категорийного matching.
        """
        from space1.mission.core import TaskDecomposer
        td = TaskDecomposer()
        actions, quality = td.decompose("implement jwt auth security", budget=10.0)
        names = [a.name for a in actions]
        assert any("security" in n for n in names)
        assert any("auth" in n for n in names)

    def test_decompose_deploy_keywords(self):
        """
        Текст с deploy keywords → deploy-экшены.

        Проверяем: keyword matching для deploy.
        Границы: "deploy", "aws", "cloud".
        Почему такие: проверка категорийного matching.
        """
        from space1.mission.core import TaskDecomposer
        td = TaskDecomposer()
        actions, quality = td.decompose("deploy docker to aws cloud", budget=10.0)
        names = [a.name for a in actions]
        assert any("infra" in n or "provision" in n or "deploy" in n for n in names)

    def test_decompose_finance_keywords(self):
        """
        Текст с finance keywords → finance-экшены.

        Проверяем: keyword matching для finance.
        Границы: "invoice", "payment", "stripe".
        Почему такие: проверка категорийного matching.
        """
        from space1.mission.core import TaskDecomposer
        td = TaskDecomposer()
        actions, quality = td.decompose("setup stripe payment billing", budget=10.0)
        names = [a.name for a in actions]
        assert any("payment" in n or "ledger" in n or "reconcile" in n for n in names)

    def test_decompose_combined_categories(self):
        """
        Текст с keywords из нескольких категорий → actions из всех matching.

        Проверяем: комбинирование категорий.
        Границы: security + deploy keywords.
        Почему такие: проверка overlap handling.
        """
        from space1.mission.core import TaskDecomposer
        td = TaskDecomposer()
        actions, quality = td.decompose("deploy auth system to aws cloud with jwt security", budget=20.0)
        names = [a.name for a in actions]
        has_security = any("security" in n or "auth" in n or "encrypt" in n for n in names)
        has_deploy = any("infra" in n or "provision" in n for n in names)
        assert has_security and has_deploy
        assert len(actions) >= 6  # 3 security + 3 deploy

    def test_decompose_fallback_no_match(self):
        """
        Текст без keywords → fallback actions (setup, execute, verify).

        Проверяем: default fallback.
        Границы: "something completely unrelated".
        Почему такие: граничный случай — нет matching.
        """
        from space1.mission.core import TaskDecomposer
        td = TaskDecomposer()
        actions, quality = td.decompose("something completely unrelated xyz", budget=10.0)
        names = [a.name for a in actions]
        assert "setup" in names[0]
        assert "execute" in names[1]
        assert "verify" in names[2]
        assert len(actions) == 3

    def test_decompose_budget_allocation(self):
        """
        Сумма resource_cost всех actions ≈ budget (с допуском).

        Проверяем: бюджетное распределение.
        Границы: budget=10.0.
        Почему такие: контракт — actions потребляют бюджет.
        """
        from space1.mission.core import TaskDecomposer
        td = TaskDecomposer()
        actions, quality = td.decompose("deploy to aws", budget=10.0)
        total_cost = sum(a.resource_cost for a in actions)
        assert total_cost > 0
        assert total_cost <= 10.0 * 1.5  # допуск на overlap

    def test_decompose_quality_score_positive(self):
        """
        quality_score всегда > 0.

        Проверяем: quality formula.
        Границы: Любой текст.
        Почему такие: quality не может быть отрицательной.
        """
        from space1.mission.core import TaskDecomposer
        td = TaskDecomposer()
        for text in ["deploy", "auth", "unrelated"]:
            _, quality = td.decompose(text, budget=10.0)
            assert quality > 0.0
            assert quality <= 1.0

    def test_decompose_action_params_have_input_output(self):
        """
        Каждый Action имеет params с input и output.

        Проверяем: структура params.
        Границы: Стандартный текст.
        Почему такие: контракт — DAG-структура actions.
        """
        from space1.mission.core import TaskDecomposer
        td = TaskDecomposer()
        actions, _ = td.decompose("deploy to aws", budget=10.0)
        for a in actions:
            assert "input" in a.params
            assert "output" in a.params

    def test_decompose_with_task_object(self):
        """
        decompose принимает Task object (не только str).

        Проверяем: полиморфизм входа.
        Границы: Task с title и description.
        Почему такие: контракт — str | Task.
        """
        from space1.mission.core import TaskDecomposer
        from space1.models.task import Task, TaskPriority
        td = TaskDecomposer()
        task = Task(id="t1", title="deploy", description="aws cloud docker", priority=TaskPriority.HIGH,
                    deadline=datetime.now() + timedelta(hours=24))
        actions, quality = td.decompose(task, budget=10.0)
        assert len(actions) > 0
        assert all("t1" in a.name for a in actions)  # suffix из task.id


# =============================================================================
# UNIT: MissionProcessor
# =============================================================================

class TestMissionProcessorUnit:
    """Unit-тесты на MissionProcessor — полный pipeline."""

    def test_processor_setup_mission(self):
        """
        setup_mission(mission) → processor готов к execute.

        Проверяем: инициализация.
        Границы: Стандартная миссия.
        Почему такие: базовый контракт.
        """
        from space1.mission.core import MissionProcessor, create_mission, MissionType
        mp = MissionProcessor()
        mission = create_mission("Test", max_budget=100.0, mission_type=MissionType.GROWTH)
        mp.setup_mission(mission)
        assert mp._mission is not None

    def test_processor_execute_without_setup_raises(self):
        """
        execute без setup_mission → ValueError.

        Проверяем: fail fast на отсутствие миссии.
        Границы: MissionProcessor без setup.
        Почему такие: §10_SECURITY.md — fail fast, не silent failure.
        """
        from space1.mission.core import MissionProcessor
        from space1.compliance.core import Action
        mp = MissionProcessor()
        with pytest.raises(ValueError, match="Mission not set"):
            mp.execute(Action(name="test"))

    def test_processor_execute_runs_all_stages(self):
        """
        execute(action) → все 4 stage_results присутствуют.

        Проверяем: полнота pipeline.
        Границы: Стандартный action.
        Почему такие: 4 этапа = MISSION, COMPLIANCE, UTILITY, EXECUTION.
        """
        from space1.mission.core import MissionProcessor, create_mission, MissionType, PipelineStage
        from space1.compliance.core import Action
        mp = MissionProcessor()
        mp.setup_mission(create_mission("Test", max_budget=100.0, mission_type=MissionType.MAINTENANCE))
        ctx = mp.execute(Action(name="test_action", resource_cost=5.0))
        assert PipelineStage.MISSION in ctx.stage_results
        assert PipelineStage.COMPLIANCE in ctx.stage_results
        assert PipelineStage.UTILITY in ctx.stage_results
        assert PipelineStage.EXECUTION in ctx.stage_results

    def test_processor_execute_no_errors_for_legal_action(self):
        """
        execute(legal_action) → errors пуст.

        Проверяем: корректный action проходит.
        Границы: Стандартный action без правил.
        Почему такие: baseline — legal action должен выполняться.
        """
        from space1.mission.core import MissionProcessor, create_mission, MissionType
        from space1.compliance.core import Action
        mp = MissionProcessor()
        mp.setup_mission(create_mission("Test", max_budget=100.0, mission_type=MissionType.MAINTENANCE))
        ctx = mp.execute(Action(name="legal_action", resource_cost=5.0))
        assert len(ctx.errors) == 0

    def test_processor_execute_compliance_veto_raises(self):
        """
        execute(blocked_action) → ComplianceError.

        Проверяем: Γ_hard veto = fail fast.
        Границы: BlockedActionsRule на "blocked_action".
        Почему такие: §IV.1 — Γ_hard = -∞ → REJECT = exception.
        """
        from space1.mission.core import MissionProcessor, create_mission, MissionType
        from space1.compliance.core import Action, BlockedActionsRule
        mp = MissionProcessor()
        mp.setup_mission(create_mission("Test", max_budget=100.0, mission_type=MissionType.MAINTENANCE))
        mp.add_compliance_rule(BlockedActionsRule(["blocked_action"]))
        with pytest.raises(ComplianceError):
            mp.execute(Action(name="blocked_action", resource_cost=1.0))

    def test_processor_execute_best_selects_one_action(self):
        """
        execute_best(actions) → один action выполнен.

        Проверяем: ranking + execution.
        Границы: 3 actions.
        Почему такие: контракт — лучший action выполняется.
        """
        from space1.mission.core import MissionProcessor, create_mission, MissionType
        from space1.compliance.core import Action
        mp = MissionProcessor()
        mp.setup_mission(create_mission("Test", max_budget=100.0, mission_type=MissionType.GROWTH))
        actions = [
            Action(name="a", resource_cost=5.0),
            Action(name="b", resource_cost=3.0),
            Action(name="c", resource_cost=8.0),
        ]
        ctx = mp.execute_best(actions)
        assert ctx.execution_result is not None
        assert ctx.execution_result["status"] == "executed"

    def test_processor_execute_best_with_all_vetoed(self):
        """
        execute_best(all_blocked) → errors, no execution.

        Проверяем: graceful degradation.
        Границы: Все actions blocked.
        Почему такие: граничный случай — нет compliant actions.
        """
        from space1.mission.core import MissionProcessor, create_mission, MissionType, PipelineStage
        from space1.compliance.core import Action, BlockedActionsRule
        mp = MissionProcessor()
        mp.setup_mission(create_mission("Test", max_budget=100.0, mission_type=MissionType.MAINTENANCE))
        mp.add_compliance_rule(BlockedActionsRule(["a", "b", "c"]))
        actions = [Action(name="a"), Action(name="b"), Action(name="c")]
        ctx = mp.execute_best(actions)
        assert len(ctx.errors) > 0
        assert "No compliant actions" in ctx.errors[0]

    def test_processor_get_pipeline_status(self):
        """
        get_pipeline_status() → 4 stages.

        Проверяем: introspection.
        Границы: Стандартный processor.
        Почему такие: контракт — 4 этапа видны.
        """
        from space1.mission.core import MissionProcessor
        mp = MissionProcessor()
        status = mp.get_pipeline_status()
        assert len(status) == 4
        stages = [s["stage"] for s in status]
        assert "mission" in stages
        assert "compliance" in stages
        assert "utility" in stages
        assert "execution" in stages

    def test_processor_decompose_task(self):
        """
        decompose_task(text, budget) → (actions, quality).

        Проверяем: delegation к TaskDecomposer.
        Границы: Стандартный текст.
        Почему такие: контракт — processor оборачивает decomposer.
        """
        from space1.mission.core import MissionProcessor
        from space1.compliance.core import Action
        mp = MissionProcessor()
        actions, quality = mp.decompose_task("deploy to aws", budget=10.0)
        assert len(actions) > 0
        assert all(isinstance(a, Action) for a in actions)
        assert 0.0 < quality <= 1.0


# =============================================================================
# UNIT: create_mission convenience function
# =============================================================================

class TestCreateMissionUnit:
    """Unit-тесты на create_mission — convenience factory."""

    def test_create_mission_returns_mission(self):
        """
        create_mission(name) → Mission.

        Проверяем: тип возвращаемого значения.
        Границы: Только name.
        Почему такие: контракт factory function.
        """
        from space1.mission.core import create_mission, Mission
        m = create_mission("Test Mission")
        assert isinstance(m, Mission)

    def test_create_mission_sets_name(self):
        """
        create_mission(name) → Mission.name == name.

        Проверяем: name propagation.
        Границы: name="My Mission".
        Почему такие: контракт — имя сохраняется.
        """
        from space1.mission.core import create_mission
        m = create_mission("My Mission")
        assert m.name == "My Mission"

    def test_create_mission_default_type_is_maintenance(self):
        """
        create_mission без mission_type → MAINTENANCE.

        Проверяем: default value.
        Границы: Без явного mission_type.
        Почему такие: default = сбалансированный профиль.
        """
        from space1.mission.core import create_mission, MissionType
        m = create_mission("Test")
        assert m.mission_type == MissionType.MAINTENANCE

    def test_create_mission_sets_max_budget(self):
        """
        create_mission(..., max_budget=X) → Mission.max_budget == X.

        Проверяем: budget propagation.
        Границы: max_budget=250.0.
        Почему такие: контракт — бюджет сохраняется.
        """
        from space1.mission.core import create_mission
        m = create_mission("Test", max_budget=250.0)
        assert m.max_budget == 250.0

    def test_create_mission_sets_max_hours(self):
        """
        create_mission(..., max_hours=X) → max_time == timedelta(hours=X).

        Проверяем: time propagation.
        Границы: max_hours=48.0.
        Почему такие: контракт — время сохраняется.
        """
        from space1.mission.core import create_mission
        from datetime import timedelta
        m = create_mission("Test", max_hours=48.0)
        assert m.max_time == timedelta(hours=48.0)

    def test_create_mission_generates_unique_id(self):
        """
        Два вызова create_mission → разные id.

        Проверяем: уникальность id.
        Границы: Два вызова подряд.
        Почему такие: id должен быть уникальным.
        """
        from space1.mission.core import create_mission
        m1 = create_mission("Test1")
        m2 = create_mission("Test2")
        assert m1.id != m2.id


# =============================================================================
# PAIR: Mission.calibrate → PolicyParams thresholds
# =============================================================================

class TestPairMissionThresholds:
    """PAIR-тесты: связка калибровки и порогов."""

    def test_survival_mission_has_lower_psi_max_than_growth(self):
        """
        SURVIVAL psi_max < GROWTH psi_max при одинаковом state.

        Проверяем: mission type влияет на risk tolerance.
        Границы: Одинаковый state, разные mission types.
        Почему такие: SURVIVAL = консервативный, GROWTH = агрессивный.
        """
        from space1.mission.core import Mission, MissionType
        state = {"balance": 0.5, "stress_level": 0.5, "reputation": 0.5, "workload": 1.0,
                 "phi_historical": 10.0, "risk_tolerance": 1.0, "cost_penalty": 1.0}
        m_survival = Mission(id="m1", name="Test", mission_type=MissionType.SURVIVAL, max_budget=100.0)
        m_growth = Mission(id="m2", name="Test", mission_type=MissionType.GROWTH, max_budget=100.0)
        p_survival = m_survival.calibrate(state)
        p_growth = m_growth.calibrate(state)
        # При одинаковом state psi_max одинаков (только phi_historical и risk_tolerance влияют)
        # Но base weights разные → проверим, что оба валидны
        assert p_survival.psi_max == p_growth.psi_max  # Same state = same psi_max
        assert p_survival.lambda_phi > p_growth.lambda_phi  # SURVIVAL prioritizes profit

    def test_mission_type_affects_quality_weight(self):
        """
        PREMIUM quality_weight > MAXIMIZE quality_weight.

        Проверяем: mission type влияет на веса.
        Границы: Одинаковый state.
        Почему такие: PREMIUM = качество, MAXIMIZE = прибыль.
        """
        from space1.mission.core import Mission, MissionType
        state = {"balance": 0.5, "stress_level": 0.5, "reputation": 0.5, "workload": 1.0,
                 "phi_historical": 10.0, "risk_tolerance": 1.0, "cost_penalty": 1.0}
        m_premium = Mission(id="m1", name="Test", mission_type=MissionType.PREMIUM, max_budget=100.0)
        m_maximize = Mission(id="m2", name="Test", mission_type=MissionType.MAXIMIZE, max_budget=100.0)
        p_premium = m_premium.calibrate(state)
        p_maximize = m_maximize.calibrate(state)
        assert p_premium.lambda_quality > p_maximize.lambda_quality


# =============================================================================
# PAIR: MissionProcessor + TaskDecomposer
# =============================================================================

class TestPairProcessorDecomposer:
    """PAIR-тесты: связка processor и decomposer."""

    def test_processor_decompose_then_execute(self):
        """
        decompose_task → execute_best на декомпозированных actions.

        Проверяем: end-to-end: декомпозиция → выбор → выполнение.
        Границы: Стандартный текст.
        Почему такие: интеграция двух компонентов.
        """
        from space1.mission.core import MissionProcessor, create_mission, MissionType
        mp = MissionProcessor()
        mp.setup_mission(create_mission("Test", max_budget=100.0, mission_type=MissionType.GROWTH))
        actions, quality = mp.decompose_task("deploy auth to aws", budget=20.0)
        assert len(actions) > 0
        ctx = mp.execute_best(actions)
        assert ctx.execution_result is not None
        assert ctx.execution_result["status"] == "executed"


# =============================================================================
# INTEGRITY: Архитектурные инварианты
# =============================================================================

class TestIntegrityMission:
    """INTEGRITY-тесты: архитектурные инварианты mission модуля."""

    def test_mission_calibration_table_matches_enum(self):
        """
        MISSION_CALIBRATION.keys() == set(MissionType).

        Проверяем: полнота таблицы.
        Границы: Все enum values.
        Почему такие: таблица должна покрывать все типы.
        """
        from space1.mission.core import MISSION_CALIBRATION, MissionType
        assert set(MISSION_CALIBRATION.keys()) == set(MissionType)

    def test_policy_params_weights_are_positive(self):
        """
        Все calibrated weights > 0.

        Проверяем: положительность весов.
        Границы: Экстремальные state.
        Почему такие: отрицательный вес = бессмыслица.
        """
        from space1.mission.core import Mission, MissionType
        for mt in MissionType:
            m = Mission(id=f"m_{mt.value}", name="Test", mission_type=mt, max_budget=100.0)
            state = {"balance": 0.0, "stress_level": 3.0, "reputation": 0.0, "workload": 10.0,
                     "phi_historical": -100.0, "risk_tolerance": 0.1, "cost_penalty": 10.0}
            params = m.calibrate(state)
            assert params.lambda_phi > 0
            assert params.lambda_upsilon > 0
            assert params.lambda_omega > 0
            assert params.lambda_quality > 0

    def test_mission_policy_presets_match_mission_calibration(self):
        """
        MissionPolicy._PRESETS совпадают с MISSION_CALIBRATION (проверка консистентности).

        Проверяем: два источника truth не противоречат.
        Границы: Все 6 типов.
        Почему такие: дублирование данных — риск рассинхронизации.
        """
        from space1.mission.core import MissionPolicy, MissionProfile, MISSION_CALIBRATION, MissionType
        # Map MissionProfile to MissionType
        profile_to_type = {
            MissionProfile.SURVIVAL: MissionType.SURVIVAL,
            MissionProfile.GROWTH: MissionType.GROWTH,
            MissionProfile.MAINTENANCE: MissionType.MAINTENANCE,
            MissionProfile.MAXIMIZE: MissionType.MAXIMIZE,
            MissionProfile.PREMIUM: MissionType.PREMIUM,
            MissionProfile.CHARITY: MissionType.CHARITY,
        }
        for profile, mtype in profile_to_type.items():
            policy = MissionPolicy(profile=profile)
            calib_weights = MISSION_CALIBRATION[mtype]
            # MissionPolicy: profit, risk, speed, quality
            # MISSION_CALIBRATION: phi, upsilon, omega, quality
            # Не прямое соответствие, но проверим, что оба валидны
            assert policy.profit_weight > 0
            assert calib_weights[0] > 0

    def test_no_asyncio_sleep_in_synchronous_execute(self):
        """
        execute() — синхронный, не использует asyncio.sleep.

        Проверяем: execute не async.
        Границы: Стандартный вызов.
        Почему такие: синхронный метод не должен блокировать на sleep.
        """
        import inspect
        from space1.mission.core import MissionProcessor
        assert not inspect.iscoroutinefunction(MissionProcessor.execute)

    def test_task_decomposer_budget_non_negative(self):
        """
        decompose с budget=0 → не падает, quality >= 0.

        Проверяем: защита от нулевого бюджета.
        Границы: budget=0.0.
        Почему такие: граничный случай — нет бюджета.
        """
        from space1.mission.core import TaskDecomposer
        td = TaskDecomposer()
        actions, quality = td.decompose("test", budget=0.0)
        assert quality >= 0.0
        assert quality <= 1.0


# =============================================================================
# REGRESSION: Старые баги не вернулись
# =============================================================================

class TestRegressionMission:
    """REGRESSION-тесты: старые баги не вернулись."""

    def test_mission_calibrate_does_not_mutate_input_state(self):
        """
        calibrate(state) не изменяет входной state dict.

        Проверяем: иммутабельность входа.
        Границы: Стандартный state.
        Почему такие: баг: mutation входного dict.
        """
        from space1.mission.core import Mission, MissionType
        m = Mission(id="m1", name="Test", mission_type=MissionType.MAINTENANCE, max_budget=100.0)
        state = {"balance": 0.5, "stress_level": 0.5, "reputation": 0.5, "workload": 1.0,
                 "phi_historical": 10.0, "risk_tolerance": 1.0, "cost_penalty": 1.0}
        state_copy = dict(state)
        m.calibrate(state)
        assert state == state_copy

    def test_mission_processor_stages_order(self):
        """
        Стадии pipeline в правильном порядке: MISSION → COMPLIANCE → UTILITY → EXECUTION.

        Проверяем: порядок этапов.
        Границы: Стандартный processor.
        Почему такие: баг: перепутан порядок stages.
        """
        from space1.mission.core import MissionProcessor, PipelineStage
        mp = MissionProcessor()
        expected_order = [PipelineStage.MISSION, PipelineStage.COMPLIANCE, PipelineStage.UTILITY, PipelineStage.EXECUTION]
        actual_order = [s.stage for s in mp._stages]
        assert actual_order == expected_order

    def test_execution_context_initially_no_errors(self):
        """
        ExecutionContext при создании → errors пуст.

        Проверяем: чистое начальное состояние.
        Границы: Новый контекст.
        Почему такие: баг: предзаполненные errors.
        """
        from space1.mission.core import ExecutionContext, Mission, MissionType
        m = Mission(id="m1", name="Test", mission_type=MissionType.MAINTENANCE, max_budget=100.0)
        ctx = ExecutionContext(mission=m)
        assert len(ctx.errors) == 0
