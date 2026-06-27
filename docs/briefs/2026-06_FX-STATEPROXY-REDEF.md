# Task Brief: FX-STATEPROXY-REDEF - state_proxy_hit の再定義 (持続性→正しさ)

## Phase
engine_review_2026_06 §1 ★2' — engine_version 非依存の eval メトリクス変更。
着手順序 §2 で独立、いつでも着手可。

## Goal
`state_proxy_hit` が「本日の dominant_state == 翌日の forecast dominant_state」
という**状態の持続性**を測っており、状態が変化する (最も情報価値の高い) 局面で
必ず 0 になる現状を是正する。6月は state率が週ごと 0↔100 で振動し、方向 100% の
週ですら 0% という、向きが逆の KPI になっている。realized outcome から導く実現
状態に対する一致へ再定義するか、最低でも「持続性指標」と明示して精度指標として
扱うのをやめる。

## Acceptance Criteria
- [ ] `state_proxy_hit` の判定基準が文書化され、現行の「翌日 forecast state との
      一致 = 持続性」である旨が spec に明記される
- [ ] 次のいずれかが実装される: (A) realized OHLC 由来の実現状態ラベルに対する
      一致へ再定義、または (B) 現メトリクスを `state_persistence_hit` 等へ改名し
      持続性指標と明示した上で、別途「正しさ」指標を追加。どちらを採るかは
      実装前に Open Question として PR に明記し判断を仰ぐ
- [ ] **in-place 再定義の禁止 (semantics 混在防止)**。Option A を採る場合でも、
      同一 CSV 列 / 永続 JSON フィールド `state_proxy_hit` に旧 (persistence) と
      新 (correctness) の両意味が混在させてはならない。現状 report 経路は
      `state_proxy_hit` を直接集計し theory/engine version でのみ stratify する
      (eval-metric semantics では区別しない) ため、rollout を跨ぐ週次/月次窓が
      汚染される。よって **(i) 列 rename / 新メトリクス追加 (実質 Option B; 推奨)**、
      または **(ii) schema/protocol version bump + 集計時 filtering** のいずれかを。
      ※ (ii) を採る場合、`schema_version`/`protocol_version` は現状 3 箇所で `v1`
      既定 (`automation_models.py:23-24` / `fx-daily-protocol.yml:40-41` /
      `scripts/run_fx_daily_protocol.py:59-60`) なので、filtering が機能するには
      これら default + テストを sync する必要がある (engine_version と同じ
      3 箇所 sync パターン)。sync 漏れだと live/manual run が引き続き `v1` を出し
      新旧 semantics が混在する。sync まで担保できないなら (i) を採ること
      必須とする
- [ ] CSV schema (evaluation / weekly / monthly の state_proxy_* 列) を変更する
      場合、producer・reader・spec・テストの全 occurrence を grep sync
      (axes-mismatch 防止)
- [ ] baseline 戦略の評価 (state_proxy_hit = None) は不変
- [ ] 既存テストは意図した変化のみ更新、`pytest -q` / `ruff check .` clean

## Scope
- IN: `src/ugh_quantamental/fx_protocol/outcomes.py`
  (`build_evaluation_record` の state_proxy 判定, realized_state_proxy 取得),
  `outcome_models.py` / 関連 schema (列名変更時),
  `csv_exports.py` (CSV 列), 週次/月次集計の該当箇所,
  `docs/specs/fx_daily_outcome_evaluation_workflow_v1.md`,
  `tests/fx_protocol/test_outcomes*.py`
- OUT: engine state 算出ロジック (state.py)、forecast magnitude/range、
  persistence ORM 列の物理変更 (もし ORM 列追加が必要なら Alembic とペア +
  escalation 検討)、baseline 評価

## Allowed Dependencies (optional)
なし。

## Implementation Hints (optional)
- 現状 (outcomes.py:253-255):
  `state_proxy_hit = forecast.dominant_state.value == realized_state_proxy`;
  `realized_state_proxy` は翌日バッチの UGH forecast の dominant_state
  (outcomes.py:341-351)。これは実現値ではなく「翌日のモデル出力」なので、
  安定レジームで 100% (state が動かない)、遷移日に 0% になる。
- 案 (A): realized OHLC から実現状態プロキシを導く純関数を用意し、それと比較。
  ⚠️ **語彙の制約**: `state_proxy_hit` は `forecast.dominant_state.value`
  (= `LifecycleState`: dormant/setup/fire/expansion/exhaustion/failure,
  `schemas/enums.py:25-33`) と比較するため、realized ラベルも**必ず
  LifecycleState 語彙**で導出すること。FX-ANNOT-LIVE の regime/volatility 軸
  (trending/choppy, low/normal/high) とは**別物**で、それを流用すると metric が
  systematically false / semantically invalid になる (両者の enum を揃えてはな
  らない)。regime/vol ベースの正しさを測りたい場合は state_proxy とは独立した
  別メトリクスとして定義する。
- CSV 列名は permanent foot-gun。`state_proxy_hit_count` / `state_proxy_hit_rate`
  を rename する場合は monthly/weekly の両 exporter と spec を必ず同時更新。
- engine_version には触れない (forecast ロジック不変、eval メトリクスのみ)。

## Required Outputs
- Branch name: `codex/fx-stateproxy-redef`
- PR title: `refactor(fx_protocol): redefine state_proxy_hit as realized-state correctness`
- Expected files changed: `outcomes.py`, `outcome_models.py`, `csv_exports.py`,
  週次/月次集計, spec, `tests/fx_protocol/`
- Required tests: 遷移日に「正しさ」が persistence と乖離するケース、baseline=None
  不変、CSV 列の整合

## Done When
- All acceptance criteria are checked
- `ruff check .` passes
- `pytest -q` passes
- PR body starts with a Completion Summary
