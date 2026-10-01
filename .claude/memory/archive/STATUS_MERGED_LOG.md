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

## 2026-09-13 (PR #130 merge sweep overflow)

- **PR #124 / 2026-08 月次レビュー + briefs 4 本 + 運用修正** (2026-08-31) - docs/skills/CI。8 月週報 3 本 + `engine_review_2026_08_findings.md` + Task Brief 4 本 (ESTAR-LAG / GOV-FLAT-AWARE / OUTCOME-CATCHUP / PRICE-ALERT) + mail step `continue-on-error` + skill 更新 (2 層 ops check、prose↔table 自己整合ルール)。Codex レビュー 16+ rounds / 41+ threads 全 resolve・全件採用 — 主要訂正: e_star 転換年表 (up 予測 ⟺ e_star 正で引き直し、β 6 営業日 / α・γ 14 営業日、variant 間 8 営業日分散)、レンジ較正トレードオフの定量化 (縮小余地 9pips 未満)、briefs の実装可能性硬化 (実在 API 名、CSV history export、typed config 経路、ablation の参照値/抽出規則/派生入力再構築、result contract)。5 round 到達で自己整合チェックを skill に encode。

## 2026-09-13 (PR #131 merge sweep overflow)

- **PR #125 / 2026-08 briefs 4 本の一括実装** (2026-08-31) - GOV-FLAT-AWARE (excl-flat 列 + 同一 cohort delta 判定移行) / OUTCOME-CATCHUP (有界遡及 FX_OUTCOME_CATCHUP_DAYS=5、savepoint 隔離、window-END dir 発行、publication repair) / ESTAR-LAG (`scripts/analyze_estar_lag.py` + `docs/analysis/estar_lag_2026_08.md` — **SMA20 仮説棄却、momentum_5d が律速**) / PRICE-ALERT (`run_fx_price_alert.py` + workflow、stdlib-only、真 bp 単位、22:00 JST gap 監視、Issue 通知)。Claude 完結実装 (Sonnet worktree agent 4 並列 → cherry-pick 統合 → self-review 1 回で 10+ 件修正)。Codex 2 rounds 全採用 (evaluation_id / forecast_id dedupe、snapshot lookup 全 dir 探索 ほか)。ユーザー側 auto-fix runner と並走し衝突ゼロで統合。

## 2026-10-01 (PR #132 sweep overflow)

- **PR #127 / daily-protocol cron の :23 移動** (2026-09-03) - ops-only。GitHub Actions の毎時 0 分 schedule が 8/28 (欠測) / 8/31 / 9/1 (手動 dispatch で救済) と 3 営業日連続で遅延・欠落したため、daily cron 3 本を :23 へ、監視側 price-alert cron を :37 へ移動。`FX_LAST_RETRY` の cron 文字列一致も同期 (見落とすと最終 retry の fail-hard が静かに外れる)。self-review で spec の猶予算術誤り (20:23+2h≠22:00) を訂正し、旧時刻の記述 6 箇所を同期、daily script のコメントは時刻非依存化。Codex 2 rounds (round 1 = 2 件、いずれも self-review で先回り済み / round 2 = 指摘なし)。境界宣言 (round 11 以降は critical bug / 実コード破壊 / 将来汚染のみ) を PR に掲示、発動前に収束。

## 2026-10-01 (PR #133/#134/#135 merge sweep overflow)

- **PR #130 / business-day guard の as_of 繰り越し** (2026-09-13) - #129 で確定した実害 2 つ (毎週金曜の CI 赤 + Saturday 週次 artifact の 3 週欠落) の恒久対策。非営業日着地時、**前営業日の forecast batch が完備している場合に限り**その日へ繰り越して継続 → 週次ブロック到達 → exit 0。完備は既存基準 (`make_forecast_batch_id` → `load_fx_forecast_batch` → `EXPECTED_DAILY_BATCH_SIZE`) を流用。batch 不在・不完全は本物の欠測として従来どおり raise。繰り越し先は前**営業**日なので日曜着地も金曜に落ちる (安全性の担保は gap 幅ではなく batch 完備)。Codex 2 件 (うち P1 1 件) 全採用: (1) Step 7 の provider lag が wall-clock 基準のため救済 run が `provider_health.csv` に偽 lag 行を積み、同 run が生成する週報・月次が数えてしまう → 実際に問い合わせた as_of 基準へ。(2) **P1**: provider 退行時に通常の 1 日 fallback が金曜→木曜へさらに戻し、`latest/` を古い日で上書きしつつ週次ゲートからも外れる → 繰り越し後は後退を拒否して raise。却下 1 件 (carry-over 専用列の追加 — CSV スキーマ変更が週次・月次の読み手に波及、warning ログと `run_status` で識別可能)。テスト 5 本、各々「自分の修正だけを戻すと落ちる」ことを確認。3 rounds で収束。
- **PR #129 / 9/7–9/11 週報 + skill 診断手順の再構成** (2026-09-12) - BoJ 9 月利上げ観測で 152.87 (7 か月ぶり安値)、UGH 方向 2/4・Range 3/4。**週最大の下げ日 (9/7、−102.0bp) だけ全 variant FLAT**、翌日 15 発行ぶりの `fire` 点火。epsilon は動的ではなく **固定 3.0bp** と確定。**金曜 guard 赤の実害が 2 つ確定** (CI 赤 + Saturday 付 artifact 3 週欠落) し queue 最優先へ。前週持ち越しの 202608 governance 再生成結果 (`inspect_magnitude_mapping` 新規発火) をレポートに回収し、点予測 magnitude を独立 queue 化。skill は週次 trigger の **4 節すべて**で診断する形に再構成 (3 節は健全な run でも落ちる)。Codex 14 rounds / 24 件全採用、境界宣言 (round 11 以降は critical bug / 実コード破壊 / 将来汚染) 後の 4 件はすべて「将来汚染」として境界内判定。訂正の主因は自分の機序誤認 (guard の分岐、volatility ラベルの入力、PRICE-ALERT の再武装条件)。
- **PR #128 / 8/31–9/4 週報 + labeled_observations 二重計上修正** (2026-09-05) - 9/2–9/3 ショック週 (−272bp、UGH 方向 1/4・Range 2/4)。発行方向の転換は β 1 / α・γ・δ 2 営業日 (8 月の 6 / 14 と同じ物差し、順序同一)。初運用: catch-up が 8/27 batch を回収、price-alert が Issue #126。**実害修正**: `_collect_labeled_observation_rows` (labeled_observations.csv の書き手) に forecast_id dedupe が無く、catch-up 再発行 (8/21〜9/2) を週次・月次・governance が二重計上 (週次 7 obs / 正 4、**202608 governance は要再生成**)。regression test 付き。skill 硬化 (Obs 期待値は distinct 評価 window 数から導出、detail helper は as_of キー + recovered 行の表示規則)。Codex 5 rounds / 5 件全採用、境界宣言は発動前に収束。

## 2026-10-01 (PR #136 merge sweep overflow)

- **PR #131 / 実装可能フォローアップの一括処理** (2026-09-13) - catch-up 書き側 / replay script の前提 / governance バナー / stC rollup / 純関数化 を 1 PR で。**(1) catch-up 書き側**: 完備判定が catch-up 専用 dir しか見ず、通常評価済み窓を毎 run 再 publish → 読み手が二重計上 (#128 破損の発生源)。END-date dir も publish 済みと認める。判定は**内容検証 7 条件**へ (outcome_id 一致 / evaluation 行数 / 行の forecast_id 集合一致 / forecast 行の archive / `strict=True` / 構造的短長行の棄却 / 両ヘッダが reader の index 列を持つ) — 各条件が単独で破れることを unit test で固定。**発生源は spec の記述**「END-date recovery dir は正常 run では先在しない」で、候補条件が距離 `>= 1` である以上これは誤り。spec 訂正済。**(2) `analyze_estar_lag.py`**: 窓の CLI 化 / `pre_expansion_close_change_bp` と 3 成分 / `estar_term` 軸 (compute_e_raw・compute_gravity_bias の実引数 8 項を消費点で置換、`compute_u` は常に元 features) / 全 variant 日次系列。**(3)** stC rollup + spec、**(4)** `resolve_annotation_source` 純関数化、**(5)** governance spec を Implemented へ。Codex **10 rounds / 19 件全採用**、却下 1 (provider_health 列追加 — CSV スキーマ変更が週次・月次に波及)。**自分の誤りの訂正 3 件**: 「one term of e_star」は成立せず (compute_u が混ぜる)、`alignment` neutral=0.0 は退化介入で「alignment が律速」は所見でなくアーティファクト、2026-08 の β×neutral は tie を単独名で報告していた。テスト 4 本は「修正なしで通る」状態から書き直し。2026-08 回帰: 統計軸 18 行・alpha 日次 27 行が byte-identical。

## 2026-10-01 (PR #137 merge sweep overflow)

- **PR #132 / 9/14–9/18 週報** (2026-09-23) - 日米同時利上げ週 (FOMC 3.75–4.00% 12-0、日銀 1.25% 7-2)、USDJPY 3 連騰 +189bp。UGH Range 16/16、方向 α1/β2/γ1/δ0。前週の「1 日遅れ追随」を 2 週 10 日で数え直し、前窓 down 後 20/20・up 後 2/20 の非対称を報告 (→ 9/25 週報で撤回、10/1 月次で機序を「同符号に揃う冗長入力の多数決」と特定)。運用: #130 の金曜繰り越しが本番初動作 (15:02Z 着地で金曜完走、Saturday artifact 4 週ぶり)、#131 の重複 0 件。月〜木最終 retry の偽 provider lag を新規発見。Codex 6 rounds / 8 件全採用 (数え間違い・因果の時系列・持ち越し番号ずれ・p_weight 順位・グリッド週数・volatility baseline の 5 日窓)。
