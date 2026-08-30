# Task Brief: FX-PRICE-ALERT - 価格閾値 + データ欠測の GitHub-native 監視層

## Phase
2026-08 月次レビュー §5 B3/B4 / STATUS queue #1 (findings 2026-07 §7 起源)。
engine 非改変の独立監視層。通知はメール不使用 (2026-08-29 ユーザー判断で B1 見送り)
— **GitHub Issue のみ**。

## Goal
エンジンが見ない時間帯 (スナップショット間の 24h、週末、run 欠測時) の急変とパイプ
ライン停止を検知し、GitHub Issue で可視化する。7/30 (−321pips を 10 時間未検知) と
8/28 (run 欠測をゼロ経路で通過) の再発防止。

## Acceptance Criteria
- [ ] `scripts/run_fx_price_alert.py` (新規) が以下を判定する:
      (a) 直近スポット vs **最終 forecast snapshot に保存された `current_spot`** の乖離
      ≥ `FX_ALERT_MOVE_BP` (default 60)。completed OHLC の終値は基準に使わない —
      Yahoo の `regularMarketPrice` は completed bar close とは別に取得され、forecast 時点で
      engine が見た正確な spot は `input_snapshot.json` の `current_spot` に保存されるため、
      ここを基準にして「前回 snapshot 後の新規 move」だけを測る
      (b) 監視ライン横断 — `FX_ALERT_LINES` (default "161.50" — グリッド下限のみ。
      160.50 は 2026-08-30 のユーザー判断で追跡終了しており default に含めない。
      ユーザーが必要なら variable で追加する) を直近バーが跨いだ
      (c) データ欠測 — **schedule-aware 判定**: 当日 (JST 営業日) の cutoff
      **22:00 JST** (最終 cron 11:00 UTC = 20:00 JST の開始時刻 + 猶予 2h) を
      過ぎても当日 as_of の forecast が存在しなければ発報する。cutoff 直前 /
      直後の両側を test すること。「1 営業日超過去」のような age 閾値は不可 — 金曜の run
      欠測 (8/28 の実例) では木曜分がちょうど 1 営業日前のため月曜まで検知でき
      ない。土日は前営業日 (金曜) 分の存在を確認する
- [ ] 判定ロジックは純関数 (入力: バー列 + 最終 forecast メタ + 閾値、出力: alert
      リスト) として分離され、ネットワークなしの unit test を持つ
- [ ] 発報は GitHub Issue: label `fx-alert` の open Issue があれば comment 追記、
      なければ新規作成。**同一 alert 種の連続発報は状態比較で抑止** (毎時 cron でも
      同じ乖離で Issue が毎時伸びない)
- [ ] **解除→再発火の re-arm を永続 state で扱う**: 条件が一旦クリアされたら
      その遷移を記録し (例: Issue へ「cleared」comment または close)、次に同条件を
      跨いだら新規発報する。「アラートなし run は何も書かない」の例外はこの
      clear 遷移の記録のみ (クリア継続中の run は引き続き何も書かない)。バー時刻を
      state に含めて毎 poll 発報させる逃げは不可。test: 発火→クリア→再発火の系列で
      2 度目が抑止されないこと
- [ ] `.github/workflows/fx-price-alert.yml` (新規) が平日 2 時間毎 + 土日 6 時間毎に
      走り、alert なし時は何も書き込まず green で終わる。**`permissions:` を明示
      宣言する: `issues: write` + `contents: read`** (restricted default token では
      未宣言だと Issue 作成が 403 になる。他 workflow も全て明示宣言が本 repo の
      慣例)
- [ ] スポット取得は Yahoo chart API (`query2.finance.yahoo.com/v8/finance/chart/USDJPY=X`
      — `fx-intraday-fetch.yml` で実証済みの経路) を使い、取得失敗はそれ自体を
      (c) と同様に Issue で可視化する (silent skip 禁止)
- [ ] `fx-daily-data` ブランチへの書き込みなし・DB なし・engine import なし

## Scope
- IN: 上記 2 新規ファイル + 純関数部の test + `docs/specs/` への 1 節 (監視層は
      予測系と独立である旨と閾値の意味)
- OUT: `src/ugh_quantamental/` 全体 (import もしない — 監視層は protocol 非依存の
      軽量スクリプトとして独立させ、fx_protocol 障害時にも動くこと)、メール通知、
      既存 workflow の変更

## Allowed Dependencies
標準ライブラリのみ (urllib / json / csv)。GitHub API は `gh` CLI ではなく
`GITHUB_TOKEN` + REST (urllib) で叩く (runner に既定で存在する範囲のみ)。

## Implementation Hints
- 「最終 forecast as_of / 最終 forecast spot」は `fx-daily-data` ブランチの
  `csv/forecasts/` から最新 batch/as_of を特定し、その batch に対応する
  `csv/history/.../input_snapshot.json` の `current_spot` を読む。**completed OHLC close を
  move alert の baseline に再構成しない** (checkout は workflow 側で
  `ref: fx-daily-data` の read-only checkout を別 path に)
- 監視ラインの default 161.50 はグリッドの下限 (稼働帯への接近 = 事実情報)。
  ユーザーが設定を変えたら repository variable で追従できるよう env 化する
- 営業日判定は「土日 (JST) を除く」の簡易版で足りる (fx_protocol 非依存のため
  calendar.py は使わない — 精度より独立性を優先する設計判断。spec に明記)

## Required Outputs
- Branch name: `codex/fx-price-alert`
- PR title: `feat(ops): add a GitHub-native price threshold and data-gap alert layer`
- Expected files changed: 新規 2 ファイル + test + spec 追記
- Required tests: 純関数の閾値/横断/欠測/抑止の unit tests

## Done When
- All acceptance criteria are checked
- `ruff check .` passes
- `pytest -q` passes
- PR body starts with a Completion Summary
