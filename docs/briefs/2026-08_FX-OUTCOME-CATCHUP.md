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
- [ ] `run_fx_daily_automation` (automation.py) の outcome 段が、snapshot の
      `completed_windows` のうち「complete な forecast batch (`EXPECTED_DAILY_BATCH_SIZE`
      本) が存在し、かつ evaluation 未登録」の window を **古い順に最大
      `FX_OUTCOME_CATCHUP_DAYS` (default 5) 営業日分**評価する
- [ ] 既存挙動の後方互換: 欠測がない通常日は従来どおり直前 window 1 件のみが評価
      され、出力 (CSV / DB 行) は現行と同一 (既存 test 無改変で pass)
- [ ] 冪等: 同日に複数回 run しても評価は重複登録されない (既存の idempotent 経路を
      catch-up 分にも適用)
- [ ] 途中 1 window の評価失敗が他 window の評価とその日の forecast 発行を巻き込まない
      (batch 不在/不完全は skip + observability 記録、raise しない — 現行の
      `_prior_batch_ready` ガードと同じ防御思想)
- [ ] test: 「D1 forecast 発行 → D2 run 欠測 → D3 run」を模した fixture で、D3 の
      run が D1 分の評価を登録し、lookback 外 (>5 営業日) の未評価 batch は対象外に
      なることを検証
- [ ] `docs/specs/` の該当 spec (daily protocol) に catch-up 仕様 (対象条件・上限・
      順序・冪等) を追記

## Scope
- IN: `src/ugh_quantamental/fx_protocol/automation.py`、必要なら
      `request_builders.py` (新 helper 追加は可、`previous_window_matches` の既存
      semantics は温存)、`scripts/run_fx_daily_protocol.py` (env 読み取りのみ)、
      対応 test、spec 追記
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
