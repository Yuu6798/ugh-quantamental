# FX Execution Layer v1 — UGH 売買エンジン (執行層) とベンチマーク観測スキーム

Status: **Implemented (v1, FX-EXEC-LAYER — 判断の記録・評価・automation 配線; 集計・ゲート・backfill は
FX-EXEC-REPORTING で実装済)**
Owner: Claude (design) / Codex (implementation)
Related: `fx_daily_automation_v1.md` (Step 構成)、`fx_daily_csv_exports_v1.md` (CSV 規約)、
`fx_ugh_engine_v2.md` (予測エンジン)、`fx_monthly_governance_v1.md` (統治)、
`docs/engine_review_2026_09_findings.md` §4 (conviction と magnitude の結合の問題)

## 1. Purpose

予測エンジン (`engine/` + `fx_protocol/forecasting.py`) は方向・レンジ・state を出す予測器として
現行の集計と月次レビューを継続する。本 spec はその**外側**に、保存済み予測を消費して日次の仮想
売買判断を**記録・評価・集計**する執行層を定義する。目的は 2 つ:

1. UGH の方向情報を売買損益に変換する方針 (賭け幅・見送り) を、engine の数式から切り離して
   事前登録し、前向き (forward) に検証できる形で観測する。
2. 同じ土俵のベンチマーク (`bench_gpt_m3`、`bench_long`) と並走させ、「UGH 固有の変換が
   追加価値を生むか」を売買損益で判定できるデータを自動で蓄積する。

2026-10 の試算 (`.claude/memory/2026-10-08.md`) で確定した前提:

- UGH β の方向は賭けた日の 60% 前後で当たるが、conviction が逆相関 (低いほど当たる) で、
  magnitude が conviction に比例するため損益はゼロ近辺になる。
- 4 モデル合議は高 conviction 日だけを選ぶ規則で、最悪の部分集合になる。
- 損益の順位は政策ショック日 (|Δ| > 110bp、2026 年は 8 日) のポジションで決まる。
- 63 営業日では t 値 1.3 以下で優位性を判定できない。判定には 100 取引以上・半年以上が要る。
- 予測公開時刻 (20 時台〜翌 3 時 JST) の価格を保存していないため、約定に正直な検証ができない。

## 2. Scope

IN:
- 執行判断の生成 (純関数)、公開時刻 spot の取得と記録、翌日の評価、CSV 永続化、
  週次・月次の集計、合格ゲートの定義。
- `execution_version` による版管理 (予測エンジンの `engine_version` とは独立)。

OUT:
- 予測エンジン (`engine/`、`forecasting.py`、`market_ugh_builder.py`) の変更。
- 実際の発注・口座連携。本 spec は**仮想売買**のみ。
- `monthly_review.py` / `monthly_governance.py` の flag・判定ロジック。執行層の集計は
  governance 入力に加えない (v1)。
- ORM テーブルと Alembic migration。v1 は CSV (history/ 配下) を唯一の永続化とする。
  `fx_daily_csv_exports_v1.md` §4 の「CSV は永続記録の正本」に揃える。

## 3. Timing contract (最重要)

予測 batch `as_of_jst = D 08:00 JST` の対象窓は `[D 08:00, D+1 08:00)`。予測が計算・公開されるのは
run 実行時 (観測実績 18:00〜翌 03:00 JST) であり、**D 08:00 に約定した前提は未来情報ではなく
約定価格の捏造**になる (予測の情報集合は 08:00 で閉じている。`AlphaVantageXMarketDataProvider`
の `current_spot` は直近完了窓の終値)。

そこで執行層は 1 判断につき 2 つの価格を記録する:

| 価格 | 定義 | 役割 |
|---|---|---|
| `entry_price_live` | 判断時刻に取得した live spot (§6) | **正本**。約定に正直な損益 |
| `realized_open` | 窓 D の outcome の始値 (`OutcomeRecord.realized_open`) | 楽観側の上限 (当日足方式)。live が欠けた日の参考値 |

出口は両方とも窓 D の終値 `OutcomeRecord.realized_close` (D+1 08:00 JST)。保有は最長 1 窓、翌日
持ち越しなし。従来の試算で使った「翌営業日足」方式は、live 価格が記録される v1 では廃止する
(別仮説の検証になるため)。

判断は、batch D が存在し、かつ `history/{D}/{batch}/execution.csv` が**完全な形で未発行**の run が
記録する (完全 = 6 book それぞれ 1 行が検証付きで読める。header のみ・途中で切れたファイルは未発行と
同じ扱いで置き換える。書き込みは一時ファイルから `os.replace` で原子的に行う)。
通常は batch D を作成した run がこれに当たる。同日の 2 本目以降の retry は、ファイルがあれば
live spot を取り直さず何もしない。前 run が判断の書き込みに失敗していた場合だけ、次の run が
その時刻の live spot で記録して回復する (`entry_time_utc` が実際の判断時刻)。回復 run の baseline と closes
は当日の provider snapshot ではなく archive の `history/{D}/{batch}/input_snapshot.json` から再導出する
(forecast と同じ入力。archive が無ければ当日 snapshot で代用し warning)。既存ファイルは
決して上書きしない。繰り越し run (#130 / #135) は batch を作らないが、既存 batch の `execution.csv`
が欠けていれば同じ回復経路で記録する。ただし判断を作るのは **run 時刻 (`now_utc`) が窓の終了
`window_end_jst` (翌営業日 08:00 JST) より前**のときだけ。窓が閉じた batch (前営業日 fallback で
翌朝に作られた batch、前日の全 run が書き込みに失敗した batch) には live 判断を作らない — 窓の終わりに
取った live 価格は約定価格として意味を持たないため。その日の live 観測は失われたものとして受け入れ、
§10 の backfill が `backfill_bar` 行で埋める (bar 系列のみ、ゲート対象外)。persisted batch 全体を
走査して判断を作り直す回復経路は設けない。

## 4. Books (事前登録、`execution_version = "x1"`)

| book_id | 方向 | サイズ (資産比) | 見送り条件 (`skip_reason`) |
|---|---|---|---|
| `ugh_x1` (本線) | `ugh_v2_beta` の `forecast_direction` | `min(1.0, 30.0 / trailing_mean_abs_close_change_bp)` | `flat`: β が FLAT。`shock_filter`: `abs(previous_close_change_bp) > 2.5 × trailing_mean_abs_close_change_bp` |
| `ugh_beta_unit` | 同上 | 1.0 | `flat` |
| `ugh_consensus` | 4 variant の up/down 数で決定 | 4/4 一致 1.0、3 一致 + 1 FLAT 0.5 | `no_consensus`: それ以外 (3 対 1 の反対、2 対 2、FLAT 優勢を含む) |
| `ugh_divergence` | β の方向 | 1.0 | `flat`、`agree_with_technical`: β の方向 = `baseline_simple_technical` の方向 |
| `bench_gpt_m3` | `sign(C[t-2] - C[t-5])`、C[t-1] = 直近完了窓の終値 (`completed_windows[-1].close_price`)、t = D | 1.0 | `momentum_zero`: 差がゼロ |
| `bench_long` | 常に +1 | 1.0 | なし |

- 入力はすべて判断時刻に確定しているもの: 当日の forecast batch の方向 (`strategy_kind → forecast_direction`
  の対応。builder は `ForecastRecord` ではなくこの対応を受け取るので、CSV からの backfill でも同じ
  関数を使える)、`BaselineContext` (`build_baseline_context(snapshot)` の `previous_close_change_bp` /
  `trailing_mean_abs_close_change_bp`)、snapshot の完了窓終値、`entry_status` と live 価格。
- `ugh_x1` のサイズは「日次 30bp のボラ目標、レバ 1 倍上限」。ショックフィルタは
  「前窓が 2.5σ 相当を超えたら翌窓は賭けない」。いずれも conviction を使わない。
- `ugh_divergence` は試算で「β が単純テクニカルと割れた日に 25 勝 10 敗」だった観察の
  **前向き検証用**であり、採用根拠ではない。
- 現金 (取引なし) は book にしない。各 book の資産曲線を初期資産と比べれば足りる。
- パラメータ (30.0、2.5、0.5、初期資産 3,000,000 円、往復コスト 0.01 円/USD) は定数として
  `execution.py` に置き、変更は本 spec の改訂と `execution_version` の bump を伴う。
  月次レビューは観測するだけで、途中で調整しない (§9)。

## 5. Records

### 5.1 `ExecutionDecision` (1 run × 6 行)

| 列 | 内容 |
|---|---|
| `execution_version` | `"x1"` |
| `book_id` | §4 |
| `as_of_jst`, `window_end_jst`, `forecast_batch_id` | 消費した batch (`ForecastRecord` と同値) |
| `source_strategy_kind` | `ugh_x1` / `ugh_beta_unit` / `ugh_divergence` は `ugh_v2_beta`。`ugh_consensus` (単一の元戦略が無い) と bench 2 つは空 |
| `side` | `1` / `-1` / `0` |
| `size` | `[0.0, 1.0]`、`side == 0` なら `0.0` |
| `skip_reason` | §4 の識別子、取引時は空 |
| `entry_status` | `live` / `live_unavailable` / `backfill_bar` (§10 の backfill 行。live 価格なし) |
| `entry_price_live` | live spot、取得失敗時は空 |
| `entry_time_utc` | live spot の取得時刻 (失敗時は判断時刻) |
| `entry_vendor`, `entry_feed` | `yahoo_finance` / `chart/USDJPY=X` (§6) |
| `beta_direction`, `consensus_up_count`, `consensus_down_count`, `technical_direction`, `momentum_3d`, `trailing_mean_abs_close_change_bp`, `previous_close_change_bp` | 監査用の入力値 |

### 5.2 `ExecutionEvaluation` (窓の outcome 確定時に 1 行 × 6 book)

| 列 | 内容 |
|---|---|
| `execution_version`, `book_id`, `as_of_jst`, `window_end_jst`, `forecast_batch_id`, `outcome_id` | キー |
| `side`, `size`, `skip_reason`, `entry_status`, `entry_price_live` | 判断の写し。`skip_reason` は見送り内訳の集計用 (取引行は空) — 集計層は評価ファイルだけを読む |
| `realized_open`, `realized_close` | `OutcomeRecord` の写し。出口 = `realized_close` |
| `pnl_live_bp` | `side × (realized_close − entry_price_live) / entry_price_live × 1e4`、live 欠落時は空 |
| `pnl_bar_bp` | `side × (realized_close − realized_open) / realized_open × 1e4` |
| `cost_live_bp` | `abs(side) × 0.01 / entry_price_live × 1e4`。live 価格が無い行は空、`side == 0` なら 0 |
| `cost_bar_bp` | `abs(side) × 0.01 / realized_open × 1e4`。`side == 0` なら 0 |
| `hit` | `side × (realized_close − realized_open) > 0`、`side == 0` なら空 |
| `evaluated_at_utc` | 評価時刻 |

行の `pnl_*_bp` / `cost_*_bp` は**単位サイズ** (size 1.0) の値で、capture など方向の価値の指標に使う。
売買方針そのものの日次リターンは size を掛けた `size × (pnl_live_bp − cost_live_bp)` (live 系列) /
`size × (pnl_bar_bp − cost_bar_bp)` (bar 系列) で、資産曲線・t 値・ゲートはこちらを使う
(どちらも自分の entry 価格で正規化する)。金額 (円) は行に持たない。資産曲線は集計層 (§8) が行を
時系列順に畳み込んで計算する
(`position_usd = equity × size / entry`、`pnl_jpy = side × position_usd × (exit − entry) − abs(side) × position_usd × 0.01`、
初期資産 3,000,000 円、複利)。live 系列は `entry_status == live` の行だけで構成し、欠落日は
取引なし (資産据え置き) として数え、欠落率を別途報告する。

## 6. Live spot

- 取得元: Yahoo Finance chart API の `meta.regularMarketPrice` (既存の
  `YahooFinanceFxMarketDataProvider` と `scripts/run_fx_price_alert.py` の `fetch_yahoo_daily` が
  同じ endpoint を使用)。API key 不要。`data_sources.py` に `fetch_live_spot_yahoo(timeout=30)`
  (new) を追加し、`(spot, retrieved_at_utc)` を返す。
- 取得は judgment 1 回につき 1 回。失敗 (`FxDataFetchError` または `ValueError`) は warning ログと
  `entry_status = live_unavailable` で記録し、**run を失敗させない**。
- live spot は mid の参考値であり約定価格を保証しない。スプレッドは往復コスト (0.01 円/USD =
  約 0.6bp) に含めたものとみなす。

## 7. Automation integration

`run_fx_daily_protocol_once` (`automation.py`) に次を追加する。いずれも
`config.write_csv_exports and config.run_execution_layer` のときだけ動く。

| Step | 内容 |
|---|---|
| 3b (Step 3 の直後) | batch が存在し `history/{date}/{batch}/execution.csv` が無く、`now_utc < window_end_jst` のとき: batch と `build_baseline_context(snapshot)` と snapshot から 6 件の `ExecutionDecision` を作る (純関数 `build_execution_decisions`)。live spot を取得して記録する。ファイルがあれば何もしない (§3) |
| 4c (Step 4b の直後) | **archive 全体の独立スキャン**: `history/*/*/execution.csv` のうち完全なもので、同 dir に完全な `execution_evaluation.csv` が無い batch を列挙し、その窓の outcome が DB にある (`make_outcome_id` で id を再計算して `load_fx_outcome_record`) ものだけ `ExecutionEvaluation` 6 件を作る (純関数 `evaluate_execution_decisions`)。outcome が無い窓 (当日の pending) は skip。候補は通常 0〜1 件なので全走査でも軽い。Step 4 の直前窓と Step 4b の catch-up 窓はこのスキャンに含まれるので個別の配線は不要。評価の書き込みに失敗した窓は、`outcome_catchup_days` の外に出ても次 run のスキャンで再試行される |
| 5b / 6b | `execution.csv` / `execution_evaluation.csv` を `history/{date}/{batch}/` に書き、`latest/execution.csv` を更新する。既存の `execution.csv` は上書きしない (§3) |

`FxDailyAutomationConfig` に `run_execution_layer: bool = True` (new) を追加。
`FxDailyAutomationResult` に `execution_csv_path`, `execution_evaluation_csv_path` (評価した窓のうち
最新のもの), `execution_decisions_recorded: int`, `execution_evaluations_recorded: int` (全窓の合計),
`execution_evaluation_windows: tuple[ExecutionEvaluationWindowResult, ...]` (スキャンが評価した窓を
全件、`forecast_batch_id` / `as_of_jst` / `evaluation_csv_path` / `evaluation_count`) (new) を追加。

失敗分離: 執行層の例外は Step 8 と同じく non-fatal (warning ログ、結果に `None`)。予測・outcome・
評価の記録を止めない。

## 8. Aggregation (FX-EXEC-REPORTING)

`execution_reporting.py` が集計・合格ゲート・artifact を担う。時計を読まず (`generated_at_utc` は
呼び出し元が渡す)、`export_*` 以外は読み取り専用、network なし、SQLAlchemy 非依存。activation marker
`EXECUTION_ACTIVATION_AS_OF` と除外集合 `EXECUTION_EXCLUDED_AS_OF` は呼び出し時に module 属性として
参照する (テストが境界を patch できる)。

### 8.1 Collector

`collect_execution_evaluation_rows(history_dir, *, generated_at_utc) -> CollectedExecutionEvaluations`
が `history/<date>/<batch>/` を sorted 走査 (`labeled_observations.collect_evaluated_forecast_rows`
と同じ規約) して次を返す。`history_dir` が無ければ空の archive として扱う。

- `rows`: `execution_evaluation.csv` (`load_execution_evaluations_csv` で読めないファイルは warning
  で skip) の生の行を `(forecast_batch_id, book_id)` で重複排除 (先勝ち) したもののうち、**完全**
  (6 book が揃う) かつ **重複でない** batch の行。`(as_of_jst, forecast_batch_id, book 順)` で整列。
- `incomplete_batches` (`forecast_batch_id`, `execution_version`, `as_of_jst`, `missing_books`,
  `inconsistent_fields`): 6 book が揃わない `forecast_batch_id`、または 6 行が `execution_version` /
  `as_of_jst` で食い違う batch (版境界・部分コピー。`inconsistent_fields` に列名、先頭行の値に黙って
  丸めない。block / report の振り分けは最も遅い `as_of_jst` と、1 行でも現行版なら現行版で行う)。
  集計にもゲートにも入れない。
- `incomplete_decision_batches` (`history/{date}/{batch}` 相対 path): `execution.csv` はあるが完全で
  ない dir。完全 = 6 book 1 行ずつが検証付きで読め、`forecast_batch_id` / `execution_version` /
  `as_of_jst` / `window_end_jst` が 1 組 (header のみ、6 book 未満、読めない、batch id・版・窓の混在は
  不完全。先頭行の値に丸めない)。
- `missing_evaluations` (`forecast_batch_id`, `execution_version`, `as_of_jst`, `window_end_jst`):
  完全な `execution.csv` で、同じ batch id **かつ同じ `execution_version` / `as_of_jst` /
  `window_end_jst`** の完全な評価ファイル (6 行がその 4 つで一致するもの) が archive のどこにも無く、
  `window_end_jst <= generated_at_utc` のもの。pending 窓は入れない。版や窓が違う評価ファイルは
  別 batch の評価であって、この判断ファイルの評価にはならない。
- `duplicate_batches` (日付): 同じ `(execution_version, as_of_jst の日付)` に完全 batch (判断
  ファイルまたは評価 batch) が 2 つ以上ある日。その batch はすべて `rows` から外す (黙って片方を
  選ばない)。
- `missing_decisions` (`as_of_jst`, `forecast_batch_id`): 期待日のうち、**自分の日付 dir** に現行版
  (`execution_version == EXECUTION_VERSION`) の完全な `execution.csv` が 1 つも無い日。
  `forecast_batch_id` はその日の dir の `forecast.csv` に `as_of_jst` がその日の行があればその id、
  無ければ None。forecast の有無で欠落かどうかは変わらない。
- `missing_live` (日付): 期待日のうち、自分の日付 dir の現行版の完全な判断ファイルに `ugh_x1` の
  `entry_status == live` の行が無い日 (ファイル無し・`backfill_bar`・`live_unavailable`・旧版のみ)。

読めない `execution_evaluation.csv` (検証エラー・I/O エラー) は collector が warning を 1 行出すだけで、
評価側の inventory には現れない。同 dir に完全な `execution.csv` があれば判断側の棚卸しが拾い、窓が閉じて
いれば `missing_evaluations` (日付と版に応じて block または `archive_defects`) として見える。判断ファイル
の無い activation 前の backfill batch は報告されず、単に bar 系列から抜ける。

期待日 `expected_decision_days(generated_at_utc) -> (expected, excluded)`: `EXECUTION_ACTIVATION_AS_OF`
から順に、protocol 営業日 (`calendar.is_protocol_business_day`) で窓が閉じた日
(`next_as_of_jst(D) <= generated_at_utc`) を集め、`EXECUTION_EXCLUDED_AS_OF` に含まれる日は
`excluded` 側に分ける。

block と archive の振り分け: `is_gate_blocking_defect(as_of_jst, execution_version)` が True —
日付 (dir の日付または行の `as_of_jst`) が `EXECUTION_ACTIVATION_AS_OF` 以降、かつ version が現行値
または読めない (None、`incomplete_decision_batches` の場合。dir 名が日付でない dir も block 側) —
の欠損だけが上の 6 つの inventory に入り、`blocked_reasons()` の母集団になる。それ以外 (activation
前、他 version) は同じ 6 フィールドの `archive_defects` に入り、報告のみで block しない。
`missing_decisions` / `missing_live` は期待日由来なので `archive_defects` 側は常に空。

### 8.2 Report

`run_execution_report(csv_output_dir, *, start_as_of_jst, end_as_of_jst, generated_at_utc) -> dict`
(純粋な読み、書き込みなし)。窓は行の `as_of_jst` の **JST 日付**で比較し両端を含む。
`None` はその端を無制限にし、両方 None で history 全体。返す dict (JSON 化可能):

| キー | 内容 |
|---|---|
| `report_kind` | `"fx_execution"` |
| `execution_version` | 現行 `EXECUTION_VERSION` |
| `generated_at_utc` | 渡された値 (ISO 8601、UTC) |
| `window` | `{start_as_of_jst, end_as_of_jst}` (JST 日付 `YYYY-MM-DD`、無制限なら null) |
| `row_count`, `batch_count` | 窓内の評価行数と完全 batch 数 |
| `history_row_count` | history 全体の (完全・非重複) 評価行数 |
| `strata[version]` | 版ごとの層 (版を跨いで足さない): `execution_version`, `row_count`, `batch_count`, `first_as_of_jst`, `last_as_of_jst`, `books[book_id]` (§8.3), `benchmark_deltas` (§8.4) |
| `gate` | §9 の合格ゲート (期間窓に依存しない) |
| `inventory` | §8.1 の 6 inventory それぞれ `{count, items}` と、同形の `archive_defects` |

### 8.3 Book metrics (`strata[version].books[book_id]` = `execution_{scope}.csv` の列)

列順は `EXECUTION_REPORT_BOOK_FIELDNAMES`。CSV では None は空セル、`skip_counts` は
`reason=count;reason=count` (理由名順。`|` は md の表セルを壊すので使わない)。「取引行」は `side != 0` の行、「live 行」は
`entry_status == live` の行。

| 列 | 定義 |
|---|---|
| `execution_version`, `book_id` | 層と book |
| `decision_count` | 窓内の評価行数 (= 判断数) |
| `trade_count` | 取引行数 |
| `live_trade_count` | 取引行のうち live で `pnl_live_bp` / `cost_live_bp` が揃う行数 (live 系列の mean / sd / t の n) |
| `skip_counts` | 見送り行 (`side == 0`) の `skip_reason` 別件数 |
| `live_coverage_rate` | live 行数 / `decision_count` |
| `direction_hit_rate` | 取引行のうち `hit` の割合 (取引なしなら None) |
| `capture_bp` | `Σ side × (realized_close − realized_open) / realized_open × 1e4` (取引行、単位サイズ) |
| `signed_bp_live_mean` / `_sd` / `_t` | `size × (pnl_live_bp − cost_live_bp)` (live の取引行のみ) の平均、標本標準偏差 (`statistics.stdev`、n − 1)、t 値 `mean / (sd / √n)`。**sd は n = 2 から出す** (n < 2 は None)。**t は n < 3 または sd == 0 なら None** (sd が出ていても t だけ None になる。テストで固定) |
| `signed_bp_bar_mean` / `_sd` / `_t` | `size × (pnl_bar_bp − cost_bar_bp)` (全 entry_status の取引行) の同上 |
| `pnl_jpy_live`, `pnl_jpy_bar` | 資産曲線の最終資産 − 初期資産 (円)。§5.2 の式 (初期 3,000,000 円、複利、`position_usd = equity × size / entry`、`pnl_jpy = side × position_usd × (exit − entry) − |side| × position_usd × 0.01`、exit = `realized_close`) を `as_of_jst` 昇順に畳む。live 系列は live 行のみ (entry = `entry_price_live`)、bar 系列は全行 (`backfill_bar` を含む、entry = `realized_open`)。見送り行は据え置き。取引行に正の entry が無ければ ValueError |
| `final_equity_jpy_live`, `final_equity_jpy_bar` | 最終資産 (円) |
| `max_drawdown_live`, `max_drawdown_bar` | `max_t (peak_t − equity_t) / peak_t` (0 以上 1 以下の正の大きさ) |
| `profit_factor_live` | live 資産曲線の取引ごとの純損益 (コスト控除後) について `Σ 正 / |Σ 負|`。負の取引が無い (取引が無い) ときは None (`inf` は出さない) |
| `cost_jpy_live`, `cost_jpy_bar` | 各系列の資産曲線で発生した円コスト合計 (`|side| × position_usd × 0.01`) |

md の数値書式: 率は `_fmt_pct`、bp は `_fmt_bp` (`weekly_report_exports` と同じ)、円は 3 桁区切りの
整数、t 値と PF は小数 2 桁、None は `-`。

### 8.4 Benchmark deltas (`strata[version].benchmark_deltas[bench]`)

`bench_gpt_m3` / `bench_long` それぞれについて `pnl_jpy_live_delta` (= `ugh_x1` の `pnl_jpy_live` −
bench の `pnl_jpy_live`) と `capture_bp_delta` (= `capture_bp` の差)。どちらかの book が層に無ければ
null。

### 8.5 Artifacts

- `export_execution_report_artifacts(report, csv_output_dir, scope, date_str) ->
  {execution_{scope}_md, execution_{scope}_csv, execution_{scope}_json}` (絶対 path) が
  `analytics/execution/{scope}/{date_str}/execution_{scope}.{md,csv,json}` を書く (`scope` は
  `weekly` / `monthly`。path 区切りを含む scope は ValueError)。md は層ごとに
  `## Stratum execution_version=<v>` (`### Books` 表、`### Benchmark deltas` 表)、
  `## Acceptance gate` (コホート 1 行、4 条件の表、`Passed: yes|no`、`Blocked reasons: <list|none>`)、
  `## Archive inventory (blocking)` と `### Archive defects` (inventory ごとの件数と items)、`## Notes`。
  窓内に完全 batch が無ければ `No complete batches in the window.`。csv は §8.3 の book 行 (層 × book)。
  json は report dict そのまま。`latest/` には触れない。
- `export_execution_latest_summary(cumulative_report, csv_output_dir) -> path` が
  `latest/execution_summary.json` を書く。引数は両端 None の report (history 全体) に限り、窓付きの
  report は ValueError で拒否するので、latest の内容は直前に走った scope に依存しない。

### 8.6 Callers

| 呼び出し元 | 窓 | ラベル (dir 名) |
|---|---|---|
| `scripts/run_fx_daily_protocol.py` の金曜 weekly block (`FX_LAST_RETRY=1`、weekly v2 の `export_weekly_report_artifacts` と `[OK]` の後) — `generate_execution_weekly_artifacts(csv_output_dir, report_date_jst, generated_at_utc)` | `report_window.resolve_business_day_window(report_date, 5)`、`report_date = as_of_jst + 1 日` (土曜) → 月〜金 | `weekly/<report_date の YYYYMMDD>` (weekly v2 と同じ dir 名) |
| `scripts/run_fx_analysis_pipeline.py` weekly モード (既存 weekly の直後) — `run_execution_report_step(csv_output_dir, "weekly", report_date_jst, FX_WEEK_DAYS, generated_at_utc)` | `resolve_business_day_window(FX_REPORT_DATE, FX_WEEK_DAYS)` | `weekly/<FX_REPORT_DATE>` |
| 同 monthly モード (既存 monthly pipeline の直後) — `run_execution_report_step(..., "monthly", ..., FX_MONTH_DAYS, ...)` | `resolve_business_day_window(FX_REPORT_DATE, FX_MONTH_DAYS)` (monthly review と同じ月窓) | `monthly/<窓の最終日の YYYYMM>` (4/1 の run は `202603`) |

いずれも scoped artifact を書いた直後に history 全体の report で `latest/execution_summary.json` を
書き直す。失敗は non-fatal: 金曜 block は `[WARN] Execution report generation failed (non-fatal): ...`、
pipeline は `[WARN] Execution <scope> report generation failed (non-fatal): ...` を出して続行する。
金曜 block は weekly v2 の生成が成功した後にだけ走り、月曜の pipeline weekly モードが安全網になる
(weekly v2 artifact と同じ)。daily script の結果表示 (`=== FX Daily Protocol Summary ===`) には
`execution_decisions_recorded` / `execution_evaluations_recorded` / `execution_evaluation_windows`
(件数) を 1 行ずつ出し、執行層の non-fatal 失敗が warning 以外からも (0 として) 見えるようにする。

## 9. Governance and acceptance gate

- `execution_version` は `x1` で凍結。book の追加・パラメータ変更・サイズ式の変更はすべて
  本 spec の改訂、`x2` への bump、改訂日の記録を伴う。bump 前の行は旧版として残す。
- 月次レビューは執行層の集計を**観測**し、`docs/engine_review_YYYY_MM_findings.md` に 1 節を
  設ける。途中でのパラメータ調整は禁止 (同じデータで選んだ変更は検証にならない)。
- 合格ゲート (`ugh_x1` を実運用候補に進める条件、すべて live 系列。母集団は現行 `execution_version`
  の累積コホート = history 全体の `rows` (§8.1) のうち `execution_version == EXECUTION_VERSION` かつ
  `entry_status == live` の行で、週次・月次の期間窓とは独立。版を bump したらコホートもゼロから始まる。
  取引数・t 値・DD は **`ugh_x1` の行だけ**から計算し、ベンチマーク book は条件 4 の比較にのみ使う):
  1. `ugh_x1` の取引 (`side != 0`) 100 回以上かつ観測 6 か月以上。「6 か月」はコホートの
     `first_as_of_jst` から `last_as_of_jst` までの**暦日数** (`observation_calendar_days` =
     `(last − first).days`) が 182 以上 (定数 `GATE_MIN_CALENDAR_DAYS = 182`)。観測日数
     (`observation_days`、評価済み窓の数) は情報として出すが閾値には使わない
  2. コスト控除後・size 加重の live 日次リターン (`size × (pnl_live_bp − cost_live_bp)`、取引行のみ) の
     t 値 ≥ 2.0 (標本標準偏差 `stdev`、n − 1 で割る。`pstdev` は使わない。n < 3 または sd = 0 なら
     t は None で不充足)
  3. 最大 DD ≤ 10% (`max_drawdown_live` は正の大きさ `max_t (peak_t − equity_t) / peak_t`、0 以上 1 以下。
     判定は `≤ 0.10`: ちょうど 10.00% は合格、10.01% は不合格)
  4. 同コホートの `bench_gpt_m3` と `bench_long` の両方を live 損益 (`pnl_jpy_live`) で上回る (`>`)
- 現行 version の batch に 6 book 未満のもの (§8.1 の `incomplete_batches`)、または完全な `execution.csv`
  があるのに完全な `execution_evaluation.csv` が無い batch (`missing_evaluations`。期待コホートは判断
  ファイルの棚卸しから導く。`window_end_jst` が集計時刻より後の pending 窓は除く)、または
  `execution.csv` はあるが完全でない dir (`incomplete_decision_batches`。version は読めないので dir の
  日付が activation marker 以降なら現行版扱い、それより前は報告のみ)、または**期待日** — `calendar` の
  protocol 営業日のうち activation marker (`execution.EXECUTION_ACTIVATION_AS_OF`、コードに固定した初回
  運用日。最初に publish に成功した日から推定しない — 初日の publish 失敗を見失うため) 以降で窓が閉じた
  日から、明示的に諦めた日 `execution.EXECUTION_EXCLUDED_AS_OF` (追加は §12 に理由を書く PR で行う) を
  引いたもの — に現行版 (`execution_version == EXECUTION_VERSION`) の完全な `execution.csv` が 1 つも無い日
  (`missing_decisions`。archive の forecast の有無には
  依存しない: publish が壊れた日もプロトコルが走らなかった日も同じ欠落)、または期待日のうち `ugh_x1` の
  判断が現行版の live 行でない日 (`missing_live`: ファイル無し・`backfill_bar`・`live_unavailable`・旧版の
  行のみ。backfill では
  消えず、`EXECUTION_EXCLUDED_AS_OF` への理由付き追加でのみ解消。除外日数は常に表示)、または同じ版・
  同じ `as_of_jst` に完全 batch が 2 つ以上ある日 (`duplicate_batches`。黙って片方を選ばず両方除外) が
  1 つでもあれば、条件の現在値は出すがゲートは **blocked** (`passed = False`、`blocked_reasons` に
  `incomplete_batches` / `missing_evaluations` / `incomplete_decisions` / `missing_decisions` /
  `missing_live` / `duplicate_batches`)。欠けた archive を黙って短くした上で合格にはしない
  (昇格証拠は欠落・部分 batch で fail する、`AGENTS.md` §5)。修復は Step 4c の再スキャンか §10 の
  backfill で行い、修復できない欠落は data 側の問題として扱う (ゲートは外さない)。block の判定は
  現行 version かつ **activation marker 以降** (`as_of_jst >= EXECUTION_ACTIVATION_AS_OF`) の batch /
  日に限る (`is_gate_blocking_defect`、§8.1): backfill は activation 前の過去 batch にも現行 version を
  付けるため、version だけで絞ると bar 系列専用の過去欠損が forward の live ゲートを永久に block する。
  activation 前の欠損は `archive_defects` として報告のみ (旧版の欠損も同じく block しない)。
- 不合格なら `x2` として設計し直し、観測を 1 からやり直す (期間を継ぎ足さない)。
- ゲート通過後も実弾の判断は人が行う (本 spec の対象外)。

### 9.1 `gate` のキー

定数は `execution_reporting.py`: `GATE_MIN_TRADE_COUNT = 100`, `GATE_MIN_CALENDAR_DAYS = 182`,
`GATE_MIN_T_STAT = 2.0`, `GATE_MAX_DRAWDOWN = 0.10`。`blocked_reasons` の値と順序は
`GATE_BLOCKED_REASONS`。

| キー | 内容 |
|---|---|
| `execution_version` | 現行版 (コホートの版) |
| `cohort.first_as_of_jst`, `cohort.last_as_of_jst` | コホートの最初と最後の `as_of_jst` (ISO、JST。コホートが空なら null) |
| `cohort.trade_count` | `ugh_x1` の取引行数 |
| `cohort.observation_days` | 評価済み窓の数 (コホート内の `as_of_jst` の種類数) |
| `cohort.observation_calendar_days` | `(last − first).days` (空なら null) |
| `cohort.excluded_days`, `cohort.excluded_as_of_jst` | `EXECUTION_EXCLUDED_AS_OF` のうち期待範囲内の日数と日付 (常に表示) |
| `cohort.signed_bp_live_mean`, `cohort.signed_bp_live_sd` | 条件 2 の系列の平均と標本標準偏差 |
| `criteria.trades_and_duration` | `current {trade_count, observation_calendar_days}`, `threshold {trade_count: 100, observation_calendar_days: 182}`, `met` |
| `criteria.t_stat_live` | `current` (t 値または null), `threshold: 2.0`, `met` (`>=`) |
| `criteria.max_drawdown_live` | `current` (0〜1 または null), `threshold: 0.10`, `met` (`<=`) |
| `criteria.beats_benchmarks` | `current` (`ugh_x1` の `pnl_jpy_live`), `threshold {bench_gpt_m3, bench_long}` (各 `pnl_jpy_live`、行が無ければ null), `met` (両方を `>` で上回る。null があれば不充足) |
| `passed` | `blocked_reasons` が空かつ 4 条件すべて `met` |
| `blocked_reasons` | inventory が空でない理由のリスト (`incomplete_batches`, `missing_evaluations`, `incomplete_decisions`, `missing_decisions`, `missing_live`, `duplicate_batches` の順。通常は空) |

## 10. Backfill

`scripts/backfill_execution_history.py --fxdata-dir <dir> [--dry-run]` が保存済み予測 (2026-05-08
以降) について `execution.csv` / `execution_evaluation.csv` を `entry_status = backfill_bar` で生成する
(live なし、`pnl_live_bp` / `cost_live_bp` 空)。`--fxdata-dir` は `fx-daily-data` の checkout root
(`<dir>/csv/history`) または CSV root そのもの (`<dir>/history`; どちらも無ければ exit 1)。時計も
network も使わず、再実行で byte 同一の出力になる。2026-05-07 以前は予測が無いので対象外 (2026-10-08 の
Jan〜Oct 再計算は分析であり、観測記録には入れない)。

入力の結合は history 全体の横断 join (評価と outcome は翌日の batch dir、または catch-up の END-dir に
あるため): (1) `evaluation.csv` の行を `forecast_id`、`outcome.csv` の行を `outcome_id` でグローバルに
索引する (後の dir が勝つ、`labeled_observations.collect_evaluated_forecast_rows` と同じ)、(2)
`forecast.csv` の行を `forecast_batch_id` ごとに `forecast_id` で重複排除して集める (catch-up の END-dir
コピーが 2 つ目の batch になることはない)。batch の正本 dir は行の `as_of_jst` から
`history/{as_of:%Y%m%d}/{forecast_batch_id}/` で、snapshot はそこに直接解決する (日付だけで探さない)。
forecast 行の無い `execution.csv` dir も unit に入れ、`missing_forecast` として報告する。unit は
`(date, forecast_batch_id)` 順に処理する。

| batch の状態 | 結果 (summary のカウンタ) |
|---|---|
| `execution.csv` と `execution_evaluation.csv` が両方完全 | `already_complete`。何もしない (完全な既存ファイルは一切上書きしない) |
| 評価は完全だが判断が不完全 | `contradictory_archive` (archive の自己矛盾)。`[WARN]` を出してその batch には触れず、**次の batch に進む**。summary を出した後に exit 1 (手で直して再実行) |
| その batch の forecast 行が archive のどこにも無い | `missing_forecast` (outcome を forecast_id 経由で引けないため、判断ファイルの有無によらず) |
| `execution.csv` が完全、評価ファイルが無い・不完全 (前回の中断、日次 run の評価失敗) | 修復経路: 既存の判断 6 行を `load_execution_decisions_csv` で読み (行の日付・batch id が dir と食い違えば `contradictory_archive`: `[WARN]` + 触れずに次へ、summary 後に exit 1)、(b) の outcome だけで評価 6 行を書く → `written_evaluations_only`。forecast が 7 行揃っていなくても、snapshot が無くても進む |
| それ以外 (判断ファイルが無い・不完全) | (a) `forecast.csv` が distinct な 7 kind 揃い、全行が同じ `as_of_jst` / `window_end_jst` で、`ugh_v2_alpha/beta/gamma/delta` と `baseline_simple_technical` の `forecast_direction` が読めなければ `partial_forecast`; (b) 評価行が指す outcome (`outcome_id` が 1 つに定まり、`window_start_jst` / `realized_open` / `realized_close` / `evaluated_at_utc` が読める) が無ければ `missing_outcome` (評価がまだ無い窓もここ); (c) その batch 自身の `input_snapshot.json` (`observability.load_input_snapshot`) が読めなければ `missing_snapshot`。3 つ揃えば `build_execution_decisions(forecast_directions, build_baseline_context(snapshot), completed closes, ..., entry_status="backfill_bar", live_entry=None, decided_at_utc=as_of_jst→UTC)` と `evaluate_execution_decisions` で判断 6 行と評価 6 行 → `written_decisions_and_evaluations` |

`decided_at_utc` は `as_of_jst` を UTC に変換した値 (`forecast.csv` には `locked_at_utc` 列が無い)、
`evaluated_at_utc` は batch の `evaluation.csv` 行の `evaluated_at_utc` の最大値。書き込みは実 exporter
(`export_execution_csv` / `export_execution_evaluation_csv` → 一時 staging dir) と `publish_execution_csvs`
(原子的コピー、完全な `execution.csv` は上書きしない) で行い、`latest/execution.csv` は publish 前の
bytes に戻す (無かった場合は消す。latest は最新 live batch の鏡で、閉じた backfill 窓はそれになり得ない)
ので、checkout には `history/` の archive ファイルだけが増える。`--dry-run` は同じ判断・評価をメモリ上で
組み立てて件数と対象 path だけ出し、何も書かない。skip は `[SKIP] <date> <batch>: <理由>` を 1 行ずつ、
summary (`print_summary`) はカウンタごとに 1 行 (`batches scanned`、written 2 種、skipped 4 種、archive
files)。commit / push はしない (`fx-daily-data` の checkout を `git status` / `git diff` で確認して人が
push)。backfill 行は集計で bar 系列にのみ入り、ゲート判定 (live 系列) には入らない。backfill で
`missing_decisions` は解消するが `missing_live` は残る (§9)。

## 11. Module layout

```
src/ugh_quantamental/fx_protocol/
├── execution_models.py     # ExecutionDecision / ExecutionEvaluation (frozen, extra=forbid)、BookId enum
├── execution.py            # 純関数: build_execution_decisions / evaluate_execution_decisions、定数
├── execution_exports.py    # CSV fieldnames、export、publish (history/ + latest/)
├── execution_reporting.py  # 集計 (FX-EXEC-REPORTING)
└── data_sources.py         # fetch_live_spot_yahoo (new)
scripts/backfill_execution_history.py   # FX-EXEC-REPORTING
```

`execution.py` は I/O を持たない (live spot の取得と CSV は automation / exports 側)。
`execution_models.py` は SQLAlchemy 非依存。

## 12. Open questions

### 12.1 FX-EXEC-LAYER 実装時の逸脱・補足 (2026-10-08)

- Step 5b / 6b (export と publish) は Step 3b / 4c の helper の中で実行する。判断の publish は
  Step 4〜7 より前に走るため、後続 Step が fatal になって batch が rollback されても
  `history/{date}/{batch}/execution.csv` と `latest/execution.csv` は残る (CI では workspace ごと
  破棄されるので影響なし。ローカルの永続 dir では、再実行が同じ batch id を再生成し既存の判断を保持する)。
- 窓内の回復経路 (判断ファイルが無い・不完全な場合の再記録) は archive の
  `history/{date}/{batch}/input_snapshot.json` (`observability.load_input_snapshot`) から
  `build_baseline_context` と closes を再導出する。archive が無い (元の run が CSV exports 無しだった)
  場合だけ回復 run 自身の snapshot で代用し warning を出す (Codex round 21 を反映)。
- live spot の失敗は `FxDataFetchError` に加え `ValueError` (`LiveEntry` の検証失敗) も
  `live_unavailable` に落とす。取得 URL は provider と同じ chart endpoint で `range=5d`。
- `latest/execution.csv` は判断を記録した run だけが書き、削除されない。同日 rerun で archive が完全なら
  bytes が異なるときだけ archive から再同期する。窓が閉じた日・層が無効な日・失敗した日は前 batch の
  まま残る (`fx_daily_csv_exports_v1.md` § execution/ policy)。
- `FxDailyAutomationResult.execution_evaluation_windows` がスキャンで評価した窓を全件返し、
  `execution_evaluation_csv_path` は最新窓、`execution_evaluations_recorded` は合計。
- Step 4c は判断ファイルの行とディレクトリ (日付・batch id) が食い違う場合 warning で skip する。
- `EXECUTION_ACTIVATION_AS_OF = 2026-10-08` は暫定。本番で最初に判断を記録した営業日と違えば
  その日に合わせる (reporting の期待コホートの起点)。`EXECUTION_EXCLUDED_AS_OF` は空。
- テスト規律: `tests/conftest.py` の autouse fixture が `automation.fetch_live_spot_yahoo` を
  `FxDataFetchError` に差し替えるので、CSV exports 付きで `run_fx_daily_protocol_once` を回す既存テストは
  `live_unavailable` の判断行を tmp dir に書く (観測可能な assertion は変えない)。

- live spot の取得元を alpha_vantage の realtime endpoint に切り替えるか (API key 制限との兼ね合い)。
  v1 は yahoo のみ。
- `bench_gpt_m3` は格子探索で選ばれた 1 マス (試算メモ参照)。ベンチマークとして固定するが、
  優位性の主張には使わない。
