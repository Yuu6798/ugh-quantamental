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
      `incomplete_batches: tuple[IncompleteExecutionBatch, ...]` (後者は `forecast_batch_id`,
      `execution_version` (存在する行から取る), `missing_books: tuple[str, ...]`) と
      `missing_evaluations: tuple[MissingExecutionEvaluation, ...]`
      (`forecast_batch_id`, `execution_version`, `as_of_jst`, `window_end_jst`)) があり、
      `history/*/*/execution_evaluation.csv` を読んで `(forecast_batch_id, book_id)` で重複排除し、
      **6 book が揃わない `forecast_batch_id` は丸ごと除外**して `incomplete_batches`
      (batch id と欠けた book の一覧) として返す (集計にもゲートにも入れない)。さらに
      `history/*/*/execution.csv` を棚卸しし (`is_complete_decision_file` が True のもの)、同 dir に完全な
      `execution_evaluation.csv` が無い batch を `missing_evaluations` として返す (期待コホート = 判断
      ファイルの存在。評価ファイルが丸ごと無い・header のみの batch もここで捕捉する)。棚卸しで
      `execution.csv` はあるが完全でない (header のみ・6 book 未満・読めない) dir は
      `incomplete_decision_batches: tuple[str, ...]` (`history/{date}/{batch}` の相対 path) として返す
      (version は読めないことがあるので現行版扱い)。走査規約は
      `labeled_observations.collect_evaluated_forecast_rows` と同じ。
- [ ] `run_execution_report(csv_output_dir, *, start_as_of_jst, end_as_of_jst, generated_at_utc)
      -> dict[str, Any]` が純粋な集計 (ファイル読みのみ、書き込みなし) で、**期間窓内**の行について
      (`start_as_of_jst` / `end_as_of_jst` は `datetime | None`、None はその端を無制限にする =
      両方 None で history 全体) `execution_version` ごとの層 (`strata[version].books[book_id]`、版を
      跨いで足さない) で book ごとに spec §8 の指標を返す: `decision_count`, `trade_count`,
      `skip_counts` (評価行の `skip_reason` 列の値別、取引行は含めない),
      `live_coverage_rate`, `direction_hit_rate`, `capture_bp` (`Σ side × (realized_close −
      realized_open) / realized_open × 1e4`、単位サイズ)、`signed_bp_live_mean/sd/t`
      (`size × (pnl_live_bp − cost_live_bp)`、**live かつ取引行 `side != 0`** のみ)、`signed_bp_bar_mean/sd/t`
      (`size × (pnl_bar_bp − cost_bar_bp)`、全 entry_status の取引行)、`capture_bp` だけは単位サイズのまま、
      `pnl_jpy_live`, `pnl_jpy_bar`, `final_equity_jpy_live`, `final_equity_jpy_bar`,
      `max_drawdown_live`, `max_drawdown_bar`, `profit_factor_live`, `cost_jpy_total`。資産曲線は spec §5.2 の式 (初期 3,000,000 円、複利、
      `position_usd = equity × size / entry`) で、live 系列は `entry_status == live` の行のみ、
      bar 系列は全行 (`backfill_bar` を含む)。
- [ ] 同関数が `benchmark_deltas` を層ごとに返す (`strata[version].benchmark_deltas`): `ugh_x1` と
      `bench_gpt_m3` / `bench_long` の `pnl_jpy_live` 差と `capture_bp` 差。
- [ ] 同関数が `gate` を返す。ゲートの母集団は**期間窓に依存しない累積コホート**: history 全体の
      行のうち `execution_version == execution.EXECUTION_VERSION` かつ `entry_status == live` の
      完全 batch (backfill 行と他 version は除外)。`gate.cohort` に `execution_version`,
      `first_as_of_jst`, `last_as_of_jst`, `trade_count`, `observation_days` (評価済み窓の数),
      `observation_calendar_days` (`(last_as_of_jst − first_as_of_jst).days`、条件 1 の「6 か月」は
      これが `GATE_MIN_CALENDAR_DAYS = 182` 以上) を、`gate.criteria` に
      spec §9 の 4 条件それぞれの現在値・閾値・充足可否を、`gate.passed: bool` を返す。取引数・t 値・
      DD は **`ugh_x1` の行だけ**から計算し (`trade_count` は `ugh_x1` の `side != 0` 行数)、ベンチマーク
      book は条件 4 の比較にだけ使う。t 値は `signed_bp_live` (= `size × (pnl_live_bp − cost_live_bp)`)
      から計算し、bar 系列はゲートに使わない。現行 `execution_version` に `incomplete_batches` または
      `missing_evaluations` (`window_end_jst > generated_at_utc` の pending 窓は除く) または
      `incomplete_decision_batches` が 1 つでもあれば `gate.passed = False` かつ `gate.blocked_reasons`
      (new; `tuple[str, ...]`、値は `"incomplete_batches"` / `"missing_evaluations"` /
      `"incomplete_decisions"`、通常は空) に理由を入れる — 欠けた archive を黙って短くして合格には
      しない。
- [ ] `export_execution_report_artifacts(report, csv_output_dir, scope, date_str)` が
      `csv/analytics/execution/{scope}/{date_str}/execution_{scope}.md|.csv|.json` (scope は
      `weekly` / `monthly`) を書く。md は層 (version) ごとに book 別の表 1 つとベンチマーク差の表 1 つ、
      ゲート進捗の表 1 つ (通常は層が 1 つ)。`latest/execution_summary.json` は期間窓の report からは書かず、
      `export_execution_latest_summary(cumulative_report, csv_output_dir)` (new) が
      `run_execution_report(csv_output_dir, start_as_of_jst=None, end_as_of_jst=None, ...)`
      (history 全体を 1 つの窓として集計) の結果を書く。weekly / monthly の呼び出し元は scoped
      artifact の直後にこれを呼ぶので、latest の内容は直前に走った scope に依存しない。
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
      `realized_close`、(c) その batch 自身の `history/{as_of:%Y%m%d}/{forecast_batch_id}/input_snapshot.json`
      (`forecast_batch_id` の dir を直接解決する。`find_snapshot_path` のような日付だけの探索は使わない。
      `analyze_estar_lag.load_market_snapshot` で読み `build_baseline_context` へ) の 3 つが揃う batch
      だけを対象にし、`history/{as_of}/{batch}/execution.csv` が完全 (`is_complete_decision_file`)
      で**無い**場合は `entry_status = backfill_bar` の判断 6 行と評価 6 行を生成する
      (`build_execution_decisions` に `forecast_directions` の対応と `entry_status="backfill_bar"`,
      `live_entry=None` を渡す。`ForecastRecord` / `OutcomeRecord` は復元しない)。`execution.csv` が
      完全で `execution_evaluation.csv` が完全でない batch (前回の中断、または日次 run の評価失敗) は、
      既存の判断 6 行を `load_execution_decisions_csv` で読んで評価 6 行だけを生成する (判断は
      書き直さない)。**この修復経路に必要なのは判断ファイルと (b) の outcome だけ**で、(a) forecast と
      (c) snapshot は判断を再構成するときにしか要求しない。揃わない batch は理由別に件数を出して skip。完全な既存ファイルは一切上書きしない。`--dry-run` で
      件数だけ出す。`fx-daily-data` には push しない (ローカル checkout に書き、push は人が行う)。
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
- t 値は取引行 (`side != 0`) の `mean / (stdev / sqrt(n))` (`statistics.stdev`、n − 1。`pstdev` は
  使わない)。**母集団は report の `signed_bp_*_mean/sd/t` もゲートも同じ「取引行のみ」**: 見送り日
  (side 0、リターン 0) は資産曲線では据え置きとして入るが、mean / sd / t / `trade_count` の母集団には
  入れない。live 系列は
  `size × (pnl_live_bp − cost_live_bp)` (live 行のみ)、bar 系列は `size × (pnl_bar_bp − cost_bar_bp)`。
  `capture_bp` は単位サイズの方向の価値、signed bp は売買方針の実リターンと役割を分ける。`n < 3` または `stdev == 0` なら None。
  ゲートは live 系列のみ。
- 最大 DD は資産曲線のピーク比で**正の大きさ** (`max_drawdown_* = max_t (peak_t − equity_t) / peak_t`、
  0 以上 1 以下)。ゲート条件 3 は `max_drawdown_live <= 0.10` (10.00% は合格、10.01% は不合格)。
  資産曲線は行を `as_of_jst` 昇順で畳む。
- md の数値書式は `weekly_report_exports._fmt_pct` / `_fmt_bp` に揃える。
- backfill の `decided_at_utc` は `as_of_jst` を UTC に変換した値 (forecast.csv には
  `locked_at_utc` 列が無い)、`evaluated_at_utc` は `evaluation.csv` の `evaluated_at_utc` を使い、
  再実行で同じ出力になるようにする。

## Required Outputs
- Branch name: `codex/fx-exec-reporting`
- PR title: `feat(fx): execution layer reporting, acceptance gate and history backfill`
- Expected files changed: 上記 IN の一覧
- Required tests:
  - 集計: 合成した `execution_evaluation.csv` (6 book × 6 窓の完全 batch、live 欠落 1 行、side 0
    1 行 (`skip_reason` 付き)、backfill 2 行) から、損益・資産・DD・t 値・capture・live 率・見送り
    内訳・ゲートの各値を数値で固定 (詳細な数値検証は 3 book 分で十分だが fixture は 6 book を揃える)。
    重複 batch (同じ `forecast_batch_id` が 2 つの dir にある) が 1 回だけ数えられること。
  - ゲート: 4 条件の境界 (取引 99 と 100、暦日 181 と 182 (取引 100 回あっても 181 日なら不合格)、
    t 1.99 と 2.00、DD 10.00% (合格) と 10.01% (不合格)、ベンチマーク同額)、
    期間窓を狭めてもコホートが変わらないこと、`execution_version` が違う行と backfill 行が
    コホートに入らないこと、6 book 未満の batch が集計とコホートの両方から除外され、かつその存在で
    `gate.passed` が False (`"incomplete_batches" in blocked_reasons`) になること、旧 version
    (`execution_version != EXECUTION_VERSION`) の不完全 batch は現行版のゲートを block しないこと、完全な `execution.csv`
    だけがあり評価ファイルが無い (または header のみの) 過去窓で `missing_evaluations` に入り
    `"missing_evaluations" in blocked_reasons` になること、`window_end_jst` が `generated_at_utc` より
    後の pending 窓はそこに入らないこと、header のみの `execution.csv` だけがある dir が
    `incomplete_decision_batches` に入り `"incomplete_decisions" in blocked_reasons` になること、見送り
    (side 0) の live 行を足しても `signed_bp_live_t` と `trade_count` が変わらないこと、
    `execution_version` が 2 つ混在する fixture で層が 2 つに
    分かれ版を跨いで足されないこと、`trade_count` が `ugh_x1` の取引行数だけを数えること (他 book の
    取引は数えない)。
  - export: 3 形式が書かれること、`latest/execution_summary.json` が累積 report から書かれ、
    期間窓を変えても内容が変わらないこと (`tmp_path`)。
  - backfill: 完全な既存 `execution.csv` を上書きしないこと、`execution.csv` だけある batch で評価
    6 行だけが生成されること、`--dry-run` が書かないこと、不完全 batch (forecast 6 行) を飛ばすこと。
  - 既存テストは無変更で通る。

## Done When
- All acceptance criteria are checked
- `ruff check .` passes
- `pytest -q` passes
- PR body starts with a Completion Summary
