# Task Brief: FX-ESTAR-LAG - ショック後 e_star 転換遅延の feature 別 replay 分析

## Phase
2026-08 月次レビュー §1 (`docs/engine_review_2026_08_findings.md`)。分析のみ —
engine 改変は本 brief のスコープ外 (結果を見て次 brief で判断)。

## Goal
7/30 ショック後に e_star が 9 営業日マイナスに固定された遅行の主因 feature を、
実データ replay で特定する。仮説「`fundamental_score` (spot_vs_sma20×100 の clamp
飽和、時定数 ~20 営業日) が主因」を裏付けるか棄却する。

## Acceptance Criteria
- [ ] `scripts/analyze_estar_lag.py` が `fx-daily-data` の history CSV (OHLC 完了
      window) だけを入力に、2026-07-22〜2026-08-28 の各営業日について
      `compute_snapshot_statistics` → `derive_signal_features` → projection を
      再実行し、日別の `fundamental_score` / `technical_score` /
      `price_implied_score` / `e_raw` / `gravity_bias` / `e_star` を CSV +
      Markdown 表で出力する (read-only、ネットワークなし、決定的)
- [ ] 出力に「各 feature が負に転じた日 / 正に戻った日」の一覧が含まれ、e_star の
      符号転換日 (α: 8/21) をどの feature が律速したかが表から読める
- [ ] `fundamental_score` の clamp 飽和 (|spot_vs_sma20×100| ≥ 1.0) だった営業日数が
      期間中で定量化される
- [ ] 分析結論 (主因 feature、飽和の寄与、engine 改変の要否と候補) を
      `docs/analysis/estar_lag_2026_08.md` に記録する
- [ ] 決定関数 (feature 系列 → 転換日の抽出) に unit test がある (fixture は
      合成 OHLC、ファイル I/O なし)

## Scope
- IN: `scripts/analyze_estar_lag.py` (新規)、`docs/analysis/estar_lag_2026_08.md`
      (新規)、`tests/fx_protocol/` の対応 test (新規)
- OUT: `src/ugh_quantamental/engine/` と `src/ugh_quantamental/fx_protocol/` の
      既存コード一切 (import して使うのみ)。パラメータ変更・engine_version bump 禁止

## Implementation Hints
- 入力系列は `market_ugh_builder.compute_snapshot_statistics` /
  `derive_signal_features` が要求する `FxProtocolMarketSnapshot` を history CSV から
  組み立てる。既存の replay/backfill 系スクリプトの snapshot 構築を再利用可
- `compute_e_star(e_raw, gravity_bias)` は `engine/projection.py` にある
- trailing 統計は 20 窓。7/30 (577pips) の窓内残存期間 (〜8/27 発行分) と
  feature 時系列の関係も表に出すと §2 (レンジ較正) の材料を兼ねる

## Required Outputs
- Branch name: `codex/fx-estar-lag-analysis`
- PR title: `analysis: replay signal features to locate the post-shock e_star lag`
- Expected files changed: 上記 IN の 3 点のみ
- Required tests: 決定関数の unit test (合成 fixture)

## Done When
- All acceptance criteria are checked
- `ruff check .` passes
- `pytest -q` passes
- PR body starts with a Completion Summary
