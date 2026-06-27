# Task Brief: FX-STATE-HYSTERESIS - 急変動直後の failure 過剰発火の抑制

## Phase
engine_review_2026_06 §1 ★2 — 着手順序 §2 で FX-MAG-EXPANSION の直前
(engine_version v2.3 → v2.4)。

## Goal
⚠️ **スコープ訂正 (P1)**: forecast の direction/FLAT は `projection_res.e_star`
× conviction から `_direction_from_bp_with_epsilon` で決まり、`dominant_state` は
record にコピーされるだけで **direction/FLAT 判定の入力ではない**
(`forecasting.py:340-366`)。よって 6/12・6/15 の FLAT *予測* は projection/epsilon
由来であり、`failure` state を damping しても**予測 direction は変わらない**
(state は並走ラベル)。本 brief は **state ラベル / state_proxy / レジーム別
stratification の正しさ**の cleanup に scope を限定する: 単一 `regime_shock`
スパイクだけで `failure` state に倒れ、分析の regime/state スライスや state_proxy を
歪める現状を是正する。**「過剰防御 FLAT 予測そのもの」の是正は projection/epsilon
の領分** (FX-MAG-EXPANSION + epsilon 設計) であり本 brief の対象外。
`failure` evidence における瞬間的な
`regime_shock` の瞬間支配を弱める (主アプローチは前日 state 不要の
same-snapshot shock damping。真のヒステリシス採用時のみ後述の plumbing が必要)。

## Acceptance Criteria
- [ ] `compute_state_evidence` の failure 項が、単一の高 `regime_shock` のみでは
      `failure` を dominant にしない (= `max(negative_e, disconfirmation,
      regime_shock)` の素の max 依存を緩和)。境界ケースを単体テストで固定
- [ ] **主アプローチ = same-snapshot shock damping** (前日 state 不要)。単日の高
      `regime_shock` が単独で setup→failure を起こさないよう、failure evidence
      内で shock の瞬間支配を緩和する。これは現行 live path で実現可能 (下記注記)。
      ⚠️ **「真のヒステリシス」(前日 state 参照) を採る場合のみ** workflow/fx_protocol
      の plumbing をスコープに含めること: 現状 `run_full_workflow`
      (`workflows/runners.py:162`) は same-day request で `run_state_engine`
      (:89) を呼び、`market_ugh_builder` も same-day `StateEventFeatures` で
      `FullWorkflowStateRequest` を構築 (:626-629) しており、前日 state を load/
      pass する経路が無い。`state.py`/`state_models.py` だけに閉じた実装は engine
      test を pass しても daily v2.4 では prior-day state が不在のまま空振りする。
      前日 state を使うなら runners + market_ugh_builder + 前日 state の永続化/
      ロードを明示し、それは core invariant に触れる拡張なので AGENTS.md §3
      escalation 相当として扱う。**まず same-snapshot damping で要件を満たすこと**
- [ ] determinism は維持 (同入力→同出力)
- [ ] 既存の決定論テスト (engine state) が緑、または意図した変化のみ更新
      (テスト変更は本 brief で明示的に許可する範囲のみ)
- [ ] `engine_version` を v2.4 に bump し、**3 箇所** の default を sync:
      `automation_models.py` の default、`.github/workflows/fx-daily-protocol.yml`
      の `FX_ENGINE_VERSION`、`scripts/run_fx_daily_protocol.py` の
      `_env("FX_ENGINE_VERSION", "v2.3")` default (+ 同 docstring L19)。
      script default を漏らすと手動/ローカル実行が旧バージョンで永続化し
      version-based audit/stratify を壊す
- [ ] `docs/specs/ugh_state_engine_v1.md` (または fx_ugh_engine_v2) に v2.4 の
      変更点を追記

## Scope
- IN: `src/ugh_quantamental/engine/state.py`,
  `src/ugh_quantamental/engine/state_models.py` (新 config field 追加可),
  `src/ugh_quantamental/fx_protocol/automation_models.py` (engine_version),
  `.github/workflows/fx-daily-protocol.yml` (FX_ENGINE_VERSION default),
  `scripts/run_fx_daily_protocol.py` (FX_ENGINE_VERSION default + docstring),
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
- 既存の不変条件: `compute_state_evidence` は純関数。same-snapshot damping は
  同関数内で完結し prior state 不要。仮に前日 state を使う場合も globals/mutation
  ではなく**明示的な引数**として受け取る (pure function 維持) が、その引数を供給
  する live plumbing が現状無い点に注意 (AC #2 参照)。
- `final_softmax_temperature=0.12` (state_models.py:30) は勝者総取りが鋭く、
  遷移直後の鋭敏さを増幅している。temperature 自体は変更せず failure evidence 側
  で吸収する方が変更面が小さい (要判断、Open Question として PR に記載可)。
- 検証は 6/12 / 6/22 相当の合成入力 (高 regime_shock + 正の翌日 close) で
  failure に倒れないことを test 化。

## Required Outputs
- Branch name: `codex/fx-state-hysteresis`
- PR title: `feat(engine): dampen single-shock failure firing with state hysteresis (v2.4)`
- Expected files changed: `state.py`, `state_models.py`, `automation_models.py`,
  `.github/workflows/fx-daily-protocol.yml`, `scripts/run_fx_daily_protocol.py`,
  `tests/engine/test_state*.py`, spec
- Required tests: 単一 regime_shock で failure 非発火、same-snapshot shock-damping
  での遷移 (前日 state 不要; 真のヒステリシスを明示採用する場合のみ prior-state 遷移)、
  engine_version の 3 箇所 sync の存在確認

## Done When
- All acceptance criteria are checked
- `ruff check .` passes
- `pytest -q` passes
- PR body starts with a Completion Summary
