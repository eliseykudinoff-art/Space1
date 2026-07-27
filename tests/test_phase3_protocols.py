"""Tests for Market Protocols — 06_EXTERNAL_ENVIRONMENT.md Часть II."""

import pytest
from space1.market_protocols import (
    ProtocolRegistry, ProtocolState, ProtocolOutcome, ProtocolStep,
    DisputeProtocol, PlatformComplianceProtocol, ClientExitProtocol,
)


def test_registry_has_all_ten_protocols():
    reg = ProtocolRegistry()
    protocols = reg.list_protocols()
    assert len(protocols) == 10
    expected = [
        "dispute", "payment_risk", "platform_compliance",
        "account_suspension", "competitor_dumping",
        "opportunity_arbitration", "client_boundary",
        "reputation_damage", "client_exit", "platform_diversification",
    ]
    for name in expected:
        assert name in protocols


def test_dispute_direct_resolution():
    reg = ProtocolRegistry()
    state = ProtocolState(protocol_name="dispute", step=ProtocolStep.DIRECT_RESOLUTION)
    context = {"resolved_by_recovery": True}
    result = reg.run("dispute", state, context)
    assert result.outcome == ProtocolOutcome.RESOLVED


def test_dispute_escalates_to_mediation():
    from datetime import datetime, timedelta
    reg = ProtocolRegistry()
    state = ProtocolState(protocol_name="dispute", step=ProtocolStep.DIRECT_RESOLUTION)
    context = {
        "resolved_by_recovery": False,
        "dispute_started_at": datetime.now() - timedelta(days=10),
    }
    result = reg.run("dispute", state, context)
    assert result.step == ProtocolStep.PLATFORM_MEDIATION


def test_platform_compliance_hard_rule_violation():
    reg = ProtocolRegistry()
    state = ProtocolState(protocol_name="platform_compliance", step=ProtocolStep.DOCUMENT)
    context = {"used_external_channel": True}
    result = reg.run("platform_compliance", state, context)
    assert result.outcome == ProtocolOutcome.ESCALATE
    assert "violations" in result.metadata


def test_platform_compliance_risk_score():
    reg = ProtocolRegistry()
    state = ProtocolState(protocol_name="platform_compliance", step=ProtocolStep.DOCUMENT)
    context = {
        "used_external_channel": False,
        "consistency_score": 0.3,
        "behavioral_score": 0.2,
        "complaint_rate": 0.5,
        "account_age_days": 10,
    }
    result = reg.run("platform_compliance", state, context)
    assert "platform_risk_score" in result.metadata
    assert result.metadata["platform_risk_score"] > 0.0


def test_client_exit_hard_rule():
    reg = ProtocolRegistry()
    state = ProtocolState(protocol_name="client_exit", step=ProtocolStep.FORMAL_NOTICE)
    context = {"disappeared_without_notice": True}
    result = reg.run("client_exit", state, context)
    assert result.outcome == ProtocolOutcome.ESCALATE
    assert result.metadata["hard_rule_violation"] == "Disappeared without notice"


def test_client_exit_normal():
    reg = ProtocolRegistry()
    state = ProtocolState(protocol_name="client_exit", step=ProtocolStep.FORMAL_NOTICE)
    context = {
        "disappeared_without_notice": False,
        "handover_complete": True,
        "documentation_transferred": True,
        "access_transferred": True,
    }
    result = reg.run("client_exit", state, context)
    assert result.outcome == ProtocolOutcome.RESOLVED


def test_competitor_dumping_differentiate():
    reg = ProtocolRegistry()
    state = ProtocolState(protocol_name="competitor_dumping", step=ProtocolStep.DOCUMENT)
    context = {"competitor_price": 10.0, "my_price": 100.0, "my_quality_score": 0.9}
    result = reg.run("competitor_dumping", state, context)
    assert result.metadata["recommendation"] == "differentiate"


def test_account_suspension_critical_state():
    reg = ProtocolRegistry()
    state = ProtocolState(protocol_name="account_suspension", step=ProtocolStep.DOCUMENT)
    context = {}
    result = reg.run("account_suspension", state, context)
    assert result.metadata["H"] == "CRITICAL"
    assert result.metadata["operational_status"] == "SUSPENDED"
