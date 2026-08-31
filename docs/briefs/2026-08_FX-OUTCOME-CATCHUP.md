# Task Brief: FX-OUTCOME-CATCHUP - outcome 評価の遡及処理 (run 欠測時の恒久欠測防止)

## Phase
2026-08 月次レビュー §4.2。automation 層のみ — engine / forecast 発行側は非改変。

## Goal
daily run が 1 日飛ぶと outcome 評価が恒久欠測する構造 (`previous_window_matches` が
直前 window のみを対象とする) を、評価対象を「閉じた未評価 forecast batch を有界に
遡って処理」に拡張して解消する。2026-08-28 の欠測で未評価のまま残った 8/27 発行分が、
マージ後の最初の通常 run (または workflow_dispatch) で自動的に評価されることが実地の
受け入れ確認になる。

## Acceptance Criteria
- [ ] `run_fx_daily_protocol_once` (automation.py) の outcome 段が、snapshot の
      `completed_windows` のうち「complete な forecast batch (`EXPECTED_DAILY_BATCH_SIZE`
      本) が存在し、かつ evaluation 未登録」の window を **古い順に最大
      `FX_OUTCOME_CATCHUP_DAYS` (default 5) 営業日分**評価する
- [ ] 既存挙動の後方互換: 欠測がない通常日は従来どおり直前 window 1 件のみが評価
      され、出力 (CSV / DB 行) は現行と同一 (既存 test 無改変で pass)
- [ ] **result contract を複数回収に対応させる**: `FxDailyAutomationResult` の
      単数フィールド (`outcome_id` / `outcome_csv_path` / `evaluation_csv_path` /
      `evaluation_count`) は**従来どおり「直前 window」の値のみ**を指すと定義し
      (catch-up が直前 window しか回収しない通常日は現行と完全一致)、catch-up で
      追加回収した window は**新設の typed per-window tuple フィールド**で報告する。
      frozen model の nested collection も不変に保つため Python `list` は使わず、
      `tuple[CatchupWindowResult, ...]` 相当・default `()` とする。CLI / observability の
      既存 consumer は無改変で従来値を読み続けられること。複数 window 回収時の
      result 内容・順序と、構築後に append/remove/reorder できないことを test で固定する
- [ ] 冪等: 同日に複数回 run しても評価は重複登録されない (既存の idempotent 経路を
      catch-up 分にも適用)
- [ ] catch-up で回収した outcome / evaluation も **元 forecast batch の history
      ディレクトリ (`history/{date_str}/{forecast_batch_id}/evaluation.csv` —
      `csv_exports.py` の既存レイアウト) に export される**。DB 登録だけでは
      `rebuild_fx_analytics.py` / `run_fx_monthly_review.py` が CSV history を読む
      ため欠測のまま残る — CSV export まで含めて回収完了とする test を置く
- [ ] **catch-up の export は history 専用経路で行い、`latest/` を汚さない**:
      既存 `publish_csv_to_layout` は history と同時に `latest/*.csv` も上書きする
      (`csv_exports.py:390-419`) ため、過去 batch の回収にそのまま使うと `latest/`
      が歴史データを指して当日 run と矛盾する。history のみ書く経路を追加するか、
      全 catch-up 後に当日分で `latest/` を復元する。test で「catch-up 後の
      `latest/` が当日 batch を指したまま」を検証
- [ ] 途中 1 window の評価失敗が他 window の評価とその日の forecast 発行を巻き込まない
      (batch 不在/不完全は skip + observability 記録、raise しない — 現行の
      `_prior_batch_ready` ガードと同じ防御思想)
- [ ] test: 「D1 forecast 発行 → D2 run 欠測 → D3 run」を模した fixture で、D3 の
      run が D1 分の評価を登録し、lookback 外 (>5 営業日) の未評価 batch は対象外に
      なることを検証
- [ ] `docs/specs/` の該当 spec (daily protocol) に catch-up 仕様 (対象条件・上限・
      順序・冪等) を追記

## Scope
- IN: `src/ugh_quantamental/fx_protocol/automation.py` /
      `automation_models.py` (**`FxDailyAutomationConfig` に catch-up 日数の typed
      field を追加** — frozen / `extra="forbid"` のため env の直読みでは通せない)、
      必要なら `request_builders.py` (新 helper 追加は可、`previous_window_matches`
      の既存 semantics は温存)、`csv_exports.py` (history 専用 export 経路の追加のみ
      — 既存 `publish_csv_to_layout` の挙動は不変)、`scripts/run_fx_daily_protocol.py`
      (env → config への受け渡しのみ)、`.github/workflows/fx-daily-protocol.yml`
      (**env 配線のみ**: `FX_OUTCOME_CATCHUP_DAYS: ${{ vars.FX_OUTCOME_CATCHUP_DAYS || '5' }}`
      を既存 env ブロックに追加 — repository variable は明示 mapping なしでは job に
      渡らないため、これがないと「設定可能」が絵に描いた餅になる。cron・他 step は
      不変)、対応 test、spec 追記
- OUT: forecast 発行側 (business-day ガード含む — JST 土日に発行しない現行挙動は
      正しい)、`engine/`、persistence の ORM 列 (新列不要のはず — 必要になったら
      escalation)、cron スケジュール

## Implementation Hints
- 現行ガード: automation.py の `previous_window_matches(snapshot)` +
  `make_forecast_batch_id(pair, window_start_jst, protocol_version)` +
  `FxForecastRepository.load_fx_forecast_batch`。catch-up はこの 3 点を window
  ループに一般化する形が最小
- 営業日境界は `calendar.py` の `is_protocol_business_day` / `next_as_of_jst` /
  `prev_as_of_jst` を使う (独自実装しない)
- 8/27 の実データ: forecast batch は 7 本 complete、window 8/27 08:00 → 8/28 08:00
  JST は閉じており、history に realized 窓が存在する — マージ後の初回 run で評価
  されるはず。Completion Summary に「8/27 分が評価されたか」を実測で記載すること

## Required Outputs
- Branch name: `codex/fx-outcome-catchup`
- PR title: `fix(fx): evaluate pending closed forecast windows with a bounded catch-up`
- Expected files changed: 上記 IN のファイル群
- Required tests: 欠測 fixture の catch-up test / 冪等 test / lookback 上限 test

## Done When
- All acceptance criteria are checked
- `ruff check .` passes
- `pytest -q` passes
- PR body starts with a Completion Summary
