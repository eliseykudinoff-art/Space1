"""Cold-start parameters — defaults from HOMEOSTASIS_FINAL_INDEX."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, Any

@dataclass
class HomeostasisConfig:
    S_max: float = 1.0
    G_max: float = 1.0
    S0: float = 0.08
    G0: float = 0.10
    lambda_S: float = 0.12
    lambda_G: float = 0.18
    b: float = 0.035
    tau_0: float = 10.0
    alpha_S: float = 0.50
    alpha_D: float = 0.45
    alpha_def: float = 0.30
    theta_rev: float = 0.28
    theta_break: float = 0.75
    theta_urgent: float = 0.45
    S_mid: float = 0.35
    G_mid: float = 0.20
    S_soft: float = 0.40
    w_resource: float = 0.25
    w_progress: float = 0.25
    w_idle: float = 0.50
    D_ref: float = 1.0
    alpha_L: float = 0.10
    beta_S: float = 0.50
    beta_D: float = 0.30
    beta_f: float = 0.20
    kappa_L: float = 0.35
    rho0: float = 1.0
    rho_min: float = 0.85
    rho_max: float = 1.60
    K_slow: int = 5
    c_def: float = 0.15
    S_def_max: float = 0.50
    amplitude_overrides: Dict[str, tuple] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "HomeostasisConfig":
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore
        return cls(**{k: v for k, v in d.items() if k in known})

def default_config() -> HomeostasisConfig:
    return HomeostasisConfig()
