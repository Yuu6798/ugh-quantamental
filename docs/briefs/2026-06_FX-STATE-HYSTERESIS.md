# Task Brief: FX-STATE-HYSTERESIS - 急変動直後の failure 過剰発火の抑制

## Phase
engine_review_2026_06 §1 ★2 — 着手順序 §2 で FX-MAG-EXPANSION の直前
(engine_version v2.3 → v2.4)。

## Goal
単一の `regime_shock` スパイクだけで `failure` state に倒れる現状を是正し、
急変動「翌日」の過剰防御 (6/12 failure→FLAT が翌 6/15 の +18bp 反発を逸失、
6/22 の FLAT で +17bp 逸失) を抑制する。`failure` evidence における瞬間的な
`regime_shock` の支配を弱め、状態遷移にヒステリシス (持続性) を持たせる。

## Acceptance Criteria
- [ ] `compute_state_evidence` の failure 項が、単一の高 `regime_shock` のみでは
      `failure` を dominant にしない (= `max(negative_e, disconfirmation,
      regime_shock)` の素の max 依存を緩和)。境界ケースを単体テストで固定
- [ ] 前日 state を考慮するヒステリシス/持続性が導入され、単日ショックで
      setup→failure に即遷移しない。determinism は維持 (同入力→同出力)
- [ ] 既存の決定論テスト (engine state) が緑、または意図した変化のみ更新
      (テスト変更は本 brief で明示的に許可する範囲のみ)
- [ ] `engine_version` を v2.4 に bump し、`automation_models.py` の default と
      `.github/workflows/fx-daily-protocol.yml` の `FX_ENGINE_VERSION` default を
      sync
- [ ] `docs/specs/ugh_state_engine_v1.md` (または fx_ugh_engine_v2) に v2.4 の
      変更点を追記

## Scope
- IN: `src/ugh_quantamental/engine/state.py`,
  `src/ugh_quantamental/engine/state_models.py` (新 config field 追加可),
  `src/ugh_quantamental/fx_protocol/automation_models.py` (engine_version),
  `.github/workflows/fx-daily-protocol.yml` (FX_ENGINE_VERSION default),
  `tests/engine/test_state*.py`, 該当 spec doc
- OUT: `projection.py` の e_star/conviction 経路、`forecasting.py` の magnitude
  (= FX-MAG-EXPANSION の領分)、protocol schemas、persistence/Alembic、baseline 戦略

## Allowed Dependencies (optional)
なし。

## Implementation Hints (optional)
- 現状 (state.py:134-135):
  `failure = config.failure_weight * _clamp(max(negative_e, disconfirmation, regime_shock))`。
  瞬間 `regime_shock` の素の max は急変動翌日にスパイクし単独で failure を発火
  させる。weighted-sum + minimum activation guard 化 (PR #109 が fire 項で採った
  パターン) や、`regime_shock` に減衰係数を掛ける案が候補。
- 既存の不変条件: `compute_state_evidence` は純関数。ヒステリシスは新たな globals/
  mutation で実装せず、前日 state を**明示的な引数**として受け取る形にする
  (pure function 維持; review-audit boundary と同じ原則)。
- `final_softmax_temperature=0.12` (state_models.py:30) は勝者総取りが鋭く、
  遷移直後の鋭敏さを増幅している。temperature 自体は変更せず failure evidence 側
  で吸収する方が変更面が小さい (要判断、Open Question として PR に記載可)。
- 検証は 6/12 / 6/22 相当の合成入力 (高 regime_shock + 正の翌日 close) で
  failure に倒れないことを test 化。

## Required Outputs
- Branch name: `codex/fx-state-hysteresis`
- PR title: `feat(engine): dampen single-shock failure firing with state hysteresis (v2.4)`
- Expected files changed: `state.py`, `state_models.py`, `automation_models.py`,
  `.github/workflows/fx-daily-protocol.yml`, `tests/engine/test_state*.py`, spec
- Required tests: 単一 regime_shock で failure 非発火、ヒステリシス遷移、
  engine_version sync の存在確認

## Done When
- All acceptance criteria are checked
- `ruff check .` passes
- `pytest -q` passes
- PR body starts with a Completion Summary
