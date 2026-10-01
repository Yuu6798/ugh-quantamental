# Task Brief: FX-ASOF-FIXING - 08:00 fixing 前に着地した run の前営業日への繰り越し

## Phase
2026-09 月次レビュー §6 / Axis 5 (`docs/engine_review_2026_09_findings.md`)、CC-M04
(`data_provider_remediation`)。PR #130 (business-day guard の繰り越し) の一般化。protocol / engine
version の bump なし (#130 と同じ扱い: automation の運用修正)。

## Goal
月〜木の最終 retry (cron 11:23Z) が GitHub 側の遅延で 15:00Z を越え **JST 翌日 00:xx** に着地すると、
Step 1 の `current_as_of_jst(now_utc)` が「まだ 08:00 fixing の来ていない翌日」を返し、provider の最新
完了窓が 1 営業日前に見えるため、Step 2 の 1 日 fallback で正しい日に戻ったうえで `idempotent_skip`
になる。動作は正しいが `provider_health.csv` に **偽の `snapshot_lag_business_days=1` /
`used_fallback_adjustment=True`** が積まれる (9 月 17 行 / 59 run = 28.8%、月次 flag
`provider_lag_issue` / `provider_fallback_issue` の閾値 30% まで 1 run)。これを **PR #130 の繰り越し
経路に乗せる**: run 開始時刻が `as_of_jst` (08:00 JST) より前なら、前営業日の forecast batch が完備して
いる場合に限りその日へ繰り越し、`carried_over_from_non_business_day` と同じ下流 (Step 2 の後退拒否、
Step 7 の `requested_as_of_jst` 基準の lag=0) を通す。**完備していない場合は従来どおり** (繰り越さず、
既存の fallback 経路で救済) — 救済経路の挙動は変えない。

## Acceptance Criteria
- [ ] `src/ugh_quantamental/fx_protocol/automation.py` `run_fx_daily_protocol_once` Step 1:
      `as_of_jst = current_as_of_jst(now_utc)` の後、**`now_utc < as_of_jst` (fixing 未到来)** かつ
      `_has_complete_forecast_batch(session, config, prev_as_of_jst(as_of_jst))` のとき、
      `as_of_jst = prev_as_of_jst(as_of_jst)` へ繰り越し、既存の
      `carried_over_from_non_business_day` フラグ (名前は実装判断で `carried_over` 系に一般化してよいが、
      Step 2 の後退拒否 `if carried_over_from_non_business_day:` と同じ分岐を通すこと) を立て、
      `logger.warning` で繰り越しを記録する。非営業日の既存分岐との順序: **非営業日判定を先に**
      (土曜 00:51 は従来どおり非営業日経路で金曜へ)、fixing 前判定は営業日のときだけ評価する
- [ ] fixing 前で前営業日 batch が**不完備**なら、現行どおり `as_of_jst` を変えずに Step 2 へ進む
      (fallback 経路が従来のとおり動く)。raise しない
- [ ] 繰り越した run の `provider_health.csv` 行は `snapshot_lag_business_days=0` /
      `used_fallback_adjustment=False` / `run_status=idempotent_skip` (既存
      `test_carry_over_is_not_recorded_as_provider_lag` と同型の test を、**月曜 08:00 batch 完備 →
      火曜 00:30 JST 着地** の fixture で追加)
- [ ] 繰り越し後に provider が 1 日古い窓を返した場合、Step 2 の既存の後退拒否 (`ValueError`
      「Refusing to move the as_of backwards」) が同じく働く test
- [ ] fixing 前かつ前営業日 batch 不完備の run が、provider の 1 日 fallback 経路で従来どおり
      `as_of_jst` を 1 日戻して forecast を作る (= 現行の救済挙動が不変) test。既存
      `test_one_day_lag_adjusts_as_of_jst` 系の fixture を流用
- [ ] 通常時刻 (14:23 / 16:23 / 20:23 JST = cron 05:23 / 07:23 / 11:23 UTC 定刻) の run は
      `now_utc >= as_of_jst` なので判定に入らず挙動不変 — 既存 test が通ることで確認
- [ ] `docs/specs/fx_daily_automation_v1.md` の Step 1 記述「Determine canonical `as_of_jst` (08:00 JST
      today or previous business day)」に fixing 前繰り越しの条件 (batch 完備) を追記。
      `.claude/skills/fx-weekly-report/SKILL.md` §3-3 の「月〜木の最終 retry が provider lag として
      記録される」旨の記述があれば、本修正後は出なくなることを 1 行で注記
- [ ] `ruff check .` / `pytest -q` pass

## Scope
- IN: `src/ugh_quantamental/fx_protocol/automation.py` (Step 1 のみ + Step 2/7 が参照するフラグ名)、
      `tests/fx_protocol/test_automation.py` (追加)、`docs/specs/fx_daily_automation_v1.md`、
      `.claude/skills/fx-weekly-report/SKILL.md` (注記のみ)
- OUT: `calendar.py` (`current_as_of_jst` の契約は変えない — 他の呼び出し元 (price alert / weekly) に
      波及する)、provider / data_sources、Step 3 以降、`provider_health.csv` の列 (schema 変更は #130/#131
      で却下済)、engine / protocol version、cron 時刻

## Allowed Dependencies (optional)
なし。

## Implementation Hints (optional)
- `now_utc` は Step 1 冒頭で `datetime.now(timezone.utc)` 済 (`automation.py` L366)。`as_of_jst` は
  tz-aware (JST) なので `now_utc < as_of_jst` は直接比較できる。
- 既存の非営業日分岐 (L369〜403) をそのまま残し、その `else` 側 (営業日) に fixing 前判定を足すのが
  最小。判定関数を `_should_carry_over_before_fixing(now_utc, as_of_jst, ...)` のように純関数化すると
  test が書きやすい。
- 9 月の該当 run: 9/21 17:07Z、9/22 15:33Z、9/23 15:29Z、9/24 15:51Z (いずれも翌日 00:xx JST 着地、
  `provider_health.csv` の `generated_at_utc`)。金曜 9/25 15:51Z は #130 の経路で既に lag=0。
- 繰り越し run は `_has_complete_forecast_batch` が真なので Step 3 は `idempotent_skip`、Step 4 は
  前窓の評価 (既に済なら no-op)。Step 8 の週次 trigger は金曜以外では走らない。

## Required Outputs
- Branch name: `codex/fx-asof-fixing-carry-over`
- PR title: `fix(fx): carry a pre-fixing run over to the previous business day`
- Expected files changed: 4 (automation.py / test_automation.py / spec / skill 注記)
- Required tests: 上記 3 本 (lag=0 記録、後退拒否、不完備時の従来挙動)

## Done When
- All acceptance criteria are checked
- Completion Summary に、修正前後で 9/21〜9/24 型の run が `provider_health.csv` に残す行の差 (lag 1→0、
  fallback True→False) を test の assertion として示す
