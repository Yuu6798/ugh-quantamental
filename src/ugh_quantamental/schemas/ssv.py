"""Schema models for SSV blocks and snapshots."""

from pydantic import BaseModel, ConfigDict, Field

from ugh_quantamental.schemas.enums import MacroCycleRegime, MarketRegime, QuestionDirection
from ugh_quantamental.schemas.market_svp import Phi


class QuestionRecord(BaseModel):
    """Single question contract entry."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    question_id: str = Field(min_length=1)
    direction: QuestionDirection
    score: float = Field(ge=-1.0, le=1.0)
    weight: float = Field(ge=0.0, le=1.0)


class QuestionLedger(BaseModel):
    """Normalized question ledger used in blocks and Omega."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    as_of: str = Field(min_length=1)
    questions: list[QuestionRecord] = Field(min_length=1)
    coverage_ratio: float = Field(ge=0.0, le=1.0)


class QBlock(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    ledger: QuestionLedger


class FBlock(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    factor_count: int = Field(ge=0)
    aggregate_signal: float = Field(ge=-1.0, le=1.0)


class TBlock(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    timestamp: str = Field(min_length=1)
    lookback_days: int = Field(ge=1)


class PBlock(BaseModel):
    """Price-implied payload (not lifecycle state probabilities)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    implied_move_30d: float
    implied_volatility: float = Field(ge=0.0)
    skew_25d: float


class RBlock(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    market_regime: MarketRegime
    macro_cycle_regime: MacroCycleRegime
    conviction: float = Field(ge=0.0, le=1.0)


class XBlock(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    tags: list[str] = Field(default_factory=list)
    notes: str = ""


class SSVSnapshot(BaseModel):
    """Composed SSV snapshot container."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    snapshot_id: str = Field(min_length=1)
    q: QBlock
    f: FBlock
    t: TBlock
    p: PBlock
    phi: Phi
    r: RBlock
    x: XBlock
