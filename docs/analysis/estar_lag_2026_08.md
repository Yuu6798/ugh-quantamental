# e_star 転換遅延 分析 (FX-ESTAR-LAG, 2026-08)

- Brief: `docs/briefs/2026-08_FX-ESTAR-LAG.md`
- 元 findings: `docs/engine_review_2026_08_findings.md` §1
- 再現手順: `python scripts/analyze_estar_lag.py --fxdata-dir <fx-daily-data checkout>/csv --out-dir <out>`
- 分析対象: `history/{date}/{batch_id}/input_snapshot.json` の実測値 replay。
  OHLC CSV からの再構築は不使用 (`current_spot` は別系統のため)
- 分析窓: 2026-07-22〜2026-08-28 (2026-08-28 は欠測 — GitHub Actions
  スケジューラ遅延で forecast 自体が作成されなかった日。欠測として明記し
  補完しない。評価済み営業日は 27 日)
- 転換検索窓: 2026-07-30 (ショック日) 〜 2026-08-28
- 再現性検証: 本 replay の `ugh_v2_alpha` / `beta` / `gamma` / `delta` の
  `e_star` は、`fx-daily-data` に永続化された実際の forecast レコード
  (例: 2026-08-05 の `e_star` — alpha/gamma `-0.15778`、beta `0.12`、
  delta `-0.005`) と全桁一致した。builder のスタッツ注入点
  (`market_ugh_builder.build_ugh_request_from_snapshot(..., stats=...)`)
  経由の replay が本番と bit-identical であることを実データで確認済み

## 0. TL;DR

**`fundamental_score` の SMA20 飽和仮説は、e_star の「最初の持続的正転」
(primary) 指標に関する限り、反証された** — `spot_vs_sma20` を
ショック前平均・中立値のいずれに固定しても、α/β/δ いずれの variant でも
persistent 転換日は **1 営業日も動かない** (shift = 0、全 6 セルで一致)。
一方 **`momentum_5d` (technical_score とquestion features の両方の入力)
を固定すると、常に転換が前倒しになる** (α: 参照値次第で -2〜-10 営業日、
β/δ: -2 営業日、reference 非依存で符号は一貫) — これが検証した 3 raw
statistic の中で最も persistent 転換を律速している。`prev_close_change_bp`
(price_implied_score 分子) は符号・大きさとも reference と指標 (primary
/secondary) に依存し、一貫した律速因子とは言えない (§4)。

variant 間の転換日の分散は、informal な「forecast_direction=up」基準では
β 8/11・δ 8/19・α/γ 8/21 だったが、brief が指定する厳密な e_star 符号基準
では **secondary (最初の正転) が β 8/5・δ 8/11・γ 8/18・α 8/19** と、より
早く・より広く分散する (§3)。この差は production の FLAT epsilon
判定 (`expected_close_change_bp` 側の閾値) が e_star の符号そのものより
粗い dead-zone を持つために生じる — 符号一致だけでは因果を語れないという
brief の注意がここでも成立する。**primary (持続的正転) は 4 variant すべて
2026-08-25 で一致** し、8/24 の全 variant 共通の一時的マイナス再転落が
共通の「リセット点」になっているため。engine 改変は不要 (replay のみ、
brief スコープ通り) — ただし momentum_5d 経路 (technical_score /
question_direction の時定数) を次の調査候補として記録する (§6)。

## 1. 手法

### 1.1 replay パイプライン

各評価日について:

1. `history/{date}/{batch_id}/input_snapshot.json` を読み戻し、
   `FxProtocolMarketSnapshot` を再構築 (`load_market_snapshot`)
2. `compute_snapshot_statistics(snapshot)` で raw statistics を計算
3. (ablation 時のみ) 対象 raw statistic を参照値で上書き
4. `market_ugh_builder.build_ugh_request_from_snapshot(snapshot,
   stats=<上書き済み dict>)` で `derive_question_features` /
   `derive_signal_features` / `derive_alignment_inputs` /
   `derive_state_event_features` および SSV/Omega scaffolding を **全て
   同じ stats dict から再構築** (列挙ベースの部分差し替えではなく、
   `build_ugh_request_from_snapshot` 自体が `stats` を全経路で参照する
   構造を使うことで、`momentum_5d` の第 2 の消費者
   (`derive_question_features` の `question_direction`/`q_strength`) も
   含めて漏れなく再構築される)
5. `engine.projection.run_projection_engine` に variant の
   `ProjectionConfig` を渡して `e_raw` / `gravity_bias` / `e_star` を得る

無介入 replay (stats 上書きなし) が本番出力と bit-identical であることは
`tests/fx_protocol/test_market_ugh_builder.py::TestStatsAwareInjection` と
上記の実データ照合の両方で確認済み。

### 1.2 転換抽出関数

`scripts/analyze_estar_lag.py::extract_transitions` (unit test:
`tests/fx_protocol/test_estar_lag_extraction.py`, 15 cases — multi-crossing
/ always-positive / no-recovery / zero-is-non-positive を含む合成 e_star
系列、ファイル I/O なし):

- 検索窓は `[2026-07-30, 2026-08-28]` に固定。窓開始前の正値は転換候補に
  含めない
- **primary (最初の持続的正転)**: 検索開始後に `e_star <= 0` を
  ≥1 回観測した後の正値で、かつそれ以降 (窓終端まで) 一度も
  `e_star <= 0` に戻らない最初の日
- **secondary (最初の正転、単発可)**: 上記の「正値」条件のうち、事後の
  持続性を問わない最初の日
- `ALWAYS_POSITIVE_POST_SHOCK`: 窓内で一度も `e_star <= 0` にならない
  系列 → 転換日 null、「遅延そのものが存在しない」と報告
- `NO_POST_SHOCK_RECOVERY`: 窓終端時点で `e_star <= 0` (窓内で正転が
  あっても最終的に戻らない場合を含む) → 転換日 null

### 1.3 介入対象と参照値

3 つの raw statistic (それぞれ 1 消費者ではなく統計→request 全経路を
再構築):

| raw statistic | 主な消費者 | 時定数 (findings §1 の仮説) |
|---|---|---|
| `spot_vs_sma20` | `fundamental_score` | ~20 営業日 (SMA20) |
| `momentum_5d` | `technical_score`, `question_direction`/`q_strength` | ~5 営業日 |
| `prev_close_change_bp` (分子のみ) | `price_implied_score` (分母 `trailing_mean_abs_change_bp` は不変) | 1 営業日 |

参照値は各 raw statistic につき 2 通りを両方実施:

| stat | ショック前平均 (2026-07-23〜07-29) | 中立値 |
|---|---|---|
| `spot_vs_sma20` | 0.0078265 | 0.0 |
| `momentum_5d` | 0.0051755 | 0.0 |
| `prev_close_change_bp` | 10.9033 bp | 0.0 |

参照値は分析窓全体を通して定数として固定 (「この特徴量がショック後も
ショック前水準/中立水準のまま推移していたら」という counterfactual)。
対象 variant は α・β・δ (brief 指定の 3 variant — 方向 weight 構成が
異なる代表)。γ は記述的 baseline 比較にのみ含める。

## 2. 記述統計 (baseline / alpha config, script 出力: `daily_series.csv`)

- `fundamental_score` (`spot_vs_sma20 × 100` clamp) は **2026-07-31 に
  負転し、2026-08-26 まで一度も正に戻らない** — 約 19 営業日の連続負値。
  ただし **clamp 飽和 (`|spot_vs_sma20 × 100| >= 1.0`) は 27 営業日中
  10 日のみ**: 7/31・8/3〜8/7・8/10〜8/12 (連続 9 日) + 8/20 (単発
  1 日)。8/13〜8/19 と 8/21 以降は負ではあるが非飽和 — 「符号が負」と
  「clamp に張り付いている」は別現象であり、時定数が揃って見えるのは
  符号の話であって飽和の話ではない
- `technical_score` (`momentum_5d × 100` clamp) は 2026-08-03 に負転し
  2026-08-27 に正転 — 符号反転自体の帰結期間は fundamental_score とほぼ
  同じ長さになるが、経路は異なる (momentum は 5 日ウィンドウの傾き)
- `price_implied_score` (前日変化 bp 比) は最も高頻度に符号反転
  (7 回の負転・7 回の正転、1 営業日粒度で振動) — 想定通り最短時定数
- 7/30 のショック窓 (窓始点 7/30・終点 7/31) は **8/27 発行分まで
  trailing 20 窓に残存** (`shock_window_in_trailing20 = True` が
  7/31〜8/27 の全日で成立)。8/28 は欠測のため実際に 20 窓から抜けた
  瞬間は観測できず、次の観測可能日 (8/31 以降) 待ちとなる — findings
  §2 の指摘と整合

## 3. baseline (無介入) の variant 別転換日

`transitions_baseline.csv`:

| variant | primary (持続的正転) | secondary (最初の正転) |
|---|---|---|
| ugh_v2_alpha | 2026-08-25 | 2026-08-19 |
| ugh_v2_beta | 2026-08-25 | 2026-08-05 |
| ugh_v2_gamma | 2026-08-25 | 2026-08-18 |
| ugh_v2_delta | 2026-08-25 | 2026-08-11 |

**primary は 4 variant すべて 2026-08-25 で一致する。** これは 8/24 に
全 variant が揃って `e_star <= 0` へ一時後退した (findings §1 の「8/24 は
全 variant FLAT へ一時後退」に対応) ため、8/25 が共通の「最後のリセット
点」になっているからで、律速 feature の variant 差を primary 指標だけで
語ることはできない。**variant 間の分散は secondary (最初の正転) に
現れる**: β 8/5・δ 8/11・γ 8/18・α 8/19 — 早い順の並びは informal な
「β→δ→α/γ」と大枠一致するが、絶対日付は 6〜14 営業日早い。

**この差は方法論の違いによるもので矛盾ではない**: production の
`forecast_direction` は `expected_close_change_bp` に epsilon dead-zone を
適用した結果であり、`e_star` の符号そのものより粗い。実例 (beta,
2026-08-05): `e_star = 0.12` (brief の定義では正転) だが
`forecast_direction = flat` (`expected_close_change_bp = 0.0`)。同じ
現象が delta の 2026-08-11 (`e_star = 0.0057`, direction=flat) でも
起きている。findings §1 の「β 8/11」「δ 8/19」は
`forecast_direction == up` に転じた日であり、brief が指定する
「`e_star` 符号」基準ではより早い日が最初の正転として現れる。**両者は
別の定義であり、本書は brief 通り `e_star` 符号を採用する** — 符号一致
だけで律速を断定しないという brief の注意はこの epsilon dead-zone にも
当てはまる (secondary の早い日は「弱い正転」であって「確信を持った
up 予測」ではない)。

## 4. ablation grid (`ablation.csv` の要約)

shift は `ablated_index - baseline_index` (検索窓内の営業日インデックス
差)。負 = 介入で転換が前倒し (その raw statistic の実際の推移が転換を
遅らせていた = 律速)。正 = 介入で転換が後ろ倒し (その raw statistic の
実際の推移はむしろ転換を助けていた)。

### 4.1 primary (持続的正転) への影響

| variant | stat | pre-shock 平均 参照 | 中立 (0.0) 参照 |
|---|---|---|---|
| alpha | `spot_vs_sma20` | shift 0 (8/25→8/25) | shift 0 |
| alpha | `momentum_5d` | **shift -10 (8/25→8/11)** | shift -2 (8/25→8/21) |
| alpha | `prev_close_change_bp` | shift -1 (8/25→8/24) | shift -1 |
| beta | `spot_vs_sma20` | shift 0 | shift 0 |
| beta | `momentum_5d` | shift -2 (8/25→8/21) | shift -2 |
| beta | `prev_close_change_bp` | **shift -6 (8/25→8/17)** | shift -2 |
| delta | `spot_vs_sma20` | shift 0 | shift 0 |
| delta | `momentum_5d` | shift -2 (8/25→8/21) | shift -2 |
| delta | `prev_close_change_bp` | **shift -5 (8/25→8/18)** | shift -1 |

`spot_vs_sma20` (SMA20 飽和仮説の対象) は **6 セル全てで shift = 0** —
3 variant × 2 参照のどの組み合わせでも persistent 転換日を 1 営業日も
動かさない。`momentum_5d` は 6 セル全てで負 (前倒し) — 大きさは
reference 依存 (alpha は pre-shock 参照で -10、中立参照で -2 と大きく
乖離するが、beta/delta は両参照で -2 と安定)。`prev_close_change_bp` は
alpha でわずか (-1、両参照で同じ)、beta/delta では pre-shock 参照時に
大きい (-5〜-6) が中立参照では小さい (-1〜-2) — reference 依存が明確。

### 4.2 secondary (最初の正転) への影響

| variant | stat | pre-shock 平均 参照 | 中立 (0.0) 参照 |
|---|---|---|---|
| alpha | `spot_vs_sma20` | shift 0 | shift 0 |
| alpha | `momentum_5d` | shift -12 | shift -10 |
| alpha | `prev_close_change_bp` | shift 0 | shift +3 |
| beta | `spot_vs_sma20` | shift 0 | shift 0 |
| beta | `momentum_5d` | shift -1 | shift 0 |
| beta | `prev_close_change_bp` | **shift +8** | **shift +9** |
| delta | `spot_vs_sma20` | **shift +5** | **shift +5** |
| delta | `momentum_5d` | shift -5 | shift -4 |
| delta | `prev_close_change_bp` | shift +5 | shift +6 |

secondary では `spot_vs_sma20` は alpha/beta で shift 0、**delta では
+5 (後ろ倒し)** — 中立化するとむしろ delta の最初の正転が遅くなる
(delta の実際の spot_vs_sma20 推移は初期の弱い正転を助けていた側)。
`prev_close_change_bp` は beta/delta で符号が primary と逆転し
(+5〜+9、後ろ倒し) — 「短時定数の feature を均せば早く転換する」という
単純な直感が secondary 指標では成立しない場合がある。`momentum_5d` は
secondary でも一貫して負 (前倒し) で、primary と合わせて最も方向が
安定した stat。

## 5. brief の設問への回答

**Q1. 律速 feature は variant ごとにどれか (両参照で)。**
persistent (primary) 指標では、**3 variant すべてで `momentum_5d` が
唯一 reference 非依存に前倒し方向へ動く feature**。`spot_vs_sma20` は
3 variant × 2 参照の全 6 セルで shift 0 = 律速していない。
`prev_close_change_bp` は beta/delta の pre-shock 参照でのみ momentum に
匹敵する大きさの前倒し (-5〜-6) を示すが、中立参照では小さくなる
(reference 依存)。**alpha は momentum_5d の効果量が参照によって大きく
変わる (-10 vs -2) 唯一の variant** — alpha は `u_weight=0.40` で
beta/delta (いずれも `u_weight=0.20`) の 2 倍。`u_score`
(`compute_u`) は momentum_5d 由来の `question_direction`/`q_strength`
と `technical_score` の両方を通じて momentum に感応するため、
`u_weight` が高い alpha は momentum_5d の影響が `direction_signal` に
二重の経路 (u_score 経由 + technical_score 直接) で伝わり、単純な
`t_weight` の大小 (alpha 0.30 = delta 0.30 > beta 0.20) だけでは
説明が付かない alpha 固有の感度になっていると考えられる。

**Q2. SMA20 飽和仮説は生き残るか。**
**persistent (primary) 転換に関しては棄却する。** `spot_vs_sma20` の
ablation は 3 variant × 2 参照の全パターンで shift = 0 であり、
「fundamental_score が主因」という仮説の中心的予測 (これを中立化すれば
転換が早まる) を支持しない。§2 で見た通り fundamental_score 自体は
符号として約 19 営業日連続で負だが、これは観察された遅延の期間と
「たまたま近い」だけで、causal な寄与ではない — brief が事前に警告した
「符号一致・日付一致だけの因果結論は不可」がここで実証的に裏付けられた
形になる。secondary では delta のみ nonzero (+5、しかも後ろ倒し方向) で、
どちらの指標・参照でも仮説を支持する方向の結果は一つも出ていない。

**Q3. variant 間の 8 営業日分散 (config 差) を説明できるか。**
**説明できない、あるいは説明する必要がない、が正確な結論。** primary
指標では 4 variant が 2026-08-25 に収束するため、そもそも primary
レベルでの分散は (少なくとも 8 月のこのケースでは) ほぼ存在しない
— 8/24 の全 variant 共通の一時反落が「共通リセット点」を作っている
ためで、これは config 差ではなく市場の共通ショックに起因する。
secondary レベルでは分散があるが (β 8/5〜α 8/19、14 営業日)、
`spot_vs_sma20` の ablation はこの分散をほぼ動かさない
(beta/alpha: shift 0)。`momentum_5d` は secondary でも一貫して前倒し方向に効くが、alpha
(-12/-10) が beta (-1/0) や delta (-5/-4) より明確に大きい。delta は
alpha と同じ `t_weight=0.30` を持ちながら beta に近い効果量なので、
「`t_weight` が大きいほど momentum ablation の効果が大きい」という
単純な説明はこのデータでは成立しない。alpha だけが持つ
`u_weight=0.40` (beta/delta の 2 倍) が、u_score 経由の momentum
感応 (§5 Q1) と合わせて alpha 固有の大きな効果量を生んでいる、という
方が観測と整合する。**「SMA20 飽和の variant 差」という当初の仮説の
形では variant 間の分散を説明できないが、「config の direction weight
構成が momentum_5d への感応度を変える」という別の説明はこのデータと
矛盾しない。** ただし 3 点 (alpha/beta/delta) のみの観測から一般化は
できず、これは検証ではなく観察に留める。

**Q4. reference 依存性はあるか。**
**あり、stat と指標によって程度が異なる。** `spot_vs_sma20` は
reference 非依存 (全セルで参照に関わらず結果が一致 — shift 0 または
delta の secondary で +5/+5)。`momentum_5d` は符号が reference 非依存
(常に負) だが、alpha の primary でのみ大きさが大きく異なる (-10 vs -2)。
`prev_close_change_bp` は **最も reference 依存が強い**: primary では
pre-shock 参照の方が中立参照より一貫して大きい前倒し効果を示す
(beta -6 vs -2、delta -5 vs -1) が、secondary では符号自体が
variant によって割れる (alpha は 0→+3 で参照依存の符号反転、
beta/delta は +8/+9、+5/+6 で常に後ろ倒しだが大きさが参照依存)。
**`prev_close_change_bp` に関する結論は reference の選び方に依存する
ため、「律速している」と断定はしない。**

## 6. 結論・engine 改変の要否

- **engine 改変は不要** (本 brief のスコープ通り、replay のみ)
- **SMA20 飽和仮説 (`fundamental_score` clamp) は persistent 転換の
  主因として棄却**。この結論はデータに強く支持されている
  (3 variant × 2 参照 = 6 セル全てで shift = 0)
- **`momentum_5d` (technical_score / question_direction の入力) が
  最も一貫して律速方向に効く raw statistic** — ただし「主因」と
  断定するには、単一の raw statistic のみを対象にした本 ablation の
  範囲を超える (例: `direction_signal` の 3 成分間の相互作用、
  `conviction_multiplier` との交互作用まで踏み込んだ追加分析が必要)。
  次の調査候補として記録するが、本書は「momentum_5d が主因」という
  強い主張はしない — momentum_5d のablation効果の大きさが
  alpha で reference に強く依存する (-10 vs -2) こと自体が、単純な
  単一原因モデルでは説明が終わらないことを示している
- `prev_close_change_bp` は reference 依存が強く律速因子として
  確定的な結論を出さない
- **次の brief 候補 (提案、本 brief のスコープ外)**: (a)
  `momentum_5d` を直接対象にした追加 ablation (5 日ウィンドウを
  10/15 日等に変えた感度分析)、(b) `direction_signal` の 3 成分間
  interaction を分離する counterfactual、(c) production の
  `forecast_direction` epsilon 判定と `e_star` 符号の乖離
  (§3 で発見) 自体を独立の観測課題として扱うかどうかの判断

## 7. 制限事項

- ablation は raw statistic を **分析窓全体で定数固定** する
  counterfactual であり、「もしこの feature が毎日実際の値のまま
  ノイズだけ抜いたら」等の他の counterfactual 設計は検証していない
- 2026-08-28 が欠測のため、検索窓の終端は実質 2026-08-27 (最後に
  観測可能な日) であり、primary の「持続」判定はこの日までしか
  確認できていない。8/31 以降のデータで再検証すれば primary が
  再度反転する可能性は排除できない
- 3 variant (alpha/beta/delta) のみの ablation であり、gamma は
  baseline 比較にのみ含めた。gamma への ablation は追加検証で
  裏付けが必要
- 参照値 (ショック前平均) は 2026-07-23〜07-29 の 5 営業日のみから
  算出しており、サンプルが小さい
