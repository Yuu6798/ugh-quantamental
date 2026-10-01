# STATUS - ugh-quantamental

最終更新: 2026-09-13

このファイルは日次の project snapshot として、現在フェーズ、次の発行順序、直近 merged を保持する。安定方針は `CLAUDE.md` / `AGENTS.md` に置き、canonical な milestone 表は `PLANS.md`、フェーズ計画は `docs/engine_review_2026_05_planning.md` / `docs/specs/` を参照する。

他の doc から live tracker を指す場合は、このファイルの `## 次の発行順序` にリンクする。

## Phase

Milestones 1-18 完了、engine default **v2.7** (FX-MAG-EXPANSION-REVERT #134、10/1)。**2026-09 月次レビュー完了 (10/1、`docs/engine_review_2026_09_findings.md`、PR #133)**: 9 月の UGH が random_walk に負けた +141bp (19 日) は 9/10・9/14・9/25 の 3 日で +148bp — いずれも conviction 0.75〜0.95 の大きな順張りが反転に遭った日で、8/10 と同型。機序は「ショック後に fundamental (spot−SMA20) / technical (SMA5−SMA20、5 日リターンではない) / price_implied が同符号に揃う (fundamental は飽和、technical は 9/25 のみ非飽和) → alignment 0.91〜1.0 → conviction 0.75〜0.98 → magnitude 係数上限近く → **v2.5 ボラ拡張項が ×1.2〜1.7**」。replay (4〜9 月 120 営業日、無介入系列は本番 164 件と bit-identical、`scripts/replay_magnitude_counterfactual.py`) で **`volatility_expansion_max` 1.8→1.0 だけで平均誤差 −1.33bp・中央値 −2.66bp・6 か月すべて改善・方向/FLAT 不変**、9 月の `inspect_magnitude_mapping` (+7.41) は +3.19 で非発火 → 判定 `version_promotion_candidate` → **10/1 ユーザー承認 → PR #134 で v2.7 実装・merge** (default 1 行 + version 3 箇所 + spec §5.1.3.1、Codex 指摘 0)。signal スケール ×100→k は誤差は縮むが方向改善なし・FLAT 増 (縮小効果) で**不採用**。queue の「9/7 FLAT 成分分解」は完了: epsilon/trailing/conviction ではなく price_implied と SMA 系 2 項の符号衝突で e_star≈0、閾値では救えない。e_star 転換の律速は 2 か月連続 momentum_5d、SMA20 飽和仮説は再棄却 (9/25 週報の SMA20 上抜け一致は時期の一致)。運用: 月〜木の最終 retry が JST 翌日 00:xx 着地で `provider_health.csv` に偽 lag/fallback 17 行 (28.8%、flag は > 30% で発火、あと 2 run) → **PR #135 (FX-ASOF-FIXING、10/1 merge) で #130 の繰り越し経路を fixing 前着地にも適用** (batch 不在/部分は従来の fallback、Codex 指摘 0)。10 月の `provider_health.csv` で偽 lag 行が消えることを確認する。金曜繰り越し (#130) と catch-up 修正 (#131) は 9 月本番で検証済、Saturday 週次 artifact は 9/19・9/26 と 2 週連続生成。

## 次の発行順序

active queue - 未着手または進行中の Phase / Brief / Milestone のみを置く。終了した項目は wrap-up step 4 で `## 直近 merged` に移す。

1. **10 月 A/B 検証 (11 月月次)** - `scripts/replay_magnitude_counterfactual.py` で v2.6 replay (mode A, max=1.8) vs v2.7 実績を比較。v2.7 の rollback 判定 (findings §8.1: v2.7 平均誤差が v2.6 counterfactual +1.0bp 超、または `inspect_magnitude_mapping` が v2.7 のみ発火) に使う。あわせて `provider_health.csv` の偽 lag 行が #135 後に消えているか (10 月の月〜木最終 retry) を確認。10 月は `engine_versions_in_window` が 2 値になるので月次の stratify を確認。
2. **CC-M01: 同符号に揃う冗長入力と alignment/conviction の多数決 (logic audit)** - findings 2026-09 §4。最悪 4 日 (8/10・9/10・9/14・9/25) の共通機序。conviction ≥0.9 の信頼度は 8 月以降 2/5。代替設計 (相関入力の一致を alignment の独立根拠に数えない等) は counterfactual で測ってから。conviction 係数 decouple (mode B) も v2.7 の 1 か月後に再評価。**engine 改変は replay 証拠なしに持ち込まない。**
3. **測定器の見直し (CC-M02 / CC-M03、10 月 artifact を見て判断)** - `inspect_magnitude_mapping` (5.0bp) / `inspect_state_mapping` (30bp) は絶対 bp で高ボラ月に発火しやすい (9 月 RW 平均誤差 52bp は 8 月の 2.1 倍)。RW 比の相対閾値を候補に。Axis 4 の `disconfirmer_explained` 集計が artifact に無い。
4. **レンジ幅較正の brief 化 — 据え置き** - 9 月 Range 89.5%、外した 2 日 (9/3・9/7) は設計上のテール。sharpness 基準の定義が第 1 課題、一様スケールと条件付き幅は基準決定後に比較。急がない。
5. **regime=choppy の判定保留を継続** - 標本ゼロ 13 週目。intervention_risk / volatility=high の崩落は「大変動直後に弱い」の言い換え (ラベルは move-size 由来)。
6. **売買 / execution レイヤーの planning doc 起草** - conviction は e_star 符号整合時のみ信頼可、かつ**3 方向入力が同符号に揃った日 (少なくとも fundamental が ±1) の conviction は割り引く**条件 (9/25 は technical +0.77 なので「2 項とも飽和」では外れる)を sizing 入力設計に織り込む (findings 2026-09 §4)。
7. **follow-up (低優先)** - PRICE-ALERT の sticky 挙動は open (9 月は検証機会なし、9/25 発報が未 clear で月をまたいだ)。cron 遅延 +3h39〜+6h56 は #130 で赤を生まなくなったため監視のみ。グリッド方針 (B7) は **2026-08-30 ユーザー判断で終了 — 追跡・エスカレーション対象外**。

## 直近 merged

最新 5 件のみ inline。超過分は `archive/STATUS_MERGED_LOG.md` 末尾へ移す。

- **PR #137 / 9 月 findings の正式 artifact 照合済注記** (2026-10-01) - `monthly/202610/` (commit `81cfcbf`、月次 cron は 07:29Z 発火 = 6 時間遅延・失敗なし) と Axis 1〜6 を照合、全数値一致・訂正なし。冒頭注記と §9 制限事項を照合済に書換 (docs のみ)。Codex 1 round / 1 件 (冒頭を直して §9 を残した同一主張の二重記載)。
- **PR #136 / policy encode — brief は `/new-brief` 経由、promotion evidence は検証件数を pin** (2026-10-01) - #133 の 9 rounds から 2 系統を encode: CLAUDE.md § Workflow (brief の起草・改訂は必ず `/new-brief`)、AGENTS.md §5.3 に 2 行、`/new-brief` SKILL.md §1a に flag 識別子・例外メッセージ (repo 全体 grep で append 箇所を読む、新規は `(new)` と明記して spec に根拠)・既存ガード/test fixture の挙動・validated count の単位 (forecast record = 日 × variant、164) を追加。Codex 4 rounds / 4 件全採用 — うち 3 件は「grep せよ」と書いた本文自体が未 grep だった (emitter を reporting.py と誤記、validated count を日数と誤記)。
- **PR #135 / FX-ASOF-FIXING** (2026-10-01) - Claude 実装。08:00 fixing 前に着地した run (月〜木の遅延 retry が JST 翌日 00:xx) を、前営業日 batch 完備時に #130 の繰り越し経路へ (後退拒否・`requested_as_of_jst` 基準 lag=0 を流用、フラグ名 `carried_over` に一般化)。batch 不在は従来 fallback で救済、部分 batch は既存 `partial forecast batch exists` で fail。`run_fx_daily_protocol_once(now_utc=)` を test 注入用に追加。test 4 本、spec Step 1 更新。Codex 0 件。
- **PR #134 / engine v2.7 — v2.5 ボラ拡張項の無効化** (2026-10-01) - Claude 実装、ユーザー承認 (10/1) 後。`volatility_expansion_max` default 1.8→1.0 (乗数 ≡ 1.0、v2.4 magnitude に復帰、式・不変量不変)、engine_version 3 箇所 sync、spec §5.1.3.1 (根拠 + rollback trigger)、v2.5 経路 test は 1.8 を明示。replay (4〜9 月 120 日 × 4 variant、164 件 bit-identical) で平均誤差 −1.33bp・中央値 −2.66bp・6 か月すべて改善・方向/FLAT 不変。Codex 0 件。
- **PR #133 / 2026-09 月次レビュー + briefs 2 本 + replay script + 9/21–9/25 週報** (2026-10-01) - 9 月の RW 比 +141bp は 9/10・9/14・9/25 の 3 日 (+148bp) に集中、いずれも conviction 0.75〜0.95 の順張り反転。機序は同符号に揃う冗長入力 (fundamental 飽和) → alignment≈1 → conviction 上限 → v2.5 拡張 ×1.2〜1.7。queue 2 (9/7 FLAT 分解) 決着: price_implied と SMA 系の符号衝突で e_star≈0、閾値では救えない。signal スケール案は縮小効果のみで不採用。`scripts/replay_magnitude_counterfactual.py` (persisted 全件 validate、mode A は v2.6 固定、`--expected-validated`)。**Codex 9 rounds / 13 件全採用** — script の検証網羅性 6 件、brief が名指す symbol/flag 名/条件分岐の実在確認 4 件 (`/new-brief` §1a の grounding を skip した結果)、findings の表現 3 件。