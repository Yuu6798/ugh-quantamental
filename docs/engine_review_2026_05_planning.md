# Engine Review 2026-05 — End-of-Month Planning

Status: **PLANNING (open)** — 2026-05-29 月末レビューで観測された engine 内部の
構造的問題を整理し、6 月着手する fix を P0/P1/P2 にラベル付けする計画書。
スタイル convention は `Yuu6798/semantic-ci-code/docs/*_planning.md` に準拠
(status banner / 定量現状 / non-goals / cross-ref / 各 fix の target.yaml 雛形)。

## 0. 背景と Goal

### 背景

5/8 の v1→v2 cut-over 以降、3 週間 (15 営業日 × 4 変種 = **60 サンプル**) の
data accumulation を経て月末レビュー (5/29) を実施した。weekly metrics は
表面上良好 (UGH dir rate 60-80%、close error 13-15 bp、range hit 100%) だが、
forecast.csv の **engine 内部値**を仕様 (`docs/specs/fx_ugh_engine_v2.md`)
およびコード
(`src/ugh_quantamental/engine/projection.py`, `engine/state.py`,
`fx_protocol/forecasting.py`) と照合した結果、**メトリクス解釈を歪めうる構造的
問題が複数存在**することが確認された。

要点:

- **expected_range が全 4 variants で完全共有** (`forecasting.py:53-55`,
  `314-317`)。`range_hit 20/20 = 100%` の実体は 1 予測の 4 重カウント、
  3 週累計 60/60 は実質 15/15。
- **state classifier の prob 分布が一様に近い** (softmax T=1.0 + evidence
  multiplicative gating)。dominant_state の遷移が ±0.001〜0.013 のマージン
  で flip する knife-edge 設計。
- **FLAT direction が事実上出ない** (`forecasting.py:41-46`、`expected_close
  _change_bp == 0` でしか発火しない)。**15 営業日 × 4 変種 = 60 サンプル**
  中 FLAT 0 件、無動作日
  (5/26 = -0.6 bp) も engine は強気予測を出した。
- **fire 状態が multiplicative gate で出にくい** (`state.py:88`、
  `catalyst × prior.fire × urgency × follow_through` の積)。60 サンプル中
  1 件 (5/8 alpha/delta/gamma) のみ。
- conviction の役割 (reliability スコア兼 magnitude scaler、
  `forecasting.py:302-305`) は仕様通り動作しているが、命名が誤解を招く。

これらは前回のレビュー報告 (5/29) で表面化したが、本書はそれを **コード
レベル裏取り + fix の優先順位 + semantic-ci 越しのゲート設計** に落とし込む。

### Primary Goal

**6 月の data accumulation を「信用できる評価指標」のもとで進められる状態を
作る** こと。具体的には:

- range_hit メトリクスがインフレしている件を、まず **集計修正 (短期)** で
  止血、続いて **range の意味付け再定義 (中期)** で根治。
- state classifier の dominant_state 遷移が knife-edge である件を、
  **softmax sharpening + evidence formula 見直し** で discrimination を回復。
- 売買システム構築時に「state ベースのポジションサイジング」「FLAT 認識」が
  実用可能な engine output 形に整える。

### Non-Goals

- **既存の v1 互換性破壊は行わない**。v1 は retired 済み (`spec §5.2`)、
  本書の fix はすべて v2 onward。
- **CSV / JSON 公開スキーマの破壊は行わない**。`forecast.csv` の列追加は
  許容、列削除 / 列の意味変更は別 phase。
- **`compute_e_raw` / `compute_u` / `compute_alignment` の数式は変更しない**
  (本書は spec §6.1 の v2 数式は固定として扱う)。本書のスコープは「engine が
  出した値の事後処理 + state classifier の正規化」に限定。
- **conviction の二重役割問題** (reliability × magnitude scaler) は議論待ち、
  本書では P2 として記録するのみで実装変更はしない。

## 1. 定量的現状 (3 週間 / 60 サンプルの観測)

| 観測項目 | 値 | コメント |
|---|---|---|
| UGH 4 変種 ensemble direction hit rate | 37/60 = 62% | trending 偏り、choppy 未経験 |
| UGH 4 変種 mean close error | 13-15 bp | random_walk (28-29 bp) 比で良好 |
| **range_hit (報告値)** | **60/60 = 100%** | **実体は 15/15** (variant 共有) |
| `dominant_state` 遷移回数 | 4 回 (setup⇄dormant) | すべて prob margin ≤ 0.013 |
| `fire` 観測回数 | 1 日 × 3 変種 (5/8) | 60 サンプル中 5% |
| `FLAT` direction 観測回数 | **0** | UGH 仕様上ほぼ不可能 |
| 4 変種の prob_dormant 分散 | range 0.04% | state は **architecture 上 variant 依存** (state engine が projection result を変種別に消費) だが、現状 softmax T=1.0 + conviction の variant 差が小さく empirical 分散は低い。**Phase 2 sharpening 後に増える見込み** (§6) |
| 4 変種の `expected_close_change_bp` 分散 | range 13-23% | direction signal は variant 依存 ✅ |
| 4 変種の `expected_range` 分散 | **0%** (完全一致) | **未差別化バグ** |

## 2. P0 / P1 / P2 整理

| Pri | 項目 | 影響 | コード場所 | 工数感 |
|---|---|---|---|---|
| 🔴 **P0** | [§3] **`expected_range` の variant 分離 + range_hit 集計修正** | 評価指標の正当性 (`range_hit` 4× インフレ) | `fx_protocol/forecasting.py:53-55, 314-317`, `fx_protocol/reporting.py`, `fx_protocol/weekly_reports_v2.py` | 中 |
| 🔴 **P0** | [§4] **State classifier の sharpening** (softmax_temperature 0.5 化 + fire gate 緩和) | `dominant_state` の knife-edge 遷移を解消、`fire` を観測可能領域へ | `engine/state.py:60-117, 140-156`, `engine/state_models.py:29` | 大 (test impact 大) |
| 🟡 **P1** | [§5] **FLAT direction の epsilon 閾値導入** | engine が「no-opinion / flat」を表明可能に | `fx_protocol/forecasting.py:41-46` | 小 |
| 🟡 **P1** | [§6] **per-variant scoreboard の集計整理** | `range_hit` (variant 共有) のみ per-batch 化、`state_proxy_hit` / `dominant_state` は variant 依存のため per-variant 維持 | `fx_protocol/reporting.py`, `fx_protocol/weekly_reports_v2.py` | 中 |
| 🟢 P2 | [§7] conviction の二重役割 (reliability × magnitude scaler) を spec に明文化 | 命名混乱の根治 | `docs/specs/fx_ugh_engine_v2.md` §6, `engine/projection.py` docstring | 小 |
| 🟢 P2 | [§8] dormant state ↔ forecast magnitude の整合性ルール定義 | 売買 system 設計時の入力品質 | spec §5/§7 と impl の整合 | 小 |
| 🟢 P3 | state transition driver の observability 拡張 | 月次レビュー効率 | `fx_protocol/observability.py` | 小 |

## 3. P0 Fix #1 — `expected_range` の variant 分離 + range_hit 集計修正

### 3.1 現状

`forecasting.py:53-55`:

```python
def _build_range_from_baseline_context(current_spot, trailing_mean_range_price):
    band_half = trailing_mean_range_price / 2.0
    return _shared_range(current_spot - band_half, current_spot + band_half)
```

`build_ugh_variant_forecast` (L314-317) はこのヘルパーを呼ぶ際 **variant の
ProjectionConfig を渡していない**。結果として 4 variants 全てが
`baseline_context` 由来の同一 range を出力する。

データ実証 (5/27 USDJPY):

```
ugh_v2_alpha: range_lo=158.745, range_hi=159.835
ugh_v2_beta:  range_lo=158.745, range_hi=159.835
ugh_v2_delta: range_lo=158.745, range_hi=159.835
ugh_v2_gamma: range_lo=158.745, range_hi=159.835
```

派生問題:

1. **メトリクス水増し**: weekly report の `range_hit_count=20` は実質 `5`。
2. **engine 評価指標として不適切**: range は `current_spot ± trailing_mean
   _range_price/2` という統計バンドで、e_star や conviction を一切参照
   していない。「engine が立てた予測」ではない。
3. **spec §5.2 の variant exploration 趣旨と乖離**: 4 variants は
   "different parameter spaces を探索する" のが目的だが、range 出力では
   差別化されていない。

### 3.2 提案 (二段階)

#### 3.2.1 Phase A (短期、止血): 集計修正のみ

`fx_protocol/reporting.py` および `weekly_reports_v2.py` の range_hit 集計を
**per-batch (snapshot 単位) で 1 度だけカウント** するよう変更する。同じ
`forecast_batch_id` 内の UGH variants は range が共有なので、4 重カウント
ではなく 1 度のヒット / ミスとして集計。

`MetricsRow` の意味付け:

- before: `range_hit_count = sum over (variant, day) of range_hit`
- after:  `range_hit_count = sum over (forecast_batch_id) of (UGH range_hit any)`

ただし `forecast_csv` レベルの個別レコードはこれまで通り (per-variant) で
emit する (downstream 互換性のため)。集計層だけ修正。

#### 3.2.2 Phase B (中期、根治): variant ごとに range を生成

`_build_range_from_baseline_context` に variant の ProjectionConfig を渡し、
**variant 別のスケーリングで range を組み立てる**。具体的には:

```python
def _build_range_from_projection(
    current_spot: float,
    e_star: float,
    conviction: float,
    config: ProjectionConfig,
    trailing_mean_range_price: float,
    trailing_mean_abs_close_change_bp: float,
) -> ExpectedRange:
    # engine 予測 (e_star) を中心、信頼度 (conviction) で帯幅を調整
    center_bp = e_star * trailing_mean_abs_close_change_bp * (0.5 + 0.5 * conviction)
    center_price = current_spot * (1 + center_bp / 10000)
    band_half = trailing_mean_range_price / 2.0 * (1.0 - 0.5 * conviction)  # 高 conviction → 狭い帯
    return ExpectedRange(
        low_price=center_price - band_half,
        high_price=center_price + band_half,
    )
```

これにより range も variant ごとに differ、range_hit が**意味のある engine
評価メトリクス**になる。

呼び出し側 (`build_ugh_variant_forecast`) は両方の trailing 値を `baseline
_context` から渡す:

```python
expected_range = _build_range_from_projection(
    current_spot=ctx.current_spot,
    e_star=projection_res.e_star,
    conviction=projection_res.conviction,
    config=variant_config,
    trailing_mean_range_price=ctx.trailing_mean_range_price,
    trailing_mean_abs_close_change_bp=ctx.trailing_mean_abs_close_change_bp,
)
```

> **設計議論**: Phase B の式は仮案。`bounds_base_width`, `bounds_mismatch
> _coef` 等 (`build_projection_snapshot` L194-201) で既に projection layer
> が range を計算しているので、それを直接使う案もある。両者を比較した上で
> spec に書き起こすのは Phase B 着手時に決定。

**Phase B `target.yaml` (参考雛形)**:

```yaml
intent: "Generate variant-specific expected_range from projection result (e_star, conviction, config). Concurrently revert range_hit aggregation from per-batch to per-variant (see §6)."
change:
  primary_kind: feature
  allowed_secondary_kinds: [test_update]
  scope:
    modules:
      - ugh_quantamental.fx_protocol.forecasting
      - ugh_quantamental.fx_protocol.reporting          # §6 集計を per-variant に戻す
      - ugh_quantamental.fx_protocol.weekly_reports_v2  # 同上
      - ugh_quantamental.fx_protocol.monthly_review     # 同上
      - ugh_quantamental.fx_protocol.automation_models  # engine_version v2.2 → v2.3 bump
api_surface:
  allow_changes:
    - fqn: "fx_protocol.automation_models.FxDailyAutomationConfig.engine_version"  # default v2.2 → v2.3
constraints: []
```

### 3.3 `target.yaml` (Phase A)

```yaml
intent: "Fix range_hit metric inflation: aggregate range_hit per-batch instead of per-variant, since v2 UGH variants share the same expected_range output. Add synthetic ugh_v2_ensemble strategy row and update is_ugh_kind to recognize it so monthly baseline comparison skips it."
change:
  primary_kind: refactor
  allowed_secondary_kinds: [test_update]
  scope:
    modules:
      # NOTE (2026-05-31, Phase 1A brief 起草時): fx_protocol.reporting は本 Phase A
      # から外し、別 follow-up brief で扱う。reporting.py は v1 DB weekly path
      # (M16) で StrategyWeeklyMetrics.strategy_kind が typed StrategyKind enum
      # (reporting.py:326-375) のため、§3.2.1/§6 の string-keyed `ugh_v2_ensemble`
      # 行機構を載せられない (enum member 追加が必要、本書は回避方針)。かつ
      # per-variant typed 行は既に非合算で 4× inflation を起こさない。Phase 1A は
      # string-keyed CSV path (weekly_reports_v2 + monthly_review) のみに絞る。
      # - ugh_quantamental.fx_protocol.reporting  # → 別 follow-up brief へ移送
      - ugh_quantamental.fx_protocol.weekly_reports_v2
      - ugh_quantamental.fx_protocol.monthly_review
      - ugh_quantamental.fx_protocol.models  # is_ugh_kind に ugh_v2_ensemble を追加 (§6.2)
api_surface:
  allow_changes:
    - fqn: "fx_protocol.models.UGH_V2_ENSEMBLE_KIND"  # 新 public 定数 (§6.2)
    - fqn: "fx_protocol.models.is_ugh_kind"  # ugh_v2_ensemble を True にする挙動拡張
constraints: []
```

### 3.4 検証

- 既存 weekly report の `range_hit_rate` が 100% → 100% (UGH range が
  共有のため値そのものは変わらない) のはず。
- ただし scoreboard CSV の `range_hit_count` 列は 1/4 になる。
- `tests/fx_protocol/test_weekly_report_v2.py` の golden fixture を更新。
- Phase B 着手は Phase A merge 後、別 PR。

## 4. P0 Fix #2 — State Classifier Sharpening

### 4.1 現状

`engine/state_models.py:29`:

```python
softmax_temperature: FiniteFloat = Field(default=1.0, ge=1e-8)
```

`engine/state.py:140-156` (softmax 正規化) は temperature 1.0 で各 state
evidence score を確率化する。

`compute_state_evidence` (L65-117) の各 state 式:

```python
dormant = w_d * clamp((1-conv) * (1-urg) * (1-cat) * (1-ft))
setup   = w_s * clamp(pos_e * (1-sat) * (1-p_fire) * (1-cat + 0.4*cat))
fire    = w_f * clamp(cat * prior.fire * urg * ft)
expansion = w_e * clamp(pos_e * conv * ft * (0.6 + 0.4*(p_fire + p_exp)))
exhaustion = w_x * clamp(pos_e * sat * mismatch_shrink * (0.5 + 0.5*ft))
failure = w_F * clamp(max(neg_e, disconfirmation, regime_shock))
```

各 state スコアが multiplicative + `_clamp(., 0, 1)` で [0, 1] に押し込ま
れるため、生スコアが 0.1〜0.4 のレンジに集中。softmax T=1.0 だとこの差が
exp で増幅されず、結果として 6 状態の prob が 0.10〜0.23 のほぼ均一分布
になる。

データ実証 (5/27 alpha):

| state | dormant | setup | fire | expansion | exhaustion | failure |
|---|---:|---:|---:|---:|---:|---:|
| prob | **0.213** | 0.209 | 0.107 | 0.171 | 0.105 | 0.195 |

uniform (1/6 = 0.167) との偏差は ±0.06 程度。dormant が setup を上回る
マージンは **0.004** で knife-edge。

### 4.2 提案 (2 軸 fix)

#### 4.2.1 軸 1 — softmax_temperature を 0.5 に下げる

`StateConfig.softmax_temperature` の default を `1.0 → 0.5` に変更。
これだけで evidence の差が exp で 2 乗的に増幅され、winner state の
prob が 0.21 → 0.30+ に伸びる (推定)。dominant_state の knife-edge 性が
緩和される。

> 副作用: 既存 test fixture の prob 数値が変わる。test 側 acceptable
> range の更新が必要。

#### 4.2.2 軸 2 — fire の multiplicative gate を緩和

現状の `fire = catalyst × prior.fire × urgency × follow_through` は
4 因子の積で、どれか 1 つが 0 近くだと fire が 0 に落ちる。これを
**weighted sum** に変更:

```python
# 提案: weighted sum + minimum activation guard
fire = config.fire_weight * _clamp(
    0.35 * catalyst
    + 0.35 * prior.fire
    + 0.15 * urgency
    + 0.15 * follow_through
)
```

これにより catalyst 単独が高い日 (event-driven) でも fire が出やすくなる。

> 議論: 軸 2 は spec §5.3 の "fire_probability redefinition" と直接干渉
> するため、spec の更新も同 PR で必要。**spec §5.3 の意図** (multiplicative
> gate で choppy 相場の偽 fire を抑制する) を保ちつつ、現状の「実用上 fire
> が一度しか出ない」状態を改善する妥協点を探る。
>
> **NOTE (2026-06-01, P2B brief 起草時の訂正)**: 上記の「spec §5.3」参照は
> **軸ずれ**。`fx_ugh_engine_v2.md §5.3` の `fire_probability` は
> `market_ugh_builder.py` の **signal feature** (`compute_e_raw` に入る別概念)
> であり、本 §4 が触る **state classifier の fire evidence**
> (`engine/state.py:98` `compute_state_evidence`) とは別物。Phase 2 が更新
> すべき spec は **`docs/specs/ugh_state_engine_v1.md`** (line ~33 fire
> evidence 記述 + ~39 softmax)。`fx_ugh_engine_v2.md §5.3` は触らない。
> 本訂正は §4.3 target.yaml / §4.4 検証 / §9 Phase 表にも反映済み。

### 4.3 `target.yaml`

```yaml
intent: "Sharpen state classifier discrimination: lower softmax_temperature default from 1.0 to 0.5 and relax fire's multiplicative gate to a weighted sum to make fire state operationally reachable. Extend report_window auto-detect to also stratify mixed engine_versions so the v2 → v2.1 bump is honored at all production callers."
change:
  # NOTE (2026-06-01, P2B brief 起草時): Phase 2 は P2A (report_window
  # engine_version auto-stratify、PR #108 merged) と P2B (engine sharpening
  # + bump) の 2 PR に分割済み。下記 target.yaml は P2B 用に読み替える:
  #   - report_window モジュールは P2A で完了 → P2B scope から除外
  #   - spec ファイルは ugh_state_engine_v1.md (state classifier fire) に訂正
  #     (fx_ugh_engine_v2.md §5.3 は market_ugh_builder の別 fire、触らない)
  #   - bump 対象 3 源: automation_models.py:22 / run_fx_daily_protocol.py:58
  #     (+ docstring:19) / fx-daily-protocol.yml:39。fx-analysis-pipeline.yml は
  #     reporting 専用で engine_version を持たない (当初の「workflow 2 つ」は誤り)
  primary_kind: feature  # state classifier 挙動を変えるため refactor ではない
  allowed_secondary_kinds: [test_update, doc_update]
  scope:
    modules:
      - ugh_quantamental.engine.state
      - ugh_quantamental.engine.state_models
      - ugh_quantamental.fx_protocol.forecasting
      - ugh_quantamental.fx_protocol.automation_models  # engine_version default を v2 → v2.1 に bump
      # - ugh_quantamental.fx_protocol.report_window  # → P2A (PR #108) で完了、P2B scope 外
    files:
      - docs/specs/ugh_state_engine_v1.md  # state classifier の fire evidence + softmax を更新 (§4.4 訂正)
      # - docs/specs/fx_ugh_engine_v2.md  # §5.3 は market_ugh_builder の別 fire、触らない
authorship:
  authors: [{identity: "claude-code-engine-review-2026-05"}]
api_surface:
  allow_changes:
    - fqn: "engine.state_models.StateConfig.softmax_temperature"  # default 変更
    - fqn: "fx_protocol.automation_models.FxDailyAutomationConfig.engine_version"  # default v2 → v2.1
    - fqn: "fx_protocol.report_window.stratify_observations_by_versions"  # auto-detect 挙動拡張 (§4.4)
constraints: []
```

### 4.4 検証

- **Replay**: 直近 60 サンプル (5/8-5/29) を新 config で replay し、
  dominant_state の遷移パターンが目的通り変化することを確認:
  - winner margin が 0.001-0.013 → 0.05+ に拡大
  - `fire` 観測が §11.2 の dual criterion を満たす:
    - **fire-event 日**: 1/15 → **3+/15** (engine が fire を出す "日" が増える)
    - **fire variant 記録**: 3/60 (=5%) → **10+/60** (=16%+) (sample × variant)
    - 両軸とも改善している必要があり、event-day 軸の伸びなしで variant-record
      軸だけ伸ばす loophole は不可。詳細 §11.2 参照。
- **既存 test の更新**: `tests/engine/test_state.py` の prob 数値 fixture を
  新 default で再生成。
- **Spec の整合性**: fire gate 緩和の数式を spec に反映。**訂正
  (2026-06-01)**: 更新先は `docs/specs/ugh_state_engine_v1.md` (state
  classifier の fire evidence ~line 33 + softmax ~line 39)。当初書いていた
  `fx_ugh_engine_v2.md §5.3` は `market_ugh_builder.fire_probability`
  (別概念) なので**触らない** (§4.2.2 NOTE 参照)。
- **`engine_version` の bump**: v2 → **v2.1**。`dominant_state` の出力が
  同一入力で変わるため、weekly / monthly pipeline で pre/post を分離する
  必要がある (詳細 §10)。
- **`stratify_observations_by_versions` の auto-detect 拡張** (`fx_protocol/
  report_window.py:84-94`): 現状 auto-detect は `theory_version` の混在
  しか分離しない。production callers (`analytics_rebuild.
  rebuild_analytics_and_weekly_report` @ `analytics_rebuild.py:166-171`、
  `monthly_review_exports.run_monthly_review_export` @ `monthly_review
  _exports.py:656-664`) は `engine_version_filter` を渡していないため、
  Phase 2 で v2 → v2.1 を bump しても **mid-month roll-out 時に v2 と v2.1
  の `dominant_state` が同じ weekly / monthly 報告バケットに混在**してしまう。
  本 Phase 2 PR で同関数の auto-detect 経路を **`engine_version` 混在も
  同様に latest 1 つに stratify する** よう拡張する (`theory_version` と
  同じパターン: `present = {row.get("engine_version", "") for row in rows} - {""}`
  → 複数なら latest を選択)。これにより以後のすべての bump phase
  (Phase 3 FLAT、Phase B range) で caller plumbing 変更なしに pre/post
  分離が機能する。
- **`stratify_observations_by_versions` 拡張の test**: 
  `tests/fx_protocol/test_report_window.py` に
  「mixed engine_version 行を渡すと latest 1 つに stratify される」
  fixture を追加し、auto-detect の対称性を assert。

## 5. P1 Fix #1 — FLAT Direction の epsilon 閾値

### 5.1 現状

`fx_protocol/forecasting.py:41-46`:

```python
def _direction_from_bp(change_bp: float) -> ForecastDirection:
    if change_bp > 0: return ForecastDirection.up
    if change_bp < 0: return ForecastDirection.down
    return ForecastDirection.flat  # change_bp == 0 でしか発火しない
```

UGH variants が `expected_close_change_bp = e_star × trailing_mean_abs ×
(0.5 + 0.5 × conviction)` で算出する値が浮動小数点的に 0.0 になることは
ほぼないため、FLAT は実質出ない。

5/26 (実現 -0.6 bp = 動かない日) で UGH 全 4 変種が +11〜+14 bp の UP を
出したのが症状。

### 5.2 提案

epsilon 閾値を **regime volatility に応じて動的にスケール**して導入:

```python
# ProjectionConfig に新 field として追加 (variant ごとに調整可能)
direction_flat_epsilon_ratio: float = 0.5  # 通常日想定振幅の何 % 以下を FLAT とみなすか
direction_flat_epsilon_floor_bp: float = 5.0  # trailing が極小の朝向けの最小閾値

def _direction_from_bp(
    change_bp: float,
    trailing_mean_abs_close_change_bp: float,
    config: ProjectionConfig,
) -> ForecastDirection:
    epsilon_bp = max(
        config.direction_flat_epsilon_ratio * trailing_mean_abs_close_change_bp,
        config.direction_flat_epsilon_floor_bp,
    )
    if change_bp > epsilon_bp:
        return ForecastDirection.up
    if change_bp < -epsilon_bp:
        return ForecastDirection.down
    return ForecastDirection.flat
```

**動的閾値の根拠**:

- trailing_mean_abs_close_change_bp は当該通貨ペアの「通常日の絶対値振幅」
  (= 20-30 bp が典型) を表し、regime によって変動する (低 volatility 期は
  10 bp 程度、event-driven 期は 50+ bp)。
- `ratio = 0.5` で「通常日振幅の半分以下を `FLAT`」とすると、低 vol 期は
  小幅な閾値、event-driven 期は大きめの閾値に自動追従。
- 静的な 5 bp だと **当文書の 5/26 サンプル (UGH 予測 +11〜+14 bp、実現
  -0.6 bp) で `|11| > 5` のため依然 UP を出してしまう**。動的閾値なら
  trailing ≈ 25 bp の通常期で epsilon ≈ 12.5 bp → +11 bp は FLAT、
  +14 bp は依然 UP、という variant 間の境界が現れる (§5.3 検証参照)。
- `floor_bp = 5.0` は trailing が極端に小さい朝 (warm-up 期間内) の
  divide-by-noise を防ぐ最低限の保証。

> ProjectionConfig 配置案を採るのは、variant ごとに ratio を差別化でき
> 「conservative variant (高 ratio = FLAT 出やすい)」と「aggressive variant
> (低 ratio = UP/DOWN 出やすい)」の探索が可能になるため。Phase 3
> 着手時に静的 hardcode (forecasting.py) か config 化かは spec author と
> 議論。

### 5.3 検証

- 60 サンプル replay で FLAT 観測回数を測定 (推定 5-10 件)。
- 5/26 (実現 -0.6 bp) で UGH **少なくとも一部の変種** (conservative ratio
  の alpha 等) が FLAT を出すことを確認 (+11 bp 程度の小幅予測変種が
  epsilon ≈ 12.5 bp 下回り FLAT 化、+14 bp 寄りの aggressive 変種は
  ratio を 0.6+ にしないと UP のままになりうる)。**全変種一律 FLAT を
  要求しない** — variant 間で direction signal が割れるのが本仕様の意図
  (variant exploration 趣旨と整合)。
- evaluation での FLAT 扱い: spec §9 / `evaluation_record` のスキーマ
  で FLAT 行を direction_hit としてどう扱うか規定 (既に flat 扱いはあるが
  集計挙動の確認)。
- **Spec `docs/specs/fx_ugh_engine_v2.md` の整合性**: 動的閾値
  (`direction_flat_epsilon_ratio` / `direction_flat_epsilon_floor_bp`)
  の数式と semantics、および evaluation §9 における FLAT 行の direction_hit
  集計挙動を spec に明文化する (§5.4 target.yaml の `scope.files` で
  spec を許可)。
- **`engine_version` の bump**: v2.1 → **v2.2**。`forecast_direction` が
  同一入力で変わる (UP/DOWN ↔ FLAT 境界) ため、Phase 3 を mid-month で
  roll-out すると pre/post の direction_hit が同じ v2.1 報告バケットに
  混在する。詳細 §10。

### 5.4 `target.yaml`

```yaml
intent: "Add epsilon threshold so UGH variants can emit FLAT direction when expected magnitude is small, restoring the no-opinion output capability."
change:
  primary_kind: feature
  allowed_secondary_kinds: [test_update, doc_update]
  scope:
    modules:
      - ugh_quantamental.fx_protocol.forecasting
      - ugh_quantamental.engine.projection_models  # ProjectionConfig に epsilon 設定を追加
      - ugh_quantamental.fx_protocol.automation_models  # engine_version default を v2.1 → v2.2 に bump
    files:
      - docs/specs/fx_ugh_engine_v2.md  # FLAT semantics (§5.2 提案の動的閾値) と evaluation §9 の FLAT 取扱いを反映 (§5.3)
api_surface:
  allow_changes:
    - fqn: "engine.projection_models.ProjectionConfig.direction_flat_epsilon_ratio"
    - fqn: "engine.projection_models.ProjectionConfig.direction_flat_epsilon_floor_bp"
    - fqn: "fx_protocol.automation_models.FxDailyAutomationConfig.engine_version"  # default v2.1 → v2.2
constraints: []
```

## 6. P1 Fix #2 — per-variant Scoreboard の集計整理

### 6.1 現状

`weekly_report_v2.md` / `slice_scoreboard.csv` 等で、variant 別に
`state_proxy_hit_count` / `range_hit_count` を計上している。

- **`range_hit_count`**: §3 で確認したとおり variant 非依存 (実装上
  `_build_range_from_baseline_context` が `baseline_context` のみから
  range を組み立て、ProjectionConfig を渡していない)。**真の意味で
  variant 共有**、4 重カウントが発生。
- **`state_proxy_hit_count` / `dominant_state`**: アーキテクチャ上は
  **variant 依存** (`run_state_engine` が variant ごとに走り、
  `compute_state_evidence` が `projection_result.conviction` /
  `e_star` / `urgency` / `mismatch_px` を入力に取る)。ただし**現状の
  observed 分散は極めて小さい** (例: 5/27 prob_dormant は variants 間で
  0.04% range、softmax T=1.0 + conviction の variant 差が小さいため)。
  Phase 2 sharpening (softmax T=0.5 + fire gate 緩和) **後は分散が
  exp 増幅されて variant disagreement が顕在化する**ことが見込まれる。

### 6.2 提案

per-batch (snapshot) で集計するメトリクス群と per-variant 集計するメト
リクス群を明確に分ける:

**集計ルールは Phase で変わる**:

| メトリクス | Phase A 期 (現状: range variant 共有) | Phase B 完了後 (range per-variant) | 理由 |
|---|---|---|---|
| `direction_hit_count` | per-variant | per-variant | direction は変種依存 |
| `close_error_bp` | per-variant | per-variant | exp_bp 変種依存 |
| `magnitude_error_bp` | per-variant | per-variant | exp_bp 依存 |
| `range_hit_count` | **per-batch** | **per-variant に戻す** | Phase A 期は range が完全共有なので per-batch、Phase B で variant 別 range が出るので per-variant に戻す |
| `state_proxy_hit_count` | **per-variant** | **per-variant** | architecture 上 variant 依存 (state engine が projection result を変種別に消費)。現状観測分散は低いが Phase 2 sharpening 後に増える見込み — 最初から per-variant 保持で disagreement を捨てない |
| `dominant_state` 分布 | **per-variant** | **per-variant** | 同上 |

> **state 系メトリクスを per-variant のままにする根拠**: Phase 2 で
> softmax_temperature を下げると、現状 ±0.06 にとどまる prob 分布の
> 偏差が exp で増幅され、変種間で dominant_state が flip するケースが
> 出ると想定される。その時に per-batch 集計だと alpha/beta/gamma/delta
> の state disagreement が "代表値で潰される" 形になり、まさに sharpening で
> 取りに行きたい情報量が失われる。empirical な分散の現状 (0.04%) ではなく
> architectural な variant 依存性に従って per-variant を維持する。
>
> `range_hit_count` を per-batch に集約するのは **Phase A 期の暫定
> ルール**。§3.2.2 Phase B で range が per-variant 化されたら、alpha / beta /
> gamma / delta の range disagreement が捨てられないよう **per-variant 集計
> に戻す**こと。Phase B 着手 PR で本表の更新も同梱する。

これにより:
- Phase A 完了時点で `weekly_strategy_metrics.csv` には UGH variant 4 行
  (alpha/beta/gamma/delta) に加えて新規 **`strategy_kind="ugh_v2_ensemble"`
  行**を 1 行追加し、`range_hit_count` / `range_hit_rate` は ensemble 行
  にのみ書き込み、4 つの variant 行では空文字列にする (`_compute_metrics_for_rows`
  が `range_evaluable == []` 時に既に空を返す挙動を再利用)。これにより
  variant 行のみを読む既存 BI / dashboard 利用者は 4× 重複ではなく欠損として
  扱える。
  - 具体的な実装 (`weekly_reports_v2.build_strategy_metrics`):
    1. variant 行構築時に `range_hit_count` / `range_hit_rate` を `""` で
       上書き
    2. **`forecast_batch_id` で v2 variant rows を deduplicate** してから
       `_compute_metrics_for_rows` を呼ぶ。`_compute_metrics_for_rows` は
       入力 row ごとに `range_hit` をカウントするため、4 variants × 5 days
       をそのまま渡すと 20 hits になってしまう (5/week が期待値)。
       dedupe 例:
       ```python
       seen_batches: set[str] = set()
       deduped: list[dict[str, str]] = []
       for r in ugh_v2_variant_rows:
           bid = r.get("forecast_batch_id", "")
           if bid and bid not in seen_batches:
               seen_batches.add(bid)
               deduped.append(r)
       # 抽出は range_hit_count / range_hit_rate のみ
       ensemble_metrics = _compute_metrics_for_rows(deduped)
       ```
       `forecast_batch_id` は 4 variants が完全に共有しているため
       (`labeled_observations.py:384`)、どの variant を残しても OK。
       `forecast_batch_id` が空文字列の legacy row は skip (warm-up
       期間想定)。
    3. 抽出値を持つ `strategy_kind="ugh_v2_ensemble"` 行 (他フィールドは
       空文字列) を append
  - `WEEKLY_STRATEGY_METRICS_FIELDNAMES` の **schema 変更は不要** (既存列
    のみ使用)。reader 側は `strategy_kind` の値で variant / ensemble を
    判別する。
- **slice metrics (`weekly_slice_metrics.csv`) も Phase A スコープに含める**。
  `build_slice_metrics` (`weekly_reports_v2.py:342-444`) は
  `(strategy_kind, label)` で grouping し各グループに `_compute_metrics_for_rows`
  を呼ぶため、現状各 slice 行が 4× インフレを伴う。Phase A 範囲で:
  - **regime_label / volatility_label / intervention_risk / event_tag** の
    各 `(slice_dimension, label)` について、4 variant rows に加えて
    `strategy_kind="ugh_v2_ensemble"` 行を 1 行追加 (label は variant 行と
    共通)。
  - variant 行では `range_hit_count` / `range_hit_rate` を `""` 化、
    ensemble 行は `(dim, label)` 配下の v2 variant rows を **同じく
    `forecast_batch_id` で dedupe** した上で `_compute_metrics_for_rows`
    に渡して計算する。Top-level と同じ dedupe pattern を再利用。
  - `WEEKLY_SLICE_METRICS_FIELDNAMES` の schema 変更も不要 (既存列のみ)。
  - `build_slice_metrics` 関数末尾で各 dimension のループ後に
    ensemble 行を `result.append(...)` する形になる。
- monthly review の "regime / volatility / intervention" slice (`monthly_review.py`
  の集計) も同じ ensemble 行パターン (forecast_batch_id dedupe 付き) で
  Phase A 内で揃える。Phase A の P0 stop-loss の達成基準は
  「weekly + monthly のすべての range_hit 系メトリクスが 4× インフレなし」
  であって、weekly top-level だけでは不十分。
- **`ugh_v2_ensemble` を UGH-class strategy として `is_ugh_kind` に
  認識させる** (`fx_protocol/models.py:71-85`)。**理由**: `monthly_review.
  compute_monthly_baseline_comparisons` (`monthly_review.py:217`) が
  `if is_ugh_kind(sk): continue` で UGH を baseline 比較から除外する設計
  のため、`ugh_v2_ensemble` を認識させないと「ensemble 行 vs random_walk」
  のような無意味な比較 delta 行が monthly report に混入する。
  - 実装:
    ```python
    # fx_protocol/models.py
    UGH_V2_ENSEMBLE_KIND: str = "ugh_v2_ensemble"

    def is_ugh_kind(kind: StrategyKind | str) -> bool:
        ...
        if isinstance(kind, str):
            return (
                kind == StrategyKind.ugh.value
                or kind in {k.value for k in _UGH_V2_STRATEGY_KINDS}
                or kind == UGH_V2_ENSEMBLE_KIND  # 追加
            )
    ```
  - **UGH-only filter (`is_ugh_kind` を使った行抽出) で double-count を
    避ける**: `monthly_review.py` には `ugh_rows = [r for r in obs if is_ugh_kind(...)]`
    パターンが複数 (L274/327/363/369/498) ある。ensemble 行は集計結果なので
    raw observation には現れず `labeled_observations.csv` 由来の行列に
    `ugh_v2_ensemble` が混入することはない (生 observation は 4 variants
    だけ)。よって既存 filter は `is_ugh_kind` 更新後も double-count しない。
    一方で `strategy_metrics` (集計済み) を iterate する箇所では
    ensemble 行も「UGH-class」として扱われ、baseline 比較から正しく
    除外される (これが目的)。

### 6.3 検証

- 既存 test fixture の更新 (集計数の変化、ensemble 行の存在を assert)。
- `weekly_report.md` の出力例で `ugh_v2_ensemble: range_hit_count=5/5`
  のような形になることを目視確認 (variant 行は `range_hit_count=""`
  になる)。**5/5 (週 5 営業日 × 1 batch/日)** が正しい値であり、20/20 や
  5/20 にならないことを確認 (dedupe が効いているテスト)。
- `weekly_slice_metrics.csv` の各 `(slice_dimension, label)` について
  ensemble 行が存在し、`range_hit_count` 分母が変種数 (4) ぶん inflate
  していないことを assert。
- `monthly_review.py` 集計の同等エクスポートも同じ ensemble 行を持ち、
  かつ `compute_monthly_baseline_comparisons` の出力に
  `strategy_kind="ugh_v2_ensemble"` の delta 行が **混入しない** ことを
  assert (`is_ugh_kind` 認識でスキップ済み)。

### 6.4 `target.yaml`

P0 Fix #1 Phase A と同じスコープで併合可能。または別 PR でも OK。

## 7. P2 — conviction の二重役割の spec 明文化

### 7.1 現状

`compute_conviction` の数式 (`projection.py:157-166`) は仕様通り動作している
ことを 5/8/26/27/29 の 4 サンプルで検算済み (implied evidence_confidence
≈ 0.92-0.99 で安定)。ただし:

1. **意味的に**: conviction は「prediction reliability (予測の信頼性)」で
   あって「signal strength (シグナルの強さ)」ではない。
2. **役割上**: `expected_close_change_bp` の magnitude scaler としても使われる
   (`forecasting.py:302-305`)。
3. **命名上**: 「conviction」という単語は強気/弱気のニュアンスを持つため
   誤解を招く。

### 7.2 提案 (実装変更なし、spec 改訂のみ)

`docs/specs/fx_ugh_engine_v2.md` §6 に以下を追記:

> **`conviction` の意味**: 本 engine における `conviction` は **prediction
> reliability** (= e_star を信用してよい度合い) を意味する。`fire` 状態の
> 信号強度とは別軸の独立な指標であり、両者は逆相関しうる (例: 5/8 fire +
> conviction=0.37)。
>
> **`conviction` の使用箇所**: (1) ProjectionEngineResult のフィールドとして
> downstream に渡される、(2) `expected_close_change_bp = e_star × trailing
> _mean_abs × (0.5 + 0.5 × conviction)` で magnitude scaler としても使われ
> る (PR #87 由来)。2 つの役割を持つ理由は "現状の reliability スコアは
> realized-volatility との掛け合わせで実用 magnitude として機能する" と
> いう経験則による。将来的に分離する場合は spec を更新。

### 7.3 検証

doc-only change、コード影響なし、`semantic-ci check` の `primary_kind:
docs` (該当する kind がなければ refactor + allow_changes 空) で通る想定。

## 8. P2 — dormant State ↔ Magnitude の整合性ルール

### 8.1 現状

5/27 dormant + exp_bp = +21 bp (週内最大値)、5/29 dormant + exp_bp = +6 bp
(小さい) の二例で、dormant でも magnitude が大きく出るケースがある。
spec §7 で `dominant_state → expected_close_change_bp` の damping rule が
明示されていない。

### 8.2 提案 (議論ベース、実装変更なし)

選択肢 (議論待ち):

- **Option A**: `dormant` 状態のとき expected_close_change_bp を multiplier
  で減衰させる (例: 0.5 倍)。実装は `forecasting.py:302-305` の 1 行追加。
- **Option B**: 現状維持。state と magnitude は decoupled 情報として運用、
  売買 system 側で state ベースのポジションサイジングを実装。
- **Option C**: state を bp ではなく conviction の補助 modifier として
  使う (= state が dormant なら conviction を別途下げる)。

### 8.3 検証

実装決定後に別 phase で着手。本書では選択肢の整理に留める。

## 9. Phase 化と着手順序

| Phase | 内容 | 想定 PR 数 | 依存 |
|---|---|---|---|
| **Phase 1 (P0 短期止血)** | §3.2.1 (range_hit 集計修正) + §6 (scoreboard 整理) | 1-2 | なし、即着手可 |
| **Phase 2 (P0 sharpening)** | §4 (softmax + fire gate)、spec 改訂 (`ugh_state_engine_v1.md`) | **2** (P2A: report_window auto-detect = PR #108 merged / P2B: engine sharpening + v2.1 bump) | engine_version v2 → **v2.1** bump、replay 必要 |
| **Phase 3 (P1)** | §5 (FLAT epsilon → v2.1 → **v2.2**)、§3.2.2 (range の per-variant 化 → v2.2 → **v2.3**) | 2 | Phase 2 後、各 sub-PR で個別 bump |
| **Phase 4 (P2)** | §7 spec 改訂、§8 議論 | 1 | いつでも |

**Phase 1 から着手**を推奨。これだけで range_hit の解釈が正されるので、
6 月の data accumulation が始まる前にメトリクスを修正できる。

## 10. semantic-ci の運用パターン

各 Phase で:

1. branch off main: `claude/engine-review-phase{N}-<topic>`
2. spec 改訂が必要なら同 PR に含める
3. `target.yaml` を本書記載のテンプレートから組む
4. 実装 → `ruff check . && pytest -q`
5. `semantic-ci check --baseline-rev main --candidate-rev HEAD ...` で gate
   - Phase 1 (`primary_kind: refactor`): 全 4 constraints satisfied 期待
   - Phase 2 (`primary_kind: feature`): `effects_unchanged` 違反は expected (state engine 内部に新ロジック追加)
6. PR description で satisfied / flagged-as-expected を明記

**`engine_version` の bump タイミング**: 出力されるラベル
(`forecast_direction` / `dominant_state` / `expected_range`) のいずれかが
**同一入力に対して異なる結果になる Phase は、`engine_version` を bump
する**。

| Phase | 出力ラベル変化 | bump 必要か |
|---|---|---|
| Phase 1 (§3 集計修正、§6 scoreboard) | なし (forecast.csv 不変、集計層のみ) | ❌ v2 維持 |
| Phase 2 (§4 state sharpening) | `dominant_state` 変化 | ✅ v2 → **v2.1** |
| Phase 3 (§5 FLAT epsilon) | `forecast_direction` 変化 (UP/DOWN ↔ FLAT 境界) | ✅ v2.1 → **v2.2** |
| Phase 3 (§3.2.2 range per-variant) | `expected_range_low/high` 変化 | ✅ v2.2 → **v2.3** (Phase 3 を 2 PR に分けるなら別々に bump) |
| Phase 4 (§7 spec 明文化) | なし (doc のみ) | ❌ |

**理由**: `fx_protocol/report_window.stratify_observations_by_versions` の
auto-detect は **本書 Phase 2 着手前は `theory_version` の混在しか分離せず**、
`engine_version` は明示的に指定された場合のみ filter していた。production
callers (`analytics_rebuild.rebuild_analytics_and_weekly_report`、
`monthly_review_exports.run_monthly_review_export`) は `engine_version_filter`
を渡していないため、bump しても pre/post が同じ報告バケットに混在する
リスクがあった。

**Phase 2 の付帯改修 (§4.3 / §4.4)**: 本書では Phase 2 PR 内で
`stratify_observations_by_versions` の auto-detect を `engine_version`
にも拡張する (`theory_version` と対称な実装、latest 1 つに stratify)。
これにより**以後のすべての bump phase (Phase 3 FLAT、Phase B range) で
caller plumbing 変更なしに pre/post 分離が機能する**。Phase 3 以降の
target.yaml に `report_window` を再掲する必要はない。

**代替案 (もし auto-detect 拡張をやらない選択をする場合)**: weekly /
monthly pipeline の caller (`analytics_rebuild` / `monthly_review_exports`)
側で `engine_version_filter` を明示的に渡すよう改修するか、roll-out 日を
月初に固定して切り出すこと。本書のデフォルト推奨は**Phase 2 で
auto-detect を拡張し、以後の毎フェーズで bump のみ**。

`schema_version` (CSV 列スキーマ) は本書のスコープ内で不変、v1 維持。

## 11. Acceptance Criteria

### 11.1 Ship criteria (operational gate)

- [ ] `ruff check .` clean
- [ ] `pytest -q` 1344 passing (各 Phase で fixture 更新は許容)
- [ ] `semantic-ci check` の API surface constraints satisfied
- [ ] 既存の forecast.csv / outcome.csv / evaluation.csv 列スキーマ不変
- [ ] `data/csv/observability/` の publisher 経路で error 0

### 11.2 Knowledge criteria (the actual goal)

- [ ] 6/1 以降の weekly report で `range_hit_count` が **1/day** ベースに修正
      されている (`5/week` の表示になる)
- [ ] state classifier の dominant_state 遷移で winner margin が 0.05+
      観測される頻度が 50% を超える (現状 0%)
- [ ] 60 サンプル (= 5/8-5/29 期間の 15 営業日 × 4 変種) replay で `fire` 観測
      が **以下のいずれも満たす**:
  - **fire-event 日**: 1/15 → **3+/15** に増加 (engine が `fire` を出す
    "日" が他にもあることが確認できる、event-day ベース)
  - **fire variant 記録**: 3/60 (=5%) → **10+/60** (=16%+) に増加
    (§1 と整合する sample × variant 基準、変種が独立に fire 判定する)

  > **重要**: 単独の変種が同じ fire-event 日に追加で fire しただけで target
  > を満たしてしまう loophole を避けるため、**event-day 軸 + variant-record
  > 軸の両方**を criterion とする。両方満たして初めて「fire が実用領域に
  > 入った」と判定する。
- [ ] FLAT direction が「動かない日」で観測される。5/26 type の日 (実現
      -0.6 bp、UGH 変種予測 +11〜+14 bp) で **少なくとも 1 変種** が FLAT
      を出す (動的閾値 `0.5 × trailing ≈ 12.5 bp` で +11 bp 変種 → FLAT、
      +14 bp 変種 → UP のままになるのは仕様通り — §5.3 参照)。**全変種
      一律 FLAT は要求しない** (variant exploration 趣旨で direction
      disagreement が出るのが正常)。

### 11.3 Out of scope (deferred、本書では触らない)

- conviction の reliability と magnitude scaler の分離 (§7、議論待ち)
- dormant ↔ magnitude の整合性ルール (§8、選択肢の整理のみ)
- engine_version v3 への移行検討
- 売買システム本体の構築 (本書はその前提条件整備)

## 12. Open Questions

1. **§4 fire gate の数式**: spec §5.3 の "fire_probability redefinition"
   の意図 (多重ゲートで偽 fire 抑制) を保ったまま、§11.2 の dual criterion
   (**fire-event 日 1/15 → 3+/15** かつ **fire variant 記録 3/60 → 10+/60**、
   詳細は §11.2 参照) を満たす balanced 数式は何か？単純な weighted-sum
   化だと 1 event-day 上の variant fire 数だけが増えて event-day 軸が
   伸びないリスクがある (round 4 で指摘された loophole 経路と同じ)。  
   → Phase 2 着手前に spec author と相談、replay で両軸の改善を確認。
2. **§3.2.2 range の per-variant 化**: `build_projection_snapshot` が既に
   range を計算しているのに forecasting.py が baseline_context から別途
   計算している重複の経緯は？  
   → blame で経緯を確認、unify するか別系で残すか決定。
3. **§5 epsilon の動的閾値パラメータ**: §5.2 提案では
   `direction_flat_epsilon_ratio = 0.5` (通常日振幅の半分以下を FLAT) と
   `direction_flat_epsilon_floor_bp = 5.0` (trailing 極小時の最低保証) を
   暫定値とした。5/26 サンプル (UGH +11〜+14 bp / trailing ≈ 25 bp で
   epsilon ≈ 12.5 bp) を想定すると ratio 0.5 で **一部変種のみ FLAT** に
   落ちる挙動になる。variant 探索趣旨から direction disagreement は
   許容するが、`ratio` を 0.3 / 0.5 / 0.7 のどこに置くかで「FLAT 頻度」が
   大きく変わる。  
   → 60 サンプル replay で各 ratio 候補の FLAT 観測率 (目安 5-10/60)
   と direction_hit 影響をスイープし、§11.2 acceptance を満たす最小値を
   採用する。
4. **engine_version bump の影響範囲**: v2 → v2.1 (Phase 2) → v2.2
   (Phase 3 FLAT epsilon) → v2.3 (Phase 3 range per-variant) が
   weekly / monthly pipeline で正しく分離されることを確認。**§10 / §4.3
   / §4.4 の方針として、Phase 2 PR 内で `stratify_observations_by_versions`
   の auto-detect を `engine_version` にも拡張する** ため、production
   caller (`analytics_rebuild` / `monthly_review_exports`) 側の
   `engine_version_filter` plumbing 改修は **不要** (Phase 3/B の
   target.yaml でも `report_window` を再掲する必要はない)。  
   → Phase 2 着手前に、auto-detect 拡張で latest 1 つに stratify される
   挙動が weekly + monthly の両 pipeline でテストされていることを
   確認する (`tests/fx_protocol/test_report_window.py` の新 fixture)。
   spec §7.5 の文言も `theory_version` 同様 `engine_version` でも
   auto-detect が走るよう更新する。

---

## Appendix A. 月末レビューで使った観測データの出所

| データ | コミット | 日時 (UTC) |
|---|---|---|
| 5/8 v2 first run | `4a1b313` | 2026-05-08 06:55 |
| 5/8 v2 late retry | `2ed570c` | 2026-05-08 12:06 |
| 5/11 outcome of 5/8 forecast | `59c8c77` | 2026-05-11 13:42 |
| 5/26 setup state | `b481783` | 2026-05-26 13:51 |
| 5/27 dormant state shift | `6a4cc6a` | 2026-05-27 14:23 |
| 5/29 conviction drop | `41c6ae9` | 2026-05-29 13:54 |
| Weekly report 5/11-5/15 | `2506e93` | 2026-05-18 05:02 |
| Weekly report 5/18-5/22 | `8269446` | 2026-05-25 05:15 |

## Appendix B. コード裏取りの根拠ファイル

| 観察 | 該当コード |
|---|---|
| expected_range が variant 共有 | `fx_protocol/forecasting.py:53-55, 314-317` |
| `_direction_from_bp` が epsilon なし | `fx_protocol/forecasting.py:41-46` |
| conviction = ec × align × (1 - 0.5·pen) | `engine/projection.py:157-166` |
| conviction が magnitude scaler | `fx_protocol/forecasting.py:302-305` |
| state evidence の multiplicative gating | `engine/state.py:65-117` |
| softmax_temperature default = 1.0 | `engine/state_models.py:29` |
| 変種別 ProjectionConfig 適用箇所 | `fx_protocol/forecasting.py:185-216, 230-266` |
