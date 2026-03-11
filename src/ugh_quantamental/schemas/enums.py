"""Enumerations for the market/SSV schema contracts."""

from enum import Enum


class MarketRegime(str, Enum):
    """Top-level risk posture regime label."""

    risk_on = "risk_on"
    neutral = "neutral"
    risk_off = "risk_off"


class MacroCycleRegime(str, Enum):
    """Macro-cycle taxonomy carried in regime-layer payloads."""

    expansion = "expansion"
    slowdown = "slowdown"
    contraction = "contraction"
    recovery = "recovery"
    reflation = "reflation"
    stagflation = "stagflation"


class LifecycleState(str, Enum):
    """Canonical six-state lifecycle taxonomy for the state vector."""

    dormant = "dormant"
    setup = "setup"
    fire = "fire"
    expansion = "expansion"
    exhaustion = "exhaustion"
    failure = "failure"


class QuestionDirection(str, Enum):
    """Expected directional interpretation for a question."""

    positive = "positive"
    negative = "negative"
    neutral = "neutral"
