# Task Brief: FX-ANNOT-LIVE - ライブ週次の regime/volatility アノテーション復旧

## Phase
engine_review_2026_06 §1 ★4 (enabler) — 着手順序 §2 で最優先。
関連 spec: `docs/specs/fx_ai_weekly_annotation_v1.md` (Status: Implementing),
`docs/specs/fx_annotation_analytics_v1.md`,
`docs/specs/fx_weekly_annotation_resilience_v1.md`.

## Goal
ライブ運用の週次レポートが 4 週連続 28/28 unannotated になっている原因を特定し、
**API 鍵に依存しない決定論的ルールベースの regime / volatility アノテーター**を
fallback として追加して、daily/weekly のスライス分析が常に populate される状態に
する。`fx_ai_weekly_annotation_v1` の「AI-first・人手不要」の設計意図と、CI 実測
(0 件) の乖離を埋める。

## Acceptance Criteria
- [ ] `csv/analytics/weekly/<latest>/weekly_annotation_coverage.csv` の effective
      coverage が regime_label / volatility_label について > 0 になる
      (テストデータ経由で検証可能なこと)
- [ ] 28/28 unannotated の**実際の root cause を live path で特定**する
      (API 鍵不在を前提にしない)。daily 経路 `run_annotation_analytics`
      (`analytics_annotations.py:551`, automation.py:567 から呼出) は Step A で
      `ai_annotation_suggestions.csv` を生成するが、Step C の
      `build_labeled_observations` (同 :593) にそれを渡していない (suggestions が
      effective label に昇格しない)。weekly 経路 `rebuild_weekly_report`
      (`analytics_rebuild.py:120`) は `run_ai_annotation_pass` (:85) 経由。
      この配線ギャップを特定し是正する
- [ ] **end-to-end テスト**: live rebuild 経路 (`rebuild_weekly_report`) と daily
      経路 (`run_annotation_analytics`) を通して、labeled_observations と
      `weekly_annotation_coverage.csv` の effective coverage が実際に populate
      されることを assert する (単体で `ai_annotations.py` だけ叩いて pass し、
      live artifact は 28/28 のまま、という抜けを禁止)
- [ ] **slice eligibility まで assert する**。coverage CSV と label 充填だけでは
      不十分: `weekly_reports_v2.build_slice_metrics` は `annotation_source !=
      none` の行のみ annotated 扱い (weekly_reports_v2.py:368)、月次
      regime/volatility slice は `annotation_status == "confirmed"` の行のみ
      集計 (monthly_review.py:307-310)。したがって fallback 行は適切な
      **provenance (`annotation_source`) と status (`annotation_status=confirmed`
      相当)** を持たねばならず、テストは weekly slice 行が `label=all` に潰れない
      こと・月次 (GOV) slice が空でないことを直接 assert する
- [ ] **daily AI suggestion の語彙を共有軸に正規化**。`generate_ai_annotations`
      は中間ヒット率で `ai_regime_label="mixed"` を出す (analytics_annotations.py:190-194)。
      AI は fallback より precedence が上なので、Step A suggestions を
      `build_labeled_observations` に配線すると "mixed" という第3バケットが
      混入し axes-mismatch を再導入する。AI suggestion 経路を共有語彙
      (trending/choppy, low/normal/high) に正規化 (または mixed→既定軸へ map) し、
      共有語彙に対するテストを置く
- [ ] fallback アノテーターは realized OHLC のみから regime (trending/choppy) と
      volatility (low/normal/high) を導出する純関数で、network/file I/O/乱数なし
- [ ] ⚠️ **performance leakage の除去 (循環ラベルの禁止)**。現状 live AI/default
      経路は regime を UGH `direction_hit` から、volatility を `close_error_bp`
      から導出している (`analytics_annotations.py:186-194`,
      `ai_annotations.py:85-94`)。これは「choppy = モデルが外した日」という
      **定義上の循環**で、regime 別分析が市場レジームではなくモデル成績の再エン
      コードになる (★3 GOV フラグの前提自体を無効化)。AI は fallback より
      precedence が上なので OHLC fallback も上書きされる。よって **AI/default 経路の
      ラベル導出そのものを OHLC/市場由来に是正する** (precedence 順
      `ai > auto > manual` は変更しない — AI を fallback の下に下げる案は採らない。
      それは resolve_effective_label の順序と「fallback は欠落フィールドのみ補完」
      という本 brief の要件に矛盾するため)。テストで `direction_hit` /
      `close_error_bp` 等の performance フィールドがラベルを決定しないことを
      assert する
- [ ] 既存の AI / auto / manual アノテーションが存在する場合は現行の
      AI-first precedence (`annotation_sources.py`: **ai > auto > manual**) を
      尊重し、rule-based fallback はそれら**全てが欠落しているフィールドのみ**を
      埋める (上位ソースを上書きしない)
- [ ] 新規テストが `pytest -q` で pass、`ruff check .` clean

## Scope
- IN: `src/ugh_quantamental/fx_protocol/ai_annotations.py`,
  `annotation_sources.py`, `analytics_annotations.py`
  (`run_annotation_analytics` の Step A→C 配線), `analytics_rebuild.py`
  (`rebuild_weekly_report` / `run_ai_annotation_pass`),
  `labeled_observations.py` (`build_labeled_observations`),
  `annotation_coverage.py`, `annotation_models.py`,
  `weekly_reports_v2.py` (`build_slice_metrics` の `annotation_source` ゲート確認),
  `monthly_review.py` (regime/vol slice の `annotation_status==confirmed` ゲート確認),
  対応する `tests/fx_protocol/` テスト, 必要なら
  `docs/specs/fx_ai_weekly_annotation_v1.md` の Status / fallback 節更新
- OUT: engine 関数 (`projection.py`/`state.py`)、protocol schemas
  (ForecastRecord/OutcomeRecord/EvaluationRecord)、persistence schema / Alembic、
  GitHub Actions workflow ロジック、daily automation のフォーキャスト経路、
  baseline 戦略

## Allowed Dependencies (optional)
なし。新規依存が必要と判断したら AGENTS.md §3 escalation。

## Implementation Hints (optional)
- root cause は API 鍵不在ではなく **配線**。`run_ai_annotation_pass`
  (`ai_annotations.py:176`) は決定論的 (API 不要) なのに、daily 経路は生成した
  suggestions を `build_labeled_observations` に渡さず effective label に昇格
  しない。まず `run_annotation_analytics` (Step A→C) と `rebuild_weekly_report`
  の両経路を読み、どこで suggestions が labeled_observations / coverage に
  到達せず落ちているかを実行確認すること。Scope は `automation.py` の
  forecast 経路には触れず、annotation analytics のみ。
- fallback の regime/volatility 判定はルールベースで十分: 例として連続同方向
  本数や close 変化の符号一貫性で trending/choppy、true range や
  `trailing_mean_abs_close_change_bp` 比で low/normal/high。閾値は
  module-level 定数として明示し easily-changeable に (monthly_review.py の
  THRESHOLD_* 定数の前例に倣う)。
- source precedence は `annotation_sources.py` の既存ロジック
  (`resolve_*`: **ai > auto > manual**、docstring L3-6 / L44) を崩さない。
  rule-based fallback は manual の**下**に位置する新たな最下位ティアとして、
  ai/auto/manual いずれも値を持たないフィールドのみを埋める。stale な manual
  互換ラベルが AI ラベルを上書きする逆転 (AI-first 設計の破壊) を起こさないこと。
- §2 の通り本 brief は FX-GOV-REGIME-FLAGS (★3) と FX-MAG/STATE 検証の前提。
  **共有語彙コントラクト**: fallback も AI suggestion 経路
  (`generate_ai_annotations`) も、出力 enum を monthly review のレジーム軸
  (trending/choppy, low/normal/high) と**完全一致**させること。現状 AI 経路は
  `mixed` を出すため、これを正規化しないと AI>fallback precedence 経由で第3
  バケットが slice に漏れる (axes-mismatch は PR #104 型 churn の主因)。
- **provenance / status の付与**: fallback が埋めた行は weekly の
  `annotation_source` (≠ none) と月次の `annotation_status` (confirmed 相当) の
  両ゲートを通る値を持たせる。どちらか一方だけだと「coverage は緑だが slice は
  label=all / 空」になる。

## Required Outputs
- Branch name: `codex/fx-annot-live`
- PR title: `feat(fx_protocol): deterministic regime/volatility annotation fallback`
- Expected files changed: `ai_annotations.py` or new
  `annotation_fallback.py`, `annotation_sources.py`,
  `analytics_annotations.py`, `tests/fx_protocol/test_*annotation*.py`,
  spec doc
- Required tests: fallback 発火 (配線経由)、precedence 非上書き、
  純関数 determinism (同 OHLC → 同ラベル)、E2E で coverage > 0 **かつ** weekly
  slice が `label=all` に潰れない・月次 slice が空でない、AI suggestion 語彙が
  共有軸 (mixed 非混入)

## Done When
- All acceptance criteria are checked
- `ruff check .` passes
- `pytest -q` passes
- PR body starts with a Completion Summary
