"""Тесты [HIGH-06]: KalmanFilter класс."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from space1.utility import KalmanFilter, update_phi_historical

def test_kalman_converges():
    kf = KalmanFilter(initial_state=0.0, Q=0.01, R=0.1)
    for _ in range(100):
        kf.step(5.0)
    assert 4.5 < kf.x < 5.5

def test_kalman_gain_auto():
    kf = KalmanFilter(Q=0.01, R=0.1)
    kf.step(1.0)
    assert 0.0 < kf.P < 1.0  # P decreases after update

def test_backward_compatible():
    assert update_phi_historical(1.0, 2.0, 0.5) == 1.5
