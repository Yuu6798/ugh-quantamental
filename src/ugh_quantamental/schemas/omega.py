"""Schema model for Omega contracts."""

from pydantic import BaseModel, ConfigDict, Field

from ugh_quantamental.schemas.market_svp import MarketSVP
from ugh_quantamental.schemas.ssv import QuestionLedger


class EvidenceLineageRecord(BaseModel):
    """Traceable origin metadata for an observed evidence item."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str = Field(min_length=1)
    observed_at: str = Field(min_length=1)
    source_type: str = Field(min_length=1)


class BlockObservability(BaseModel):
    """Per-block observability/confidence values for Q/F/T/P/R/X."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    q: float = Field(ge=0.0, le=1.0)
    f: float = Field(ge=0.0, le=1.0)
    t: float = Field(ge=0.0, le=1.0)
    p: float = Field(ge=0.0, le=1.0)
    r: float = Field(ge=0.0, le=1.0)
    x: float = Field(ge=0.0, le=1.0)


class Omega(BaseModel):
    """Observation quality envelope for the SSV assembly process."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    omega_id: str = Field(min_length=1)
    market_svp: MarketSVP
    question_ledger: QuestionLedger
    evidence_lineage: list[EvidenceLineageRecord] = Field(min_length=1)
    block_confidence: BlockObservability
    block_observability: BlockObservability
    confidence: float = Field(ge=0.0, le=1.0)
