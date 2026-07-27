"""Tests for Cold-start initial values — 02_MATHEMATICAL_CORE.md Часть X."""

import pytest
from space1.cold_start import (
    H_INITIAL, UPSILON_INITIAL, PHI_HISTORICAL_INITIAL,
    RLI_POPULATION_DEFAULT_Q, RLI_POPULATION_DEFAULT_PSI,
    initialize_agent_state, get_ensemble_weights, compute_ucb1_score,
    get_predictor_priors, ColdStartState,
)


def test_initial_constants():
    assert H_INITIAL == 1.0
    assert UPSILON_INITIAL == 0.5
    assert PHI_HISTORICAL_INITIAL == 0.0


def test_cold_start_state_defaults():
    cs = ColdStartState()
    assert cs.H == 1.0
    assert cs.upsilon_k == 0.5
    assert cs.n_completed == 0


def test_initialize_agent_state():
    state = initialize_agent_state()
    assert state["H"] == 1.0
    assert state["upsilon_k"] == 0.5
    assert state["phi_historical"] == 0.0
    assert state["n_completed"] == 0


def test_ensemble_weights_cold():
    w = get_ensemble_weights(0)
    assert w == (0.4, 0.2, 0.4)


def test_ensemble_weights_warm():
    w = get_ensemble_weights(10)
    assert w == (0.2, 0.5, 0.3)


def test_ensemble_weights_hot():
    w = get_ensemble_weights(25)
    assert w == (0.1, 0.7, 0.2)


def test_ucb1_cold_start_inf():
    score = compute_ucb1_score(0.5, 0, 100)
    assert score == float("inf")


def test_ucb1_normal():
    score = compute_ucb1_score(0.5, 5, 100)
    assert score > 0.5


def test_predictor_priors_default():
    q, psi = get_predictor_priors()
    assert q == RLI_POPULATION_DEFAULT_Q
    assert psi == RLI_POPULATION_DEFAULT_PSI
