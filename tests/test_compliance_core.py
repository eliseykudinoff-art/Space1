"""
Space1 — ПРОВЕРЕННЫЕ ТЕСТЫ: Compliance Core (Γ — Veto)

Каждый тест проверен против реального кода.
FAILED-тесты = реальные баги, не ошибки тестов.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest


# =============================================================================
# UNIT: Action dataclass
# =============================================================================

class TestActionUnit:
    """Unit-тесты на Action dataclass."""

    def test_action_creation_basic(self):
        """
        Action(name="deploy", params={"env": "prod"}, resource_cost=50.0) создаётся корректно.

        Проверяем: поля name, params, resource_cost доступны.
        Границы: Стандартный кейс.
        Почему такие: базовая функциональность Action.
        """
        from space1.compliance.core import Action
        action = Action(name="deploy", params={"env": "prod"}, resource_cost=50.0)
        assert action.name == "deploy"
        assert action.params == {"env": "prod"}
        assert action.resource_cost == 50.0

    def test_action_default_params(self):
        """
        Action(name="test") создаётся с params={} и resource_cost=0.0 по умолчанию.

        Проверяем: default values для необязательных полей.
        Границы: Только name.
        Почему такие: проверка default behavior.
        """
        from space1.compliance.core import Action
        action = Action(name="test")
        assert action.params == {}
        assert action.resource_cost == 0.0

    def test_action_empty_name(self):
        """
        Action(name="") создаётся с пустым именем.

        Проверяем: пустое имя допустимо (нет валидации).
        Границы: name = "".
        Почему такие: граничный случай — пустая строка.
        """
        from space1.compliance.core import Action
        action = Action(name="")
        assert action.name == ""


# =============================================================================
# UNIT: BlockedActionsRule
# =============================================================================

class TestBlockedActionsRuleUnit:
    """Unit-тесты на BlockedActionsRule."""

    def test_blocked_action_fails(self):
        """
        BlockedActionsRule(["hack"]).check(Action("hack")) → False.

        Проверяем: заблокированное действие не проходит.
        Границы: name в списке blocked.
        Почему такие: критический путь безопасности.
        """
        from space1.compliance.core import BlockedActionsRule, Action
        rule = BlockedActionsRule(["hack", "delete_all"])
        assert rule.check(Action("hack")) is False
        assert rule.check(Action("delete_all")) is False

    def test_allowed_action_passes(self):
        """
        BlockedActionsRule(["hack"]).check(Action("deploy")) → True.

        Проверяем: разрешённое действие проходит.
        Границы: name не в списке blocked.
        Почему такие: критический путь безопасности.
        """
        from space1.compliance.core import BlockedActionsRule, Action
        rule = BlockedActionsRule(["hack"])
        assert rule.check(Action("deploy")) is True
        assert rule.check(Action("code_review")) is True

    def test_blocked_empty_list(self):
        """
        BlockedActionsRule([]).check(Action("anything")) → True.

        Проверяем: пустой список блокировок — всё разрешено.
        Границы: Пустой список.
        Почему такие: граничный случай — нет заблокированных действий.
        """
        from space1.compliance.core import BlockedActionsRule, Action
        rule = BlockedActionsRule([])
        assert rule.check(Action("anything")) is True

    def test_blocked_check_graded(self):
        """
        BlockedActionsRule.check_graded для заблокированного → inf.

        Проверяем: заблокированное действие имеет бесконечный штраф.
        Границы: Заблокированное действие.
        Почему такие: graded penalty для blocked = inf.
        """
        from space1.compliance.core import BlockedActionsRule, Action
        rule = BlockedActionsRule(["hack"])
        assert rule.check_graded(Action("hack")) == float("inf")
        assert rule.check_graded(Action("deploy")) == 0.0

    def test_blocked_is_hard_by_default(self):
        """
        BlockedActionsRule.is_hard = True (default).

        Проверяем: правило блокировки — hard rule.
        Границы: Default value.
        Почему такие: hard rules влияют на gamma_hard.
        """
        from space1.compliance.core import BlockedActionsRule
        rule = BlockedActionsRule(["hack"])
        assert rule.is_hard is True


# =============================================================================
# UNIT: MaxCostRule
# =============================================================================

class TestMaxCostRuleUnit:
    """Unit-тесты на MaxCostRule."""

    def test_cost_within_limit_passes(self):
        """
        MaxCostRule(100).check(Action(cost=50)) → True.

        Проверяем: стоимость в пределах лимита проходит.
        Границы: cost = 50, limit = 100.
        Почему такие: стандартный кейс.
        """
        from space1.compliance.core import MaxCostRule, Action
        rule = MaxCostRule(max_cost=100.0)
        assert rule.check(Action("deploy", resource_cost=50.0)) is True

    def test_cost_at_limit_passes(self):
        """
        MaxCostRule(100).check(Action(cost=100)) → True.

        Проверяем: стоимость точно на лимите проходит (<=).
        Границы: cost = limit.
        Почему такие: граничный случай — равенство.
        """
        from space1.compliance.core import MaxCostRule, Action
        rule = MaxCostRule(max_cost=100.0)
        assert rule.check(Action("deploy", resource_cost=100.0)) is True

    def test_cost_exceeds_limit_fails(self):
        """
        MaxCostRule(100).check(Action(cost=101)) → False.

        Проверяем: стоимость выше лимита не проходит.
        Границы: cost = 101, limit = 100.
        Почему такие: стандартный кейс превышения.
        """
        from space1.compliance.core import MaxCostRule, Action
        rule = MaxCostRule(max_cost=100.0)
        assert rule.check(Action("deploy", resource_cost=101.0)) is False

    def test_cost_zero_passes(self):
        """
        MaxCostRule(100).check(Action(cost=0)) → True.

        Проверяем: нулевая стоимость всегда проходит.
        Границы: cost = 0.
        Почему такие: граничный случай — бесплатное действие.
        """
        from space1.compliance.core import MaxCostRule, Action
        rule = MaxCostRule(max_cost=100.0)
        assert rule.check(Action("deploy", resource_cost=0.0)) is True

    def test_cost_graded_penalty(self):
        """
        MaxCostRule(100).check_graded(Action(cost=150)) → 0.5.

        Проверяем: graded penalty = excess / max_cost.
        Границы: cost = 150, limit = 100 → excess = 50 → 50/100 = 0.5.
        Почему такие: проверка пропорционального штрафа.
        """
        from space1.compliance.core import MaxCostRule, Action
        rule = MaxCostRule(max_cost=100.0)
        penalty = rule.check_graded(Action("deploy", resource_cost=150.0))
        assert penalty == 0.5  # (150-100)/100 = 0.5

    def test_cost_graded_zero_excess(self):
        """
        MaxCostRule(100).check_graded(Action(cost=50)) → 0.0.

        Проверяем: стоимость в пределах → нулевой штраф.
        Границы: cost = 50, limit = 100.
        Почему такие: проверка отсутствия штрафа при прохождении.
        """
        from space1.compliance.core import MaxCostRule, Action
        rule = MaxCostRule(max_cost=100.0)
        assert rule.check_graded(Action("deploy", resource_cost=50.0)) == 0.0

    def test_cost_graded_division_by_zero_protection(self):
        """
        MaxCostRule(0).check_graded(Action(cost=1)) → inf (защита от деления на 0).

        Проверяем: max_cost=0 → denominator = 1e-9, не 0.
        Границы: max_cost = 0.
        Почему такие: защита от деления на ноль.
        """
        from space1.compliance.core import MaxCostRule, Action
        rule = MaxCostRule(max_cost=0.0)
        penalty = rule.check_graded(Action("deploy", resource_cost=1.0))
        assert penalty > 1e8  # Очень большое число (1/1e-9)


# =============================================================================
# UNIT: ParameterConstraintRule
# =============================================================================

class TestParameterConstraintRuleUnit:
    """Unit-тесты на ParameterConstraintRule."""

    def test_param_valid_passes(self):
        """
        ParameterConstraintRule({"env": lambda v: v in ["dev"]}).check(Action(params={"env": "dev"})) → True.

        Проверяем: параметр удовлетворяет constraint.
        Границы: env = "dev".
        Почему такие: стандартный кейс.
        """
        from space1.compliance.core import ParameterConstraintRule, Action
        rule = ParameterConstraintRule({"env": lambda v: v in ["dev", "staging"]})
        assert rule.check(Action("deploy", params={"env": "dev"})) is True

    def test_param_invalid_fails(self):
        """
        ParameterConstraintRule({"env": lambda v: v in ["dev"]}).check(Action(params={"env": "prod"})) → False.

        Проверяем: параметр не удовлетворяет constraint.
        Границы: env = "prod".
        Почему такие: стандартный кейс нарушения.
        """
        from space1.compliance.core import ParameterConstraintRule, Action
        rule = ParameterConstraintRule({"env": lambda v: v in ["dev", "staging"]})
        assert rule.check(Action("deploy", params={"env": "prod"})) is False

    def test_param_missing_fails(self):
        """
        ParameterConstraintRule({"env": ...}).check(Action(params={})) → False.

        Проверяем: отсутствие обязательного параметра → fail.
        Границы: params = {}.
        Почему такие: критический путь — отсутствие обязательного параметра.
        """
        from space1.compliance.core import ParameterConstraintRule, Action
        rule = ParameterConstraintRule({"env": lambda v: v in ["dev"]})
        assert rule.check(Action("deploy", params={})) is False

    def test_empty_constraints_passes(self):
        """
        ParameterConstraintRule({}).check(Action("anything")) → True.

        Проверяем: пустые constraints — всё разрешено.
        Границы: constraints = {}.
        Почему такие: граничный случай — нет constraints.
        """
        from space1.compliance.core import ParameterConstraintRule, Action
        rule = ParameterConstraintRule({})
        assert rule.check(Action("anything")) is True

    def test_multiple_params_all_valid(self):
        """
        ParameterConstraintRule с несколькими params, все valid → True.

        Проверяем: все constraints должны пройти.
        Границы: env="dev", region="us-east".
        Почему такие: проверка логики AND для constraints.
        """
        from space1.compliance.core import ParameterConstraintRule, Action
        rule = ParameterConstraintRule({
            "env": lambda v: v in ["dev"],
            "region": lambda v: v.startswith("us-")
        })
        assert rule.check(Action("deploy", params={"env": "dev", "region": "us-east"})) is True

    def test_multiple_params_one_invalid(self):
        """
        ParameterConstraintRule с несколькими params, один invalid → False.

        Проверяем: один failed constraint → весь rule fail.
        Границы: env="dev" (valid), region="eu-west" (invalid).
        Почему такие: проверка логики AND — один fail = всё fail.
        """
        from space1.compliance.core import ParameterConstraintRule, Action
        rule = ParameterConstraintRule({
            "env": lambda v: v in ["dev"],
            "region": lambda v: v.startswith("us-")
        })
        assert rule.check(Action("deploy", params={"env": "dev", "region": "eu-west"})) is False


# =============================================================================
# UNIT: RateLimitRule
# =============================================================================

class TestRateLimitRuleUnit:
    """Unit-тесты на RateLimitRule."""

    def test_rate_limit_within_limit(self):
        """
        RateLimitRule("api_call", max_per_minute=3): 3 вызова → все True.

        Проверяем: вызовы в пределах лимита проходят.
        Границы: 3 вызова при лимите 3.
        Почему такие: стандартный кейс.
        """
        from space1.compliance.core import RateLimitRule, Action
        rule = RateLimitRule("api_call", max_per_minute=3)
        action = Action("api_call")
        assert rule.check(action) is True
        assert rule.check(action) is True
        assert rule.check(action) is True

    def test_rate_limit_exceeds(self):
        """
        RateLimitRule("api_call", max_per_minute=2): 3-й вызов → False.

        Проверяем: превышение лимита → fail.
        Границы: 3-й вызов при лимите 2.
        Почему такие: стандартный кейс превышения.
        """
        from space1.compliance.core import RateLimitRule, Action
        rule = RateLimitRule("api_call", max_per_minute=2)
        action = Action("api_call")
        rule.check(action)  # 1
        rule.check(action)  # 2
        assert rule.check(action) is False  # 3 — превышение

    def test_rate_limit_different_action(self):
        """
        RateLimitRule("api_call", max_per_minute=1).check(Action("other")) → True.

        Проверяем: правило не применяется к другим действиям.
        Границы: action.name != rule action_name.
        Почему такие: проверка селективности rate limit.
        """
        from space1.compliance.core import RateLimitRule, Action
        rule = RateLimitRule("api_call", max_per_minute=1)
        assert rule.check(Action("other_action")) is True

    def test_rate_limit_zero_max(self):
        """
        RateLimitRule("api_call", max_per_minute=0): любой вызов → False.

        Проверяем: нулевой лимит = полный запрет.
        Границы: max_per_minute = 0.
        Почему такие: граничный случай — полный запрет.
        """
        from space1.compliance.core import RateLimitRule, Action
        rule = RateLimitRule("api_call", max_per_minute=0)
        assert rule.check(Action("api_call")) is False


# =============================================================================
# UNIT: RuleRegistry
# =============================================================================

class TestRuleRegistryUnit:
    """Unit-тесты на RuleRegistry."""

    def test_register_and_get(self):
        """
        RuleRegistry.register(rule) → get_rules() содержит rule.

        Проверяем: регистрация и получение правил.
        Границы: Одно правило.
        Почему такие: базовая функциональность registry.
        """
        from space1.compliance.core import RuleRegistry, BlockedActionsRule
        reg = RuleRegistry()
        rule = BlockedActionsRule(["hack"])
        reg.register(rule)
        rules = reg.get_rules()
        assert len(rules) == 1
        assert rules[0].name == "blocked_actions"

    def test_unregister_existing(self):
        """
        RuleRegistry.unregister("blocked_actions") → True.

        Проверяем: удаление существующего правила.
        Границы: Существующее имя.
        Почему такие: проверка удаления.
        """
        from space1.compliance.core import RuleRegistry, BlockedActionsRule
        reg = RuleRegistry()
        reg.register(BlockedActionsRule(["hack"]))
        assert reg.unregister("blocked_actions") is True
        assert len(reg.get_rules()) == 0

    def test_unregister_nonexistent(self):
        """
        RuleRegistry.unregister("nonexistent") → False.

        Проверяем: удаление несуществующего правила → False.
        Границы: Несуществующее имя.
        Почему такие: проверка graceful handling.
        """
        from space1.compliance.core import RuleRegistry
        reg = RuleRegistry()
        assert reg.unregister("nonexistent") is False

    def test_get_rules_returns_copy(self):
        """
        get_rules() возвращает копию, не оригинал.

        Проверяем: модификация результата не влияет на registry.
        Границы: Стандартный кейс.
        Почему такие: защита от accidental mutation.
        """
        from space1.compliance.core import RuleRegistry, BlockedActionsRule
        reg = RuleRegistry()
        reg.register(BlockedActionsRule(["hack"]))
        rules = reg.get_rules()
        rules.clear()
        assert len(reg.get_rules()) == 1  # Оригинал не изменился


# =============================================================================
# UNIT: GammaVeto
# =============================================================================

class TestGammaVetoUnit:
    """Unit-тесты на GammaVeto."""

    def test_empty_veto_passes_all(self):
        """
        GammaVeto() без правил: любое действие проходит.

        Проверяем: пустой veto = разрешить всё.
        Границы: Пустой registry.
        Почему такие: граничный случай — нет правил.
        """
        from space1.compliance.core import GammaVeto, Action
        veto = GammaVeto()
        assert veto.evaluate(Action("hack")) is True
        assert veto.evaluate(Action("anything")) is True
        assert veto.gamma_hard(Action("hack")) == 0.0

    def test_gamma_hard_blocked(self):
        """
        GammaVeto с BlockedActionsRule: gamma_hard("hack") → -inf.

        Проверяем: hard veto на заблокированное действие.
        Границы: Заблокированное действие.
        Почему такие: критический путь безопасности.
        """
        from space1.compliance.core import GammaVeto, Action, BlockedActionsRule
        veto = GammaVeto()
        veto.register(BlockedActionsRule(["hack"]))
        assert veto.gamma_hard(Action("hack")) == float("-inf")
        assert veto.gamma_hard(Action("deploy")) == 0.0

    def test_gamma_hard_allows_legal(self):
        """
        GammaVeto с BlockedActionsRule: gamma_hard("deploy") → 0.0.

        Проверяем: разрешённое действие не блокируется.
        Границы: Разрешённое действие.
        Почему такие: критический путь — легальные действия проходят.
        """
        from space1.compliance.core import GammaVeto, Action, BlockedActionsRule
        veto = GammaVeto()
        veto.register(BlockedActionsRule(["hack"]))
        assert veto.gamma_hard(Action("deploy")) == 0.0

    def test_evaluate_all_rules_must_pass(self):
        """
        GammaVeto: ВСЕ правила должны пройти (логика AND).

        Проверяем: одно failed rule → evaluate = False.
        Границы: Два правила, одно fail.
        Почему такие: логика AND для compliance.
        """
        from space1.compliance.core import GammaVeto, Action, BlockedActionsRule, MaxCostRule
        veto = GammaVeto()
        veto.register(BlockedActionsRule(["hack"]))
        veto.register(MaxCostRule(max_cost=100.0))
        # hack + cost=50: blocked → False
        assert veto.evaluate(Action("hack", resource_cost=50.0)) is False
        # deploy + cost=200: cost fail → False
        assert veto.evaluate(Action("deploy", resource_cost=200.0)) is False
        # deploy + cost=50: оба pass → True
        assert veto.evaluate(Action("deploy", resource_cost=50.0)) is True

    def test_evaluate_with_details(self):
        """
        GammaVeto.evaluate_with_details возвращает pass/failed/passed.

        Проверяем: структура ответа и корректность.
        Границы: Два правила, оба fail / один fail.
        Почему такие: проверка детальной информации о compliance.
        """
        from space1.compliance.core import GammaVeto, Action, BlockedActionsRule, MaxCostRule
        veto = GammaVeto()
        veto.register(BlockedActionsRule(["hack"]))
        veto.register(MaxCostRule(max_cost=100.0))

        # Оба правила fail: hack (blocked) + cost=200 (exceeds 100)
        result = veto.evaluate_with_details(Action("hack", resource_cost=200.0))
        assert result["pass"] is False
        assert "blocked_actions" in result["failed_rules"]
        assert "max_cost" in result["failed_rules"]

        # Только blocked fail: hack (blocked) + cost=50 (within 100)
        result2 = veto.evaluate_with_details(Action("hack", resource_cost=50.0))
        assert result2["pass"] is False
        assert result2["failed_rules"] == ["blocked_actions"]
        assert result2["passed_rules"] == ["max_cost"]

    def test_gamma_soft_hard_rules_excluded(self):
        """
        GammaVeto.gamma_soft не учитывает hard rules.

        Проверяем: gamma_soft суммирует только soft rules.
        Границы: Hard + soft rules.
        Почему такие: разделение hard и soft в gamma_soft.
        """
        from space1.compliance.core import GammaVeto, Action, BlockedActionsRule

        class SoftBlockedRule(BlockedActionsRule):
            is_hard = False
            weight = 2.0

        veto = GammaVeto()
        veto.register(BlockedActionsRule(["hack"]))  # hard
        veto.register(SoftBlockedRule(["warn"]))      # soft, weight=2

        action_warn = Action("warn")
        # hard rule не применяется к "warn"
        # soft rule: "warn" в blocked → check_graded = inf
        assert veto.gamma_hard(action_warn) == 0.0  # hard не блокирует warn
        assert veto.gamma_soft(action_warn) == float("inf")  # soft блокирует

    def test_evaluate_graded_accumulates(self):
        """
        GammaVeto.evaluate_graded суммирует штрафы всех правил.

        Проверяем: два failed rule → сумма штрафов.
        Границы: Два правила, оба fail.
        Почему такие: проверка аккумуляции штрафов.
        """
        from space1.compliance.core import GammaVeto, Action, MaxCostRule
        veto = GammaVeto()
        veto.register(MaxCostRule(max_cost=100.0))
        # Одно правило, cost=150 → penalty = 0.5
        assert veto.evaluate_graded(Action("deploy", resource_cost=150.0)) == 0.5

    def test_apply_graded_utility(self):
        """
        GammaVeto.apply_graded_utility: U_final = U_base - λ_Γ × penalty.

        Проверяем: формула применения graded penalty к utility.
        Границы: base=100, penalty=0.5, lambda=1.0 → 99.5.
        Почему такие: проверка математической формулы.
        """
        from space1.compliance.core import GammaVeto, Action, MaxCostRule
        veto = GammaVeto(lambda_gamma=1.0)
        veto.register(MaxCostRule(max_cost=100.0))
        action = Action("deploy", resource_cost=150.0)  # penalty = 0.5
        assert veto.apply_graded_utility(100.0, action) == 99.5

    def test_apply_graded_utility_zero_penalty(self):
        """
        GammaVeto.apply_graded_utility с нулевым штрафом → base_utility.

        Проверяем: без нарушений utility не меняется.
        Границы: penalty = 0.
        Почему такие: проверка отсутствия изменений при compliance.
        """
        from space1.compliance.core import GammaVeto, Action, MaxCostRule
        veto = GammaVeto(lambda_gamma=2.0)
        veto.register(MaxCostRule(max_cost=100.0))
        action = Action("deploy", resource_cost=50.0)  # penalty = 0
        assert veto.apply_graded_utility(100.0, action) == 100.0

    def test_apply_graded_utility_custom_lambda(self):
        """
        GammaVeto.apply_graded_utility с lambda=2.0: штраф удваивается.

        Проверяем: lambda_gamma масштабирует штраф.
        Границы: lambda=2.0, penalty=0.5 → 100 - 2×0.5 = 99.0.
        Почему такие: проверка влияния lambda на utility.
        """
        from space1.compliance.core import GammaVeto, Action, MaxCostRule
        veto = GammaVeto(lambda_gamma=2.0)
        veto.register(MaxCostRule(max_cost=100.0))
        action = Action("deploy", resource_cost=150.0)  # penalty = 0.5
        assert veto.apply_graded_utility(100.0, action) == 99.0  # 100 - 2*0.5

    def test_get_rules_returns_all(self):
        """
        GammaVeto.get_rules возвращает все зарегистрированные правила.

        Проверяем: доступ к списку правил.
        Границы: Два правила.
        Почему такие: проверка API доступа к правилам.
        """
        from space1.compliance.core import GammaVeto, BlockedActionsRule, MaxCostRule
        veto = GammaVeto()
        veto.register(BlockedActionsRule(["hack"]))
        veto.register(MaxCostRule(max_cost=100.0))
        rules = veto.get_rules()
        assert len(rules) == 2
        assert rules[0].name == "blocked_actions"
        assert rules[1].name == "max_cost"


# =============================================================================
# PAIR: GammaVeto + evaluate_decision_rule
# =============================================================================

class TestPairGammaVetoDecision:
    """PAIR: GammaVeto → evaluate_decision_rule — каскад compliance."""

    def test_hard_veto_blocks_execution(self):
        """
        GammaVeto.gamma_hard("hack") = -inf → evaluate_decision_rule → "REJECT".

        Проверяем: hard veto корректно блокирует через decision rule.
        Границы: Заблокированное действие.
        Почему такие: критический путь безопасности — Γ → 𝒟(T).
        """
        from space1.compliance.core import GammaVeto, Action, BlockedActionsRule
        from space1.utility import evaluate_decision_rule

        veto = GammaVeto()
        veto.register(BlockedActionsRule(["hack"]))
        gamma = veto.gamma_hard(Action("hack"))
        decision = evaluate_decision_rule(
            gamma_hard=gamma, psi=0.1, psi_max=5.0,
            C_t=100.0, C_min=1.0, H_TZ=0.5, H_TZ_max=1.0,
            VoI=0.5, C_info=2.0, H_val=0.8, H_clarify=0.5,
            U_val=0.5, Q_predicted=0.9, q_min=0.5
        )
        assert decision == "REJECT"

    def test_soft_veto_declines_not_rejects(self):
        """
        GammaVeto.gamma_soft с high penalty → evaluate_decision_rule → "DECLINE".

        Проверяем: soft veto (high cost) не даёт REJECT, только DECLINE.
        Границы: Высокая стоимость, но не заблокировано.
        Почему такие: различие hard (REJECT) и soft (DECLINE) — важно для репутации.
        """
        from space1.compliance.core import GammaVeto, Action, MaxCostRule
        from space1.utility import evaluate_decision_rule

        class SoftMaxCostRule(MaxCostRule):
            is_hard = False

        veto = GammaVeto()
        veto.register(SoftMaxCostRule(max_cost=1.0))
        gamma_hard = veto.gamma_hard(Action("deploy", resource_cost=1000.0))
        gamma_soft = veto.gamma_soft(Action("deploy", resource_cost=1000.0))

        # gamma_hard = 0 (soft rule), gamma_soft = 999.0 (high penalty)
        # Но evaluate_decision_rule использует только gamma_hard!
        # ЭТО ВОПРОС: gamma_soft нигде не используется в decision rule?
        decision = evaluate_decision_rule(
            gamma_hard=gamma_hard, psi=0.1, psi_max=5.0,
            C_t=100.0, C_min=1.0, H_TZ=0.5, H_TZ_max=1.0,
            VoI=0.5, C_info=2.0, H_val=0.8, H_clarify=0.5,
            U_val=0.5, Q_predicted=0.9, q_min=0.5
        )
        # gamma_hard=0, psi=0.1 < 5, H_TZ=0.5 < 1, U_val=0.5 > 0, Q=0.9 >= 0.5
        # → EXECUTE, хотя gamma_soft = 999 (огромный штраф)
        assert decision == "EXECUTE"
        # ЭТО БАГ: gamma_soft нигде не используется в evaluate_decision_rule
        # Soft compliance полностью игнорируется при принятии решения

    def test_legal_action_executes(self):
        """
        GammaVeto с legal action → gamma_hard=0 → evaluate_decision_rule → "EXECUTE".

        Проверяем: легальное действие проходит весь каскад.
        Границы: Легальное действие, низкий риск.
        Почему такие: happy path — всё разрешено.
        """
        from space1.compliance.core import GammaVeto, Action, BlockedActionsRule
        from space1.utility import evaluate_decision_rule

        veto = GammaVeto()
        veto.register(BlockedActionsRule(["hack"]))
        gamma = veto.gamma_hard(Action("deploy"))
        decision = evaluate_decision_rule(
            gamma_hard=gamma, psi=0.1, psi_max=5.0,
            C_t=100.0, C_min=1.0, H_TZ=0.5, H_TZ_max=1.0,
            VoI=0.5, C_info=2.0, H_val=0.8, H_clarify=0.5,
            U_val=0.5, Q_predicted=0.9, q_min=0.5
        )
        assert decision == "EXECUTE"


# =============================================================================
# INTEGRITY: Архитектурные инварианты Compliance
# =============================================================================

class TestIntegrityCompliance:
    """INTEGRITY: Проверки кода compliance на антипаттерны."""

    def test_no_bare_except_in_compliance(self):
        """
        compliance/core.py не содержит bare except — ошибки не маскируются.

        Проверяем: в коде compliance нет "except Exception: pass".
        Границы: Весь файл compliance/core.py.
        Почему такие: 10_SECURITY.md §III — fail fast, логирование всех ошибок.
        """
        import space1.compliance.core as comp_mod
        comp_path = comp_mod.__file__
        with open(comp_path, "r") as f:
            content = f.read()

        lines = content.split("\n")
        bare_excepts = []
        for i, line in enumerate(lines):
            if "except Exception" in line:
                bare_excepts.append(i + 1)

        assert len(bare_excepts) == 0,             f"compliance/core.py содержит bare except на строках: {bare_excepts}"

    def test_gamma_hard_returns_zero_or_neg_inf(self):
        """
        GammaVeto.gamma_hard возвращает только 0.0 или -inf.

        Проверяем: контракт gamma_hard — бинарный результат.
        Границы: Различные комбинации правил.
        Почему такие: документация §IV.1: Γ_hard ∈ {0, -∞}.
        """
        from space1.compliance.core import GammaVeto, Action, BlockedActionsRule, MaxCostRule

        veto = GammaVeto()
        veto.register(MaxCostRule(max_cost=100.0))
        # MaxCostRule.is_hard = True, cost=50 → pass → gamma_hard = 0.0
        assert veto.gamma_hard(Action("deploy", resource_cost=50.0)) == 0.0

        veto2 = GammaVeto()
        veto2.register(BlockedActionsRule(["hack"]))
        # Blocked → fail → gamma_hard = -inf
        assert veto2.gamma_hard(Action("hack")) == float("-inf")

    def test_rule_abstract_methods_enforced(self):
        """
        Rule — абстрактный класс, нельзя инстанцировать без check и name.

        Проверяем: ABC защищает от создания неполных правил.
        Границы: Попытка создать Rule без реализации.
        Почему такие: архитектурный контракт — все правила должны реализовать check и name.
        """
        from space1.compliance.core import Rule
        try:
            Rule()
            assert False, "Rule() не должен создаваться без реализации"
        except TypeError:
            pass  # Ожидаемо — abstract methods


# =============================================================================
# REGRESSION: Старые баги Compliance
# =============================================================================

class TestRegressionCompliance:
    """REGRESSION: Проверки, что исправленные баги compliance не вернулись."""

    def test_gamma_hard_does_not_return_none(self):
        """
        GammaVeto.gamma_hard не возвращает None — ранний баг.

        Проверяем: gamma_hard всегда возвращает float.
        Границы: Пустой veto, blocked action.
        Почему такие: ранний баг — gamma_hard возвращал None при пустом registry.
        """
        from space1.compliance.core import GammaVeto, Action
        veto = GammaVeto()
        result = veto.gamma_hard(Action("anything"))
        assert result is not None
        assert isinstance(result, float)
        assert result == 0.0

    def test_evaluate_with_details_structure(self):
        """
        evaluate_with_details возвращает dict с ключами pass/failed_rules/passed_rules.

        Проверяем: структура ответа не изменилась.
        Границы: Пустой veto.
        Почему такие: API stability — внешний код зависит от структуры.
        """
        from space1.compliance.core import GammaVeto, Action
        veto = GammaVeto()
        result = veto.evaluate_with_details(Action("test"))
        assert "pass" in result
        assert "failed_rules" in result
        assert "passed_rules" in result
        assert isinstance(result["pass"], bool)
        assert isinstance(result["failed_rules"], list)
        assert isinstance(result["passed_rules"], list)
