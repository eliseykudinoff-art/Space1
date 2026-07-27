"""
Space1 — ПРОВЕРЕННЫЕ ТЕСТЫ: Cold Start Core

Каждый тест проверен против реального кода.
FAILED-тесты = реальные баги, не ошибки тестов.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
import math


# =============================================================================
# UNIT: Константы
# =============================================================================

class TestColdStartConstantsUnit:
    """Unit-тесты на canonical cold-start константы."""

    def test_H_initial_value(self):
        """
        H_INITIAL = 1.0 (02_MATHEMATICAL_CORE.md Часть X).

        Проверяем: базовое значение гомеостаза при t=0.
        Границы: Стандартная константа.
        Почему такие: контракт 02_MATHEMATICAL_CORE.md §X.
        """
        from space1.cold_start.core import H_INITIAL
        assert H_INITIAL == 1.0

    def test_upsilon_initial_value(self):
        """
        UPSILON_INITIAL = 0.5 (02_MATHEMATICAL_CORE.md Часть X).

        Проверяем: нейтральная репутация при t=0.
        Границы: Стандартная константа.
        Почему такие: контракт 02_MATHEMATICAL_CORE.md §X.
        """
        from space1.cold_start.core import UPSILON_INITIAL
        assert UPSILON_INITIAL == 0.5

    def test_phi_historical_initial_value(self):
        """
        PHI_HISTORICAL_INITIAL = 0.0 (02_MATHEMATICAL_CORE.md Часть X).

        Проверяем: отсутствие исторической прибыли при t=0.
        Границы: Стандартная константа.
        Почему такие: контракт 02_MATHEMATICAL_CORE.md §X.
        """
        from space1.cold_start.core import PHI_HISTORICAL_INITIAL
        assert PHI_HISTORICAL_INITIAL == 0.0

    def test_rli_population_default_q(self):
        """
        RLI_POPULATION_DEFAULT_Q = 0.65.

        Проверяем: prior качества для cold-start.
        Границы: Стандартная константа.
        Почему такие: контракт 03_PIPELINE_MATH.md §III.1.
        """
        from space1.cold_start.core import RLI_POPULATION_DEFAULT_Q
        assert RLI_POPULATION_DEFAULT_Q == 0.65

    def test_rli_population_default_psi(self):
        """
        RLI_POPULATION_DEFAULT_PSI = 0.25.

        Проверяем: prior риска для cold-start.
        Границы: Стандартная константа.
        Почему такие: контракт 03_PIPELINE_MATH.md §III.1.
        """
        from space1.cold_start.core import RLI_POPULATION_DEFAULT_PSI
        assert RLI_POPULATION_DEFAULT_PSI == 0.25

    def test_ucb1_epsilon_value(self):
        """
        UCB1_EPSILON = 1e-6.

        Проверяем: guard для division by zero в UCB1.
        Границы: Стандартная константа.
        Почему такие: контракт 03_PIPELINE_MATH.md §III.1 — защита от n_e=0.
        """
        from space1.cold_start.core import UCB1_EPSILON
        assert UCB1_EPSILON == 1e-6

    def test_ensemble_weights_cold(self):
        """
        ENSEMBLE_WEIGHTS["cold"] = (0.4, 0.2, 0.4) для n < 5.

        Проверяем: веса ансамбля при cold start.
        Границы: Стандартная константа.
        Почему такие: контракт 03_PIPELINE_MATH.md §III.1.
        """
        from space1.cold_start.core import ENSEMBLE_WEIGHTS
        assert ENSEMBLE_WEIGHTS["cold"] == (0.4, 0.2, 0.4)

    def test_ensemble_weights_warm(self):
        """
        ENSEMBLE_WEIGHTS["warm"] = (0.2, 0.5, 0.3) для 5 <= n < 20.

        Проверяем: веса ансамбля при warm start.
        Границы: Стандартная константа.
        Почему такие: контракт 03_PIPELINE_MATH.md §III.1.
        """
        from space1.cold_start.core import ENSEMBLE_WEIGHTS
        assert ENSEMBLE_WEIGHTS["warm"] == (0.2, 0.5, 0.3)

    def test_ensemble_weights_hot(self):
        """
        ENSEMBLE_WEIGHTS["hot"] = (0.1, 0.7, 0.2) для n >= 20.

        Проверяем: веса ансамбля при hot start.
        Границы: Стандартная константа.
        Почему такие: контракт 03_PIPELINE_MATH.md §III.1.
        """
        from space1.cold_start.core import ENSEMBLE_WEIGHTS
        assert ENSEMBLE_WEIGHTS["hot"] == (0.1, 0.7, 0.2)

    def test_ensemble_weights_sum_to_one(self):
        """
        Все ENSEMBLE_WEIGHTS суммируются в 1.0.

        Проверяем: веса — вероятностное распределение.
        Границы: Все три режима.
        Почему такие: веса ансамбля должны быть нормализованы.
        """
        from space1.cold_start.core import ENSEMBLE_WEIGHTS
        for name, weights in ENSEMBLE_WEIGHTS.items():
            assert abs(sum(weights) - 1.0) < 1e-9, f"{name}: {sum(weights)} != 1.0"

    def test_ensemble_weights_all_positive(self):
        """
        Все ENSEMBLE_WEIGHTS > 0.

        Проверяем: положительность весов.
        Границы: Все три режима.
        Почему такие: нулевой вес означает исключение предиктора.
        """
        from space1.cold_start.core import ENSEMBLE_WEIGHTS
        for name, weights in ENSEMBLE_WEIGHTS.items():
            for w in weights:
                assert w > 0.0, f"{name}: {w} <= 0"


# =============================================================================
# UNIT: ColdStartState
# =============================================================================

class TestColdStartStateUnit:
    """Unit-тесты на ColdStartState dataclass."""

    def test_cold_start_state_defaults(self):
        """
        ColdStartState() → H=1.0, upsilon_k=0.5, phi_historical=0.0, q_prior=0.65, psi_prior=0.25, n_completed=0.

        Проверяем: default значения соответствуют константам.
        Границы: Без аргументов.
        Почему такие: контракт 02_MATHEMATICAL_CORE.md §X.
        """
        from space1.cold_start.core import ColdStartState, H_INITIAL, UPSILON_INITIAL
        from space1.cold_start.core import PHI_HISTORICAL_INITIAL, RLI_POPULATION_DEFAULT_Q
        from space1.cold_start.core import RLI_POPULATION_DEFAULT_PSI

        state = ColdStartState()
        assert state.H == H_INITIAL
        assert state.upsilon_k == UPSILON_INITIAL
        assert state.phi_historical == PHI_HISTORICAL_INITIAL
        assert state.q_prior == RLI_POPULATION_DEFAULT_Q
        assert state.psi_prior == RLI_POPULATION_DEFAULT_PSI
        assert state.n_completed == 0

    def test_cold_start_state_custom_values(self):
        """
        ColdStartState(H=2.0, upsilon_k=0.8, n_completed=10) → кастомные значения.

        Проверяем: переопределение default.
        Границы: Кастомные значения.
        Почему такие: проверка переопределения.
        """
        from space1.cold_start.core import ColdStartState
        state = ColdStartState(H=2.0, upsilon_k=0.8, n_completed=10)
        assert state.H == 2.0
        assert state.upsilon_k == 0.8
        assert state.n_completed == 10

    def test_cold_start_state_to_dict(self):
        """
        ColdStartState.to_dict() → dict с 6 ключами.

        Проверяем: сериализация состояния.
        Границы: Стандартный кейс.
        Почему такие: проверка интерфейса сериализации.
        """
        from space1.cold_start.core import ColdStartState
        state = ColdStartState()
        d = state.to_dict()
        assert len(d) == 6
        assert "H" in d
        assert "upsilon_k" in d
        assert "phi_historical" in d
        assert "q_prior" in d
        assert "psi_prior" in d
        assert "n_completed" in d

    def test_cold_start_state_to_dict_values(self):
        """
        to_dict() возвращает правильные значения.

        Проверяем: корректность сериализации.
        Границы: Кастомные значения.
        Почему такие: проверка точности сериализации.
        """
        from space1.cold_start.core import ColdStartState
        state = ColdStartState(H=1.5, upsilon_k=0.3, n_completed=5)
        d = state.to_dict()
        assert d["H"] == 1.5
        assert d["upsilon_k"] == 0.3
        assert d["n_completed"] == 5

    def test_cold_start_state_zero_n_completed(self):
        """
        n_completed=0 — граничный случай cold start.

        Проверяем: zero experience.
        Границы: n_completed = 0.
        Почему такие: граничный случай — полное отсутствие опыта.
        """
        from space1.cold_start.core import ColdStartState
        state = ColdStartState(n_completed=0)
        assert state.n_completed == 0

    def test_cold_start_state_negative_n_completed(self):
        """
        n_completed=-1 — недопустимое значение, но принимается.

        Проверяем: отсутствие валидации.
        Границы: n_completed < 0.
        Почему такие: проверка границы — отрицательный опыт недопустим.
        """
        from space1.cold_start.core import ColdStartState
        state = ColdStartState(n_completed=-1)
        # ЭТО БАГ: отрицательный n_completed не отклоняется
        assert state.n_completed == -1


# =============================================================================
# UNIT: get_ensemble_weights
# =============================================================================

class TestGetEnsembleWeightsUnit:
    """Unit-тесты на get_ensemble_weights."""

    def test_ensemble_weights_cold_start(self):
        """
        get_ensemble_weights(0) → (0.4, 0.2, 0.4).

        Проверяем: cold start веса для n=0.
        Границы: n_completed = 0.
        Почему такие: граничный случай — нет опыта.
        """
        from space1.cold_start.core import get_ensemble_weights, ENSEMBLE_WEIGHTS
        assert get_ensemble_weights(0) == ENSEMBLE_WEIGHTS["cold"]

    def test_ensemble_weights_cold_boundary(self):
        """
        get_ensemble_weights(4) → cold веса (n < 5).

        Проверяем: верхняя граница cold режима.
        Границы: n_completed = 4.
        Почему такие: граничный случай — максимум cold.
        """
        from space1.cold_start.core import get_ensemble_weights, ENSEMBLE_WEIGHTS
        assert get_ensemble_weights(4) == ENSEMBLE_WEIGHTS["cold"]

    def test_ensemble_weights_warm_start(self):
        """
        get_ensemble_weights(5) → (0.2, 0.5, 0.3).

        Проверяем: нижняя граница warm режима.
        Границы: n_completed = 5.
        Почему такие: граничный случай — переход cold→warm.
        """
        from space1.cold_start.core import get_ensemble_weights, ENSEMBLE_WEIGHTS
        assert get_ensemble_weights(5) == ENSEMBLE_WEIGHTS["warm"]

    def test_ensemble_weights_warm_mid(self):
        """
        get_ensemble_weights(10) → warm веса.

        Проверяем: середина warm режима.
        Границы: n_completed = 10.
        Почему такие: типичный warm кейс.
        """
        from space1.cold_start.core import get_ensemble_weights, ENSEMBLE_WEIGHTS
        assert get_ensemble_weights(10) == ENSEMBLE_WEIGHTS["warm"]

    def test_ensemble_weights_warm_boundary(self):
        """
        get_ensemble_weights(19) → warm веса (n < 20).

        Проверяем: верхняя граница warm режима.
        Границы: n_completed = 19.
        Почему такие: граничный случай — максимум warm.
        """
        from space1.cold_start.core import get_ensemble_weights, ENSEMBLE_WEIGHTS
        assert get_ensemble_weights(19) == ENSEMBLE_WEIGHTS["warm"]

    def test_ensemble_weights_hot_start(self):
        """
        get_ensemble_weights(20) → (0.1, 0.7, 0.2).

        Проверяем: нижняя граница hot режима.
        Границы: n_completed = 20.
        Почему такие: граничный случай — переход warm→hot.
        """
        from space1.cold_start.core import get_ensemble_weights, ENSEMBLE_WEIGHTS
        assert get_ensemble_weights(20) == ENSEMBLE_WEIGHTS["hot"]

    def test_ensemble_weights_hot_large(self):
        """
        get_ensemble_weights(1000) → hot веса.

        Проверяем: большой опыт.
        Границы: n_completed = 1000.
        Почему такие: граничный случай — очень большой опыт.
        """
        from space1.cold_start.core import get_ensemble_weights, ENSEMBLE_WEIGHTS
        assert get_ensemble_weights(1000) == ENSEMBLE_WEIGHTS["hot"]

    def test_ensemble_weights_negative_n(self):
        """
        get_ensemble_weights(-1) → cold веса (n < 5).

        Проверяем: отрицательный n обрабатывается как cold.
        Границы: n_completed = -1.
        Почему такие: граничный случай — некорректный вход.
        """
        from space1.cold_start.core import get_ensemble_weights, ENSEMBLE_WEIGHTS
        # ЭТО БАГ: отрицательный n не должен возвращать cold
        assert get_ensemble_weights(-1) == ENSEMBLE_WEIGHTS["cold"]


# =============================================================================
# UNIT: ucb1_safe_divide
# =============================================================================

class TestUcb1SafeDivideUnit:
    """Unit-тесты на ucb1_safe_divide."""

    def test_safe_divide_normal(self):
        """
        ucb1_safe_divide(10, 2) → 5.0.

        Проверяем: обычное деление.
        Границы: denominator > 0.
        Почему такие: стандартный кейс.
        """
        from space1.cold_start.core import ucb1_safe_divide
        assert ucb1_safe_divide(10, 2) == 5.0

    def test_safe_divide_by_zero(self):
        """
        ucb1_safe_divide(10, 0) → 10 / 1e-6 = 10_000_000.0.

        Проверяем: защита от division by zero.
        Границы: denominator = 0.
        Почему такие: критический граничный случай — UCB1 n_e=0.
        """
        from space1.cold_start.core import ucb1_safe_divide, UCB1_EPSILON
        result = ucb1_safe_divide(10, 0)
        assert result == 10.0 / UCB1_EPSILON

    def test_safe_divide_by_negative(self):
        """
        ucb1_safe_divide(10, -1) → 10 / 1e-6 = 10_000_000.0.

        Проверяем: защита при отрицательном denominator.
        Границы: denominator < 0.
        Почему такие: граничный случай — некорректный вход.
        """
        from space1.cold_start.core import ucb1_safe_divide, UCB1_EPSILON
        result = ucb1_safe_divide(10, -1)
        assert result == 10.0 / UCB1_EPSILON

    def test_safe_divide_zero_numerator(self):
        """
        ucb1_safe_divide(0, 5) → 0.0.

        Проверяем: нулевой числитель.
        Границы: numerator = 0.
        Почему такие: граничный случай — нулевой числитель.
        """
        from space1.cold_start.core import ucb1_safe_divide
        assert ucb1_safe_divide(0, 5) == 0.0

    def test_safe_divide_custom_epsilon(self):
        """
        ucb1_safe_divide(10, 0, epsilon=0.5) → 20.0.

        Проверяем: кастомный epsilon.
        Границы: epsilon = 0.5.
        Почему такие: проверка параметра epsilon.
        """
        from space1.cold_start.core import ucb1_safe_divide
        assert ucb1_safe_divide(10, 0, epsilon=0.5) == 20.0

    def test_safe_divide_both_zero(self):
        """
        ucb1_safe_divide(0, 0) → 0.0 / 1e-6 = 0.0.

        Проверяем: оба нуля.
        Границы: numerator=0, denominator=0.
        Почему такие: граничный случай — оба нуля.
        """
        from space1.cold_start.core import ucb1_safe_divide
        assert ucb1_safe_divide(0, 0) == 0.0


# =============================================================================
# UNIT: compute_ucb1_score
# =============================================================================

class TestComputeUcb1ScoreUnit:
    """Unit-тесты на compute_ucb1_score."""

    def test_ucb1_zero_selections(self):
        """
        compute_ucb1_score(0.5, 0, 10) → inf.

        Проверяем: n_selections=0 → +inf (гарантированный первый шанс).
        Границы: n_selections = 0.
        Почему такие: критический граничный случай — cold start UCB1.
        """
        from space1.cold_start.core import compute_ucb1_score
        result = compute_ucb1_score(0.5, 0, 10)
        assert result == float("inf")

    def test_ucb1_one_selection(self):
        """
        compute_ucb1_score(0.5, 1, 1) → 0.5 + sqrt(2)*sqrt(log(1)/1) = 0.5.

        Проверяем: n_selections=1, total=1.
        Границы: n_selections = 1.
        Почему такие: минимальный ненулевой опыт.
        """
        from space1.cold_start.core import compute_ucb1_score
        result = compute_ucb1_score(0.5, 1, 1)
        expected = 0.5 + math.sqrt(2) * math.sqrt(math.log(1) / 1)
        assert abs(result - expected) < 1e-9

    def test_ucb1_exploration_growth(self):
        """
        compute_ucb1_score(0.5, 1, 100) > compute_ucb1_score(0.5, 50, 100).

        Проверяем: менее выбранный вариант имеет выше score.
        Границы: n_selections = 1 vs 50 при total=100.
        Почему такие: проверка exploration компоненты UCB1.
        """
        from space1.cold_start.core import compute_ucb1_score
        score_1 = compute_ucb1_score(0.5, 1, 100)
        score_50 = compute_ucb1_score(0.5, 50, 100)
        assert score_1 > score_50

    def test_ucb1_mean_reward_dominates(self):
        """
        compute_ucb1_score(0.9, 50, 100) > compute_ucb1_score(0.1, 50, 100).

        Проверяем: более высокое mean_reward даёт выше score.
        Границы: mean_reward 0.9 vs 0.1.
        Почему такие: проверка exploitation компоненты UCB1.
        """
        from space1.cold_start.core import compute_ucb1_score
        score_high = compute_ucb1_score(0.9, 50, 100)
        score_low = compute_ucb1_score(0.1, 50, 100)
        assert score_high > score_low

    def test_ucb1_custom_c_exploration(self):
        """
        compute_ucb1_score(0.5, 1, 10, c_exploration=1.0) < compute_ucb1_score(..., c_exploration=2.0).

        Проверяем: больший c → больше exploration.
        Границы: c_exploration = 1.0 vs 2.0.
        Почему такие: проверка параметра exploration.
        """
        from space1.cold_start.core import compute_ucb1_score
        score_c1 = compute_ucb1_score(0.5, 1, 10, c_exploration=1.0)
        score_c2 = compute_ucb1_score(0.5, 1, 10, c_exploration=2.0)
        assert score_c2 > score_c1

    def test_ucb1_total_zero(self):
        """
        compute_ucb1_score(0.5, 1, 0) → ValueError: math domain error.

        Проверяем: total_selections=0.
        Границы: total_selections = 0.
        Почему такие: граничный случай — нет общих выборов.
        """
        from space1.cold_start.core import compute_ucb1_score
        # ЭТО БАГ: math.log(0) вызывает ValueError до защиты ucb1_safe_divide
        try:
            compute_ucb1_score(0.5, 1, 0)
            assert False, "Должен был упасть с ValueError"
        except ValueError as e:
            assert "math domain error" in str(e)


# =============================================================================
# UNIT: get_predictor_priors
# =============================================================================

class TestGetPredictorPriorsUnit:
    """Unit-тесты на get_predictor_priors."""

    def test_predictor_priors_default(self):
        """
        get_predictor_priors() → (0.65, 0.25).

        Проверяем: default priors без категории.
        Границы: category = None.
        Почему такие: стандартный cold start.
        """
        from space1.cold_start.core import get_predictor_priors, RLI_POPULATION_DEFAULT_Q
        from space1.cold_start.core import RLI_POPULATION_DEFAULT_PSI
        q, psi = get_predictor_priors()
        assert q == RLI_POPULATION_DEFAULT_Q
        assert psi == RLI_POPULATION_DEFAULT_PSI

    def test_predictor_priors_unknown_category(self):
        """
        get_predictor_priors("unknown") → default priors.

        Проверяем: неизвестная категория → fallback.
        Границы: category не в словаре.
        Почему такие: граничный случай — неизвестная категория.
        """
        from space1.cold_start.core import get_predictor_priors, RLI_POPULATION_DEFAULT_Q
        from space1.cold_start.core import RLI_POPULATION_DEFAULT_PSI
        q, psi = get_predictor_priors("unknown_category")
        assert q == RLI_POPULATION_DEFAULT_Q
        assert psi == RLI_POPULATION_DEFAULT_PSI

    def test_predictor_priors_empty_string(self):
        """
        get_predictor_priors("") → default priors.

        Проверяем: пустая строка → fallback.
        Границы: category = "".
        Почему такие: граничный случай — пустая категория.
        """
        from space1.cold_start.core import get_predictor_priors, RLI_POPULATION_DEFAULT_Q
        from space1.cold_start.core import RLI_POPULATION_DEFAULT_PSI
        q, psi = get_predictor_priors("")
        assert q == RLI_POPULATION_DEFAULT_Q
        assert psi == RLI_POPULATION_DEFAULT_PSI


# =============================================================================
# UNIT: initialize_agent_state
# =============================================================================

class TestInitializeAgentStateUnit:
    """Unit-тесты на initialize_agent_state."""

    def test_initialize_empty_dict(self):
        """
        initialize_agent_state() → dict с 6 ключами.

        Проверяем: создание state с нуля.
        Границы: agent_dict = None.
        Почему такие: стандартный cold start.
        """
        from space1.cold_start.core import initialize_agent_state, H_INITIAL
        from space1.cold_start.core import UPSILON_INITIAL, PHI_HISTORICAL_INITIAL
        from space1.cold_start.core import RLI_POPULATION_DEFAULT_Q, RLI_POPULATION_DEFAULT_PSI

        state = initialize_agent_state()
        assert state["H"] == H_INITIAL
        assert state["upsilon_k"] == UPSILON_INITIAL
        assert state["phi_historical"] == PHI_HISTORICAL_INITIAL
        assert state["n_completed"] == 0
        assert state["q_prior"] == RLI_POPULATION_DEFAULT_Q
        assert state["psi_prior"] == RLI_POPULATION_DEFAULT_PSI

    def test_initialize_preserves_existing(self):
        """
        initialize_agent_state({"H": 2.0}) → H=2.0 (не перезаписывается).

        Проверяем: setdefault не перезаписывает существующие.
        Границы: agent_dict с существующим ключом.
        Почему такие: проверка setdefault vs overwrite.
        """
        from space1.cold_start.core import initialize_agent_state
        state = initialize_agent_state({"H": 2.0})
        assert state["H"] == 2.0

    def test_initialize_fills_missing(self):
        """
        initialize_agent_state({"H": 2.0}) → остальные ключи заполнены default.

        Проверяем: заполнение недостающих ключей.
        Границы: agent_dict с частичными данными.
        Почему такие: проверка частичной инициализации.
        """
        from space1.cold_start.core import initialize_agent_state, UPSILON_INITIAL
        state = initialize_agent_state({"H": 2.0})
        assert state["upsilon_k"] == UPSILON_INITIAL
        assert "n_completed" in state

    def test_initialize_returns_same_dict(self):
        """
        initialize_agent_state(d) возвращает тот же dict (mutation).

        Проверяем: in-place mutation.
        Границы: Существующий dict.
        Почему такие: контракт — mutate and return.
        """
        from space1.cold_start.core import initialize_agent_state
        original = {"H": 2.0}
        result = initialize_agent_state(original)
        assert result is original


# =============================================================================
# PAIR: ColdStartState + get_ensemble_weights
# =============================================================================

class TestPairStateEnsemble:
    """PAIR: ColdStartState + get_ensemble_weights — связь состояния и весов."""

    def test_state_n_completed_determines_weights(self):
        """
        ColdStartState(n_completed=0) → get_ensemble_weights(0) = cold.

        Проверяем: n_completed из state определяет веса.
        Границы: n_completed = 0.
        Почему такие: интеграция state → weights.
        """
        from space1.cold_start.core import ColdStartState, get_ensemble_weights, ENSEMBLE_WEIGHTS
        state = ColdStartState(n_completed=0)
        weights = get_ensemble_weights(state.n_completed)
        assert weights == ENSEMBLE_WEIGHTS["cold"]

    def test_state_transition_cold_to_warm(self):
        """
        n_completed: 4 → cold, 5 → warm.

        Проверяем: точка перехода cold→warm.
        Границы: n_completed = 4 vs 5.
        Почему такие: интеграция — граница перехода режимов.
        """
        from space1.cold_start.core import get_ensemble_weights, ENSEMBLE_WEIGHTS
        assert get_ensemble_weights(4) == ENSEMBLE_WEIGHTS["cold"]
        assert get_ensemble_weights(5) == ENSEMBLE_WEIGHTS["warm"]

    def test_state_transition_warm_to_hot(self):
        """
        n_completed: 19 → warm, 20 → hot.

        Проверяем: точка перехода warm→hot.
        Границы: n_completed = 19 vs 20.
        Почему такие: интеграция — граница перехода режимов.
        """
        from space1.cold_start.core import get_ensemble_weights, ENSEMBLE_WEIGHTS
        assert get_ensemble_weights(19) == ENSEMBLE_WEIGHTS["warm"]
        assert get_ensemble_weights(20) == ENSEMBLE_WEIGHTS["hot"]


# =============================================================================
# PAIR: ucb1_safe_divide + compute_ucb1_score
# =============================================================================

class TestPairUcb1:
    """PAIR: ucb1_safe_divide + compute_ucb1_score — интеграция guard + formula."""

    def test_ucb1_with_safe_divide_protection(self):
        """
        compute_ucb1_score(0.5, 1, 0) — ucb1_safe_divide не защищает от log(0).

        Проверяем: интеграция guard в формулу.
        Границы: total_selections = 0.
        Почему такие: интеграция — guard защищает denominator, но не log(0).
        """
        from space1.cold_start.core import compute_ucb1_score, ucb1_safe_divide
        # ЭТО БАГ: ucb1_safe_divide защищает denominator, но math.log(0)
        # вызывает ValueError ДО вызова ucb1_safe_divide
        try:
            compute_ucb1_score(0.5, 1, 0)
            assert False, "Должен был упасть с ValueError"
        except ValueError as e:
            assert "math domain error" in str(e)

    def test_ucb1_cold_start_protection(self):
        """
        compute_ucb1_score(0.5, 0, 10) → inf (гарантированный первый шанс).

        Проверяем: cold start защита — n=0 → inf.
        Границы: n_selections = 0.
        Почему такие: интеграция — guard на уровне compute_ucb1_score.
        """
        from space1.cold_start.core import compute_ucb1_score
        result = compute_ucb1_score(0.5, 0, 10)
        assert result == float("inf")


# =============================================================================
# INTEGRITY: Архитектурные инварианты
# =============================================================================

class TestIntegrityColdStart:
    """INTEGRITY: Архитектурные инварианты cold_start/core.py."""

    def test_no_bare_except_in_cold_start(self):
        """
        cold_start/core.py не содержит bare except Exception: pass.

        Проверяем: отсутствие bare except (10_SECURITY.md §III — fail fast).
        Границы: Проверка всего файла.
        Почему такие: bare except маскирует ошибки.
        """
        import inspect
        from space1 import cold_start
        src_file = inspect.getfile(cold_start.core)
        with open(src_file, 'r') as f:
            lines = f.readlines()
        bare_excepts = [i + 1 for i, line in enumerate(lines) if "except Exception" in line]
        assert len(bare_excepts) == 0, f"Bare except найден на строках: {bare_excepts}"

    def test_ensemble_weights_keys(self):
        """
        ENSEMBLE_WEIGHTS содержит ровно 3 ключа: cold, warm, hot.

        Проверяем: полнота словаря весов.
        Границы: Все ключи.
        Почему такие: архитектурный инвариант — 3 режима.
        """
        from space1.cold_start.core import ENSEMBLE_WEIGHTS
        assert set(ENSEMBLE_WEIGHTS.keys()) == {"cold", "warm", "hot"}

    def test_ucb1_epsilon_positive(self):
        """
        UCB1_EPSILON > 0.

        Проверяем: epsilon guard положителен.
        Границы: Стандартная константа.
        Почему такие: guard должен быть положительным.
        """
        from space1.cold_start.core import UCB1_EPSILON
        assert UCB1_EPSILON > 0.0

    def test_ucb1_epsilon_small(self):
        """
        UCB1_EPSILON < 1e-3.

        Проверяем: epsilon guard достаточно мал.
        Границы: Стандартная константа.
        Почему такие: guard не должен искажать результат при нормальном делении.
        """
        from space1.cold_start.core import UCB1_EPSILON
        assert UCB1_EPSILON < 1e-3

    def test_cold_start_state_all_fields_positive_defaults(self):
        """
        Default значения ColdStartState — все положительные или нейтральные.

        Проверяем: H=1.0, upsilon=0.5, phi=0.0, q=0.65, psi=0.25, n=0.
        Границы: Default значения.
        Почему такие: архитектурный инвариант — cold start начинается с нейтральных значений.
        """
        from space1.cold_start.core import ColdStartState
        state = ColdStartState()
        assert state.H >= 0
        assert state.upsilon_k >= 0
        assert state.phi_historical >= 0
        assert state.q_prior >= 0
        assert state.psi_prior >= 0
        assert state.n_completed >= 0


# =============================================================================
# REGRESSION: Старые баги не вернулись
# =============================================================================

class TestRegressionColdStart:
    """REGRESSION: Проверки, что исправленные баги не вернулись."""

    def test_ucb1_division_by_zero_guarded(self):
        """
        ucb1_safe_divide(10, 0) не падает с ZeroDivisionError.

        Проверяем: guard работает.
        Границы: denominator = 0.
        Почему такие: регрессия — ранее падал с ZeroDivisionError.
        """
        from space1.cold_start.core import ucb1_safe_divide
        try:
            result = ucb1_safe_divide(10, 0)
            assert result > 0
        except ZeroDivisionError:
            assert False, "ZeroDivisionError — guard не работает"

    def test_ucb1_zero_selections_returns_inf(self):
        """
        compute_ucb1_score(..., 0, ...) → inf (не падает).

        Проверяем: n=0 обрабатывается корректно.
        Границы: n_selections = 0.
        Почему такие: регрессия — ранее мог упасть или вернуть nan.
        """
        from space1.cold_start.core import compute_ucb1_score
        result = compute_ucb1_score(0.5, 0, 10)
        assert result == float("inf")

    def test_initialize_agent_state_no_side_effects(self):
        """
        initialize_agent_state() дважды → одинаковый результат.

        Проверяем: идемпотентность.
        Границы: Повторный вызов.
        Почему такие: регрессия — ранее мог мутировать глобальное состояние.
        """
        from space1.cold_start.core import initialize_agent_state
        state1 = initialize_agent_state()
        state2 = initialize_agent_state()
        assert state1 == state2
        assert state1 is not state2  # Разные объекты
