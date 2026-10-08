# Task Brief: FX-EXEC-LAYER - UGH 売買エンジン (執行層) v1: 判断の記録・評価・CSV 永続化

## Phase
`docs/specs/fx_execution_layer_v1.md` §3〜§7、§11 (Draft、2026-10-08 設計承認)。STATUS queue 6
(execution レイヤー) の実装第 1 段。予測エンジン側の集計・月次レビューは変更しない。

## Goal
保存済みの日次予測 batch を消費して 6 book の仮想売買判断を 1 run に 1 回記録し、翌日の outcome
確定時に評価して、`history/{date}/{batch}/execution.csv` / `execution_evaluation.csv` に永続化する。
集計 (週次・月次) と backfill は次の brief FX-EXEC-REPORTING の対象で、本 brief には含めない。

## Acceptance Criteria
- [ ] `src/ugh_quantamental/fx_protocol/execution_models.py` (new) に `BookId` (str Enum、値は
      `ugh_x1` / `ugh_beta_unit` / `ugh_consensus` / `ugh_divergence` / `bench_gpt_m3` / `bench_long`
      の 6 つ、この順)、`ExecutionDecision`、`ExecutionEvaluation` (いずれも
      `ConfigDict(extra="forbid", frozen=True)`) があり、spec §5.1 / §5.2 の列をフィールドとして持つ。
      validator: `side ∈ {-1, 0, 1}`、`0.0 ≤ size ≤ 1.0`、`side == 0` と `size == 0.0` は同値、
      `entry_status` は `Literal["live", "live_unavailable", "backfill_bar"]` (`backfill_bar` は
      FX-EXEC-REPORTING の backfill 行用に今から予約)、`entry_price_live` は
      `entry_status == "live"` のときだけ非 None (他 2 値では None)、`ExecutionEvaluation` の
      `pnl_live_bp` と `cost_live_bp` は `entry_price_live` が None のときだけ None (`cost_bar_bp` は常に
      float)。
      SQLAlchemy を import しない。
- [ ] `src/ugh_quantamental/fx_protocol/execution.py` (new) が定数
      `EXECUTION_VERSION = "x1"`、`EXECUTION_INITIAL_EQUITY_JPY = 3_000_000`、
      `EXECUTION_ROUND_TRIP_COST_JPY_PER_USD = 0.01`、`UGH_X1_TARGET_BP = 30.0`、
      `UGH_X1_SHOCK_MULTIPLIER = 2.5`、`CONSENSUS_PARTIAL_SIZE = 0.5` を `__all__` 付きで公開する。
- [ ] `build_execution_decisions(*, forecast_directions: Mapping[StrategyKind, ForecastDirection],
      baseline_context, completed_closes, as_of_jst, window_end_jst, forecast_batch_id,
      entry_status: EntryStatus, live_entry: LiveEntry | None, decided_at_utc)
      -> tuple[ExecutionDecision, ...]` が純関数で、`BookId` の順に**ちょうど 6 件**返す。
      `ForecastRecord` ではなく方向の対応を受け取る (CSV からの backfill でも同じ関数を使うため)。
      `ugh_v2_alpha` / `ugh_v2_beta` / `ugh_v2_gamma` / `ugh_v2_delta` / `baseline_simple_technical`
      のいずれかが欠けるときは `ValueError` を raise する (メッセージは new:
      `"execution layer requires a complete daily forecast batch"` で始める)。
      `entry_status == "live"` と `live_entry is not None` が食い違えば `ValueError`。
      `live_unavailable` / `backfill_bar` では `entry_price_live` / `entry_vendor` / `entry_feed` は None、
      `entry_time_utc = decided_at_utc`。`completed_closes` は直近完了窓の終値を**古い順**に並べた
      タプルで、5 件未満なら `ValueError`。
- [ ] 判断規則が spec §4 の表どおり (すべて parametrized test で固定):
      - `ugh_x1`: β が `flat` → `side 0, skip_reason "flat"`。
        `abs(previous_close_change_bp) > 2.5 × trailing_mean_abs_close_change_bp` → `side 0,
        skip_reason "shock_filter"` (flat 判定より後に評価、両方該当なら `flat`)。それ以外は
        β の方向、`size = min(1.0, 30.0 / trailing_mean_abs_close_change_bp)`
        (`trailing_mean_abs_close_change_bp == 0` なら `size 1.0`)。`previous_close_change_bp`
        が None のときは shock フィルタを適用しない。
      - `ugh_beta_unit`: β の方向、`size 1.0`、flat なら `skip_reason "flat"`。
      - `ugh_consensus`: up 4 → `+1, 1.0`、down 4 → `-1, 1.0`、up 3 かつ down 0 → `+1, 0.5`、
        down 3 かつ up 0 → `-1, 0.5`、それ以外 → `0, skip_reason "no_consensus"`。
      - `ugh_divergence`: β が flat → `"flat"`、β の方向が `baseline_simple_technical` の
        `forecast_direction` と同じ → `skip_reason "agree_with_technical"`、違えば β の方向で `size 1.0`。
      - `bench_gpt_m3`: `momentum_3d = completed_closes[-2] - completed_closes[-5]`、正 → `+1`、
        負 → `-1`、ゼロ → `0, skip_reason "momentum_zero"`、`size 1.0`。
      - `bench_long`: 常に `+1, 1.0`。
      監査列 (`beta_direction`, `consensus_up_count`, `consensus_down_count`, `technical_direction`,
      `momentum_3d`, `trailing_mean_abs_close_change_bp`, `previous_close_change_bp`) は 6 行すべてに
      同じ値を書く。
- [ ] `evaluate_execution_decisions(decisions, *, outcome_id, window_start_jst, realized_open,
      realized_close, evaluated_at_utc) -> tuple[ExecutionEvaluation, ...]` が純関数で
      (`OutcomeRecord` ではなく outcome.csv にもある 4 値を受け取る)、spec §5.2 の式どおりに
      `pnl_live_bp` / `pnl_bar_bp` / `cost_live_bp` / `cost_bar_bp` / `hit` を計算する。`decisions` が
      空、`forecast_batch_id` が揃っていない、`window_start_jst != decisions[0].as_of_jst`、価格が
      非有限または 0 以下のときは `ValueError`。`side == 0` の行は `pnl_bar_bp 0.0`、`cost_bar_bp 0.0`、
      `hit None` (live 価格があれば `pnl_live_bp 0.0` / `cost_live_bp 0.0`、無ければ両方 None)。
- [ ] `src/ugh_quantamental/fx_protocol/data_sources.py` に `fetch_live_spot_yahoo(*, timeout: int = 30)
      -> tuple[float, datetime]` (new) があり、`YahooFinanceFxMarketDataProvider` と同じ
      `https://query2.finance.yahoo.com/v8/finance/chart/USDJPY=X` から `meta.regularMarketPrice` を
      読む。HTTP 失敗・payload 不正・spot ≤ 0 はすべて既存の `FxDataFetchError` に包んで raise する。
      戻りの datetime は aware UTC。
- [ ] `src/ugh_quantamental/fx_protocol/execution_exports.py` (new) に
      `EXECUTION_FIELDNAMES` / `EXECUTION_EVALUATION_FIELDNAMES` (spec §5 の列順)、
      `export_execution_csv(decisions, as_of_jst, pair, csv_output_dir) -> str`
      (`{csv_output_dir}/execution/{pair}_{YYYYMMDD}_execution.csv`)、
      `export_execution_evaluation_csv(evaluations, as_of_jst, pair, csv_output_dir) -> str`
      (`.../execution/{pair}_{YYYYMMDD}_execution_evaluation.csv`)、
      `publish_execution_csvs(csv_output_dir, date_str, forecast_batch_id, decision_path,
      evaluation_path) -> dict[str, str | None]` がある。publish は
      `history/{date_str}/{forecast_batch_id}/execution.csv` と同 `execution_evaluation.csv` を書き、
      `latest/execution.csv` を更新する。**完全な既存の `history/.../execution.csv` は上書きせず**その
      パスをそのまま返す。完全 = `load_execution_decisions_csv` が 6 book それぞれ 1 行を検証付きで
      返せること (`is_complete_decision_file(path) -> bool` (new) で判定)。header のみ・途中で切れた
      ファイルは不完全として置き換える。`execution_evaluation.csv` は上書き可。書き込みは一時ファイルに
      書いて `os.replace` で原子的に差し替える。書き方は既存 `csv_exports.write_csv_rows` と
      `csv_utils` を再利用し、`make_daily_csv_stem` の命名に揃える。
- [ ] `FxDailyAutomationConfig` に `run_execution_layer: bool = True` (new)、
      `FxDailyAutomationResult` に `execution_csv_path: str | None = None`、
      `execution_evaluation_csv_path: str | None = None`、`execution_decisions_recorded: int = 0`、
      `execution_evaluations_recorded: int = 0` (new) が追加され、既存テストは無変更で通る。
- [ ] `run_fx_daily_protocol_once` が `config.write_csv_exports and config.run_execution_layer` の
      ときだけ次を行う (spec §7):
      - Step 3b: batch が存在し (`forecast_batch_id is not None`、作成直後でも既存でも) かつ
        `history/{date}/{batch}/execution.csv` が**完全な形で存在しない** (`is_complete_decision_file`
        が False。無い・header のみ・途中で切れている) ときに限り、
        `FxForecastRepository.load_fx_forecast_batch` で読んだ batch、`build_baseline_context(snapshot)`、
        `snapshot.completed_windows` の終値から `build_execution_decisions` を呼ぶ。通常は batch を作った
        run がこれに当たる。前 run が判断の書き込みに失敗していれば次の run がこの経路で回復する
        (live spot はその時刻で取り直す。`entry_time_utc` がそれを記録する)。既にファイルがあれば
        何もしない (live spot も取り直さない)。live spot は `fetch_live_spot_yahoo` を**1 回**呼び、
        失敗時は warning ログ + `entry_status "live_unavailable"`。
      - Step 4c (Step 4b の後): **archive 全体の独立スキャン**。`history/*/*/execution.csv` を列挙し
        (`glob`、ディレクトリ名から日付 D と batch id を取る)、完全な判断ファイルで、同 dir に完全な
        `execution_evaluation.csv` (6 book 揃い) が無く、`make_outcome_id(pair, D, next_as_of_jst(D),
        schema_version)` の outcome が `FxOutcomeEvaluationRepository.load_fx_outcome_record` で読める
        ときだけ、判断行を読んで `evaluate_execution_decisions` を呼ぶ。outcome が無い窓 (当日の
        pending) と条件を満たさない窓は何もしない (warning 不要)。候補は通常 0〜1 件。Step 4 の直前窓も
        Step 4b の catch-up 窓もこのスキャンに含まれるので個別の配線はしない。評価の書き込みに失敗した
        窓は `outcome_catchup_days` の外に出ても次 run のスキャンで再試行される。
      - Step 5b / 6b: export と publish。`execution_evaluation.csv` は評価した窓の batch dir に書く
        (当日の dir ではない)。
      - 執行層の例外はすべて捕捉して warning ログにし、`FxDailyAutomationResult` の該当フィールドを
        `None` / `0` のまま返す。予測・outcome・評価・CSV の既存 Step に影響しない。判断の書き込みに
        失敗した日は、上の「`execution.csv` が無ければ作る」経路により次の run (同日の retry または
        翌日の run が同じ batch を見る場合) で再試行される。評価の書き込み失敗も同様で、Step 4c は
        `execution_evaluation.csv` が無い窓を毎 run 再評価する (outcome が DB にある限り冪等)。
- [ ] 全 Step で `datetime.now` を使う箇所は automation 側に限り、`execution.py` には入れない。
- [ ] `docs/specs/fx_execution_layer_v1.md` の Status を `Implemented (v1, FX-EXEC-LAYER)` に更新し、
      逸脱があれば §12 に記す。`docs/specs/fx_daily_automation_v1.md` の Step 一覧に 3b / 4c / 5b / 6b を
      追記、`docs/specs/fx_daily_csv_exports_v1.md` §3 の layout に `execution.csv` /
      `execution_evaluation.csv` / `latest/execution.csv` を追記する。

## Scope
- IN: `src/ugh_quantamental/fx_protocol/{execution_models,execution,execution_exports}.py` (new)、
  `data_sources.py` (`fetch_live_spot_yahoo` の追加のみ)、`automation.py` (Step 3b/4c/5b/6b の追加)、
  `automation_models.py` (フィールド追加)、`tests/fx_protocol/test_execution*.py` (new)、
  `tests/fx_protocol/test_automation.py` (追加のみ)、上記 3 spec。
- OUT: `engine/`、`forecasting.py`、`market_ugh_builder.py`、`outcomes.py`、`csv_exports.py` の既存関数
  シグネチャ、`monthly_review.py` / `monthly_governance.py`、`reporting.py` / `weekly_reports_v2.py`、
  `scripts/` (集計と backfill は FX-EXEC-REPORTING)、ORM と Alembic (v1 は CSV のみ)、
  `.github/workflows/*` (`run_execution_layer` は既定 True なので env 追加不要)、
  spec §4 の book 定義とパラメータ値 (変更は escalation)。

## Allowed Dependencies
なし (stdlib `urllib` と既存依存のみ)。

## Implementation Hints
- 判断の入力: batch は `PersistedDailyForecastBatch.forecasts` (`forecast_models.py`)、各行は
  `ForecastRecord`。automation は `{f.strategy_kind: f.forecast_direction for f in batch.forecasts}` を
  `forecast_directions` に渡す。β は `StrategyKind.ugh_v2_beta`、単純テクニカルは
  `StrategyKind.baseline_simple_technical`。
- `BaselineContext` (`forecast_models.py`) の `previous_close_change_bp: float | None` と
  `trailing_mean_abs_close_change_bp: float` をそのまま使う。`build_baseline_context(snapshot)` は
  `request_builders.py:37`。
- 評価の入力: `OutcomeRecord` (`models.py`) の `outcome_id`, `window_start_jst`, `realized_open`,
  `realized_close` をスカラーで渡す。Step 4c のスキャンは `make_outcome_id(config.pair, D,
  next_as_of_jst(D), config.schema_version)` (`ids.py`、Step 4 と同じ引数規約) で id を再計算し
  `FxOutcomeEvaluationRepository.load_fx_outcome_record(session, outcome_id)` で読む (None なら skip)。
  `prev_as_of_jst` / `next_as_of_jst` は `calendar.py`。
- Step 4c で読む判断行は CSV から `ExecutionDecision` に復元する (型変換は `csv_exports` の
  `_blank` 規約に揃える: 空文字は None)。
- `publish_csv_to_history_only` (`csv_exports.py:426`) が history/ だけに書く既存パターン。
  `publish_execution_csvs` はそれに倣いつつ `latest/execution.csv` も書く。
- live spot の取得は `scripts/run_fx_price_alert.py` の `fetch_yahoo_daily` (484 行) と同じ
  payload 形状。テストは `urllib.request.urlopen` を monkeypatch するか、`data_sources` の
  関数を `MagicMock` に差し替える (`tests/fx_protocol/test_automation.py` の
  `TestYahooFinanceFxMarketDataProvider` に同じ手法がある)。
- automation の統合テストは `TestRunFxDailyProtocolOnce._make_session` / `_make_provider` /
  `_build_windows_raw` を再利用する。`run_fx_daily_protocol_once` は `now_utc` を受けるので
  fixing 後の時刻を渡す。
- `forecast_created` の判定は Step 3 の既存変数をそのまま使う (batch が既存なら False)。

## Required Outputs
- Branch name: `codex/fx-exec-layer`
- PR title: `feat(fx): execution layer v1 - record and evaluate six paper-trading books`
- Expected files changed:
  `src/ugh_quantamental/fx_protocol/execution_models.py`, `execution.py`, `execution_exports.py`
  (new); `data_sources.py`; `automation.py`; `automation_models.py`;
  `tests/fx_protocol/test_execution.py`, `test_execution_exports.py` (new);
  `tests/fx_protocol/test_automation.py` (追加のみ); `docs/specs/fx_execution_layer_v1.md`;
  `docs/specs/fx_daily_automation_v1.md`; `docs/specs/fx_daily_csv_exports_v1.md`
- Required tests:
  - 判断規則: 6 book × (flat / shock / 4-4 / 3-1 flat / 3-1 反対 / 2-2 / divergence 一致・不一致 /
    momentum 正・負・ゼロ) を parametrized で固定。サイズ式 (`trailing 60bp → 0.5`、`20bp → 1.0`、
    `0bp → 1.0`)。batch 欠落・variant 欠落・closes 不足の `ValueError`。出力順が `BookId` 順。
  - 評価式: live あり / live なし / side 0 の 3 ケースで `pnl_live_bp` / `pnl_bar_bp` / `cost_live_bp` /
    `cost_bar_bp` / `hit` を数値で固定 (例: entry live 150.00、`realized_open` 150.10、close 150.30、
    side +1 → `pnl_live_bp 20.0`、`pnl_bar_bp ≈ 13.32`、`cost_live_bp ≈ 0.6667`、`cost_bar_bp ≈ 0.6662`)。
    空・batch id 不一致・窓不一致・価格 0 以下の `ValueError`。`backfill_bar` の判断行を評価した
    ケース (live 系列が None)。
  - `fetch_live_spot_yahoo`: 正常 payload、`result` 空、`regularMarketPrice` 欠落、HTTP 例外の
    4 ケース (後者 3 つは `FxDataFetchError`)。ネットワークは monkeypatch。
  - exports: fieldnames が spec の列順、publish が既存 `execution.csv` を上書きしないこと、
    `latest/execution.csv` が更新されること (`tmp_path`)。
  - automation: (a) `forecast_created` の run が 6 行の `execution.csv` を書き
    `execution_decisions_recorded == 6`、(b) 同日 2 回目の run (batch 既存、`execution.csv` あり) が
    判断を作らず既存ファイルを変えない (live spot も呼ばれない)、(b2) batch 既存で `execution.csv` が
    無い run が判断を作る (回復経路)、(c) 翌日の run が `execution_evaluation.csv` 6 行を前日の batch dir に書き
    `execution_evaluations_recorded == 6`、(c2) `outcome_catchup_days + 3` 営業日前の窓の
    `execution_evaluation.csv` を消して run すると (outcome は DB にある) スキャンが書き直す、(c3) 既に
    完全な `execution_evaluation.csv` がある窓は再評価されない、(c4) header のみの `execution.csv` は
    不完全とみなされ判断が作り直される、(d) live 取得失敗で `entry_status live_unavailable` かつ
    run は成功、(e) `run_execution_layer=False` で何も書かない、(f) 執行層で例外を起こしても
    `forecast_created` と outcome 記録は保たれる。
  - 既存テストは無変更で通る。

## Done When
- All acceptance criteria are checked
- `ruff check .` passes
- `pytest -q` passes
- PR body starts with a Completion Summary
