# Task Brief: FX-ESTAR-LAG - ショック後 e_star 転換遅延の feature 別 replay 分析

## Phase
2026-08 月次レビュー §1 (`docs/engine_review_2026_08_findings.md`)。分析のみ —
engine 改変は本 brief のスコープ外 (結果を見て次 brief で判断)。

## Goal
7/30 ショック後の e_star 転換遅延 (β は底から 6 営業日 (8/11) で断続的に正転、δ は
8/19、α/γ は 14 営業日 (8/21) — variant 間で最大 8 営業日ばらけた) の主因 feature を、
実データ replay で特定する。仮説「`fundamental_score` (spot_vs_sma20×100 の clamp
飽和、時定数 ~20 営業日) が主因」を裏付けるか棄却する。variant 間の転換日の分散
(config 差だけで 8 営業日ずれる) も判別材料として説明できること。

## Acceptance Criteria
- [ ] `scripts/analyze_estar_lag.py` が `fx-daily-data` の
      **`history/{date}/{batch_id}/input_snapshot.json`** (`observability.py` が
      永続化する当日実測の `current_spot` + completed windows) を入力に、
      2026-07-22〜2026-08-28 の各営業日について `compute_snapshot_statistics` →
      `derive_signal_features` → projection を再実行し、日別の
      `fundamental_score` / `technical_score` / `price_implied_score` / `e_raw` /
      `gravity_bias` / `e_star` を CSV + Markdown 表で出力する (read-only、
      ネットワークなし、決定的)。**OHLC history CSV からの再構築は不可** —
      `current_spot` は完了バーと別系統 (`data_sources.py` の Yahoo 経路) のため、
      再構築系列は本番 forecast と別物になり得る。snapshot 欠落日はその旨を
      出力に明記して skip する (補完しない)
- [ ] 出力に「各 feature が負に転じた日 / 正に戻った日」の一覧が含まれる (記述統計)
- [ ] **律速の判定は counterfactual/ablation で行う**: **α・β・δ の 3 variant**
      (方向 weight 構成が相異なる代表 — β は α 比で p_weight 2 倍 / u_weight 半分
      など `forecasting.py` の variant config 差があり、α 単独では「なぜ β が
      8 営業日早く転換したか」を説明できない) について、feature を 1 つずつ固定して
      projection を再実行し、e_star の符号転換日が何営業日動くかを feature 別・
      variant 別に比較する。**参照値は 2 種を両方実施する
      (sensitivity pair — どちらか一方の選択は実装依存の結論差を生むため不可)**:
      (i) ショック前水準 = 当該 raw statistic の 2026-07-23〜07-29 (ショック前
      最後の 5 営業日: 7/23, 24, 27, 28, 29) の平均、(ii) 中立値 = 0.0。両参照で転換日シフトを並記し、
      結論が参照値に依存する場合はそれ自体を結果として報告する。
      符号一致・日付一致だけの表からの因果結論は不可 (`fundamental_score` は
      compute_u / alignment / gravity 経由で間接的に効き、clamp 下で相互作用する
      ため、同時転換は律速の証明にならない)
- [ ] **介入は raw statistic 水準で行い、その statistic の全消費者を再構築する**:
      介入対象は `compute_snapshot_statistics` の出力 (例: `spot_vs_sma20`、
      `momentum_5d`) と明記し、projection request 全体を statistics から毎回
      組み直す — `derive_signal_features` (scores → alignment gaps d_qf〜d_tp →
      `narrative_dispersion`) だけでなく **`derive_question_features`
      (`question_direction` / `q_strength` / `s_q` — `momentum_5d` の第 2 の
      消費者) を含む**。built 済み request の一部差し替えは不可 — stale な派生
      入力が残ると介入と無関係な理由で e_star が動く。列挙に頼らず「statistics →
      request の全経路を通し直す」実装にすること。test: 「無介入の再構築 =
      本番系列と一致」を fixture で確認してから介入系列を比較する
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
- 入力系列は各日の `input_snapshot.json` を `FxProtocolMarketSnapshot` に戻して
  使う (`observability.py` の build 側と対になる読み戻し)。既存の replay/backfill
  系スクリプトに読み戻しがあれば再利用可
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
