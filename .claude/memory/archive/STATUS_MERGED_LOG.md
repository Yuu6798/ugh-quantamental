# STATUS merged archive

## 2026-06-01

- **PR #105** (2026-05-30) - wrap-up session memory for 2026-05-30。`.claude/memory/2026-05-30.md` + `_index.md` を追記。
- **PR #104** (2026-05-30) - `docs/engine_review_2026_05_planning.md`。計画書のみ、コード変更なし。Codex P2 review 13 rounds / 22 threads を処理してマージ。

## 2026-06-01 (Session 2 wrap-up overflow)

- **PR #108** (2026-06-01) - ENGINE-P2A report_window `engine_version` auto-stratify。mixed-version window を theory first, engine second で latest に絞る。
- **PR #107** (2026-06-01) - ENGINE-P1A range_hit aggregation。v2 UGH variants の range metrics を `ugh_v2_ensemble` row に per-batch dedupe 集計。
- **PR #106** (2026-05-31) - semantic-ci-code の dev-flow / session-end protocol / 設計をローカライズ移植。AGENTS.md handoff protocol、CLAUDE.md tiered reading + 8-step wrap-up、STATUS.md、`/wrap-up` + `/new-brief` skills、session-start hook、`tests/discipline/` 3 gates を追加。

## 2026-06-27 (wrap-up overflow)

- **PR #109** (2026-06-01) - ENGINE-P2B state classifier sharpening。softmax T=0.5、fire weighted-sum + catalyst floor、final softmax T=0.12 を導入し、engine default を v2.1 に bump。

## 2026-06-28 (wrap-up overflow)

- **PR #110** (2026-06-01) - ENGINE-P3A rare FLAT epsilon。UGH variant 限定で fixed 3.0bp FLAT epsilon (`ratio=0.0`, `floor=3.0`) を導入し、engine default を v2.2 に bump。

## 2026-08-02 (PR #122 merge sweep overflow)

- **PR #111** (2026-06-01) - ENGINE-P3B variant-specific expected_range。projection width 一本化で range 生成、非 FLAT recenter + 半幅 floor + `range_width_scale=2.0`、`ugh_v2_ensemble` 撤去で per-variant 集計復帰、engine default を v2.3 に bump。(注: この range 構成は 2026-07 月次レビューで包含率 45.5% と判明し、PR #122 (v2.6) が実現ボラ基準へ置換。variant 固有レンジも意図的に反転している。)

## 2026-08-09 (PR #123 merge sweep overflow)

- **PR #112** (2026-06-01) - ENGINE-P4 conviction 意味論明文化 (docs-only)。conviction = prediction reliability + magnitude scaler の二重役割を spec/docstring に明記、dormant↔magnitude は Option B (decouple) を記録。engine_version 据え置き。

## 2026-08-31 (PR #124 merge sweep overflow)

- **M18 確認 / PLANS 同期** (2026-06-01) - Milestone 18 (FX Monthly Review) が既存実装済み (`run_monthly_review` / `rebuild_monthly_review` + spec 2本 + workflow 2本 + test 1745行) と確認し end-to-end スモーク検証。PLANS.md を実態同期 (branch `claude/remaining-tasks-review-YkIQi`, PR pending)。

## 2026-08-31 (PR #125 merge sweep overflow)

- **PR #114** (2026-06-27) - 2026-06 engine review program (docs-only)。`docs/engine_review_2026_06_planning.md` + Task Brief 5 本 (`docs/briefs/`)。Codex 8 round/20 thread を全 resolve (P1: state は forecast direction 非入力)。横断契約を planning §5 に一元化。

## 2026-09-03 (PR #127 merge sweep overflow)

- **2026-06 engine review program 実装** (2026-06-28) - 5 briefs を全実装・マージ (#116-#120)。FX-ANNOT-LIVE (#116, OHLC fallback + leakage 除去 + daily 配線, Codex P2 8件) / FX-STATE-HYSTERESIS (#117, v2.4) / FX-MAG-EXPANSION (#118, v2.5) / FX-STATEPROXY-REDEF (#119, state_correctness_hit 新設) / FX-GOV-REGIME-FLAGS (#120, レジーム層別 collapse フラグ, Codex P2 4件)。engine default v2.5。

## 2026-09-05 (PR #128 merge sweep overflow)

- **PR #122 / 2026-07 月次レビュー** (2026-08-02) - FX-RANGE-DECOUPLE (v2.6)。`expected_range` を実現ボラ基準へ置換 (`trailing_mean_range_price` × `range_width_scale=1.25`、中心 = spot、recenter 撤去)、実装コードでの実データリプレイで包含率 45.5% → 95% / 中変動帯 0% → 86%。テール (≥100bp) は対象外と spec 明記。ENGINE-P3B の variant 固有レンジを意図的に反転。magnitude は代替 5 案が改善せず据え置き (findings §5.6 で訂正記録)。Codex P1 2件 / P2 3件、採用 4 / 却下 1 (根拠提示)。CI の ruff 未ピン留めで main が既に red だった件もピン留めで解消。

## 2026-09-12 (PR #129 merge sweep overflow)

- **PR #123 / fx-market-context skill + v2.6 初運用週の事後検証** (2026-08-09) - docs/skills-only。`fx-market-context` skill 新設 (WebSearch で相場コンテキストをリサーチ、週報の必須ステップ化) + `fx-weekly-report` skill 更新 + 8/3–8/7 週報 + findings §10 追補。v2.6 初運用週は Range 4/4 (100%、リプレイ予測と整合)。レビュー ~13 round / 23 threads 全 resolve — 主要訂正: 介入の向き (円買いは USDJPY 押し下げ、底の説明にならない)、state→方向の因果否定 (方向は e_star 経路のみ、state は projection の部分的下流だが fire evidence の主項は prior 自己強化 + event features)、exhaustion ラベルは転換の ground truth でない、intervention_risk は move-size のみで裏付けに使えない、半幅使用率は終値軸で中央値 36%。却下 1 件 (窓の非重複をデータで提示)。
