# 2026-07 月次ロジック見直し — 事前準備 (prep)

Status: Prep note (レビュー当日の pre-reading。planning doc ではない)
作成: 2026-07-30、データは 7/29 発行分の評価まで反映

レビュー本体の位置づけ: STATUS 次の発行順序 #1「月次分析の再検証 (FX-ANNOT-LIVE 後)」
+ 7 月 governance flag の判定。結論が実装を要する場合は
`docs/engine_review_2026_07_planning.md` を起草し Task Brief 化する (AGENTS.md フロー)。

## 0. 成果物の所在

- 月次レビュー (再生成済み): `fx-daily-data` branch `csv/analytics/monthly/202607/`
  — window 7/1–7/29 (20 営業日、140 確定観測、coverage 100%)。
  ⚠️ 7/30–7/31 発行分の評価確定後に最終版を再生成すること:
  `FX_CSV_OUTPUT_DIR=<data>/csv FX_REVIEW_DATE=20260801 FX_MONTH_DAYS=23 python scripts/run_fx_monthly_review.py`
- 週次レポート 4 本: `docs/reports/fx_weekly_report_2026*.md` (6/29 週〜7/20 週)
- 1h 検証データ: `analysis/usdjpy_60m_3mo.csv` (branch 直下、7/29 取得)

## 1. Governance flag の判定 (最重要論点)

7 月の monthly review は **`inspect_direction_logic`** を発火:
「UGH 方向精度が baseline_simple_technical 比 −15.0pt (閾値 10pt)」。

事前分解の結果、**flag は測定構造のアーティファクトであり、方向ロジック自体の欠陥ではない**:

| 集計 | UGH | technical |
|---|---|---|
| 全観測 (80 obs) | 58.8% | 75.0% |
| **FLAT 予測を除く 63 obs (同一日比較)** | **74.6%** | 75.0% |
| close error (mean) | 23.4bp | 26.6bp |

- ギャップ −15pt は **17 個の FLAT 観測 (5 日: 7/3, 7/8, 7/10, 7/13, 7/15) が
  binary 判定で機械的に 0%** になることに全て由来する。方向を出した日の的中率は
  baseline と同率で、誤差では UGH が上回る。
- state 別でも整合: fire 日 100% (6 obs) / setup 59.4% / failure (=FLAT 退避) 0%。
- **ただし flag を「誤報」で closing するのは誤り**。FLAT 5 日のうち実現 |Δ|<10bp は
  4/17 obs のみで、7/13 (+53.2bp) のような取りこぼしは実害。真の論点は
  方向ロジックではなく **退避 (FLAT) の発動・解除ポリシー** にある (→ §4)。

判断オプション:
- (a) scoreboard に FLAT-aware 指標を追加 (例: `direction_hit_excl_flat` +
  FLAT 日の |realized| 分布)。governance 閾値はそのまま、解釈レイヤーで補正
- (b) governance flag の比較を「非 FLAT 日の同日比較」に変更 (閾値ロジック改修)
- (c) 現状維持で月次サマリーに手動注記
- 推奨: (a)。flag の感度は保ちつつ誤読を構造的に防ぐ。brief 1 本相当

## 2. Range 較正の系統誤差 (定量確定)

週次で 4 週連続観測した「大変動日のレンジ外れ」が閾値つきで確定:

| \|realized Δclose\| | range_hit (UGH, 7月) |
|---|---|
| < 15bp | 34/48 = 71% |
| 15–30bp | 4/4 = 100% |
| **≥ 30bp** | **0/28 = 0%** |

expected_range が ≥30bp の実現をただの一度も包含していない。ENGINE-P3B の
projection width 一本化 (`range_width_scale=2.0`) がトレンド局面の実現分布に対して
系統的に狭い。検討: realized vol 連動の width scaling / 非 FLAT 時の recenter 抑制。
engine 変更なので spec 改訂 + brief。

## 3. Magnitude 過小 (v2.5 拡張項の不作動疑い)

|realized| ≥ 30bp の非 FLAT 19 obs で **mean |expected| 6.1bp vs mean |realized|
52.1bp (8.5 倍の過小)**。FX-MAG-EXPANSION (v2.5) のボラ拡張 magnitude 項が
続伸局面で作動していない。§2 と同根の可能性が高く、原因切り分けは同一 brief で
扱うのが効率的。stC が「強トレンド週 0% / 小動き週 75%」に割れる現象 (7/13 週 vs
7/20 週レポート) も同じ根 (setup 滞留 = レンジ幅 regime の先読み失敗) とみられる。

## 4. Hysteresis 退避解除ラグ (ペア標本あり)

- 機能した例: 7/2 ショック → 7/3 FLAT 退避 (レンジ的中・誤差 17bp) → **7/6 即復帰**して的中
- 機能しなかった例: 7/9–10 下落 → 7/10 FLAT (−41.9bp を取り逃し) → **7/13 も退避継続**
  で +53.2bp 取りこぼし (7 月最大の機会損失)
- 論点: 減衰パラメータ (v2.4) の解除条件が 1 営業日粒度でしか判断できないこと自体が
  制約か。イントラデイ化 (1h) の判断基準はここに置く — execution planning
  (queue #3) 起草時に「復帰ラグの改善幅 X 以上なら 1h protocol 起案」として encode
  する方針 (7/29 議論済み)。当面は日足内での解除条件チューニングを先に検討

## 5. Regime / Volatility ラベル再検証 (queue #1 の本来テーマ)

#116 で市場 (OHLC) 由来に是正後、初のフルマンス:

- regime: 7 月は全日 trending — choppy の標本ゼロのため「choppy 全敗が構造的弱点か」の
  検証は **今月では不能**。継続観測 (choppy が出る月まで判定保留) を明記する
- volatility 層別 (UGH): high 50% / err 54bp、normal 47.5% / 19bp、low 83.3% / 11bp。
  「high-vol で弱い」は市場由来ラベルでも再現。ただし §2–3 の較正問題と交絡しており、
  レンジ/magnitude 修正後に再判定すべき
- intervention_risk medium 日の全敗 (7/2, 7/13): 標本 2 のまま。カウント継続

## 6. 運用ヘルス / その他

- provider: 7 月フル成功、yahoo_finance fallback 1 回 (7/10) のみ。異常なし
- annotation coverage 100%、state_correctness_hit は月次で 20–25% (初のフルマンス値)
- ユーザーのリピート注文グリッド (7/27 稼働、161.50–163.50 買) が週次モニタ対象。
  §2 のレンジ較正はグリッド運用の参考値にも波及するため優先度に反映してよい

## 7. 提案する進め方 (レビュー当日の判断リスト)

1. flag 判定: §1 のオプション (a)/(b)/(c) を決める → 必要なら brief
2. §2+§3 を単一の較正 brief として起草するか、原因調査 (docs-only) を先行させるか
3. §4 は日足内チューニング先行を確認、1h 化判断基準の encode 先を決める
4. §5 は「choppy 判定保留」を STATUS / 月次サマリーにどう記録するか
5. 優先順位を STATUS 次の発行順序に反映 (現 #2 governance バナー、#3 execution
   planning との並び替え)
