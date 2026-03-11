# UGH Market SSV v1 — Formal Spec Snapshot

## Purpose
This document freezes the v1 data contracts for the UGH market stack as schema-only interfaces.

## Layer split

### 1) MSVP (Market-SVP)
Represents a deterministic market state vector primitive:
- top-level risk posture regime (`risk_on` / `neutral` / `risk_off`)
- lifecycle state probability envelope (`Phi`)

### 2) Omega
Represents observation quality for the assembled view:
- evidence lineage metadata
- block-wise confidence values for `Q/F/T/P/R/X`
- block-wise observability weights for `Q/F/T/P/R/X`

### 3) SSV
Represents a composed snapshot made of explicit blocks:
- `QBlock`: question ledger payload
- `FBlock`: factor summary payload
- `TBlock`: timing/lookback payload
- `PBlock`: price-implied payload
- `RBlock`: regime payload
- `XBlock`: extension metadata payload
- `phi`: lifecycle state probabilities

### 4) Projection
Represents output contracts for projected values and confidence bounds, without defining projection math.

## Core state definitions
v1 fixes six mutually exclusive **lifecycle** states:

1. `dormant`
2. `setup`
3. `fire`
4. `expansion`
5. `exhaustion`
6. `failure`

The lifecycle probability vector is valid only when:
- each state probability is in `[0, 1]`
- the total sums to `1.0` within a small numeric tolerance

## Regime taxonomy
The macro-cycle taxonomy is retained but explicitly placed in the regime layer (`RBlock`):
- `expansion`
- `slowdown`
- `contraction`
- `recovery`
- `reflation`
- `stagflation`

This taxonomy is not the lifecycle state-probability vector.

## What is frozen in v1
- Enum contracts for:
  - market regime
  - macro-cycle regime
  - lifecycle state
  - question direction
- Data contracts for:
  - `MarketSVP` and `Phi`
  - `QuestionLedger`
  - `Omega` (with evidence lineage + block-wise confidence/observability)
  - `QBlock`, `FBlock`, `TBlock`, `PBlock`, `RBlock`, `XBlock`
  - `StateProbabilities`
  - `SSVSnapshot`
  - `ProjectionSnapshot`
- Field-level bounds for deterministic invariants (probabilities/confidence in `[0,1]`, non-negative counts, positive horizons, valid bound ordering).

## Intentionally deferred
The following are out-of-scope in v1:
- projection math / model equations
- state-transition dynamics
- persistence/database models
- migration logic
- runtime connectors/CLI/notebooks
- optimization and calibration procedures

v1 remains a formal interface freeze for validation and contract consistency.
