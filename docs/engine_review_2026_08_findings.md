# 2026-08 月次ロジックレビュー findings (USDJPY daily protocol)

- 対象期間: 2026-08-03〜2026-08-28 (評価済み 15 営業日 / 8/27 未評価 / 8/28 欠測)
- エンジン: v2.6 (FX-RANGE-DECOUPLE、8/3 が初運用日) — 8 月は全日 v2.6
- 元データ: `fx-daily-data` ブランチ、週報 4 本 (`docs/reports/fx_weekly_report_202608*.md`)
- 前月レビュー: `docs/engine_review_2026_07_findings.md` (§10 に v2.6 初週の事後検証)
- 正式な月次集計 artifact は 9/1 の `fx-monthly-review.yml` が生成する。本書の数値は
  週次 artifact と評価レコードからの引用で、9/1 以降に月次 artifact と照合すること

## 0. TL;DR

8 月の方向成績の悪さは複数の欠陥ではなく、**単一の現象 — 7/30 ショック後の e_star
転換遅延 (9 営業日 / +420pips) — にほぼ集約される** (§1)。転換完了後のエンジンは方向・
conviction とも 7 月の較正水準に戻った。v2.6 のレンジは月間 14/15 (93%) で、系列初の
高 vol 日的中 (8/19) を含む一方、幅の過大 (使用率中央値 36%) と片側 6pips 差の miss
(8/10) が較正の両側基準点として揃った (§2)。運用側では 2 インシデント (§4) が発覚し、
再発防止 2 件 + 監視 1 件を brief 化する (§5)。

## 1. e_star 転換遅延 — 8 月の支配的欠陥 (最優先)

### 事実 (全て評価レコードから)

| 期間 | e_star / 出力 | 市場 | 帰結 |
|---|---|---|---|
| 8/3–8/13 (9 営業日) | 全日マイナス (−0.158〜−0.513)、down/flat のみ | 155.21 → 159.48 (+427pips) | up 6 日を全て miss (例外: 8/11 β のみ up hit) |
| 8/10 | conviction 0.935 (系列最高) で down | +98.9bp 反発 | 週最大の外れ + range miss |
| 8/19–8/21 | β/δ → 全 variant の順で up へ転換 | 転換初手 8/19 は −90.2bp 急落 | 転換の遅さ由来の別種の外れ |
| 8/24–8/26 (転換後) | up 継続、conviction 0.80–0.89 | ジリ高 | **2/3 hit、stC 100%、誤差 2.4–5.1bp** |

- 転換所要: 市場の底 (8/3) から **9 営業日 / +420pips**。7/13 週「退避解除の遅れ」、
  7/27 週「fire/down 固執」と同型で、これで 3 例目。
- **conviction 較正は独立の欠陥ではない**: 転換前の高 conviction 逆行 (0.935 / 0.868)
  と転換後の高 conviction 一致 (0.80–0.89) は、いずれも「e_star の符号が市場とズレて
  いる/いない」の従属変数として説明できる。7 月レビュー §6 の較正確認と矛盾しない。

### 遅行源の仮説 (grep 済み、未検証 — brief FX-ESTAR-LAG で検証)

`derive_signal_features` (`market_ugh_builder.py`) の 3 入力は時定数が大きく異なる:

| feature | 定義 (実装から) | 時定数 |
|---|---|---|
| `fundamental_score` | `spot_vs_sma20 × 100` を [−1,1] clamp | **~20 営業日** — 577pips 級の急落後は spot が SMA20 を数週間下回り続け、かつ ×100 で即 −1.0 に飽和する |
| `technical_score` | `momentum_5d × 100` clamp | ~5 営業日 |
| `price_implied_score` | `prev_close_change_bp / trailing_mean_abs_change_bp` | 1 営業日 |

仮説: **ショック後の e_star 固定は SMA20 系 `fundamental_score` の飽和が主因**。
8/19–8/21 の転換タイミングが「spot が SMA20 を取り戻す時期」と一致するかが判別点。
検証は実データ replay で feature 別時系列を出すだけで足り、engine 改変は不要。

## 2. レンジ幅較正 — 9 月中旬に実装判断 (材料は揃った)

- 月間 Range: variant あたり **14/15 (93.3%)** (週別 4/4, 3/4, 4/4, 3/3)。
- 両側の基準点: **8/10 上に 6pips 超過で miss** / **8/19 下に 9pips 余裕で hit**
  (−90.2bp 高 vol 日、系列初)。幅を締めれば 8/19 を失い、緩めても 8/10 は救えない。
- 幅の過大は継続 (使用率中央値 36%、7 月 findings §10.1)。原因の 7/30 577pips は
  8/27 発行分まで trailing 20 窓に残存。**抜けた直後 (8/28) が欠測**のため、自然縮小後
  の幅は 8/31 以降で観測する。
- 論点 3 つ: ①単純平均 → 中央値 / trimmed mean、②中心の置き方 (spot 対称 vs 方向
  シフト — 8/10 は +99bp の片側ジャンプ)、③較正目標は終値軸 (半幅使用率 or 区間
  スコア)。日中レンジ比での最適化は禁止 (7 月 findings §10.1 の軸混同)。
- **8 月中は実装しない**: 自然縮小後の標本 (8/31〜) を 2 週分見てから brief 化。

## 3. 小粒の継続論点

1. **FLAT epsilon の取り逃し**: 8/24 の flat 抜け (+12.0bp) が非遅行系の唯一の方向
   miss。FLAT 退避の通算 1 勝 2 敗と併せ、集計層の FLAT-aware 化 (brief
   FX-GOV-FLAT-AWARE) で誤報を止めてから、epsilon 自体の再調整は標本を待つ。
2. **choppy regime**: 標本ゼロ 9 週目。スライス維持・判定保留を継続。
3. **intervention_risk 非 low 日**: 28 obs 中 26 miss / 2 hit。方向の「大変動日に弱い」
   は継続だが、**レンジは 8 月の非 low 日 8/8 で全的中** — v2.6 で片軸は克服。label は
   move-size 由来 (>100bp→high) という読み替えを月次集計でも維持すること。
4. **state / stC**: stC 0% → 100% まで動いたが方向に効かない経路のまま。優先度最下位。
   state 側実験の設計有効性は 7 月 findings §10.2 末尾 (PR #123 訂正) を参照。

## 4. 運用インシデント (2026-08-28 週に発覚)

### 4.1 メール通知の Gmail 535 (少なくとも 8/17 以降)

通知 step が `535 BadCredentials` で毎回失敗 → 全 run が赤 → **本物の障害が赤ノイズに
埋没**。protocol 本体は正常で provider_health.csv は健全に見えた (週報 2 本が「安定
稼働」と誤記載 → 訂正済み、skill に 2 層チェックを追記済み)。
**ユーザー判断 (2026-08-29): メール通知の復旧は不要 — 見送り。** よって通知チャネル
としてのメールは今後当てにしない。`continue-on-error` 追加 (branch) で赤ノイズのみ
解消する。今後の通知は GitHub-native (Issue / run conclusion) に寄せる (§5 B3/B4)。

### 4.2 GitHub Actions スケジューラ遅延 → 8/28 欠測 (実害)

8/27・8/28 の cron (05/07/11 UTC) が **~11 時間遅延**発火。8/28 分は 3 run とも JST
土曜に着地し business-day ガードが正しく拒否 → **8/28 forecast なし / 8/27 評価なし /
週次 artifact なし**。Jackson Hole 講演日 (8/28) と「7/30 が 20 窓から抜ける最初の
予測日」が同時に欠測した。

構造的欠陥: outcome 評価は `previous_window_matches` (`request_builders.py`) で
**直前 window のみ**を対象とするため、run が 1 日飛ぶと評価が恒久欠測する。8/27 分が
該当 (要 backfill)。再発防止は brief FX-OUTCOME-CATCHUP。

## 5. 対応キュー (2026-08-29 決定)

| # | 項目 | 種別 | 状態 |
|---|---|---|---|
| B1 | メール通知復旧 | 運用 | **見送り (ユーザー判断)** |
| B5 | branch → main の PR (週報 3 本 + CI 修正 + skill + 本書 + briefs) | 運用 | 本レビューで実施 |
| A3 | FX-GOV-FLAT-AWARE (`direction_hit_excl_flat` 追加、誤報是正) | 集計層 | brief 発行 |
| B2 | FX-OUTCOME-CATCHUP (評価の遡及処理 + 8/27 backfill) | automation 層 | brief 発行 |
| A1 | FX-ESTAR-LAG (遅行源の replay 分析) | 分析 | brief 発行 |
| B3/B4 | FX-PRICE-ALERT (閾値監視 + データ欠測検知、GitHub Issue 通知) | 新規 workflow | brief 発行 |
| A2 | レンジ幅較正 | engine | 9 月中旬に brief 化 (標本待ち) |
| B7 | グリッド方針 + 160.50 リセット定義 | 運用 | **ユーザー判断待ち (5 週目)** |
| B6 | 8/31 復旧確認 / 8/27 評価確認 / 9/1 月次 workflow 確認 | 監視 | Claude が月曜に実施 |
