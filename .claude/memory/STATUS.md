# STATUS - ugh-quantamental

最終更新: 2026-08-29

このファイルは日次の project snapshot として、現在フェーズ、次の発行順序、直近 merged を保持する。安定方針は `CLAUDE.md` / `AGENTS.md` に置き、canonical な milestone 表は `PLANS.md`、フェーズ計画は `docs/engine_review_2026_05_planning.md` / `docs/specs/` を参照する。

他の doc から live tracker を指す場合は、このファイルの `## 次の発行順序` にリンクする。

## Phase

Milestones 1-18 完了、engine default **v2.6** (FX-RANGE-DECOUPLE #122)。2026-08 月次レビュー (`docs/engine_review_2026_08_findings.md`) 完了: 8 月の方向不振は **ショック後 e_star 転換遅延** (9 営業日 / +420pips、仮説 = SMA20 系 `fundamental_score` の clamp 飽和) に集約、conviction 較正は e_star 符号の従属変数と判明。Range は月間 14/15 で較正の両側基準点 (8/10 上 6pips miss / 8/19 下 9pips hit) が揃い、幅較正 brief は自然縮小後の標本を待って 9 月中旬。運用インシデント 2 件: Gmail 535 (メール通知は**ユーザー判断で廃止**、`continue-on-error` で赤ノイズのみ解消) / スケジューラ遅延で 8/28 欠測 (評価恒久欠測の構造露呈)。briefs 4 本発行 (ESTAR-LAG / GOV-FLAT-AWARE / OUTCOME-CATCHUP / PRICE-ALERT)、反映 PR #124 レビュー中。

## 次の発行順序

active queue - 未着手または進行中の Phase / Brief / Milestone のみを置く。終了した項目は wrap-up step 4 で `## 直近 merged` に移す。

1. **PR #124 を merge まで運転** - 8 月週報 3 本 + 2026-08 findings + briefs 4 本 + CI 修正 (mail step `continue-on-error`) + skill 更新。CI 修正は merge されるまで効かない。
2. **[brief 発行済] FX-GOV-FLAT-AWARE** (`docs/briefs/2026-08_FX-GOV-FLAT-AWARE.md`) - `direction_hit_excl_flat` 追加 + `inspect_direction_logic` の判定移行。9/1 月次 governance の誤報を止めるため最優先で Codex へ。
3. **[brief 発行済] FX-OUTCOME-CATCHUP** (`docs/briefs/2026-08_FX-OUTCOME-CATCHUP.md`) - outcome 評価の有界遡及。8/27 発行分の backfill を実地受け入れ確認に使う。
4. **[brief 発行済] FX-ESTAR-LAG** (`docs/briefs/2026-08_FX-ESTAR-LAG.md`) - 転換遅延の feature 別 replay 分析。engine 改変はこの結果を見てから。
5. **[brief 発行済] FX-PRICE-ALERT** (`docs/briefs/2026-08_FX-PRICE-ALERT.md`) - GitHub Issue ベースの価格閾値 + データ欠測監視 (メール不使用)。
6. **レンジ幅較正の brief 化 — 9 月中旬** - robust statistic + 中心の置き方 + 終値軸目標。7/30 が 20 窓から抜けた後 (8/31〜) の幅を 2 週分観測してから。基準点: 8/10 上 6pips miss / 8/19 下 9pips hit。
7. **regime=choppy の判定保留を継続** - 標本ゼロ 9 週目。intervention_risk 非 low 日は 28 obs 中 26 miss / 2 hit (方向のみ弱い。レンジは 8 月の非 low 日 8/8 全的中)。label は move-size 由来、「大変動日に弱い」と読む。
8. **governance spec `Status: Draft` バナーの実態確認** - 実装完備なのにバナーが `Draft`。確認し必要なら更新。
9. **売買 / execution レイヤーの planning doc 起草** - conviction は e_star 符号整合時のみ信頼可 (2026-08 findings §1) — sizing 入力設計はこの条件付けを織り込む。
10. **follow-up (低優先)** - #116 `_resolve_annotation_source` 純関数化 / #119 stC scoreboard rollup。グリッド方針判断 (5 週目) + 160.50 リセット定義は**ユーザー判断待ち** (週報で追跡)。

## 直近 merged

最新 5 件のみ inline。超過分は `archive/STATUS_MERGED_LOG.md` 末尾へ移す。

- **PR #123 / fx-market-context skill + v2.6 初運用週の事後検証** (2026-08-09) - docs/skills-only。`fx-market-context` skill 新設 (WebSearch で相場コンテキストをリサーチ、週報の必須ステップ化) + `fx-weekly-report` skill 更新 + 8/3–8/7 週報 + findings §10 追補。v2.6 初運用週は Range 4/4 (100%、リプレイ予測と整合)。レビュー ~13 round / 23 threads 全 resolve — 主要訂正: 介入の向き (円買いは USDJPY 押し下げ、底の説明にならない)、state→方向の因果否定 (方向は e_star 経路のみ、state は projection の部分的下流だが fire evidence の主項は prior 自己強化 + event features)、exhaustion ラベルは転換の ground truth でない、intervention_risk は move-size のみで裏付けに使えない、半幅使用率は終値軸で中央値 36%。却下 1 件 (窓の非重複をデータで提示)。
- **PR #122 / 2026-07 月次レビュー** (2026-08-02) - FX-RANGE-DECOUPLE (v2.6)。`expected_range` を実現ボラ基準へ置換 (`trailing_mean_range_price` × `range_width_scale=1.25`、中心 = spot、recenter 撤去)、実装コードでの実データリプレイで包含率 45.5% → 95% / 中変動帯 0% → 86%。テール (≥100bp) は対象外と spec 明記。ENGINE-P3B の variant 固有レンジを意図的に反転。magnitude は代替 5 案が改善せず据え置き (findings §5.6 で訂正記録)。Codex P1 2件 / P2 3件、採用 4 / 却下 1 (根拠提示)。CI の ruff 未ピン留めで main が既に red だった件もピン留めで解消。
- **2026-06 engine review program 実装** (2026-06-28) - 5 briefs を全実装・マージ (#116-#120)。FX-ANNOT-LIVE (#116, OHLC fallback + leakage 除去 + daily 配線, Codex P2 8件) / FX-STATE-HYSTERESIS (#117, v2.4) / FX-MAG-EXPANSION (#118, v2.5) / FX-STATEPROXY-REDEF (#119, state_correctness_hit 新設) / FX-GOV-REGIME-FLAGS (#120, レジーム層別 collapse フラグ, Codex P2 4件)。engine default v2.5。
- **PR #114** (2026-06-27) - 2026-06 engine review program (docs-only)。`docs/engine_review_2026_06_planning.md` + Task Brief 5 本 (`docs/briefs/`)。Codex 8 round/20 thread を全 resolve (P1: state は forecast direction 非入力)。横断契約を planning §5 に一元化。
- **M18 確認 / PLANS 同期** (2026-06-01) - Milestone 18 (FX Monthly Review) が既存実装済み (`run_monthly_review` / `rebuild_monthly_review` + spec 2本 + workflow 2本 + test 1745行) と確認し end-to-end スモーク検証。PLANS.md を実態同期 (branch `claude/remaining-tasks-review-YkIQi`, PR pending)。