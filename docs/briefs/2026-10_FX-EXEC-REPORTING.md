# Task Brief: FX-EXEC-REPORTING - 執行層の週次・月次集計、合格ゲート、backfill

## Phase
`docs/specs/fx_execution_layer_v1.md` §8〜§10。FX-EXEC-LAYER (判断の記録・評価) が merge された後に
着手する。前提: `history/{date}/{batch}/execution.csv` と `execution_evaluation.csv` が本番で
生成されている。

## Goal
`execution_evaluation.csv` を集計して book 別の損益・capture・t 値・最大 DD・ベンチマーク差・
合格ゲート進捗を週次と月次の artifact に出し、保存済み予測 (2026-05-08 以降) の backfill 行を
`entry_status = backfill_bar` で生成する。

## Acceptance Criteria
- [ ] `src/ugh_quantamental/fx_protocol/execution_reporting.py` (new) に
      `collect_execution_evaluation_rows(history_dir) -> CollectedExecutionEvaluations` (new、frozen
      dataclass または Pydantic model: `rows: tuple[dict[str, str], ...]` と
      `incomplete_batches: tuple[IncompleteExecutionBatch, ...]`、後者は `forecast_batch_id` と
      `missing_books: tuple[str, ...]`) があり、
      `history/*/*/execution_evaluation.csv` を読んで `(forecast_batch_id, book_id)` で重複排除し、
      **6 book が揃わない `forecast_batch_id` は丸ごと除外**して `incomplete_batches`
      (batch id と欠けた book の一覧) として返す (集計にもゲートにも入れない)。走査規約は
      `labeled_observations.collect_evaluated_forecast_rows` と同じ。
- [ ] `run_execution_report(csv_output_dir, *, start_as_of_jst, end_as_of_jst, generated_at_utc)
      -> dict[str, Any]` が純粋な集計 (ファイル読みのみ、書き込みなし) で、**期間窓内**の行について
      book ごとに spec §8 の指標を返す: `decision_count`, `trade_count`, `skip_counts` (skip_reason 別),
      `live_coverage_rate`, `direction_hit_rate`, `capture_bp` (`Σ side × (realized_close −
      realized_open) / realized_open × 1e4`、単位サイズ)、`signed_bp_live_mean/sd/t`
      (`pnl_live_bp − cost_live_bp`、live 行のみ)、`signed_bp_bar_mean/sd/t` (`pnl_bar_bp − cost_bar_bp`、全行)、
      `pnl_jpy_live`, `pnl_jpy_bar`, `final_equity_jpy_live`, `final_equity_jpy_bar`,
      `max_drawdown_live`, `max_drawdown_bar`, `profit_factor_live`, `cost_jpy_total`。資産曲線は spec §5.2 の式 (初期 3,000,000 円、複利、
      `position_usd = equity × size / entry`) で、live 系列は `entry_status == live` の行のみ、
      bar 系列は全行 (`backfill_bar` を含む)。
- [ ] 同関数が `benchmark_deltas` を返す: `ugh_x1` と `bench_gpt_m3` / `bench_long` の
      `pnl_jpy_live` 差と `capture_bp` 差。
- [ ] 同関数が `gate` を返す。ゲートの母集団は**期間窓に依存しない累積コホート**: history 全体の
      行のうち `execution_version == execution.EXECUTION_VERSION` かつ `entry_status == live` の
      完全 batch (backfill 行と他 version は除外)。`gate.cohort` に `execution_version`,
      `first_as_of_jst`, `last_as_of_jst`, `trade_count`, `observation_days` を、`gate.criteria` に
      spec §9 の 4 条件それぞれの現在値・閾値・充足可否を、`gate.passed: bool` を返す。t 値は
      `signed_bp_live` (= `pnl_live_bp − cost_live_bp`) から計算し、bar 系列はゲートに使わない。
- [ ] `export_execution_report_artifacts(report, csv_output_dir, scope, date_str)` が
      `csv/analytics/execution/{scope}/{date_str}/execution_{scope}.md|.csv|.json` (scope は
      `weekly` / `monthly`) と `latest/execution_summary.json` を書く。md は book 別の表 1 つ、
      ベンチマーク差の表 1 つ、ゲート進捗の表 1 つ。
- [ ] `scripts/run_fx_daily_protocol.py` の金曜 weekly block (`--- Weekly report (Friday auto-trigger) ---`
      の中、`export_weekly_report_artifacts` の後) で、同じ週窓について執行層の weekly artifact を
      生成する。失敗は `[WARN] Execution report generation failed (non-fatal)` (new) で握りつぶす。
- [ ] `scripts/run_fx_analysis_pipeline.py` の weekly / monthly モードで、既存の weekly / monthly の
      直後に執行層の weekly / monthly artifact を生成する (monthly は月窓全体、`FX_REPORT_DATE` と
      同じ窓解決を使う)。失敗は non-fatal。
- [ ] `scripts/backfill_execution_history.py` (new) が `--fxdata-dir` の `history/` を**横断 join** で
      走査する: 評価と outcome は翌日の batch dir にあるので、`labeled_observations.collect_evaluated_forecast_rows`
      と同じく `forecast_id → evaluation`、`outcome_id → outcome` のグローバル索引を先に作り、
      `forecast_batch_id` ごとに (a) `forecast.csv` の 7 行の `strategy_kind` / `forecast_direction`、
      (b) その batch の評価行が指す `outcome.csv` の `outcome_id` / `window_start_jst` / `realized_open` /
      `realized_close`、(c) `analyze_estar_lag.find_snapshot_path(fxdata_dir, as_of.date())` で見つけた
      `input_snapshot.json` (`load_market_snapshot` で読み `build_baseline_context` へ) の 3 つが揃う batch
      だけを対象にし、`history/{as_of}/{batch}/execution.csv` が**無い**場合だけ
      `entry_status = backfill_bar` の判断 6 行と評価 6 行を生成する (`build_execution_decisions` に
      `forecast_directions` の対応と `entry_status="backfill_bar"`, `live_entry=None` を渡す。
      `ForecastRecord` / `OutcomeRecord` は復元しない)。揃わない batch は理由別に件数を出して skip。
      既存ファイルは一切上書きしない。`--dry-run` で件数だけ出す。`fx-daily-data` には push しない
      (ローカル checkout に書き、push は人が行う)。
- [ ] `docs/specs/fx_execution_layer_v1.md` §8〜§10 を実装に合わせて更新 (Status は
      `Implemented (v1)` のまま、集計の列定義を追記)。`.claude/skills/fx-weekly-report/SKILL.md` §4 に
      `## 執行層 (仮想売買)` 節の追加手順を 1 段落で記す (artifact のパスと、ゲート進捗を 1 行で
      書く規約)。

## Scope
- IN: `execution_reporting.py` (new)、`scripts/backfill_execution_history.py` (new)、
  `scripts/run_fx_daily_protocol.py` と `scripts/run_fx_analysis_pipeline.py` (執行層ブロックの追加のみ)、
  `tests/fx_protocol/test_execution_reporting.py` (new)、`tests/scripts/` 相当の backfill テスト、
  spec §8〜§10、weekly report skill の 1 段落。
- OUT: `execution.py` の判断規則とパラメータ、`weekly_reports_v2.py` / `monthly_review.py` /
  `monthly_governance.py` (執行層の数値を governance flag に混ぜない)、`labeled_observations.csv` の
  スキーマ、ORM、`.github/workflows/*`。

## Allowed Dependencies
なし。

## Implementation Hints
- 週窓の解決は `report_window.resolve_business_day_window` (weekly_reports_v2 が使うもの) を
  使う (金曜 block は `report_date = as_of + 1 日`)。
- t 値は取引行 (`side != 0`) の `mean / (pstdev / sqrt(n))`。live 系列は `pnl_live_bp − cost_live_bp`
  (live 行のみ)、bar 系列は `pnl_bar_bp − cost_bar_bp`。`n < 3` または `pstdev == 0` なら None。
  ゲートは live 系列のみ。
- 最大 DD は資産曲線のピーク比。資産曲線は行を `as_of_jst` 昇順で畳む。
- md の数値書式は `weekly_report_exports._fmt_pct` / `_fmt_bp` に揃える。
- backfill の `decided_at_utc` は `as_of_jst` を UTC に変換した値 (forecast.csv には
  `locked_at_utc` 列が無い)、`evaluated_at_utc` は `evaluation.csv` の `evaluated_at_utc` を使い、
  再実行で同じ出力になるようにする。

## Required Outputs
- Branch name: `codex/fx-exec-reporting`
- PR title: `feat(fx): execution layer reporting, acceptance gate and history backfill`
- Expected files changed: 上記 IN の一覧
- Required tests:
  - 集計: 合成した `execution_evaluation.csv` (3 book × 6 窓、live 欠落 1 行、side 0 1 行、
    backfill 2 行) から、損益・資産・DD・t 値・capture・live 率・ゲートの各値を数値で固定。
    重複 batch (同じ `forecast_batch_id` が 2 つの dir にある) が 1 回だけ数えられること。
  - ゲート: 4 条件の境界 (取引 99 と 100、t 1.99 と 2.00、DD −10% と −10.01%、ベンチマーク同額)、
    期間窓を狭めてもコホートが変わらないこと、`execution_version` が違う行と backfill 行が
    コホートに入らないこと、6 book 未満の batch が集計とコホートの両方から除外されること。
  - export: 3 形式と `latest/execution_summary.json` が書かれること (`tmp_path`)。
  - backfill: 既存 `execution.csv` を上書きしないこと、`--dry-run` が書かないこと、
    不完全 batch (forecast 6 行) を飛ばすこと。
  - 既存テストは無変更で通る。

## Done When
- All acceptance criteria are checked
- `ruff check .` passes
- `pytest -q` passes
- PR body starts with a Completion Summary
