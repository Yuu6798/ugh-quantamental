# Task Brief: FX-GOV-FLAT-AWARE - direction_hit_excl_flat 集計と governance 誤報是正

## Phase
2026-08 月次レビュー §3-1 / STATUS queue #2。集計層のみ — engine 非改変。

## Goal
FLAT 予測日 (実現が小動きでも binary miss になる) が direction 率を歪め、
`inspect_direction_logic` flag が 2 ヶ月連続で誤報した問題を、FLAT 除外の direction
指標を追加して閾値判定をそちらへ移すことで是正する。

## Acceptance Criteria
- [ ] 週次/月次の戦略別集計に `direction_hit_excl_flat_count` /
      `direction_obs_excl_flat` / `direction_hit_excl_flat_rate` が追加される
      (既存の `direction_hit_count` / `direction_hit_rate` は互換のため残す)
- [ ] 非 FLAT 予測が 0 件の戦略 (例: baseline_random_walk は常時 flat) では
      excl_flat rate が空値になり、ゼロ除算も 0% 偽装もしない
- [ ] `monthly_review.py` の `inspect_direction_logic` flag (現行:
      `direction_accuracy_delta_vs_ugh` >
      `THRESHOLD_DIRECTION_DEFICIT_VS_TECHNICAL_PCT`) が excl_flat ベースの
      delta で判定されるようになり、reason 文字列にも excl_flat と明記される。
      **比較は同一日付コホートで行う**: baseline 側の rate も「canonical UGH
      variant が非 FLAT だった日付集合」の上で再計算する — 各戦略を独立に
      excl_flat 集計して引き算すると、UGH が退避した日の baseline 成績が delta に
      混入し、flag が誤発火/誤抑止する。UGH と baseline の FLAT 日が非対称な
      合成データで test する
- [ ] 判定移行を検証する test: 「FLAT 込みでは baseline 優位・FLAT 除外では UGH
      優位」の合成データで flag が立たないこと、および逆ケースで立つこと
- [ ] 既存 CSV 列の名称・順序は不変 (新列は末尾追加)。新列名は producer /
      consumer / test / spec 記述の全 occurrence で grep 同期済み

## Scope
- IN: `src/ugh_quantamental/fx_protocol/weekly_reports_v2.py` (**実働の週次
      集計 — `run_fx_weekly_report.py` → `analytics_rebuild.rebuild_weekly_report`
      経由で呼ばれるのはこちら**。列リストもここが持つ) /
      `monthly_review_exports.py` (月次 CSV 列リスト) /
      `analytics_annotations.py` / `analytics_rebuild.py` / `monthly_review.py` /
      `monthly_governance.py` (flag 文言の追従のみ)、対応 test、
      `docs/specs/fx_monthly_governance_v1.md` の該当節追記。
      `reporting.py` は legacy 経路 — 触るのは追従が自明な場合のみ
- OUT: `engine/` 一切、FLAT epsilon の値や `_direction_from_bp_with_epsilon` の
      挙動 (予測側は不変)、既存 CSV 列のリネーム・削除、engine_version

## Implementation Hints
- 発火箇所は `monthly_review.py` ~L630 (`tech["direction_accuracy_delta_vs_ugh"]`)。
  excl_flat の delta を並記フィールドとして追加し、flag 判定のみ切替えるのが最小
- 集計の元は評価レコードの `forecast_direction` + `direction_hit`。FLAT 除外は
  「forecast_direction == flat の観測を分母から除く」であり、実現方向は関与しない
- 参考実測 (2026-07): FLAT 込み UGH 45.8% < technical 66.7% / FLAT 除外 UGH 68.1%
  > technical 66.7% — この月で flag が立たなくなることが実データ上の期待挙動

## Required Outputs
- Branch name: `codex/fx-gov-flat-aware`
- PR title: `feat(fx): add FLAT-excluded direction metrics and re-base the governance flag`
- Expected files changed: 上記 IN のファイル群
- Required tests: 合成データでの flag 判定切替 test + excl_flat 集計の空値 test

## Done When
- All acceptance criteria are checked
- `ruff check .` passes
- `pytest -q` passes
- PR body starts with a Completion Summary
