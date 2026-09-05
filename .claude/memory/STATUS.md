# STATUS - ugh-quantamental

最終更新: 2026-09-05

このファイルは日次の project snapshot として、現在フェーズ、次の発行順序、直近 merged を保持する。安定方針は `CLAUDE.md` / `AGENTS.md` に置き、canonical な milestone 表は `PLANS.md`、フェーズ計画は `docs/engine_review_2026_05_planning.md` / `docs/specs/` を参照する。

他の doc から live tracker を指す場合は、このファイルの `## 次の発行順序` にリンクする。

## Phase

Milestones 1-18 完了、engine default **v2.6** (FX-RANGE-DECOUPLE #122)。2026-08 月次レビューの briefs 4 本 (GOV-FLAT-AWARE / OUTCOME-CATCHUP / ESTAR-LAG / PRICE-ALERT) を **PR #125 で全実装・main 反映済み** (2026-08-31 merge、Claude 完結実装: Sonnet 並列 agent 4 本 + self-review 1 回 + Codex 2 rounds)。ESTAR-LAG の実データ ablation で **SMA20 飽和仮説は棄却** (spot_vs_sma20 差し替えは 6 セル全てで転換 0 営業日シフト)、**momentum_5d が一貫した律速** (−2〜−10 営業日)。raw e_star 符号転換は emitted 方向より早い (epsilon dead-zone の方法論差、順序は同一)。governance は excl-flat 判定へ移行済 (9/1 月次で初運用)、outcome catch-up は 8/27 stranded batch を初回実行で回収見込み、price alert は GitHub Issue 通知で稼働開始。次: 9/1 月次 governance 初運用確認 → 9 月中旬レンジ幅較正 brief → momentum_5d × variant 重み相互作用の追調査。フォローアップ候補: 正常評価済み window の lag-1 catch-up 再該当による冗長 history 書込 (データ破損は dedupe で防止済)。運用: scheduler 遅延 3 営業日連続を受け daily/price-alert cron を :23/:37 へ移動 (#127、9/3 merge) — GitHub 側の広域遅延 (全 cron 4〜5h) が続き効果は未判定。9/5 週報 (#128) で catch-up 再発行の二重計上を検出・修正、202608 governance は要再生成。

## 次の発行順序

active queue - 未着手または進行中の Phase / Brief / Milestone のみを置く。終了した項目は wrap-up step 4 で `## 直近 merged` に移す。

1. **[要ユーザー判断] 202608 月次 governance の再生成** - PR #128 の二重計上修正後、`fx-analysis-pipeline.yml` を monthly mode で dispatch して decision log / flags / excl-flat delta を作り直す (fx-daily-data の analytics を書き換える outward 操作)。再生成前の数値は引用しない。
2. **lag-1 catch-up 再該当の書き側修正 (brief 候補)** - 正常評価済み window を候補判定で除外し、冗長な END-dir 再発行を止める。読み側 dedupe (#125 / #128) で破損は防止済だが、#128 の二重計上はこれが原因。
3. **レンジ幅較正の brief 化 — 9 月中旬** - robust statistic + 中心の置き方 + 終値軸目標。7/30 が 20 窓から抜けた後 (8/31〜) の幅を 2 週分観測してから。基準点: 8/10 上 6pips miss / 8/19 下 9pips hit。
4. **momentum_5d × variant 重み相互作用の追調査** - ESTAR-LAG ablation の帰結 (SMA20 棄却、momentum_5d が律速 −2〜−10 営業日)。9/2 ショック後は発行方向が 1–2 営業日で転換 (8 月 6 / 14) — 「転換速度はショックの型に依存」を補助仮説に、raw e_star を `analyze_estar_lag.py` で確定してから比較。engine 改変はこの調査を見てから。
5. **regime=choppy の判定保留を継続** - 標本ゼロ 9 週目。intervention_risk 非 low 日は 28 obs 中 26 miss / 2 hit (方向のみ弱い。レンジは 8 月の非 low 日 8/8 全的中)。label は move-size 由来、「大変動日に弱い」と読む。
6. **governance spec `Status: Draft` バナーの実態確認** - 実装完備なのにバナーが `Draft`。確認し必要なら更新。
7. **売買 / execution レイヤーの planning doc 起草** - conviction は e_star 符号整合時のみ信頼可 (2026-08 findings §1) — sizing 入力設計はこの条件付けを織り込む。
8. **follow-up (低優先)** - #116 `_resolve_annotation_source` 純関数化 / #119 stC scoreboard rollup / 最終 retry が JST 日付をまたいだ場合の business-day ガード赤 (9/4、実害なし) / PRICE-ALERT の sticky 挙動 (連続急落が 1 通知に畳まれる)。グリッド方針 (B7) は **2026-08-30 ユーザー判断で終了 — 追跡・エスカレーション対象外** (週報モニタは事実報告のみ継続)。

## 直近 merged

最新 5 件のみ inline。超過分は `archive/STATUS_MERGED_LOG.md` 末尾へ移す。

- **PR #128 / 8/31–9/4 週報 + labeled_observations 二重計上修正** (2026-09-05) - 9/2–9/3 ショック週 (−272bp、UGH 方向 1/4・Range 2/4)。発行方向の転換は β 1 / α・γ・δ 2 営業日 (8 月の 6 / 14 と同じ物差し、順序同一)。初運用: catch-up が 8/27 batch を回収、price-alert が Issue #126。**実害修正**: `_collect_labeled_observation_rows` (labeled_observations.csv の書き手) に forecast_id dedupe が無く、catch-up 再発行 (8/21〜9/2) を週次・月次・governance が二重計上 (週次 7 obs / 正 4、**202608 governance は要再生成**)。regression test 付き。skill 硬化 (Obs 期待値は distinct 評価 window 数から導出、detail helper は as_of キー + recovered 行の表示規則)。Codex 5 rounds / 5 件全採用、境界宣言は発動前に収束。
- **PR #127 / daily-protocol cron の :23 移動** (2026-09-03) - ops-only。GitHub Actions の毎時 0 分 schedule が 8/28 (欠測) / 8/31 / 9/1 (手動 dispatch で救済) と 3 営業日連続で遅延・欠落したため、daily cron 3 本を :23 へ、監視側 price-alert cron を :37 へ移動。`FX_LAST_RETRY` の cron 文字列一致も同期 (見落とすと最終 retry の fail-hard が静かに外れる)。self-review で spec の猶予算術誤り (20:23+2h≠22:00) を訂正し、旧時刻の記述 6 箇所を同期、daily script のコメントは時刻非依存化。Codex 2 rounds (round 1 = 2 件、いずれも self-review で先回り済み / round 2 = 指摘なし)。境界宣言 (round 11 以降は critical bug / 実コード破壊 / 将来汚染のみ) を PR に掲示、発動前に収束。
- **PR #125 / 2026-08 briefs 4 本の一括実装** (2026-08-31) - GOV-FLAT-AWARE (excl-flat 列 + 同一 cohort delta 判定移行) / OUTCOME-CATCHUP (有界遡及 FX_OUTCOME_CATCHUP_DAYS=5、savepoint 隔離、window-END dir 発行、publication repair) / ESTAR-LAG (`scripts/analyze_estar_lag.py` + `docs/analysis/estar_lag_2026_08.md` — **SMA20 仮説棄却、momentum_5d が律速**) / PRICE-ALERT (`run_fx_price_alert.py` + workflow、stdlib-only、真 bp 単位、22:00 JST gap 監視、Issue 通知)。Claude 完結実装 (Sonnet worktree agent 4 並列 → cherry-pick 統合 → self-review 1 回で 10+ 件修正)。Codex 2 rounds 全採用 (evaluation_id / forecast_id dedupe、snapshot lookup 全 dir 探索 ほか)。ユーザー側 auto-fix runner と並走し衝突ゼロで統合。
- **PR #124 / 2026-08 月次レビュー + briefs 4 本 + 運用修正** (2026-08-31) - docs/skills/CI。8 月週報 3 本 + `engine_review_2026_08_findings.md` + Task Brief 4 本 (ESTAR-LAG / GOV-FLAT-AWARE / OUTCOME-CATCHUP / PRICE-ALERT) + mail step `continue-on-error` + skill 更新 (2 層 ops check、prose↔table 自己整合ルール)。Codex レビュー 16+ rounds / 41+ threads 全 resolve・全件採用 — 主要訂正: e_star 転換年表 (up 予測 ⟺ e_star 正で引き直し、β 6 営業日 / α・γ 14 営業日、variant 間 8 営業日分散)、レンジ較正トレードオフの定量化 (縮小余地 9pips 未満)、briefs の実装可能性硬化 (実在 API 名、CSV history export、typed config 経路、ablation の参照値/抽出規則/派生入力再構築、result contract)。5 round 到達で自己整合チェックを skill に encode。
- **PR #123 / fx-market-context skill + v2.6 初運用週の事後検証** (2026-08-09) - docs/skills-only。`fx-market-context` skill 新設 (WebSearch で相場コンテキストをリサーチ、週報の必須ステップ化) + `fx-weekly-report` skill 更新 + 8/3–8/7 週報 + findings §10 追補。v2.6 初運用週は Range 4/4 (100%、リプレイ予測と整合)。レビュー ~13 round / 23 threads 全 resolve — 主要訂正: 介入の向き (円買いは USDJPY 押し下げ、底の説明にならない)、state→方向の因果否定 (方向は e_star 経路のみ、state は projection の部分的下流だが fire evidence の主項は prior 自己強化 + event features)、exhaustion ラベルは転換の ground truth でない、intervention_risk は move-size のみで裏付けに使えない、半幅使用率は終値軸で中央値 36%。却下 1 件 (窓の非重複をデータで提示)。