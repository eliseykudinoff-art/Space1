"""Tests for Client Psychometrics — 06_EXTERNAL_ENVIRONMENT.md §I.2, 02_MATHEMATICAL_CORE.md §IV.4."""

import pytest
from space1.client_psychometrics import compute_ccrs, risk_premium, RiskZone, payment_terms_from_ccrs


def test_risk_premium_all_flags():
    rp = risk_premium(
        task_description="short",
        category_median_hours=100.0,
        agent_has_history_with_client=False,
        agent_has_skill_in_domain=False,
        has_milestones=False,
        is_fixed_price=True,
        deadline_hours=1.0,
    )
    assert 0.0 <= rp <= 0.5
    assert rp > 0.3  # Most flags active


def test_risk_premium_no_flags():
    rp = risk_premium(
        task_description="This is a very detailed task description with many words and clear requirements that span multiple sentences",
        category_median_hours=8.0,
        agent_has_history_with_client=True,
        agent_has_skill_in_domain=True,
        has_milestones=True,
        is_fixed_price=False,
        deadline_hours=100.0,
    )
    assert rp == 0.0


def test_ccrs_green_zone():
    profile = compute_ccrs("Standard task, clear requirements, fair payment terms")
    assert profile.zone == RiskZone.GREEN
    assert profile.ccrs < 0.3


def test_ccrs_red_zone():
    """Test that high-risk keywords result in elevated CCRS and ORANGE/RED zone."""
    text = ("Urgent cheap test task free exposure unlimited revisions "
            "daily call hourly update must be online no upfront payment")
    profile = compute_ccrs(text)
    # CCRS >= 0.6 indicates ORANGE/RED zone with elevated risk premium
    assert profile.zone in (RiskZone.ORANGE, RiskZone.RED)
    assert profile.ccrs >= 0.6


def test_ccrs_components_present():
    profile = compute_ccrs("Some task")
    assert 0.0 <= profile.scope_creep <= 1.0
    assert 0.0 <= profile.micromanage <= 1.0
    assert 0.0 <= profile.payment_risk <= 1.0
    assert 0.0 <= profile.unrealistic <= 1.0
    assert 0.0 <= profile.comm_friction <= 1.0


def test_payment_terms_yellow():
    terms = payment_terms_from_ccrs(0.4)
    assert terms["milestone_required"] is True
    assert terms["premium_pct"] == 15


def test_payment_terms_orange():
    terms = payment_terms_from_ccrs(0.7)
    assert terms["milestone_required"] is True
    assert terms["premium_pct"] == 30


def test_payment_terms_red():
    terms = payment_terms_from_ccrs(0.9)
    assert terms["escrow_required"] is True
    assert terms["premium_pct"] == 50
