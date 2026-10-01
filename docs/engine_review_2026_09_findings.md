# 2026-09 月次ロジックレビュー findings (USDJPY daily protocol)

- 対象期間: 2026-09-03〜2026-09-30 (governance 窓 20 営業日、評価済み 19 / 9/30 は 10/1 評価のため未評価)。
  本文の一部は 9/1〜9/2 を含む 21 営業日、または 4〜9 月 120 営業日の replay を用いる — 各表に明記
- エンジン: v2.6 (全日)
- 元データ: `fx-daily-data` ブランチ (commit `b06a071`, 2026-09-30)、週報 4 本
  (`docs/reports/fx_weekly_report_202609*.md`)
- 月次 artifact: 10/1 01:30 UTC の `fx-analysis-pipeline.yml` 実行前に、同一コードで scratchpad に
  再生成した (`FX_PIPELINE_MODE=monthly FX_REPORT_DATE=20261001 python scripts/run_fx_analysis_pipeline.py`)。
  正式 artifact が push されたら数値を照合すること (`csv/analytics/monthly/202610/`)
- 前月レビュー: `docs/engine_review_2026_08_findings.md`、`docs/analysis/estar_lag_2026_08.md`
- 手順: `docs/specs/fx_monthly_governance_v1.md` §8 の 10 step を順守 (§1〜§7 が step 1〜7、§8 が step 8〜10)

## 0. TL;DR

**9 月の UGH が random walk に負けた分 (+7.4bp/日、19 日で +141bp) は、3 日 — 9/10・9/14・9/25 —
で +148bp を占め、残り 16 日はネットで UGH が勝っている。** 3 日とも conviction 0.75〜0.95 の大きな
順張りが翌日の反転に遭った日で、8 月の最悪日 (8/10、conviction 0.94) と同型である (§4)。
機序は 2 段: (a) ショック後は `fundamental_score` (spot vs SMA20)・`technical_score` (SMA5 vs SMA20)・
`price_implied_score` (前日変化) が**同符号で飽和**し、3 入力が機械的に一致 → alignment ≈ 1 → conviction
0.94〜0.98 → magnitude 係数が上限、(b) そこに **v2.5 のボラ拡張項が ×1.6〜1.8 を掛けて**賭けを最大化
していた。

**replay (4〜9 月 120 営業日 × 4 variant、無介入系列は本番 forecast 164 件と bit-identical) で、
v2.5 拡張項を切る (`volatility_expansion_max` 1.8 → 1.0) だけで平均誤差 −1.3bp (30.9 → 29.6)、
中央値 −2.7bp、6 か月すべてで平均誤差が改善し、方向・FLAT 判定は 1 日も変わらない** (§5)。
9 月の `inspect_magnitude_mapping` (RW 比 +7.4bp) は +3.2bp まで下がり閾値 5.0 を割る — この flag が
2 か月連続で指していたのは magnitude mapping 一般ではなく v2.5 拡張項だった。**判定は
`version_promotion_candidate` (engine_version v2.6 → v2.7、default 1 行の変更)** — 実施はユーザー承認後
(§8)。一方、**飽和の根 (×100 スケール) を触る案は replay で「誤差は縮むが方向は改善せず FLAT が増える」
= 縮小効果にすぎないため採用しない** (§5.3)。

queue 2 の「9/7 FLAT の成分分解」は完了: FLAT は epsilon でも trailing 幅でも conviction でもなく、
**1 日の `price_implied_score` と SMA 系 2 項の符号衝突で `e_star` 自体がゼロ近傍になった**結果 (§2)。
e_star 転換の律速は 2 か月連続で `momentum_5d` (= SMA5−SMA20 スプレッド、5 日リターンではない)、
SMA20 飽和仮説は再度棄却 (§3)。運用では、月〜木の最終 retry が JST 翌日に着地して `provider_health.csv`
に **偽の lag=1 / fallback=True が 17 行 (28.8%、flag 閾値 30%)** 積まれており、1 run で
`provider_lag_issue` が誤発火する距離にある (§6、brief FX-ASOF-FIXING)。

## 1. 6 軸診断 (step 2〜7)

### Axis 1: Basic Performance (`monthly_strategy_metrics.csv`、19 評価日)

| 戦略 | N | 方向 | 方向 (excl FLAT) | Range | stC | 平均誤差 | 中央値誤差 |
|---|---|---|---|---|---|---|---|
| ugh_v2_alpha | 19 | 8 (42.1%) | 8/15 (53.3%) | 89.5% | 26.3% | 59.7 | 46.4 |
| ugh_v2_beta | 19 | 10 (52.6%) | 10/15 (66.7%) | 89.5% | 26.3% | 56.8 | 42.2 |
| ugh_v2_gamma | 19 | 8 (42.1%) | 8/15 (53.3%) | 89.5% | 26.3% | 59.5 | 46.6 |
| ugh_v2_delta | 19 | 6 (31.6%) | 6/11 (54.5%) | 89.5% | 26.3% | 58.7 | 47.3 |
| baseline_random_walk | 19 | 0 | — | — | — | **52.3** | 47.3 |
| baseline_prev_day_direction | 19 | 9 (47.4%) | 47.4% | — | — | 74.0 | 77.6 |
| baseline_simple_technical | 19 | 8 (42.1%) | 42.1% | — | — | 69.5 | 63.4 |

- 9 月は **高ボラ月**: random_walk の平均誤差 (= 平均 |実現変化|) 52.3bp は 8 月 25.3bp の 2.1 倍。
  絶対 bp の指標は月をまたいで比べられない (→ §7 の閾値論点)。
- 方向 (excl FLAT) は β 66.7% が最良で、ベースライン最良 (prev_day 47.4%) を上回る。
  α/γ/δ も 53〜55% で baseline_simple_technical (42.1%) の上。**方向ロジックは baseline 劣後ではない。**
- Range 89.5% (17/19)。外した 2 日は 9/2 (−90.5bp) と 9/3 (−181.5bp) で、いずれも v2.6 の設計上
  「対象外」としたテール (|Δ| ≥ 90bp)。9/7 (−102.0bp) は包含。
- UGH 中央値誤差 (42〜47) は RW 中央値 (47.3) を下回る一方、**平均誤差 (57〜60) が RW (52.3) を上回る**
  — 分布の裾、すなわち少数の大外れが平均を押し上げている (→ §4)。

### Axis 2: Baseline Differential (`monthly_review.json`)

| Baseline | 方向 Δ | 方向 Δ (excl FLAT) | 誤差 Δ | Mag Δ |
|---|---|---|---|---|
| baseline_random_walk | −0.42 | −0.53 | **−7.41 bp** | +12.61 bp |
| baseline_prev_day_direction | +0.05 | −0.07 | +14.23 bp | +6.64 bp |
| baseline_simple_technical | 0.00 | −0.07 | +9.74 bp | −10.63 bp |

(Δ = baseline − UGH。誤差 Δ が負 = UGH の誤差が大きい。) random_walk 比 −7.41bp が
`inspect_magnitude_mapping` (閾値 5.0) を 8 月 (−5.53) に続いて発火させた。他 2 baseline には
誤差で勝っている。

### Axis 3: State / Regime / Volatility / Intervention slice (`monthly_slice_metrics.csv`、UGH 4 variant 合算 76 obs)

| 軸 | ラベル | N | 方向 | 平均誤差 |
|---|---|---|---|---|
| dominant_state | fire | 44 | 34.1% | 52.6 |
| | setup | 27 | 44.4% | 71.2 |
| | failure | 5 | 100% | 44.4 |
| regime | trending | 76 | 42.1% | 58.7 |
| volatility | high | 12 | **8.3%** | **134.3** |
| | normal | 56 | 48.2% | 49.7 |
| | low | 8 | 50.0% | 8.3 |
| intervention_risk | high | 8 | 12.5% | 141.1 |
| | medium | 28 | 25.0% | 88.7 |
| | low | 40 | **60.0%** | 21.1 |

- choppy 標本ゼロは **13 週目** (4 月以降ゼロ)。regime 軸は判定不能のまま。
- volatility=high (12 obs) と intervention_risk ≠ low (36 obs) に外れが集中。ただし両ラベルは
  **直近の実現変動の大きさだけから自己生成される** (`annotation_fallback.py` / `analytics_annotations.py`)。
  「大変動の直後に弱い」の言い換えであり、§4 と同じ現象を別の切り口で見ている。
- 8 月の `regime_direction_collapse` (trending 32%) / `volatility_direction_collapse` (normal 27%) は
  9 月は非発火 (42.1% / 48.2%)。8 月の崩落は 7/30 ショック後の転換遅延に紐づく一過性と読める。

### Axis 4: Disconfirmer / False Positive

- 代表的失敗は 3 件すべて 9/3 (全 variant FLAT、実現 −181.5bp、state=setup)。
- `monthly_review.json` は `disconfirmer_explained` の集計を持たない (spec §3 Axis 4 が要求する項目が
  artifact に無い)。本軸は §4 の日別分解で代替した。artifact 側の欠落は logic audit 候補に記録 (§8 CC-M03)。
- 偽陽性の集中: dominant_state=fire (44 obs、方向 34.1%)。fire は 9/8〜9/21 の 10 発行日連続で
  点火しており (α)、この間に 9/10・9/14 の最悪 2 日を含む。

### Axis 5: Provider / Observability

| 指標 | 値 | 閾値 | 判定 |
|---|---|---|---|
| missing windows | 1 / 20 (9/30 = 生成時点で未評価) | 25% | OK |
| provider lag | **17 / 59 = 28.8%** | 30% | **閾値まで 1 run** |
| fallback adjustment | **17 / 59 = 28.8%** | 30% | 同上 |
| provider mix | alpha_vantage 58 / yahoo_finance 1 | — | OK |
| annotation coverage | 133 / 133 = 100% | 30% | OK |

**17 行の lag/fallback はすべて偽**: 月〜木の最終 retry (cron 11:23Z) が GitHub 側の遅延で 15:00Z を
越え JST 翌日 00:xx に着地 → `current_as_of_jst` が「まだ 08:00 fixing の来ていない翌日」を返す →
provider の最新完了窓が 1 営業日前に見える → 既存の 1 日 fallback で正しい日に戻り `idempotent_skip`。
動作は正しいが記録が「provider が遅れた」になる (9/19・9/25 週報の運用ヘルス 4 で指摘済)。
全期間で lag=1 かつ `run_status=ok` (= fallback 経路で forecast を**作った**) は 2026-08-27 16:19Z の
1 行のみ (8/28 欠測インシデントの当日)。金曜は PR #130 の繰り越し経路が `requested_as_of_jst` 基準で
lag を測るため lag=0 — 同じ週のデータに修正の有無が並んで出ている。**brief FX-ASOF-FIXING** (§8)。

### Axis 6: Review Flags (`monthly_review_flags.csv`)

| flag | 発火 | 読み |
|---|---|---|
| `inspect_magnitude_mapping` | **発火** (RW 比 −7.41bp、2 か月連続) | §4〜§5: 実体は v2.5 拡張項。切ると −3.19bp で非発火 |
| `inspect_state_mapping` | **発火** (state proxy 73.7% だが magnitude 誤差 39.7bp > 30) | 高ボラ月では magnitude 誤差 (bp 絶対値) が自動的に閾値を越える。§7 |
| `inspect_direction_logic` | 非発火 (excl FLAT で simple_technical を上回る) | 方向ロジック維持 |
| `regime_/volatility_direction_collapse` | 非発火 | 8 月の崩落は解消 |
| `provider_lag_issue` / `provider_fallback_issue` | 非発火 (28.8% < 30%) | **偽陽性寸前** (Axis 5) |
| `missing_windows` / `low_annotation_coverage` / `insufficient_data` | 非発火 | — |

## 2. queue 2: 9/7 FLAT の成分分解 (完了)

`pre_expansion_close_change_bp = e_star × trailing_mean_abs_close_change_bp × (0.5 + 0.5 × conviction)`、
FLAT は `|…| ≤ 3.0bp` (固定)。replay (`scripts/analyze_estar_lag.py`、9 月窓) の実値:

| 日 | variant | e_star | trailing (bp) | conviction → 係数 | pre-expansion (bp) | 判定 | 実現 |
|---|---|---|---|---|---|---|---|
| 9/3 | α | **−0.016** | 30.2 | 0.31 → 0.66 | −0.31 | FLAT | −181.5 |
| 9/3 | β | −0.185 | 30.2 | 0.33 → 0.67 | −3.72 | down | −181.5 |
| 9/7 | α | **−0.120** | 36.4 | 0.32 → 0.66 | −2.88 | FLAT | −102.0 |
| 9/7 | β | **+0.103** | 36.4 | 0.34 → 0.67 | +2.53 | FLAT | −102.0 |
| 9/7 | δ | +0.007 | 36.4 | 0.33 → 0.67 | +0.18 | FLAT | −102.0 |
| 9/8 | α | −0.910 | 36.6 | 0.98 → 0.99 | −32.9 | down | −25.3 |

(i) **主因は e_star**: trailing (30〜36bp) と conviction 係数 (0.66) は前後の日と同水準で、|e_star| が
0.01〜0.12 まで落ちている。(ii) e_star がゼロ近傍になったのは**項の符号衝突**: 9/7 α は
`technical_score` −0.54・`u_score` −0.70・`fundamental_score` −1.0 (SMA 系、負) に対し
`price_implied_score` **+0.72** (9/4→9/7 窓の +26.3bp 反発、正) が相殺。9/3 は逆向き (SMA 系 +、
price_implied −1.0)。β (p_weight 0.40) は price_implied 側に寄るため 9/7 に符号が逆 (+0.103) になり、
variant 間で符号が割れた。(iii) **epsilon は lever ではない**: 9/7 を down にする epsilon (< 2.88bp) は
同日の β を up (MISS) に変える。variant 間で符号が割れている日を閾値で救うことはできない。

**結論**: FLAT 判定・epsilon・trailing 幅は据え置き。9/3・9/7 の FLAT は「1 日の反発が 5〜20 日の
トレンド項を打ち消した」結果で、同じ構造 (入力の冗長性と時定数差) が §4 の高 conviction 逆行の裏面に
ある。engine 改変の対象にはしない。

## 3. e_star 転換の分解 (9 月、`scripts/analyze_estar_lag.py`)

再現: `--analysis-start 2026-08-24 --analysis-end 2026-09-30 --search-start 2026-09-03 --search-end 2026-09-30
--shock-day 2026-09-03 --pre-shock-ref-dates 2026-08-26 2026-08-27 2026-08-31 2026-09-01 2026-09-02`
(8/28 欠測は skip)。

| variant | 最初の持続的正転 (primary) | 最初の正転 (secondary) |
|---|---|---|
| α / γ | **9/22** | 9/22 |
| β / δ | 9/21 | 9/7 (単発) |

ablation (primary の shift、営業日。負 = 前倒し):

| 介入 | α (pre-shock 参照 / 中立) | β | δ |
|---|---|---|---|
| statistic `momentum_5d` | **−5 / −1** (secondary −11) | +6 / +6 (遅延) | −4 / +6 |
| statistic `spot_vs_sma20` | **0 / 0** | 0 / 0 | 0 / 0 |
| statistic `prev_close_change_bp` | 0 / +1 | +1 / +1 | +1 / +2 |
| estar_term `technical_score` | −1 / −1 (secondary −11 / −5) | 0 / 0 | 0 / 0 |
| estar_term `u_score` | −1 / −1 (secondary −11) | 0 / 0 | 0 / 0 |
| estar_term `price_implied_score` | 0 / +1 | 0 / +1 (secondary +10 / +11) | +1 / +1 (secondary +11) |
| estar_term `grv_lock` | −1 / 0 | 0 / 0 | 0 / 0 |
| 他 (`fire_probability` / `alignment` / `regime_fit` / `narrative_dispersion`) | 0〜+1 | 0〜+6 | 0〜+1 |

- **α の律速は 2 か月連続で `momentum_5d`** (`technical_score` と `u_score` の両経路)。
  `momentum_5d` は実装上 **(SMA5 − SMA20) / SMA20** であり 5 日リターンではない — 時定数は SMA20 で
  決まり、9/14〜9/17 の +186bp 反発でも −1.2〜−1.9% のまま clamp (×100) に張り付いていた
  (`technical_score` = −1.0 が 9/8・9/16・9/17・9/18)。これが 9/14 週に α/γ が 5 日連続 down を出した
  機序 (週報 9/19 の観測 1・2 に対応)。
- **SMA20 飽和仮説は再度棄却** (`spot_vs_sma20` 固定で全 6 セル shift 0)。9/25 週報が「α/γ の up 転換は
  SMA20 上抜け (9/22) と一致」と書いた観察は**時期の一致にすぎない**と確定。週報 §構造的観測 (c) の
  留保どおり。
- **β/δ の早い正転 (9/7・9/16・9/17・9/21) は `price_implied_score` 由来**: 固定すると secondary が
  +10〜+11 営業日遅れる。p_weight 0.40 の β は 1 日項に引かれて符号が先に動く。
- 「追随は下方向にしか起きない」(9/19 週報) は 9/25 週報で撤回済。本分解で残る非対称は
  **反応の大きさ**: 9/17 窓 −17bp で α の e_star は −0.13 → −0.51 (price_implied が −0.39 に転じ、
  SMA 系 2 項の −1 と同符号に揃った)、9/16 窓 +75bp では −0.138 → −0.134 (price_implied +1 を
  SMA 系 2 項の −1 が打ち消す)。**符号が揃う方向にだけ大きく動く** = 冗長な入力の多数決。

## 4. 9 月の支配的欠陥: 飽和入力の多数決が最大 conviction を生み、反転日に最大の賭けになる

### 事実 (評価レコード、α、9/1〜9/29 の 21 評価日)

| 日 | 実現 | α 予測 (bp) | conviction | e_star | 誤差 | RW 誤差 | 差 (α − RW) |
|---|---|---|---|---|---|---|---|
| 9/8 | −25.3 | down −57.1 | 0.98 | −0.91 | 31.9 | 25.3 | +6.6 |
| 9/9 | −29.2 | down −39.8 | 0.90 | −0.73 | 10.6 | 29.2 | −18.6 |
| **9/10** | **+56.0** | down −45.3 | **0.94** | −0.77 | 101.3 | 56.0 | **+45.3** |
| **9/14** | **+63.9** | down −56.3 | **0.95** | −0.82 | 120.2 | 63.9 | **+56.3** |
| 9/18 | +60.3 | down −20.5 | 0.60 | −0.50 | 80.8 | 60.3 | +20.5 |
| 9/24 | +34.7 | up +25.2 | 0.43 | +0.48 | 9.5 | 34.7 | −25.2 |
| **9/25** | **−99.5** | up +46.5 | **0.75** | +0.81 | 145.9 | 99.5 | **+46.5** |
| 他 14 日 | | | | | | | 合計 −1.4 |
| **合計 (21 日)** | | | | | | | **+149.6** |

governance 窓 (9/3〜9/30、19 日) の合計 +140.9bp (= 7.41 × 19) のうち、**9/10・9/14・9/25 の 3 日で
+148.1bp、残り 16 日は −7.2bp**。方向を外した日は他にもある (9/4・9/15・9/16・9/18) が、賭けが小さい
(|予測| 6〜20bp) ため RW との差は +7〜+20bp に留まる。差を作ったのは**外したことではなく、外した日の
賭けの大きさ**である。

### 機序

3 日とも直前 1〜3 窓が同方向の大きな動き (9/10: 9/8 −102 → 9/9 −25、9/14: 9/11 −54、9/25: 4 連騰)。
その日の入力は

| 日 | fundamental (spot−SMA20) | technical (SMA5−SMA20) | price_implied (前日/trailing) | alignment | conviction | v2.5 乗数 |
|---|---|---|---|---|---|---|
| 9/10 | −1.0 (飽和) | −1.0 (飽和) | −0.80 | 1.00 | 0.94 | ×1.63 |
| 9/14 | −1.0 (飽和) | −1.0 (飽和) | −1.0 (飽和) | 1.00 | 0.95 | ×1.63 |
| 9/25 | +1.0 (飽和) | +0.77 | +0.73 | 0.91 | 0.75 | ×1.25 |

(乗数は `expected_close_change_bp / pre_expansion_close_change_bp`。) **3 入力は独立ではない**: 2 つは
SMA20 からのスプレッド、1 つは前日変化で、ショック後は機械的に同符号で飽和する。engine の alignment は
「3 つの異なる根拠が一致した」と読んで conviction を 0.94〜0.98 に上げ、magnitude 係数 (0.5 + 0.5 ×
conviction) が上限に達し、さらに v2.5 の `_volatility_expansion_multiplier` (catalyst・urgency・
fire_probability の平均が高い = まさに大変動直後) が ×1.6 を掛ける。**同じ情報を 3 回数えて確信を
作り、その確信で賭けを最大化し、拡張項でさらに増やす** — これが 8/10 (conviction 0.94、−39bp → 実現
+98.9bp、8 月の代表的失敗) を含む Aug–Sep の最悪 4 日すべてに共通する。

### conviction の信頼度は 8 月以降崩れている (α、非 FLAT、RW との差は合計 bp)

| 月 | conviction 0.7–0.9 | conviction ≥ 0.9 |
|---|---|---|
| 5 月 | 3/7 (+34.4) | — |
| 6 月 | 10/12 (−34.6) | 1/1 (−6.0) |
| 7 月 | 5/6 (+19.8) | 1/1 (−4.3) |
| 8 月 | 3/5 (+19.4) | **0/1 (+39.0)** |
| 9 月 | **0/1 (+46.5)** | **2/4 (+89.5)** |

7 月レビュー §6「conviction ≥ 0.7 で 86%」は平時 (4〜7 月) の性質で、ショック後の飽和局面では
成立しない。conviction を reliability として使う下流 (売買レイヤー planning、queue) は**飽和日の
conviction を割り引く条件**を前提に置くこと。

## 5. counterfactual replay: magnitude 経路と signal スケール (`scripts/replay_magnitude_counterfactual.py`)

再現: `python scripts/replay_magnitude_counterfactual.py --fxdata-dir <fxdata>/csv --out-dir <out>`
(既定 2026-04-01〜2026-09-30)。各日の `input_snapshot.json` を `compute_snapshot_statistics` →
`build_ugh_request_from_snapshot(stats=…)` → projection → `forecasting.py` と同じ magnitude 式で
再構築する。**無介入系列 (A) は本番の v2.6 forecast 164 件 (8/3〜9/30 × 4 variant) と方向・
`expected_close_change_bp` が bit-identical** (script が不一致で fail する)。4〜7 月は v2.3〜v2.5 で
運用されていた期間を v2.6 で replay した値。

### 5.1 magnitude 経路 (方向入力は不変)

| mode | 定義 |
|---|---|
| A | 現行 v2.6: `e_star × trailing × (0.5 + 0.5 × conviction)` → v2.5 拡張乗数 |
| B | conviction 係数を定数 0.75 に (decouple)、拡張あり |
| **C** | conviction 係数そのまま、**拡張乗数 = 1.0** (`volatility_expansion_max = 1.0` と同値) |
| D | B + C |

α (120 営業日。β/γ/δ も同符号・同程度、`summary_*.md` 参照):

| 期間 | mode | FLAT | 方向 (excl FLAT) | 平均誤差 | 中央値誤差 | RW 比 | 平均 \|予測\| |
|---|---|---|---|---|---|---|---|
| 4〜9 月 | A | 22 | 61/98 | 30.90 | 16.46 | +2.63 | 12.0 |
| | B | 20 | 62/100 | 30.14 | 16.35 | +1.86 | 10.6 |
| | **C** | **22** | **61/98** | **29.57** | **13.80** | **+1.30** | 9.5 |
| | D | 20 | 62/100 | 29.16 | 13.76 | +0.89 | 8.3 |
| 4〜7 月 | A | 14 | 45/65 | 23.32 | 12.89 | +0.60 | 9.4 |
| | C | 14 | 45/65 | 22.77 | 11.66 | +0.05 | 8.0 |
| 8〜9 月 | A | 8 | 16/33 | 45.51 | 31.85 | +6.55 | 17.2 |
| | C | 8 | 16/33 | 42.67 | 23.96 | +3.71 | 12.4 |

- **C は方向・FLAT を 1 日も変えず** (拡張は非 FLAT の magnitude だけに掛かる設計)、平均誤差を 4〜9 月
  全体で −1.33bp、8〜9 月で −2.84bp、中央値を −2.66 / −7.89bp 改善する。**月別でも 6 か月すべてで平均
  誤差が改善** (4 月 −0.1、5 月 −0.1、6 月 −0.8、7 月 −1.0、8 月 −1.6、9 月 −4.0bp)。日別では α で
  **43 日改善 (計 −201bp) / 18 日悪化 (計 +41bp)**。悪化日の最大は 9/24 (+7.4bp、up +25 で実現 +35 の
  当たり日)。9 月の中央値だけは 46.4 → 49.6 と 3bp 悪化する (当たり日の賭けも縮むため)。
- 拡張項が導入時 (FX-MAG-EXPANSION、2026-06 ★1) に狙った「方向が正しい大変動日」は、6 か月で
  当たりの利得 (+41bp) より外れの損失 (−201bp) がはるかに大きい。拡張を駆動する catalyst・urgency・
  fire_probability は**どの日が大きく動くか**を当てていない (7 月レビュー §5.5 の corr(conviction,
  実現 |Δ|) = −0.28 と同じ構図)。
- governance 窓 (9/3〜9/30) の RW 比: α +7.41 → **+3.19**、β +4.46 → +1.31、γ +7.17 → +3.02、
  δ +6.42 → +2.60。`inspect_magnitude_mapping` (閾値 5.0) は C では非発火。8 月も +5.94 → +4.27 で
  非発火。**2 か月連続の発火は拡張項 1 つに帰着する。**
- B (conviction decouple) も平均誤差を改善するが、FLAT の集合が変わる (係数 0.75 > 低 conviction 日の
  実係数) ため方向判定に副作用があり、定数 0.75 は新しい任意係数になる。7 月 §5.6 の見送り判断を維持し、
  **C の 1 か月運用後に B を再評価**する (10 月は C 単独で因果を切り分ける)。

### 5.2 最悪日への効果 (α、bp / 誤差)

| 日 | A | C | RW 誤差 |
|---|---|---|---|
| 8/10 | −39.0 / 137.9 | −25.0 / 123.9 | 98.9 |
| 9/8 | −57.1 / 31.9 | −32.9 / 7.7 | 25.3 |
| 9/10 | −45.3 / 101.3 | −28.8 / 84.8 | 56.0 |
| 9/14 | −56.3 / 120.2 | −34.8 / 98.6 | 63.9 |
| 9/25 | +46.5 / 145.9 | +37.9 / 137.4 | 99.5 |

C は最悪日の損失を 1/3〜1/4 削るが**消しはしない** — 残りは §4 の conviction 多数決 (係数 0.97〜0.99)
の分で、これは拡張項の外にある。

### 5.3 signal スケール (×100 → k): 採用しない

`derive_signal_features` / `derive_question_features` の `× 100` (|SMA スプレッド| 1% で飽和) を k に
変える counterfactual (raw `momentum_5d` / `spot_vs_sma20` を k/100 倍して全消費者を再構築):

| k | FLAT | 方向 (excl FLAT) | 平均誤差 | RW 比 | 飽和日 (technical) | conviction ≥ 0.9 | Aug 転換 / Sep 転換 (α) |
|---|---|---|---|---|---|---|---|
| 100 (現行) | 22 | 61/98 (62.2%) | 30.90 | +2.63 | 18 | 4/7 | 8/25 / 9/22 |
| 50 | 26 | 57/94 (60.6%) | 29.66 | +1.39 | 7 | 5/12 | 8/21 / 9/21 |
| 33 | 35 | 53/85 (62.4%) | 28.90 | +0.63 | 0 | 6/10 | 8/21 / 9/21 |
| 25 | 35 | 54/85 (63.5%) | 28.46 | +0.17 | 0 | 8/13 | 8/21 / 9/21 |

- 誤差は k を下げるほど縮むが、**方向の的中率は改善せず、FLAT (= 二値判定の外れ) が 22 → 35 に増える**。
  β は 63.0% → 57.8% と悪化。転換は 1〜2 営業日しか早まらない。
- k=50 では最悪 3 日 (8/10・9/10・9/14) の予測値が**一切変わらない** (スプレッド −2.7% は 2% でも飽和)。
  k=25 でも conviction 0.74〜0.77 で同方向。
- つまりスケール変更の「改善」は賭けの縮小 (平均 |予測| 12.0 → 8.5bp) で、7 月 §5.6 が退けた
  「定数 6bp が最良」と同種の L1 縮小効果。**方向ロジックの改善ではないため採用しない。** 飽和・冗長性
  そのものへの対処 (alignment が飽和入力の一致を根拠として数えない等) は別の設計論点として logic audit に
  残す (CC-M01)。

## 6. 運用 (Axis 5 の詳細と修正方針)

- **偽 lag/fallback 17 行 (28.8%)** — 機序は Axis 5 のとおり。`provider_lag_issue` / `provider_fallback_issue`
  は 30% で発火し、10 月に遅延 run が 1 本増えれば**偽陽性で `data_provider_remediation` に分類される**
  (優先度 1 で理論の判断を止める)。修正は PR #130 の繰り越し経路の一般化: Step 1 で「`current_as_of_jst`
  の 08:00 fixing がまだ来ていない (run 開始 < as_of)」場合、前営業日の batch が完備していればその日へ
  繰り越す (既存の `carried_over_from_non_business_day` 経路に乗せ、Step 2 の後退拒否・Step 7 の
  `requested_as_of_jst` 基準の lag 計測をそのまま使う)。完備していなければ**従来どおり** fallback 経路に
  落とす (救済経路の挙動は変えない)。→ brief **FX-ASOF-FIXING**。
- 金曜の繰り越し (PR #130) は 9/18・9/25 の 2 週連続で機能し、Saturday 付 weekly artifact は 2 週連続で
  生成。cron 遅延は +3h39〜+6h56 で継続 (監視のみ、優先度低)。
- PRICE-ALERT: 9 月は 7 往復 + 9/25 発報 1 件が未 clear のまま月をまたいだ。sticky 論点は未検証継続。
- catch-up 二重 publish (PR #131) は 9 月の重複ディレクトリ 0 件で実地検証済。

## 7. 測定器への所見 (閾値は spec §5.1 で月次見直し可)

- `inspect_magnitude_mapping` (RW 比 5.0bp 固定) と `inspect_state_mapping` (magnitude 誤差 30bp 固定) は
  **絶対 bp** のため、月のボラティリティに比例して発火しやすくなる (9 月の RW 平均誤差 52bp は 8 月の
  2.1 倍)。9 月の `inspect_state_mapping` は state proxy 73.7% と「magnitude 誤差 39.7bp」の組だが、
  後者は random_walk ですら 52.3bp の月である。RW 平均誤差に対する比 (例: 10〜20%) への変更を
  logic audit 候補に挙げる (CC-M02)。今月は変更しない — v2.7 で平均誤差が下がったあとの 10 月 artifact で
  絶対閾値のまま挙動を確認してから決める。
- Axis 4 の `disconfirmer_explained` 集計が artifact に無い (CC-M03)。

## 8. 判定 (step 8〜10)

### 8.1 判定カテゴリ: **`version_promotion_candidate`**

| 条件 (spec §4) | 充足 |
|---|---|
| 先行する logic audit で調査済 | 7 月 §5「v2.5 ボラ拡張項が実質的に効いていない疑い」→ 8 月 `inspect_magnitude_mapping` 発火 → 本レビュー §5 |
| 期待効果の文書化 | §5.1: 平均誤差 −1.33bp (4〜9 月) / −2.84bp (8〜9 月)、中央値 −2.66 / −7.89bp、6 か月すべてで改善、方向・FLAT 不変 |
| リスクの文書化 | §5.1〜5.2: 方向が正しい大変動日の過小が広がる (α 18 日 / +41bp)。9 月の中央値 +3bp。range_hit は無関係 (v2.6 でレンジは e_star 非依存) |
| 1 layer / 1 変更 | `engine_version` のみ。`volatility_expansion_max` default 1.8 → 1.0 (コードは不変、§5.1.3 の式で乗数 ≡ 1.0) |

**実施はユーザー承認後** (governance 出力は自動生成、logic 変更は人の判断 — spec §3 末尾)。承認時の
Version Decision Record: `engine_version` v2.6 → v2.7、freeze 10/1〜10/30、**rollback trigger =
10 月の replay (本 script、A vs C) で v2.7 の平均誤差が v2.6 replay を 1.0bp 以上上回る、または
`inspect_magnitude_mapping` が v2.7 で発火し v2.6 replay では発火しない**。→ brief
**FX-MAG-EXPANSION-REVERT**。

### 8.2 Change Candidate List

| ID | 分類 | 内容 | 根拠 | 状態 |
|---|---|---|---|---|
| CC-001 (自動) | → version_promotion_candidate | magnitude/close-error mapping | 実体は v2.5 拡張項 (§5) | accepted → brief |
| CC-002 (自動) | logic_audit | state-to-magnitude mapping | 高ボラ月の絶対閾値アーティファクト (§7) | deferred (10 月 artifact で再判定) |
| CC-M01 | logic_audit | 飽和入力の冗長性と alignment/conviction の多数決 (§4) | 最悪 4 日の共通機序。設計案は未検証、counterfactual から | proposed |
| CC-M02 | logic_audit | 絶対 bp 閾値の相対化 (§7) | 9 月 RW 52bp vs 8 月 25bp | proposed |
| CC-M03 | logic_audit | Axis 4 `disconfirmer_explained` 集計の欠落 | spec と artifact の不一致 | proposed |
| CC-M04 | data_provider_remediation | 偽 provider lag の記録 (§6) | 28.8%、閾値 30% | accepted → brief FX-ASOF-FIXING |
| CC-M05 | keep | signal スケール ×100 (§5.3) | 縮小効果のみ、方向改善なし | rejected |
| CC-M06 | keep | FLAT epsilon 3.0bp / trailing 幅 (§2) | variant 間で符号が割れる日は閾値で救えない | rejected |

### 8.3 対応キュー (2026-10-01 決定)

| # | 項目 | 種別 | 状態 |
|---|---|---|---|
| M1 | FX-MAG-EXPANSION-REVERT (`volatility_expansion_max` 1.0、v2.7) | engine | brief 発行、**ユーザー承認待ち** |
| M2 | FX-ASOF-FIXING (fixing 前着地の繰り越し) | automation | brief 発行 |
| M3 | 10 月の A/B 検証 (本 script で v2.6 replay vs v2.7 実績) | 分析 | 11 月月次で実施 |
| M4 | CC-M01 飽和/冗長性の設計 counterfactual | 分析 | 10 月中に設計、11 月月次で判断 |
| M5 | レンジ幅較正 brief (queue 1) | engine | 据え置き。9 月 89.5%、外した 2 日は設計上のテール |
| M6 | CC-M02 / CC-M03 (測定器) | 集計層 | 10 月 artifact を見て判断 |

## 9. 制限事項

- 4〜7 月の replay 値は当時の v2.3〜v2.5 運用値ではなく **v2.6 コードでの再計算**。8/3 以降 (v2.6) は
  本番と一致を確認済。
- counterfactual は magnitude 経路の変更が方向入力に影響しないことを前提にしている (v2.5 の設計不変量
  「sign/FLAT は expansion 前に確定」に依存)。B/D の FLAT 変化は係数の置換による。
- 月次 artifact は正式 run 前の再生成値。正式 artifact と差があれば本書を訂正する。
- 飽和・冗長性の機序 (§4) は replay の実値と日別分解に基づくが、代替設計の効果は未測定 (CC-M01)。
