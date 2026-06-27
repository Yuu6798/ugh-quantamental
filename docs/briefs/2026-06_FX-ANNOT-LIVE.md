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
- [ ] 既存 AI アノテーション経路 (`ai_annotations.py`) が 0 件になる条件
      (例: `ANTHROPIC_API_KEY` 不在) を特定し、その場合に決定論的 fallback が
      発火することを単体テストで保証
- [ ] fallback アノテーターは realized OHLC のみから regime (trending/choppy) と
      volatility (low/normal/high) を導出する純関数で、network/file I/O/乱数なし
- [ ] 既存の AI / auto / manual アノテーションが存在する場合は現行の
      AI-first precedence (`annotation_sources.py`: **ai > auto > manual**) を
      尊重し、rule-based fallback はそれら**全てが欠落しているフィールドのみ**を
      埋める (上位ソースを上書きしない)
- [ ] 新規テストが `pytest -q` で pass、`ruff check .` clean

## Scope
- IN: `src/ugh_quantamental/fx_protocol/ai_annotations.py`,
  `annotation_sources.py`, `analytics_annotations.py`,
  `annotation_coverage.py`, `annotation_models.py`,
  対応する `tests/fx_protocol/` テスト, 必要なら
  `docs/specs/fx_ai_weekly_annotation_v1.md` の Status / fallback 節更新
- OUT: engine 関数 (`projection.py`/`state.py`)、protocol schemas
  (ForecastRecord/OutcomeRecord/EvaluationRecord)、persistence schema / Alembic、
  GitHub Actions workflow ロジック、daily automation のフォーキャスト経路、
  baseline 戦略

## Allowed Dependencies (optional)
なし。新規依存が必要と判断したら AGENTS.md §3 escalation。

## Implementation Hints (optional)
- まず CI の `fx-analysis-pipeline` / weekly 実行で `ai_annotations` が 0 件に
  なる経路を grep + 実行確認 (API 鍵 secret 不在が最有力。`build_notification`
  系は `anthropic` を best-effort import している前例あり)。
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
  fallback ラベルの enum 値は monthly review のレジーム軸 (trending/choppy,
  low/normal/high) と**完全一致**させること (axes-mismatch は PR #104 型 churn)。

## Required Outputs
- Branch name: `codex/fx-annot-live`
- PR title: `feat(fx_protocol): deterministic regime/volatility annotation fallback`
- Expected files changed: `ai_annotations.py` or new
  `annotation_fallback.py`, `annotation_sources.py`,
  `analytics_annotations.py`, `tests/fx_protocol/test_*annotation*.py`,
  spec doc
- Required tests: API 鍵不在時の fallback 発火、precedence 非上書き、
  純関数 determinism (同 OHLC → 同ラベル)、coverage > 0

## Done When
- All acceptance criteria are checked
- `ruff check .` passes
- `pytest -q` passes
- PR body starts with a Completion Summary
