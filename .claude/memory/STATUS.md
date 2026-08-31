# STATUS - ugh-quantamental

最終更新: 2026-08-31

このファイルは日次の project snapshot として、現在フェーズ、次の発行順序、直近 merged を保持する。安定方針は `CLAUDE.md` / `AGENTS.md` に置き、canonical な milestone 表は `PLANS.md`、フェーズ計画は `docs/engine_review_2026_05_planning.md` / `docs/specs/` を参照する。

他の doc から live tracker を指す場合は、このファイルの `## 次の発行順序` にリンクする。

## Phase

Milestones 1-18 完了、engine default **v2.6** (FX-RANGE-DECOUPLE #122)。2026-08 月次レビュー (`docs/engine_review_2026_08_findings.md`) 完了・**PR #124 で main 反映済み** (2026-08-31 merge): 8 月の方向不振は **ショック後 e_star 転換遅延** (β は底から 6 営業日で断続正転、α/γ は 14 営業日 / 約 +380pips — variant 間で最大 8 営業日ばらける。仮説 = SMA20 系 `fundamental_score` の clamp 飽和、判定は counterfactual replay) に集約、conviction 較正は e_star 符号の従属変数と判明。Range は月間 14/15 で較正の許容変更幅が定量化 (縮小余地 9pips 未満 / 8/10 救済には +6pips)、幅較正 brief は自然縮小後の標本を待って 9 月中旬。運用インシデント 2 件: Gmail 535 (メール通知は**ユーザー判断で廃止**、通知は GitHub-native へ一本化) / スケジューラ遅延で 8/28 欠測 (評価恒久欠測の構造露呈)。次は briefs 4 本の Codex 実装 (順序: GOV-FLAT-AWARE → OUTCOME-CATCHUP → ESTAR-LAG → PRICE-ALERT)。

## 次の発行順序

active queue - 未着手または進行中の Phase / Brief / Milestone のみを置く。終了した項目は wrap-up step 4 で `## 直近 merged` に移す。

1. **[brief 発行済] FX-GOV-FLAT-AWARE** (`docs/briefs/2026-08_FX-GOV-FLAT-AWARE.md`) - `direction_hit_excl_flat` 追加 + `inspect_direction_logic` の判定移行。9/1 月次 governance の誤報を止めるため最優先で Codex へ。
2. **[brief 発行済] FX-OUTCOME-CATCHUP** (`docs/briefs/2026-08_FX-OUTCOME-CATCHUP.md`) - outcome 評価の有界遡及。8/27 発行分の backfill を実地受け入れ確認に使う。
3. **[brief 発行済] FX-ESTAR-LAG** (`docs/briefs/2026-08_FX-ESTAR-LAG.md`) - 転換遅延の feature 別 replay 分析。engine 改変はこの結果を見てから。
4. **[brief 発行済] FX-PRICE-ALERT** (`docs/briefs/2026-08_FX-PRICE-ALERT.md`) - GitHub Issue ベースの価格閾値 + データ欠測監視 (メール不使用)。
5. **レンジ幅較正の brief 化 — 9 月中旬** - robust statistic + 中心の置き方 + 終値軸目標。7/30 が 20 窓から抜けた後 (8/31〜) の幅を 2 週分観測してから。基準点: 8/10 上 6pips miss / 8/19 下 9pips hit。
6. **regime=choppy の判定保留を継続** - 標本ゼロ 9 週目。intervention_risk 非 low 日は 28 obs 中 26 miss / 2 hit (方向のみ弱い。レンジは 8 月の非 low 日 8/8 全的中)。label は move-size 由来、「大変動日に弱い」と読む。
7. **governance spec `Status: Draft` バナーの実態確認** - 実装完備なのにバナーが `Draft`。確認し必要なら更新。
8. **売買 / execution レイヤーの planning doc 起草** - conviction は e_star 符号整合時のみ信頼可 (2026-08 findings §1) — sizing 入力設計はこの条件付けを織り込む。
9. **follow-up (低優先)** - #116 `_resolve_annotation_source` 純関数化 / #119 stC scoreboard rollup。グリッド方針 (B7) は **2026-08-30 ユーザー判断で終了 — 追跡・エスカレーション対象外** (週報モニタは事実報告のみ継続)。

## 直近 merged

最新 5 件のみ inline。超過分は `archive/STATUS_MERGED_LOG.md` 末尾へ移す。

- **PR #124 / 2026-08 月次レビュー + briefs 4 本 + 運用修正** (2026-08-31) - docs/skills/CI。8 月週報 3 本 + `engine_review_2026_08_findings.md` + Task Brief 4 本 (ESTAR-LAG / GOV-FLAT-AWARE / OUTCOME-CATCHUP / PRICE-ALERT) + mail step `continue-on-error` + skill 更新 (2 層 ops check、prose↔table 自己整合ルール)。Codex レビュー 16+ rounds / 41+ threads 全 resolve・全件採用 — 主要訂正: e_star 転換年表 (up 予測 ⟺ e_star 正で引き直し、β 6 営業日 / α・γ 14 営業日、variant 間 8 営業日分散)、レンジ較正トレードオフの定量化 (縮小余地 9pips 未満)、briefs の実装可能性硬化 (実在 API 名、CSV history export、typed config 経路、ablation の参照値/抽出規則/派生入力再構築、result contract)。5 round 到達で自己整合チェックを skill に encode。
- **PR #123 / fx-market-context skill + v2.6 初運用週の事後検証** (2026-08-09) - docs/skills-only。`fx-market-context` skill 新設 (WebSearch で相場コンテキストをリサーチ、週報の必須ステップ化) + `fx-weekly-report` skill 更新 + 8/3–8/7 週報 + findings §10 追補。v2.6 初運用週は Range 4/4 (100%、リプレイ予測と整合)。レビュー ~13 round / 23 threads 全 resolve — 主要訂正: 介入の向き (円買いは USDJPY 押し下げ、底の説明にならない)、state→方向の因果否定 (方向は e_star 経路のみ、state は projection の部分的下流だが fire evidence の主項は prior 自己強化 + event features)、exhaustion ラベルは転換の ground truth でない、intervention_risk は move-size のみで裏付けに使えない、半幅使用率は終値軸で中央値 36%。却下 1 件 (窓の非重複をデータで提示)。
- **PR #122 / 2026-07 月次レビュー** (2026-08-02) - FX-RANGE-DECOUPLE (v2.6)。`expected_range` を実現ボラ基準へ置換 (`trailing_mean_range_price` × `range_width_scale=1.25`、中心 = spot、recenter 撤去)、実装コードでの実データリプレイで包含率 45.5% → 95% / 中変動帯 0% → 86%。テール (≥100bp) は対象外と spec 明記。ENGINE-P3B の variant 固有レンジを意図的に反転。magnitude は代替 5 案が改善せず据え置き (findings §5.6 で訂正記録)。Codex P1 2件 / P2 3件、採用 4 / 却下 1 (根拠提示)。CI の ruff 未ピン留めで main が既に red だった件もピン留めで解消。
- **2026-06 engine review program 実装** (2026-06-28) - 5 briefs を全実装・マージ (#116-#120)。FX-ANNOT-LIVE (#116, OHLC fallback + leakage 除去 + daily 配線, Codex P2 8件) / FX-STATE-HYSTERESIS (#117, v2.4) / FX-MAG-EXPANSION (#118, v2.5) / FX-STATEPROXY-REDEF (#119, state_correctness_hit 新設) / FX-GOV-REGIME-FLAGS (#120, レジーム層別 collapse フラグ, Codex P2 4件)。engine default v2.5。
- **PR #114** (2026-06-27) - 2026-06 engine review program (docs-only)。`docs/engine_review_2026_06_planning.md` + Task Brief 5 本 (`docs/briefs/`)。Codex 8 round/20 thread を全 resolve (P1: state は forecast direction 非入力)。横断契約を planning §5 に一元化。