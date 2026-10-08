# FX Execution Layer v1 — UGH 売買エンジン (執行層) とベンチマーク観測スキーム

Status: **Draft (design approved 2026-10-08, implementation via briefs FX-EXEC-LAYER / FX-EXEC-REPORTING)**
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
その時刻の live spot で記録して回復する (`entry_time_utc` が実際の判断時刻)。既存ファイルは
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

`execution_reporting.py` (new) が `history/*/*/execution_evaluation.csv` を `(forecast_batch_id,
book_id)` で重複排除して読み、**6 book が揃わない batch は丸ごと除外** (件数と id を報告) した上で、
`execution_version` ごとの層に分けて (版を跨いで足さない。`x2` 以降が混在する境界の週・月と累積
サマリは版ごとに別の表になる) book ごとに次を出す:

- 判断数、取引数、見送り内訳 (評価行の `skip_reason` 別)、live 取得率
- 方向的中率 (取引日)、capture bp (`Σ side × realized bp`、単位サイズ)、size 加重の日次リターン
  (live 系列 = `size × (pnl_live_bp − cost_live_bp)`、bar 系列 = `size × (pnl_bar_bp − cost_bar_bp)`) の
  平均・標準偏差・t 値を別々に (母集団は取引行 `side != 0` のみ。見送り日は資産曲線に据え置きで入る
  が mean / sd / t には入れない)
- 損益 (円、live 系列と bar 系列)、最終資産、最大 DD、PF、コスト合計
- ベンチマーク差: `ugh_x1` と `bench_gpt_m3` / `bench_long` の損益差と capture 差
- 合格ゲート進捗 (§9)。ゲートの母集団は週次・月次の期間窓とは独立で、history 全体のうち
  `execution_version` が現行値かつ `entry_status == live` の完全 batch の累積コホート

出力先: `csv/analytics/execution/weekly/<YYYYMMDD>/execution_weekly.{md,csv,json}`
(金曜最終 retry の weekly block と月曜の `run_fx_analysis_pipeline.py` weekly モード) と
`csv/analytics/execution/monthly/<YYYYMM>/execution_monthly.{md,csv,json}` (monthly モード)。
`latest/execution_summary.json` は期間窓の report からは書かず、history 全体を 1 つの窓として
同じ集計を走らせた累積の book 別サマリ (ゲート進捗を含む) を置く。weekly / monthly の生成時に
それぞれ更新するが、内容は呼び出し元の期間窓に依存しない。

## 9. Governance and acceptance gate

- `execution_version` は `x1` で凍結。book の追加・パラメータ変更・サイズ式の変更はすべて
  本 spec の改訂、`x2` への bump、改訂日の記録を伴う。bump 前の行は旧版として残す。
- 月次レビューは執行層の集計を**観測**し、`docs/engine_review_YYYY_MM_findings.md` に 1 節を
  設ける。途中でのパラメータ調整は禁止 (同じデータで選んだ変更は検証にならない)。
- 合格ゲート (`ugh_x1` を実運用候補に進める条件、すべて live 系列。母集団は現行 `execution_version`
  の累積コホートで、版を bump したらコホートもゼロから始まる。取引数・t 値・DD は **`ugh_x1` の行だけ**
  から計算し、ベンチマーク book は条件 4 の比較にのみ使う):
  1. `ugh_x1` の取引 (`side != 0`) 100 回以上かつ観測 6 か月以上。「6 か月」はコホートの
     `first_as_of_jst` から `last_as_of_jst` までの**暦日数** (`observation_calendar_days` =
     `(last − first).days`) が 182 以上 (定数 `GATE_MIN_CALENDAR_DAYS = 182`)。観測日数
     (`observation_days`、評価済み窓の数) は情報として出すが閾値には使わない
  2. コスト控除後・size 加重の live 日次リターン (`size × (pnl_live_bp − cost_live_bp)`) の t 値 ≥ 2.0
     (標本標準偏差 `stdev`、n − 1 で割る。`pstdev` は使わない)
  3. 最大 DD ≤ 10% (`max_drawdown_live` は正の大きさ `max_t (peak_t − equity_t) / peak_t`、0 以上 1 以下。
     判定は `≤ 0.10`: ちょうど 10.00% は合格、10.01% は不合格)
  4. 同期間の `bench_gpt_m3` と `bench_long` の両方を損益で上回る
- 現行 version の batch に 6 book 未満のもの (§8 の `incomplete_batches`)、または完全な `execution.csv`
  があるのに完全な `execution_evaluation.csv` が無い batch (`missing_evaluations`。期待コホートは判断
  ファイルの棚卸しから導く。`window_end_jst` が集計時刻より後の pending 窓は除く)、または
  `execution.csv` はあるが完全でない dir (`incomplete_decision_batches`、version 不明なら現行版扱い) が
  1 つでもあれば、条件の現在値は出すがゲートは **blocked** (`passed = False`、`blocked_reasons` に
  `incomplete_batches` / `missing_evaluations` / `incomplete_decisions`)。欠けた archive を黙って短くした上で合格にはしない
  (昇格証拠は欠落・部分 batch で fail する、`AGENTS.md` §5)。修復は Step 4c の再スキャンか §10 の
  backfill で行い、修復できない欠落は data 側の問題として扱う (ゲートは外さない)。block の判定は
  現行 version の batch に限る (`incomplete_batches` / `missing_evaluations` は `execution_version` を
  持ち、旧版の欠損は現行版のゲートを block しない)。
- 不合格なら `x2` として設計し直し、観測を 1 からやり直す (期間を継ぎ足さない)。
- ゲート通過後も実弾の判断は人が行う (本 spec の対象外)。

## 10. Backfill

保存済み予測 (2026-05-08 以降) について、`scripts/backfill_execution_history.py` (new) が
`execution.csv` / `execution_evaluation.csv` を `entry_status = backfill_bar` で生成する
(live なし、`pnl_live_bp` / `cost_live_bp` 空)。入力の結合は history 全体の横断 join で行う
(評価と outcome は翌日の batch dir にあるため、`labeled_observations.collect_evaluated_forecast_rows`
と同じく `forecast_id` でグローバルに引く)。方向は `forecast.csv` の `strategy_kind` /
`forecast_direction`、outcome は `outcome.csv` の `outcome_id` / `window_start_jst` / `realized_open` /
`realized_close`、snapshot はその batch 自身の `history/{as_of}/{forecast_batch_id}/input_snapshot.json`
を直接解決する (日付だけで探さない。無ければその batch は skip)。2026-05-07 以前は予測が無いので対象外 (2026-10-08 の
Jan〜Oct 再計算は分析であり、観測記録には入れない)。backfill 行は集計で bar 系列にのみ入り、
ゲート判定 (live 系列) には入らない。完全な既存ファイルは上書きしない。`execution.csv` が完全で
`execution_evaluation.csv` が無い (または不完全な) batch は前回の中断とみなし、既存の判断 6 行を
読んで評価 6 行だけを生成する (再実行で修復される)。

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

- live spot の取得元を alpha_vantage の realtime endpoint に切り替えるか (API key 制限との兼ね合い)。
  v1 は yahoo のみ。
- `bench_gpt_m3` は格子探索で選ばれた 1 マス (試算メモ参照)。ベンチマークとして固定するが、
  優位性の主張には使わない。
